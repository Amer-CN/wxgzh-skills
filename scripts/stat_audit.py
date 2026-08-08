#!/usr/bin/env python3
"""
stat_audit.py — zh-human-writing v1 统计检测层（档72C-6R/任务4，任务书 §4 逐字实现）

九项指标（ST-001~ST-009）：
  ST-001 句长变异系数 CV      —— 仅统计 >=4 汉字的句子,有效句 >=12 才计算;
                                  CV=标准差/均值;CV 小于阈值 → 命中
  ST-002 连词密度             —— 10 连词总次数 / 总汉字数(H) * 1000;H>=600 才统计;
                                  大于阈值 → 命中
  ST-003 「」高亮             —— 成对「」短语处数 > max(3, H//700)
  ST-004 软路标               —— 9 词总出现 > max(2, H//900)
  ST-005 长前置成分           —— 句首到第一个逗号片段汉字数 >=12 计 1 处;
                                  总数 > max(2, H//1200)
  ST-006 重"的"长句           —— 汉字数 >=38 且"的">=4 的句子数 > max(1, H//1500)
  ST-007 单句段占比           —— 仅 1 句的段落占比 >=75%(段落总数 >=10 才统计)
  ST-008 连续短段             —— 连续 >=4 个段落,每段 <=24 汉字且 <=1 句
  ST-009 段落开场重复         —— 11 个开场词中任一词作为段落开头出现 >=4 次

profile 分档（档72C-6R 裁定 D1~D3,原文照填,禁止统一乘数）:
  essay    : CV 0.42;连词密度 7‰;其余照任务书公式
  technical: CV 0.30;连词密度 10‰;列表项与有序步骤段不参与 ST-001/002/007/008
             的计算(整段剔除,分子分母同域);其余同 essay
  social   : 关闭 ST-001/002/007/008;其余保持基线

全部阈值与词表在 config/default.yaml 的 statistical 段(标注「待校准基线」),
代码禁止硬编码(R111 无兜底)。

统计层只输出 audit:severity=audit, action=review_only, 不进 pass_fail,
不影响任何退出码(任务书 §4 明令)。

退出码:本模块自身不产生退出码;配置错误由调用方统一 exit 3。
"""

import re
import statistics
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("错误: 缺少 PyYAML 依赖,无法读取配置 (pip install pyyaml)", file=sys.stderr)
    sys.exit(3)

_PROFILES = ('essay', 'technical', 'social')

# 统计层 finding 元信息(档72C-6/任务4-2:severity 一律 audit,action 一律 review_only;
# confidence=medium:统计类为参考信号而非直接证据。)
_GROUP_META = {
    'severity': 'audit',
    'action': 'review_only',
    'suggestion': '统计信号,仅提示;由人工判断是否需要处理',
}

# 段落/句子切分:与 pattern_audit.py 同口径(档72C-6R:避免循环 import,此处复制)。
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


def _hanzi_count(text):
    """汉字数(H 的口径,D1:屏蔽后统计,frontmatter/围栏代码/行内代码/URL/HTML 不计)。"""
    return len(re.findall(r'[\u4e00-\u9fff]', text))


# 列表项与有序步骤段(technical 豁免域,档72C-6R 裁定):
# Markdown 无序列表(- / * / + 加空格)与有序列表(数字 + . 、 ))。
_LIST_STEP_RE = re.compile(r'^\s*(?:[-*+] |\d{1,3}[.、)])')


def _is_list_step(para):
    return bool(_LIST_STEP_RE.match(para))


def _exempt_domain_paras(paras, indicator_cfg, profile):
    """technical 且指标声明豁免时,剔除列表项/有序步骤段(整段剔除,档72C-6R 裁定)。"""
    if profile == 'technical' and indicator_cfg.get('exempt_list_steps', False):
        return [p for p in paras if not _is_list_step(p[0])]
    return paras


# ============================================================
# 配置加载(fail-closed,R111 无兜底)
# ============================================================

_REQUIRED_KEYS = (
    'st001_cv', 'st002_conjunction_density', 'st003_quote_highlight',
    'st004_soft_signposts', 'st005_long_prelude', 'st006_heavy_de',
    'st007_single_sentence_para', 'st008_consecutive_short_paras',
    'st009_para_opening_repeat',
)


def _fail(msg):
    print(f'错误: {msg}', file=sys.stderr)
    sys.exit(3)


