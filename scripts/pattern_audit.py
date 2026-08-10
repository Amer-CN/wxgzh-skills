#!/usr/bin/env python3
"""
pattern_audit.py — zh-human-writing v1 模式审计脚本

检测文本中的 AI 模式，按模式级别输出检测结果。
不自动修改文本，不输出 AI 概率，不输出质量分。

用法:
    python pattern_audit.py --text TEXT.txt [OPTIONS]

选项:
    --text PATH            待检测文本文件路径（必需）
    --profile NAME         文体场景（essay/technical/social，默认 essay）
    --check-level LEVEL    检测范围（hard_residue_only/full，默认 hard_residue_only）
    --output FORMAT        输出格式（json/text，默认 json）
    --help                 显示帮助

退出码:
    0 — pass（无 hard-residue）
    2 — fail（有 hard-residue）
    3 — 错误（文件不存在、编码错误、参数错误）
"""

import argparse
import json
import re
import sys
from pathlib import Path

# 档72C-6/任务4:统计检测层(任务书 §4,管道先行,指标待 §4 注入)。
# 显式把本脚本目录加入 sys.path:CLI 直跑与 tests/run_tests.py 的
# importlib 直载两种场景都能解析同目录的 stat_audit 模块。
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import stat_audit

try:
    import yaml
except ImportError:
    # 档72C-2/OBS-219:配置真源化后 PyYAML 为硬依赖;缺依赖=退出 3,不兜底。
    print("错误: 缺少 PyYAML 依赖,无法读取配置 (pip install pyyaml)", file=sys.stderr)
    sys.exit(3)


class _P(argparse.ArgumentParser):
    """档72C-3/OBS-234:argparse 错误统一退出码 3(exit 2 已被 hard-residue/fail 占用)。"""
    def error(self, message):
        sys.stderr.write(f"argument error: {message}\n")
        sys.exit(3)