def load_stat_config(config_path=None):
    """读取统计层配置段;文件缺失/yaml 错/结构不合 → exit 3。

    statistical 段缺省 = 空规则集(72C-2 起 --config 部分覆盖契约,见 PB-013);
    非空段必须包含全部九项指标键(fail-closed,缺键即 exit 3,防部分配置静默失效)。
    """
    path = (Path(config_path) if config_path
            else Path(__file__).resolve().parents[1] / 'config' / 'default.yaml')
    try:
        text = path.read_text(encoding='utf-8')
    except OSError as exc:
        _fail(f'配置文件读取失败: {path}: {exc}')
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        _fail(f'配置文件 YAML 解析失败: {path}: {exc}')
    if not isinstance(data, dict):
        _fail('配置顶层必须为对象')
    stat = data.get('statistical')
    if stat is None:
        return {}
    if not isinstance(stat, dict):
        _fail('配置 statistical 段必须为对象(统计检测层,见档72C-6/任务4)')
    if not stat:
        return stat
    missing = [k for k in _REQUIRED_KEYS if k not in stat]
    if missing:
        _fail(f'配置 statistical 段缺失指标: {missing}(任务书 §4 九项,缺键即 exit 3)')
    for key in _REQUIRED_KEYS:
        item = stat[key]
        if not isinstance(item, dict):
            _fail(f'配置 statistical.{key} 必须为对象')
        enabled = item.get('enabled')
        if not isinstance(enabled, dict) or any(p not in enabled for p in _PROFILES):
            _fail(f'配置 statistical.{key}.enabled 必须显式包含 essay/technical/social')
        if any(not isinstance(enabled[p], bool) for p in _PROFILES):
            _fail(f'配置 statistical.{key}.enabled 取值必须为布尔')
        if 'threshold' in item:
            thr = item['threshold']
            if not isinstance(thr, dict) or any(p not in thr for p in _PROFILES):
                _fail(f'配置 statistical.{key}.threshold 必须显式包含 essay/technical/social')
            for p in _PROFILES:
                if enabled[p] and (thr[p] is None):
                    _fail(f'配置 statistical.{key}.threshold.{p} 在启用时不能为 null')
        for wkey in ('words',):
            words = item.get(wkey)
            if words is not None and (not isinstance(words, list) or not words):
                _fail(f'配置 statistical.{key}.{wkey} 必须为非空列表')
            if words is not None and any(not isinstance(w, str) or not w for w in words):
                _fail(f'配置 statistical.{key}.{wkey} 条目必须为非空字符串')
    return stat


def _stat_finding(profile, rule_id, name, location, span, original, reason,
                  suggestion=None, metric_value=None, threshold=None):
    """构造统计层十字段 finding(档72C-3 §1 十字段 + 档72C-6/任务4-2/4-4)。

    location: 全文级填「全文」,段落级填「第N段」。
    span:     (start, end) 原文偏移(masked 与 original 等长,偏移可直接用)。
    span_text: 截断 100 字(与 pattern_audit._excerpt 同风格)。
    """
    start, end = span
    seg = original[start:end]
    if len(seg) > 100:
        seg = seg[:100] + '…'
    f = {
        'rule_id': rule_id,
        'group': 'statistical',
        'severity': _GROUP_META['severity'],
        'confidence': 'medium',
        'profile': profile,
        'action': _GROUP_META['action'],
        'location': location,
        'span_text': seg,
        'reason': reason,
        'suggestion': suggestion or _GROUP_META['suggestion'],
        'language_origin': 'language_general',
    }
    if metric_value is not None:
        f['metric_value'] = metric_value
    if threshold is not None:
        f['threshold'] = threshold
    return f


# ============================================================
# 九项指标
# ============================================================

def _indicator_st001(cfg, masked, original, paras, profile, h, gates):
    if not cfg['enabled'][profile]:
        gates['ST-001'] = 'skipped:profile'
        return []
    domain = _exempt_domain_paras(paras, cfg, profile)
    valid = [s for para, _, _ in domain for s, _, _ in _sent_spans(para)
             if _hanzi_count(s) >= cfg['min_sentence_len']]
    if len(valid) < cfg['min_sentences']:
        gates['ST-001'] = f'gate:min_sentences({len(valid)}<{cfg["min_sentences"]})'
        return []
    lens = [_hanzi_count(s) for s in valid]
    mean = sum(lens) / len(lens)
    # 样本标准差(档72C-6R 决定日志:CV 用样本标准差 stdev,n>=12 无退化风险)。
    cv = statistics.stdev(lens) / mean
    thr = cfg['threshold'][profile]
    gates['ST-001'] = 'computed'
    if cv < thr:
        return [_stat_finding(
            profile, 'ST-001', cfg['name'], '全文', (0, len(original)), original,
            f"句长变异系数 CV={cv:.3f} 低于阈值 {thr}(有效句 {len(valid)})",
            metric_value=round(cv, 4), threshold=thr)]
    return []