def read_file(path):
    """读取文件，处理编码错误。"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f'错误: 文件不存在: {path}', file=sys.stderr)
        sys.exit(3)
    except UnicodeDecodeError:
        print(f'错误: 文件编码错误（请使用 UTF-8）: {path}', file=sys.stderr)
        sys.exit(3)
    except Exception as e:
        print(f'错误: 读取文件失败: {path}: {e}', file=sys.stderr)
        sys.exit(3)


def split_paragraphs(text):
    """按空行分段。"""
    paras = re.split(r'\n\s*\n', text)
    return [p.strip() for p in paras if p.strip()]


def split_sentences(text):
    """按句号、问号、叹号分句。"""
    sentences = re.split(r'(?<=[。！？!?])', text)
    return [s.strip() for s in sentences if s.strip()]


# ============================================================
# hard-residue 检测
# ============================================================

HARD_RESIDUE_PATTERNS = [
    {
        'id': 'HR-001',
        'name': '模板占位符',
        # 档72E-1:补 <...> 变体(72C-1 M-2a 遗留;mask_non_prose 已屏蔽 HTML 标签,
        # 检测跑在屏蔽后文本上,不误伤真 HTML)。
        'patterns': [r'\{\{[^}]+\}\}', r'\[INSERT[^\]]*\]', r'\[待填\]', r'<[^>\n]{1,40}>'],
        'language_origin': 'language_general',
    },
    {
        'id': 'HR-002',
        'name': 'AI自我标识',
        'patterns': [r'作为AI', r'作为一个人工智能', r'我是一个AI', r'作为语言模型', r'作为一款AI'],
        'language_origin': 'language_general',
    },
    {
        'id': 'HR-003',
        'name': '知识截止声明',
        'patterns': [r'截至我的知识', r'截至我所知', r'我的知识截止', r'根据我的训练数据'],
        'language_origin': 'language_general',
    },
    {
        'id': 'HR-004',
        'name': '聊天助手残留',
        'patterns': [r'请问还有什么可以帮助', r'还有什么我可以帮助', r'如果您有其他问题', r'还有什么我可以为您',
                     r'希望这对你有帮助', r'如果还有其他问题', r'请随时告诉我'],
        'language_origin': 'language_general',
    },
    {
        'id': 'HR-005',
        'name': 'AI来源参数泄露',
        'patterns': [r'model=gpt', r'temperature=', r'top_p=', r'max_tokens='],
        'language_origin': 'language_general',
    },
    {
        # 档72C-2/§3(任务书 §3.1):元话语路标由 strong-contextual 移入 hard-residue,
        # 新 id HR-007,命中即 exit 2(0C 基线三词零命中,行为不受影响)。
        'id': 'HR-007',
        'name': '元话语路标',
        'patterns': [r'先说结论', r'说白了', r'说穿了'],
        'language_origin': 'chinese_specific',
    },
]


# ============================================================
# 屏蔽层与保护区（档72C-3/§2,任务书 §7）
# ============================================================

def mask_non_prose(text):
    """等长屏蔽五类非散文内容(保持字符偏移,location 依赖偏移)。

    1. YAML frontmatter(文件开头 --- 到下一个 ---)
    2. 围栏代码块(``` 与 ~~~ 变体)
    3. 行内代码(单反引号成对)
    4. Markdown 链接 URL 与裸 URL(https?://\S+)
    5. HTML 标签及标签内内容(<tag ...>...</tag> 与自闭合标签)
    """
    spans = []
    m = re.match(r'^---\r?\n', text)
    if m:
        end = text.find('\n---', m.end())
        if end != -1:
            spans.append((0, end + 4))
    for pat in (r'```.*?```', r'~~~.*?~~~'):
        spans.extend(x.span() for x in re.finditer(pat, text, re.S))
    spans.extend(x.span() for x in re.finditer(r'`[^`\n]+`', text))
    spans.extend(x.span(1) for x in re.finditer(r'\]\((https?://[^)\s]+)\)', text))
    spans.extend(x.span() for x in re.finditer(r'https?://[^\s)\]>]+', text))
    for x in re.finditer(r'<([a-zA-Z][a-zA-Z0-9]*)(\s[^>]*)?>', text):
        tag = x.group(1)
        if x.group(0).endswith('/>'):
            spans.append((x.start(), x.end()))
            continue
        close = re.search(r'</' + re.escape(tag) + r'\s*>', text[x.end():], re.I)
        spans.append((x.start(), x.end() + close.end() if close else x.end()))
    spans.sort()
    merged = []
    for s, e in spans:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    chars = list(text)
    for s, e in merged:
        for i in range(s, min(e, len(chars))):
            chars[i] = ' '
    return ''.join(chars)


def _protected_spans(text):
    """用户显式保护区:[[protected]]...[[/protected]] 与 <!--keep-->...<!--/keep-->。"""
    spans = []
    for pat in (r'\[\[protected\]\].*?\[\[/protected\]\]',
                r'<!--keep-->.*?<!--/keep-->'):
        spans.extend(x.span() for x in re.finditer(pat, text, re.S))
    return spans


def _para_spans(text):
    """与 split_paragraphs 同口径的段落切分,附带 (para, start, end) 偏移。"""
    spans = []
    pos = 0
    for part in re.split(r'(\n\s*\n)', text):
        if re.fullmatch(r'\n\s*\n', part):
            pos += len(part)
            continue
        stripped = part.strip()
        if not stripped:
            pos += len(part)
            continue
        start = pos + part.index(stripped)
        spans.append((stripped, start, start + len(stripped)))
        pos += len(part)
    return spans


def _sent_spans(para):
    """与 split_sentences 同口径的句切分,附带 (sent, start, end) 偏移。"""
    spans = []
    pos = 0
    for part in re.split(r'(?<=[。！？!?])', para):
        stripped = part.strip()
        if stripped:
            start = pos + part.index(stripped)
            spans.append((stripped, start, start + len(stripped)))
        pos += len(part)
    return spans


_GROUP_META = {
    'hard_residue': {'severity': 'audit', 'action': 'mark',
                     'suggestion': '删除或替换该片段',
                     'reason': '单次出现即可判定为AI残留'},
    'strong_contextual': {'severity': 'strong', 'action': 'suggest',
                          'suggestion': '结合上下文复核;确为无信息填充则改写或删除',
                          'reason': '聚集出现时需结合上下文判断'},
    'advisory_only': {'severity': 'advisory', 'action': 'suggest',
                      'suggestion': '仅提示,不自动修改',
                      'reason': '真人写作中也常见,仅作建议'},
}


def _excerpt(original, start, limit=100):
    seg = original[start:start + limit]
    return seg + ('…' if len(original) - start > limit else '')


def _finding(group, profile, pattern_def, location, span, original, protected,
             confidence='high', cluster_count=None, cluster_threshold=None,
             reason=None, suggestion=None, context_note=None):
    """构造十字段 finding(档72C-3/§1);命中保护区 → action 强制 review_only。"""
    start, end = span
    action = _GROUP_META[group]['action']
    if any(s <= start < e or s < end <= e for s, e in protected):
        action = 'review_only'
    f = {
        'rule_id': pattern_def['id'],
        'group': group,
        'severity': _GROUP_META[group]['severity'],
        'confidence': confidence,
        'profile': profile,
        'action': action,
        'location': location,
        'span_text': _excerpt(original, start),
        'reason': reason or f"{pattern_def['name']}:{_GROUP_META[group]['reason']}",
        'suggestion': suggestion or _GROUP_META[group]['suggestion'],
        'language_origin': pattern_def['language_origin'],
    }
    if cluster_count is not None:
        f['cluster_count'] = cluster_count
        f['cluster_threshold'] = cluster_threshold
    if context_note:
        f['context_note'] = context_note
    return f


def detect_hard_residue(masked, original, profile, protected):
    """检测 hard-residue 模式。单次出现即报告(屏蔽层后文本,span_text 取原文)。"""
    findings = []
    for para_idx, (para, pstart, pend) in enumerate(_para_spans(masked)):
        for sent_idx, (sent, sstart, send) in enumerate(_sent_spans(para)):
            for pattern_def in HARD_RESIDUE_PATTERNS:
                for pat in pattern_def['patterns']:
                    for m in re.finditer(pat, sent):
                        findings.append(_finding(
                            'hard_residue', profile, pattern_def,
                            f'第{para_idx+1}段第{sent_idx+1}句',
                            (pstart + sstart, pstart + send), original, protected))
    return findings


# ============================================================
# strong-contextual 检测
# ============================================================

STRONG_CONTEXTUAL_PATTERNS = [
    {
        'id': 'SC-001',
        'name': '无信息开场',
        'patterns': [r'让我们来看看', r'在当今.{0,10}的时代', r'随着.{0,10}的发展'],
        'thresholds': {'essay': 2, 'technical': 3, 'social': 2},  # 档72C-2:文档逐条声明
        'language_origin': 'language_general',
    },
    {
        'id': 'SC-002',
        'name': '无信息导航',
        'patterns': [r'接下来我们将', r'下面我们来看', r'首先.{0,20}其次.{0,20}最后'],
        'thresholds': {'essay': 2, 'technical': 3, 'social': 2},  # 档72C-2
        'language_origin': 'language_general',
    },
    {
        'id': 'SC-003',
        'name': '无信息总结',
        'patterns': [r'总而言之', r'综上所述', r'总结来说', r'通过以上分析可以看出'],
        'thresholds': {'essay': 2, 'technical': 3, 'social': 2},  # 档72C-2
        'language_origin': 'language_general',
    },
    {
        'id': 'SC-004',
        'name': '无来源权威铺垫',
        'patterns': [r'研究表明', r'数据显示', r'据统计'],
        'thresholds': {'essay': 2, 'technical': 2, 'social': 2},  # 档72C-2:三档均正常
        'language_origin': 'language_general',
    },
    {
        'id': 'SC-005',
        'name': '连续同构结构',  # 档72E-1/OBS-227:语义重写为句式同构(见专用块)
        'patterns': [],  # 需要特殊检测逻辑
        # 档72E-1/OBS-227:检测同段落内句式骨架相同的句子聚集(功能词/标点
        # 保留、内容占位 X、数字占位 N);分句不跨段落、取消只比紧邻前句、
        # 每句只归属一个同构簇消除双重计数。详见专用块实现。
        'thresholds': {'essay': 3, 'technical': 3, 'social': 3},  # 档72C-2:文档三档均正常
        'language_origin': 'language_general',
    },
    {
        'id': 'SC-006',
        'name': '明显假互动',
        'patterns': [r'你可能会问', r'你想想看', r'你有没有想过'],
        'thresholds': {'essay': 2, 'technical': 2, 'social': 4},  # 档72C-2:social ×2.0
        'language_origin': 'language_general',
    },
    {
        'id': 'SC-007a',
        'name': '伪对比结构',
        'patterns': [
            r'不在于[^。！？\n]{1,60}而在于',
            r'与其说[^。！？\n]{1,60}(?:不如|毋宁|倒不如)',
            r'表面(?:上)?[^。！？\n]{1,60}(?:其实|实际|实则)',
            r'看似[^。！？\n]{1,60}(?:其实|实际|实则)',
            r'[。！？!?]\s*而是',
        ],
        # 档72C-2/§4:阈值改 1(单次命中即 strong),并补第 5 条正则。
        'thresholds': {'essay': 1, 'technical': 1, 'social': 1},
        'language_origin': 'chinese_specific',
    },
    {
        # 档72C-4/§2:抒情聚集——同段 AO-014 命中 >=2 时额外产出一条 strong,
        # confidence=low。patterns 为空,走下方专用块(同 SC-005 模式);
        # 阈值由 config pattern_thresholds.SC-011 注入。
        'id': 'SC-011',
        'name': '抒情聚集',
        'patterns': [],
        'language_origin': 'chinese_specific',
    },
]

# 档72B-2R OBS-228/R111:模块加载期结构断言——thresholds 必须显式包含
# 全部 profile 且为 >=1 整数;缺键即报错,禁止 or 兜底/静默默认(fail-open)。
_PROFILES = ('essay', 'technical', 'social')

# 档72B-2F OBS-229:按 id 索引的查找表——SC-005 的 patterns 为空数组,
# 主循环会 continue 跳过,专用检测块必须从这里取同一个 thresholds 真源。

def load_config(config_path=None):
    """读取配置;缺失/yaml 错/schema 错 → 打印错误并 sys.exit(3),无兜底(R111)。"""
    path = (Path(config_path) if config_path
            else Path(__file__).resolve().parents[1] / 'config' / 'default.yaml')
    try:
        text = path.read_text(encoding='utf-8')
    except OSError as exc:
        print(f'错误: 配置文件读取失败: {path}: {exc}', file=sys.stderr)
        sys.exit(3)
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        print(f'错误: 配置文件 YAML 解析失败: {path}: {exc}', file=sys.stderr)
        sys.exit(3)
    if not isinstance(data, dict) or not isinstance(data.get('pattern_thresholds'), dict):
        print('错误: 配置必须包含 pattern_thresholds 段', file=sys.stderr)
        sys.exit(3)
    return data


def _validate_thresholds():
    """模块加载期结构断言:每个 strong 规则 thresholds 三 profile 齐备且 >=1 整数。"""
    for _r in STRONG_CONTEXTUAL_PATTERNS:
        _t = _r.get('thresholds')
        if not isinstance(_t, dict) or any(p not in _t for p in _PROFILES):
            print(f"错误: {_r.get('id')}: thresholds 必须显式包含 essay/technical/social",
                  file=sys.stderr)
            sys.exit(3)
        if any(not isinstance(_t[p], int) or _t[p] < 1 for p in _PROFILES):
            print(f"错误: {_r.get('id')}: thresholds 值必须为 >=1 的整数", file=sys.stderr)
            sys.exit(3)


def _apply_pattern_thresholds(config):
    """把 config.pattern_thresholds 注入 STRONG_CONTEXTUAL_PATTERNS(单一真源,R111)。"""
    pt = config['pattern_thresholds']
    missing = [r['id'] for r in STRONG_CONTEXTUAL_PATTERNS if r['id'] not in pt]
    if missing:
        print(f'错误: 配置 pattern_thresholds 缺失规则: {missing}', file=sys.stderr)
        sys.exit(3)
    for rule in STRONG_CONTEXTUAL_PATTERNS:
        rule['thresholds'] = dict(pt[rule['id']])
    _validate_thresholds()


# 模块加载即注入默认配置;缺文件/错 schema 直接 exit 3,不存在内置兜底。
_apply_pattern_thresholds(load_config())

# 档72B-2F OBS-229:按 id 索引的查找表——SC-005 的 patterns 为空数组,
# 主循环会 continue 跳过,专用检测块必须从这里取同一个 thresholds 真源。
_SC_BY_ID = {_r['id']: _r for _r in STRONG_CONTEXTUAL_PATTERNS}

# 档72C-2/§5d(任务书 §2 硬要求):翻案腔判定的上下文提示,SC-007a/SC-007b 命中时携带。
_CONTEXT_NOTE = (
    "该结构是否为翻案腔,取决于前半句是否被前文或材料真实建立;"
    "若只是正常分类或澄清,应忽略。")



def detect_strong_contextual(masked, original, profile, protected):
    """检测 strong-contextual 模式。聚集时才报告(屏蔽层后文本,span_text 取原文)。"""
    findings = []
    paragraphs = _para_spans(masked)

    for para_idx, (para, pstart, pend) in enumerate(paragraphs):
        for pattern_def in STRONG_CONTEXTUAL_PATTERNS:
            if not pattern_def['patterns']:
                # 仅 SC-005 走下方专用块(同一 thresholds 真源,见 _SC_BY_ID)。
                continue

            count = 0
            for pat in pattern_def['patterns']:
                count += len(re.findall(pat, para))

            # 档72B-2R OBS-228/R111:直接下标,缺键即 KeyError,不许兜底。
            threshold = pattern_def['thresholds'][profile]

            if count >= threshold:
                first_span = None
                first_si = 0
                for sent_idx, (sent, sstart, send) in enumerate(_sent_spans(para)):
                    if any(re.search(pat, sent) for pat in pattern_def['patterns']):
                        first_span = (pstart + sstart, pstart + send)
                        first_si = sent_idx
                        break
                confidence = 'medium' if pattern_def['id'] == 'SC-007a' else 'high'
                reason = f"{pattern_def['name']}:同段聚集{count}次,达到阈值{threshold}"
                findings.append(_finding(
                    'strong_contextual', profile, pattern_def,
                    f'第{para_idx+1}段第{first_si+1}句', first_span,
                    original, protected, confidence=confidence,
                    cluster_count=count, cluster_threshold=threshold,
                    reason=reason,
                    context_note=_CONTEXT_NOTE if pattern_def['id'] == 'SC-007a' else None))

    # 检测句式同构聚集（SC-005,档72E-1/OBS-227 语义重写:量对对象=句式骨架,
    # 非句长;分句不跨段落;取消只比紧邻前句;每句只归属一个同构簇,消除双重计数。
    # 骨架=功能词与标点原样保留、内容字符占位 X、数字占位 N;同骨架句=同构。
    # 阈值与其余 SC 规则共用同一 thresholds 真源(档72B-2F/OBS-229)。
    sc005_def = _SC_BY_ID['SC-005']
    sc005_threshold = sc005_def['thresholds'][profile]
    _SC005_FUNC_WORDS = ("随着", "通过", "对于", "关于", "为了", "除了", "无论", "尽管",
                        "虽然", "但是", "因为", "所以", "如果", "那么", "不仅", "而且",
                        "并且", "然而", "于是", "因此", "其实", "不过", "当然", "后来",
                        "当时", "然后", "没有", "不是", "而是", "就是", "还是", "还有",
                        "以及", "或者", "只是", "可是")
    _SC005_FUNC_CHARS = set("的了是在把被就也都还又但而和与或这那从向对为以按比")
    for para_idx, (para, pstart, pend) in enumerate(paragraphs):
        candidates = []
        for sent, sstart, send in _sent_spans(para):
            skel = []
            i = 0
            n = len(sent)
            while i < n:
                matched = False
                for w in _SC005_FUNC_WORDS:
                    if sent.startswith(w, i):
                        skel.append(w)
                        i += len(w)
                        matched = True
                        break
                if matched:
                    continue
                ch = sent[i]
                if ch in _SC005_FUNC_CHARS or ch in "，。！？；：、,.;:!?":
                    skel.append(ch)
                elif ch.isdigit():
                    if not skel or skel[-1] != "N":
                        skel.append("N")
                else:
                    if not skel or skel[-1] != "X":
                        skel.append("X")
                i += 1
            skeleton = "".join(skel)
            if skeleton.count("X") == len(skeleton) and "X" in skeleton:
                continue  # 无功能词/标点的句子没有句式结构特征,不参与同构
            candidates.append((sent, sstart, send, skeleton))
        clusters = []
        for sent, sstart, send, skel in candidates:
            for cl in clusters:
                if cl[0] == skel:
                    cl[1].append((sent, sstart, send))
                    break
            else:
                clusters.append((skel, [(sent, sstart, send)]))
        for skel, members in clusters:
            if len(members) >= sc005_threshold:
                first, last = members[0], members[-1]
                span = (pstart + first[1], pstart + last[2])
                reason = f"{sc005_def['name']}:{len(members)}句句式同构聚集"
                findings.append(_finding(
                    'strong_contextual', profile, sc005_def,
                    f'第{para_idx+1}段第{first[1]+1}句', span,
                    original, protected,
                    cluster_count=len(members), cluster_threshold=sc005_threshold,
                    reason=reason,
                    suggestion='复核是否真为模板化句式;修辞排比应保留'))

    # 档72C-2/§5:SC-007b 升级机制——同一段落内 AO-001(不是…而是 / 并非…而是)
    # 命中 >= 2 时升级为 strong finding(confidence=low);单发只留 advisory。
    ao001 = next((r for r in ADVISORY_ONLY_PATTERNS if r.get('id') == 'AO-001'), None)
    if ao001 is not None:
        ao_pats = ao001.get('patterns') or [ao001['pattern']]
        for para_idx, (para, pstart, pend) in enumerate(paragraphs):
            ao_count = sum(len(re.findall(pat, para)) for pat in ao_pats)
            if ao_count >= 2:
                first_span = None
                first_si = 0
                for sent_idx, (sent, sstart, send) in enumerate(_sent_spans(para)):
                    if any(re.search(pat, sent) for pat in ao_pats):
                        first_span = (pstart + sstart, pstart + send)
                        first_si = sent_idx
                        break
                sc007b_def = {'id': 'SC-007b',
                              'name': '不是…而是…(低置信升级)',
                              'language_origin': 'language_general'}
                findings.append(_finding(
                    'strong_contextual', profile, sc007b_def,
                    f'第{para_idx+1}段第{first_si+1}句', first_span,
                    original, protected, confidence='low',
                    cluster_count=ao_count, cluster_threshold=2,
                    reason=f'同段AO-001聚集{ao_count}次,低置信升级',
                    suggestion='判断前半句是否被前文真实建立;仅正常分类/澄清则忽略',
                    context_note=_CONTEXT_NOTE))

    # 档72C-4/§2:SC-011 抒情聚集——同一段落内 AO-014(抒情词)命中 >= 阈值时
    # 额外产出一条 strong finding(confidence=low);阈值来自 config 的 SC-011 行。
    ao014 = next((r for r in ADVISORY_ONLY_PATTERNS if r.get('id') == 'AO-014'), None)
    sc011_def = _SC_BY_ID.get('SC-011')
    if ao014 is not None and sc011_def is not None:
        sc011_threshold = sc011_def['thresholds'][profile]
        ao14_pats = ao014.get('patterns') or [ao014['pattern']]
        for para_idx, (para, pstart, pend) in enumerate(paragraphs):
            ao14_count = sum(len(re.findall(pat, para)) for pat in ao14_pats)
            if ao14_count >= sc011_threshold:
                first_span = None
                first_si = 0
                for sent_idx, (sent, sstart, send) in enumerate(_sent_spans(para)):
                    if any(re.search(pat, sent) for pat in ao14_pats):
                        first_span = (pstart + sstart, pstart + send)
                        first_si = sent_idx
                        break
                findings.append(_finding(
                    'strong_contextual', profile, sc011_def,
                    f'第{para_idx+1}段第{first_si+1}句', first_span,
                    original, protected, confidence='low',
                    cluster_count=ao14_count, cluster_threshold=sc011_threshold,
                    reason=f'同段抒情词聚集{ao14_count}次,达到阈值{sc011_threshold}',
                    suggestion='复核是否确为矫饰抒情;承载真实感受的保留'))

    return findings


# ============================================================
# advisory-only 检测
# ============================================================

ADVISORY_ONLY_PATTERNS = [
    # 档72B-2 OBS-177/3-3:原地扩宽(不进 strong_contextual,ME-010 继续绿);
    # 可选「并」前缀 + 中间 0~90 字(不跨句),置信度排序不再倒置。
    # 档72C-2/§5:patterns 列表承载两条正则;同段命中 >=2 升级 SC-007b(见
    # detect_strong_contextual),单发只留 advisory。AO-001 不再用单数 pattern 键。
    {'id': 'AO-001', 'name': '不是…而是…',
     'patterns': [r'(?:并)?不是[^。！？\n]{0,90}而是',
                  r'并非[^。！？\n]{0,90}而是'],
     'language_origin': 'language_general'},
    {'id': 'AO-002', 'name': '先…再…', 'pattern': r'先.{0,20}再', 'language_origin': 'language_general'},
    {'id': 'AO-003', 'name': '从…到…', 'pattern': r'从.{0,20}到', 'language_origin': 'language_general'},
    {'id': 'AO-004', 'name': '破折号', 'pattern': r'——', 'language_origin': 'chinese_specific'},
    # 档72E-1:补「不是吗？」独立变体(72C-1 M-2a 遗留)。
    {'id': 'AO-006', 'name': '反问', 'pattern': r'(?:难道.{0,20}[吗呢？?])|(?:不是吗？)', 'language_origin': 'language_general'},
    {'id': 'AO-007', 'name': '二人称', 'pattern': r'你', 'language_origin': 'language_general'},
    {'id': 'AO-011', 'name': '第一人称', 'pattern': r'[我]', 'language_origin': 'language_general'},
]


# 档72C-6/任务3:按段落聚合输出的人称规则(只改聚合方式)。
_AO_PER_PARAGRAPH_IDS = {'AO-007', 'AO-011'}


# ============================================================
# 检测词表加载（档72C-4/§1,OBS-233 闭合）
# ============================================================

# 词表 → 规则映射:SC-009/SC-010 进 strong,AO-013/AO-014 进 advisory。
# SC-011 是 AO-014 的聚集升级(专用块),无词表条目。
_LEXICON_RULES = {
    'SC-009': {'name': '绝对黑话', 'key': 'absolute_jargon', 'group': 'strong'},   # 27 词
    'SC-010': {'name': '模型路标', 'key': 'model_signposts', 'group': 'strong'},  # 6 词
    'AO-013': {'name': '语境黑话', 'key': 'contextual_jargon', 'group': 'advisory'},  # 14 词
    'AO-014': {'name': '抒情词', 'key': 'lyrical', 'group': 'advisory'},  # 12 词
}

# 「还有一层」按前缀模式(任务书 §3.5 注):后接实际内容才命中,单独成句不命中。
_MODEL_SIGNPOST_PREFIX = {'还有一层': r'还有一层[^。！？!?\n]'}


def _lexicon_patterns(words):
    """词表条目 → 正则列表;普通词 re.escape,前缀词走专用模式。"""
    out = []
    for word in words:
        if not isinstance(word, str) or not word:
            raise ValueError(f'词表条目必须为非空字符串: {word!r}')
        if word in _MODEL_SIGNPOST_PREFIX:
            out.append(_MODEL_SIGNPOST_PREFIX[word])
        else:
            out.append(re.escape(word))
    return out


def load_lexicon(lexicon_path=None):
    """读取检测词表;缺失/yaml 错/schema 不合 → 打印错误并 sys.exit(3),无兜底(R111)。"""
    path = (Path(lexicon_path) if lexicon_path
            else Path(__file__).resolve().parents[1] / 'references' / 'lexicon-deai.yaml')
    try:
        text = path.read_text(encoding='utf-8')
    except OSError as exc:
        print(f'错误: 词表文件读取失败: {path}: {exc}', file=sys.stderr)
        sys.exit(3)
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        print(f'错误: 词表 YAML 解析失败: {path}: {exc}', file=sys.stderr)
        sys.exit(3)
    if not isinstance(data, dict):
        print('错误: 词表顶层必须为对象', file=sys.stderr)
        sys.exit(3)
    for rid, meta in _LEXICON_RULES.items():
        words = data.get(meta['key'])
        if not isinstance(words, list) or not words:
            print(f'错误: 词表缺少非空列表 {meta["key"]}(规则 {rid})', file=sys.stderr)
            sys.exit(3)
    return data


def _apply_lexicon(data):
    """把词表注入 STRONG_CONTEXTUAL_PATTERNS / ADVISORY_ONLY_PATTERNS(单一真源)。"""
    for rid, meta in _LEXICON_RULES.items():
        pats = _lexicon_patterns(data[meta['key']])
        entry = {'id': rid, 'name': meta['name'], 'patterns': pats,
                 'language_origin': 'chinese_specific'}
        if meta['group'] == 'strong':
            STRONG_CONTEXTUAL_PATTERNS[:] = [
                r for r in STRONG_CONTEXTUAL_PATTERNS if r['id'] != rid]
            STRONG_CONTEXTUAL_PATTERNS.append(entry)
        else:
            ADVISORY_ONLY_PATTERNS[:] = [
                r for r in ADVISORY_ONLY_PATTERNS if r['id'] != rid]
            ADVISORY_ONLY_PATTERNS.append(entry)
    # 词表注入后重建查找表(SC-009 供 AO-013 长词优先去重引用)。
    global _SC_BY_ID
    _SC_BY_ID = {_r['id']: _r for _r in STRONG_CONTEXTUAL_PATTERNS}


# 模块加载即注入词表(默认路径);--lexicon 覆盖时 main() 里重注入。
_apply_lexicon(load_lexicon())
# 词表注入后再应用配置阈值(SC-009/010/011 阈值只在 config;R111 无兜底),
# 并重跑结构断言(覆盖词表规则)。
_apply_pattern_thresholds(load_config())

# 档72C-4/§3-2:strong 输出的高/低置信分组(按规则归属,非按 confidence 字段值;
# SC-007a 的 confidence 字段为 medium 但按指令归入 high 桶)。
_SC_HIGH_IDS = {'SC-001', 'SC-002', 'SC-003', 'SC-004', 'SC-005', 'SC-006',
                'SC-007a', 'SC-009', 'SC-010'}
_SC_LOW_IDS = {'SC-007b', 'SC-011'}


def detect_advisory_only(masked, original, profile, protected):
    """检测 advisory-only 模式。只列出，不影响 pass/fail。
    档72C-6/任务3:AO-007/AO-011 按段落聚合——每段产出一条 finding,
    occurrence_count 记录该段内命中次数, span_text 取该段首次命中处;
    其余 AO 规则逐次命中各产出一条。只改聚合方式,不改检测逻辑/级别/退出码。"""
    findings = []
    for para_idx, (para, pstart, pend) in enumerate(_para_spans(masked)):
        for pattern_def in ADVISORY_ONLY_PATTERNS:
            # 档72C-2:AO-001 用 patterns 列表(双正则),其余用单数 pattern 键。
            pats = pattern_def.get('patterns') or [pattern_def['pattern']]

            # 档72C-6/任务3:人称规则按段落聚合输出,避免单篇数十条同规则
            # finding 把真信号埋掉(0C 的 AO-007=22 即此类)。
            if pattern_def['id'] in _AO_PER_PARAGRAPH_IDS:
                total = 0
                first_si, first_span = 0, None
                for sent_idx, (sent, sstart, send) in enumerate(_sent_spans(para)):
                    cnt = sum(len(re.findall(pat, sent)) for pat in pats)
                    if cnt:
                        total += cnt
                        if first_span is None:
                            first_si, first_span = sent_idx, (pstart + sstart, pstart + send)
                if total:
                    f = _finding(
                        'advisory_only', profile, pattern_def,
                        f'第{para_idx+1}段第{first_si+1}句',
                        first_span, original, protected,
                        confidence='medium')
                    f['occurrence_count'] = total
                    findings.append(f)
                continue

            for sent_idx, (sent, sstart, send) in enumerate(_sent_spans(para)):
                matches = []
                for pat in pats:
                    matches.extend(re.finditer(pat, sent))
                # 档72C-4/§1:长词优先——AO-013 命中若落在 SC-009 已命中区间内
                # (如「闭环」被「商业闭环」覆盖)则跳过,不重复计数。
                if pattern_def['id'] == 'AO-013':
                    sc009 = _SC_BY_ID.get('SC-009')
                    sc009_spans = []
                    if sc009:
                        for sp in sc009.get('patterns') or []:
                            sc009_spans.extend(x.span() for x in re.finditer(sp, sent))
                    matches = [m for m in matches
                              if not any(s < m.end() and m.start() < e
                                         for s, e in sc009_spans)]
                for m in matches:
                    findings.append(_finding(
                        'advisory_only', profile, pattern_def,
                        f'第{para_idx+1}段第{sent_idx+1}句',
                        (pstart + sstart, pstart + send), original, protected,
                        confidence='medium'))

    return findings


# ============================================================
# 主函数
# ============================================================

def main():
    parser = _P(
        description='zh-human-writing v1 模式审计脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
退出码:
    0 — pass（无 hard-residue）
    2 — fail（有 hard-residue）
    3 — 错误

注意: strong-contextual 和 advisory-only 不影响 pass/fail。
'''
    )
    parser.add_argument('--text', required=True, help='待检测文本文件路径')
    parser.add_argument('--profile', default='essay', choices=['essay', 'technical', 'social'], help='文体场景')
    parser.add_argument('--check-level', default='hard_residue_only',
                        choices=['hard_residue_only', 'full'],
                        help='检测范围（hard_residue_only 只检测 hard-residue；full 检测全部级别）')
    parser.add_argument('--output', default='json', choices=['json', 'text'], help='输出格式')
    parser.add_argument('--config', default=None, help='配置文件路径(默认 config/default.yaml)')
    parser.add_argument('--lexicon', default=None, help='检测词表路径(默认 references/lexicon-deai.yaml)')
    # 档72C-4/§3-1(任务书 §3.1 后半句):preserve 策略下 HR-007 只标记不判 fail。
    parser.add_argument('--strategy', default='balance',
                        choices=['preserve', 'balance', 'rebuild'], help='编辑策略')

    args = parser.parse_args()
    # 档72C-2/§7:显式 --config 覆盖默认配置;错误路径在 load_config/_apply 内 exit 3。
    if args.config:
        _apply_pattern_thresholds(load_config(args.config))
    # 档72C-4/§1:显式 --lexicon 覆盖默认词表;错误路径在 load_lexicon 内 exit 3。
    if args.lexicon:
        _apply_lexicon(load_lexicon(args.lexicon))
        # 词表重注入后阈值必须一并重注入(SC-009/010/011 阈值只在 config),
        # 否则新注入的条目无 thresholds → 运行时 KeyError。
        _apply_pattern_thresholds(load_config(args.config))

    text = read_file(args.text)

    # 检测
    # 档72C-3/§2:所有检测前先等长屏蔽非散文;span_text 取自原文(不取自 masked)。
    masked = mask_non_prose(text)
    protected = _protected_spans(text)
    hr_findings = detect_hard_residue(masked, text, args.profile, protected)
    sc_findings = []
    ao_findings = []

    if args.check_level == 'full':
        sc_findings = detect_strong_contextual(masked, text, args.profile, protected)
        ao_findings = detect_advisory_only(masked, text, args.profile, protected)

    # 档72C-6/任务4:统计检测层(full 与 hard_residue_only 均计算——统计层
    # 只读不判:命中只进 statistical 段,不参与 pass_fail/退出码;--config 覆盖时走同一 fail-closed 加载)。
    stat_findings = stat_audit.run_stat_audit(masked, text, args.profile, args.config)

    # pass/fail 只由 hard-residue 决定
    # 档72C-4/§3-1(任务书 §3.1 例外):退出码判定——HR-001~006 任何策略下均 fail;
    # HR-007 仅 strategy=preserve 时只标记不判 fail(仍出现在 items 里)。
    hr_non007 = [f for f in hr_findings if f['rule_id'] != 'HR-007']
    has_hr007 = any(f['rule_id'] == 'HR-007' for f in hr_findings)
    exit_code = 2 if (hr_non007 or (has_hr007 and args.strategy != 'preserve')) else 0
    pass_fail = 'fail' if exit_code == 2 else 'pass'

    result = {
        'hard_residue': {
            'count': len(hr_findings),
            'items': hr_findings,
        },
        'strong_contextual': {
            # 档72C-4/§3-2(任务书 §6 后半句):高置信与低置信分组展示,count 为两者之和。
            # high 桶=SC-001~006/007a/009/010;low 桶=SC-007b/011。
            'count': len(sc_findings),
            'high_confidence': [f for f in sc_findings if f['rule_id'] in _SC_HIGH_IDS],
            'low_confidence': [f for f in sc_findings if f['rule_id'] in _SC_LOW_IDS],
        },
        'advisory_only': {
            'count': len(ao_findings),
            'items': ao_findings,
        },
        'statistical': {
            # 档72C-6/任务4-1:顶层第四段,独立于 strong/advisory,不污染既有计数基线。
            'count': len(stat_findings),
            'items': stat_findings,
        },
        'overall': {
            'pass_fail': pass_fail,
            'description': 'pass: 无 hard-residue。fail: 有 hard-residue。strong-contextual 和 advisory-only 不影响 pass/fail。'
        }
    }

    if args.output == 'json':
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f'=== 模式审计结果 ===')
        print(f'hard-residue: {len(hr_findings)} 个')
        for f in hr_findings:
            print(f'  [{f["rule_id"]}] {f["reason"]} @ {f["location"]}')
            print(f'    {f["span_text"][:60]}')
        if args.check_level == 'full':
            print(f'strong-contextual: {len(sc_findings)} 个')
            for f in sc_findings:
                print(f'  [{f["rule_id"]}] {f["reason"]} @ {f["location"]} (聚集 {f["cluster_count"]}/{f["cluster_threshold"]})')
                print(f'    {f["span_text"][:60]}')
            print(f'advisory-only: {len(ao_findings)} 个')
            print(f'statistical: {len(stat_findings)} 个')
            for f in ao_findings:
                print(f'  [{f["rule_id"]}] {f["reason"]} @ {f["location"]}')
                print(f'    {f["span_text"][:60]}')
        print(f'总体: {pass_fail}')

    # 退出码只由 hard-residue 决定
    # 档72C-4/§3-1:退出码按策略判定(HR-007 preserve 例外)。
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