def _indicator_st002(cfg, masked, original, paras, profile, h, gates):
    if not cfg['enabled'][profile]:
        gates['ST-002'] = 'skipped:profile'
        return []
    if h < cfg['min_h']:
        gates['ST-002'] = f'gate:min_h({h}<{cfg["min_h"]})'
        return []
    # 分子:列表/步骤段中的连词不参与(technical 豁免);分母:全局 H(D1 裁定)。
    if profile == 'technical' and cfg.get('exempt_list_steps', False):
        domain_text = ''.join(p for p, _, _ in paras if not _is_list_step(p))
    else:
        domain_text = masked
    count = sum(len(re.findall(re.escape(w), domain_text)) for w in cfg['words'])
    density = count / h * 1000
    thr = cfg['threshold'][profile]
    gates['ST-002'] = 'computed'
    if density > thr:
        return [_stat_finding(
            profile, 'ST-002', cfg['name'], '全文', (0, len(original)), original,
            f"连词密度 {density:.1f}‰ 高于阈值 {thr}‰(连词 {count} 次,H={h})",
            metric_value=round(density, 2), threshold=thr)]
    return []


def _indicator_st003(cfg, masked, original, paras, profile, h, gates):
    if not cfg['enabled'][profile]:
        gates['ST-003'] = 'skipped:profile'
        return []
    n = len(re.findall(r'「[^」]*」', masked))
    thr = max(cfg['formula_base'], h // cfg['formula_divisor'])
    gates['ST-003'] = 'computed'
    if n > thr:
        return [_stat_finding(
            profile, 'ST-003', cfg['name'], '全文', (0, len(original)), original,
            f"「」高亮 {n} 处,超过阈值 max({cfg['formula_base']}, H//{cfg['formula_divisor']})={thr}",
            metric_value=n, threshold=thr)]
    return []


def _indicator_st004(cfg, masked, original, paras, profile, h, gates):
    if not cfg['enabled'][profile]:
        gates['ST-004'] = 'skipped:profile'
        return []
    n = sum(len(re.findall(re.escape(w), masked)) for w in cfg['words'])
    thr = max(cfg['formula_base'], h // cfg['formula_divisor'])
    gates['ST-004'] = 'computed'
    if n > thr:
        return [_stat_finding(
            profile, 'ST-004', cfg['name'], '全文', (0, len(original)), original,
            f"软路标词 {n} 次,超过阈值 max({cfg['formula_base']}, H//{cfg['formula_divisor']})={thr}",
            metric_value=n, threshold=thr)]
    return []


def _indicator_st005(cfg, masked, original, paras, profile, h, gates):
    if not cfg['enabled'][profile]:
        gates['ST-005'] = 'skipped:profile'
        return []
    n = 0
    for para, _, _ in paras:
        for sent, _, _ in _sent_spans(para):
            m = re.match(r'^([^，,]*)[，,]', sent)
            if m and _hanzi_count(m.group(1)) >= cfg['min_hanzi']:
                n += 1
    thr = max(cfg['formula_base'], h // cfg['formula_divisor'])
    gates['ST-005'] = 'computed'
    if n > thr:
        return [_stat_finding(
            profile, 'ST-005', cfg['name'], '全文', (0, len(original)), original,
            f"长前置成分 {n} 处(句首至首逗号 >= {cfg['min_hanzi']} 汉字),"
            f"超过阈值 max({cfg['formula_base']}, H//{cfg['formula_divisor']})={thr}",
            metric_value=n, threshold=thr)]
    return []


def _indicator_st006(cfg, masked, original, paras, profile, h, gates):
    if not cfg['enabled'][profile]:
        gates['ST-006'] = 'skipped:profile'
        return []
    n = 0
    for para, _, _ in paras:
        for sent, _, _ in _sent_spans(para):
            if (_hanzi_count(sent) >= cfg['min_sentence_hanzi']
                    and len(re.findall('的', sent)) >= cfg['min_de']):
                n += 1
    thr = max(cfg['formula_base'], h // cfg['formula_divisor'])
    gates['ST-006'] = 'computed'
    if n > thr:
        return [_stat_finding(
            profile, 'ST-006', cfg['name'], '全文', (0, len(original)), original,
            f"重'的'长句 {n} 句(>= {cfg['min_sentence_hanzi']} 汉字且'的'>={cfg['min_de']}),"
            f"超过阈值 max({cfg['formula_base']}, H//{cfg['formula_divisor']})={thr}",
            metric_value=n, threshold=thr)]
    return []


def _indicator_st007(cfg, masked, original, paras, profile, h, gates):
    if not cfg['enabled'][profile]:
        gates['ST-007'] = 'skipped:profile'
        return []
    domain = _exempt_domain_paras(paras, cfg, profile)
    if len(domain) < cfg['min_paragraphs']:
        gates['ST-007'] = f'gate:min_paragraphs({len(domain)}<{cfg["min_paragraphs"]})'
        return []
    single = sum(1 for para, _, _ in domain if len(_sent_spans(para)) == 1)
    ratio = single / len(domain)
    thr = cfg['ratio']
    gates['ST-007'] = 'computed'
    if ratio >= thr:
        return [_stat_finding(
            profile, 'ST-007', cfg['name'], '全文', (0, len(original)), original,
            f"单句段占比 {ratio:.1%} >= {thr:.0%}(单句 {single}/{len(domain)} 段)",
            metric_value=round(ratio, 4), threshold=thr)]
    return []


def _indicator_st008(cfg, masked, original, paras, profile, h, gates):
    if not cfg['enabled'][profile]:
        gates['ST-008'] = 'skipped:profile'
        return []
    domain = _exempt_domain_paras(paras, cfg, profile)
    run = 0
    for idx, (para, ps, pe) in enumerate(domain):
        if _hanzi_count(para) <= cfg['max_hanzi'] and len(_sent_spans(para)) <= cfg['max_sentences']:
            run += 1
            if run >= cfg['min_run']:
                start_idx = idx - run + 1
                gates['ST-008'] = 'computed'
                return [_stat_finding(
                    profile, 'ST-008', cfg['name'], f'第{start_idx+1}段',
                    (ps, pe), original,
                    f"连续 {run} 个短段(每段 <= {cfg['max_hanzi']} 汉字且 <= 1 句),"
                    f"达到 {cfg['min_run']} 段阈值",
                    metric_value=run, threshold=cfg['min_run'])]
        else:
            run = 0
    gates['ST-008'] = 'computed'
    return []


def _indicator_st009(cfg, masked, original, paras, profile, h, gates):
    if not cfg['enabled'][profile]:
        gates['ST-009'] = 'skipped:profile'
        return []
    counts = {w: 0 for w in cfg['words']}
    first = {}
    for idx, (para, ps, pe) in enumerate(paras):
        stripped = para.lstrip()
        for w in cfg['words']:
            if stripped.startswith(w):
                counts[w] += 1
                first.setdefault(w, (idx, ps, pe))
                break  # 每段只按词表顺序记首个匹配
    thr = cfg['min_hits']
    gates['ST-009'] = 'computed'
    for w in cfg['words']:
        if counts[w] >= thr:
            idx, ps, pe = first[w]
            return [_stat_finding(
                profile, 'ST-009', cfg['name'], f'第{idx+1}段',
                (ps, pe), original,
                f"段落开场词「{w}」出现 {counts[w]} 次,达到 {thr} 次阈值",
                metric_value=counts[w], threshold=thr)]
    return []


# (rule_id, config 键, 实现函数)
_INDICATORS = (
    ('ST-001', 'st001_cv', _indicator_st001),
    ('ST-002', 'st002_conjunction_density', _indicator_st002),
    ('ST-003', 'st003_quote_highlight', _indicator_st003),
    ('ST-004', 'st004_soft_signposts', _indicator_st004),
    ('ST-005', 'st005_long_prelude', _indicator_st005),
    ('ST-006', 'st006_heavy_de', _indicator_st006),
    ('ST-007', 'st007_single_sentence_para', _indicator_st007),
    ('ST-008', 'st008_consecutive_short_paras', _indicator_st008),
    ('ST-009', 'st009_para_opening_repeat', _indicator_st009),
)


def audit_stats(masked, original, profile, config_path=None):
    """运行统计检测层,返回 (findings, gates)。

    gates: {rule_id: 'computed' | 'skipped:profile' | 'gate:...'}——
    供任务 5 的「被前置门挡掉指标清单」取证用(5-2);正式输出只取 findings。
    """
    cfg = load_stat_config(config_path) if config_path is not None else _STAT_CFG
    if not cfg:
        return [], {}
    paras = _para_spans(masked)
    h = _hanzi_count(masked)
    findings = []
    gates = {}
    for rule_id, cfg_key, fn in _INDICATORS:
        findings.extend(fn(cfg[cfg_key], masked, original, paras, profile, h, gates))
    return findings, gates


def run_stat_audit(masked, original, profile, config_path=None):
    """任务书 §4 契约入口:只返回 findings(统计层不进 pass_fail、不影响退出码)。"""
    findings, _ = audit_stats(masked, original, profile, config_path)
    return findings


# 模块加载即注入默认配置(fail-closed:缺文件/错 schema 直接 exit 3,无兜底)。
_STAT_CFG = load_stat_config()


if __name__ == '__main__':
    print('stat_audit.py: 统计检测层(任务书 §4)。由 pattern_audit.py 调用,不独立使用。')
