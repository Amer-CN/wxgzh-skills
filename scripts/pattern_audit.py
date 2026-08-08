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
        'patterns': [r'\{\{[^}]+\}\}', r'\[INSERT[^\]]*\]', r'\[待填\]'],
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
]


def detect_hard_residue(text):
    """检测 hard-residue 模式。单次出现即报告。"""
    findings = []
    paragraphs = split_paragraphs(text)

    for para_idx, para in enumerate(paragraphs):
        sentences = split_sentences(para)
        for sent_idx, sent in enumerate(sentences):
            for pattern_def in HARD_RESIDUE_PATTERNS:
                for pat in pattern_def['patterns']:
                    matches = re.finditer(pat, sent)
                    for m in matches:
                        findings.append({
            'pattern_id': pattern_def['id'],
            'pattern_name': pattern_def['name'],
                            'location': f'paragraph {para_idx+1}, sentence {sent_idx+1}',
                            'excerpt': sent[:100],
                            'action': 'allow_delete_or_replace',
                            'language_origin': pattern_def['language_origin'],
                        })

    return findings


# ============================================================
# strong-contextual 检测
# ============================================================

STRONG_CONTEXTUAL_PATTERNS = [
    {
        'id': 'SC-001',
        'name': '无信息开场',
        'patterns': [r'让我们来看看', r'在当今.{0,10}的时代', r'随着.{0,10}的发展'],
        'thresholds': {'essay': 2, 'technical': 3, 'social': 4},
        'language_origin': 'language_general',
    },
    {
        'id': 'SC-002',
        'name': '无信息导航',
        'patterns': [r'接下来我们将', r'下面我们来看', r'首先.{0,20}其次.{0,20}最后'],
        'thresholds': {'essay': 2, 'technical': 3, 'social': 4},
        'language_origin': 'language_general',
    },
    {
        'id': 'SC-003',
        'name': '无信息总结',
        'patterns': [r'总而言之', r'综上所述', r'总结来说', r'通过以上分析可以看出'],
        'thresholds': {'essay': 2, 'technical': 3, 'social': 4},
        'language_origin': 'language_general',
    },
    {
        'id': 'SC-004',
        'name': '无来源权威铺垫',
        'patterns': [r'研究表明', r'数据显示', r'据统计'],
        'thresholds': {'essay': 2, 'technical': 3, 'social': 4},
        'language_origin': 'language_general',
    },
    {
        'id': 'SC-005',
        'name': '连续同构结构',
        'patterns': [],  # 需要特殊检测逻辑
        # 档72B-2R:technical = int(3*1.5) = 4(截断,非 ceil);特殊逻辑仍用固定 3(恒等)。
        'thresholds': {'essay': 3, 'technical': 4, 'social': 6},
        'language_origin': 'language_general',
    },
    {
        'id': 'SC-006',
        'name': '明显假互动',
        'patterns': [r'你可能会问', r'你想想看', r'你有没有想过'],
        'thresholds': {'essay': 2, 'technical': 3, 'social': 4},
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
        ],
        'thresholds': {'essay': 2, 'technical': 3, 'social': 4},
        'language_origin': 'chinese_specific',
    },
    {
        'id': 'SC-008',
        'name': '元话语路标',
        'patterns': [r'先说结论', r'说白了', r'说穿了'],
        'thresholds': {'essay': 1, 'technical': 2, 'social': 3},
        'language_origin': 'chinese_specific',
    },
]

# 档72B-2R OBS-228/R111:模块加载期结构断言——thresholds 必须显式包含
# 全部 profile 且为 >=1 整数;缺键即报错,禁止 or 兜底/静默默认(fail-open)。
_PROFILES = ('essay', 'technical', 'social')
for _r in STRONG_CONTEXTUAL_PATTERNS:
    _t = _r.get('thresholds')
    if not isinstance(_t, dict) or any(p not in _t for p in _PROFILES):
        raise ValueError(
            f"{_r.get('id')}: thresholds 必须显式包含 essay/technical/social")
    if any(not isinstance(_t[p], int) or _t[p] < 1 for p in _PROFILES):
        raise ValueError(f"{_r.get('id')}: thresholds 值必须为 >=1 的整数")



def detect_strong_contextual(text, profile):
    """检测 strong-contextual 模式。聚集时才报告。"""
    findings = []
    paragraphs = split_paragraphs(text)

    for para_idx, para in enumerate(paragraphs):
        for pattern_def in STRONG_CONTEXTUAL_PATTERNS:
            if not pattern_def['patterns']:
                continue

            count = 0
            matches_detail = []
            for pat in pattern_def['patterns']:
                matches = re.finditer(pat, para)
                for m in matches:
                    count += 1
                    matches_detail.append(m.group())

            # 档72B-2 OBS-218:每条规则自带 thresholds 字典,按 profile 取值,
            # 缺省回落到 essay;统一乘数 PROFILE_MULTIPLIERS 已删除。
            # 档72B-2R OBS-228/R111:直接下标,缺键即 KeyError,不许兜底。
            # 模块加载期断言已保证三 profile 齐备;argparse choices 限定 profile。
            threshold = pattern_def['thresholds'][profile]

            if count >= threshold:
                findings.append({
                    'pattern_id': pattern_def['id'],
                    'pattern_name': pattern_def['name'],
                    'location': f'paragraph {para_idx+1}',
                    'excerpt': para[:100],
                    'cluster_count': count,
                    'cluster_threshold': threshold,
                    'action': 'review',
                    'language_origin': pattern_def['language_origin'],
                })

    # 检测连续同构结构（SC-005）
    sentences = split_sentences(text)
    consecutive_count = 1
    prev_len = 0
    for i, sent in enumerate(sentences):
        curr_len = len(sent)
        if i > 0 and abs(curr_len - prev_len) <= 5 and curr_len > 10:
            consecutive_count += 1
            if consecutive_count >= 3:
                findings.append({
                    'pattern_id': 'SC-005',
                    'pattern_name': '连续同构结构',
                    'location': f'sentence {i-consecutive_count+2} to {i+1}',
                    'excerpt': ' '.join(sentences[i-consecutive_count+1:i+1])[:100],
                    'cluster_count': consecutive_count,
                    'cluster_threshold': 3,
                    'action': 'review',
                    'language_origin': 'language_general',
                })
        else:
            consecutive_count = 1
        prev_len = curr_len

    return findings


# ============================================================
# advisory-only 检测
# ============================================================

ADVISORY_ONLY_PATTERNS = [
    # 档72B-2 OBS-177/3-3:原地扩宽(不进 strong_contextual,ME-010 继续绿);
    # 可选「并」前缀 + 中间 0~90 字(不跨句),置信度排序不再倒置。
    {'id': 'AO-001', 'name': '不是…而是…', 'pattern': r'(?:并)?不是[^。！？\n]{0,90}而是', 'language_origin': 'language_general'},
    {'id': 'AO-002', 'name': '先…再…', 'pattern': r'先.{0,20}再', 'language_origin': 'language_general'},
    {'id': 'AO-003', 'name': '从…到…', 'pattern': r'从.{0,20}到', 'language_origin': 'language_general'},
    {'id': 'AO-004', 'name': '破折号', 'pattern': r'——', 'language_origin': 'chinese_specific'},
    {'id': 'AO-006', 'name': '反问', 'pattern': r'难道.{0,20}[吗呢？?]', 'language_origin': 'language_general'},
    {'id': 'AO-007', 'name': '二人称', 'pattern': r'你', 'language_origin': 'language_general'},
    {'id': 'AO-011', 'name': '第一人称', 'pattern': r'[我]', 'language_origin': 'language_general'},
]


def detect_advisory_only(text):
    """检测 advisory-only 模式。只列出，不影响 pass/fail。"""
    findings = []
    paragraphs = split_paragraphs(text)

    for para_idx, para in enumerate(paragraphs):
        sentences = split_sentences(para)
        for sent_idx, sent in enumerate(sentences):
            for pattern_def in ADVISORY_ONLY_PATTERNS:
                matches = re.finditer(pattern_def['pattern'], sent)
                for m in matches:
                    findings.append({
                        'pattern_id': pattern_def['id'],
                        'pattern_name': pattern_def['name'],
                        'location': f'paragraph {para_idx+1}, sentence {sent_idx+1}',
                        'excerpt': sent[:100],
                        'action': 'advisory',
                        'language_origin': pattern_def['language_origin'],
                    })

    return findings


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
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

    args = parser.parse_args()

    text = read_file(args.text)

    # 检测
    hr_findings = detect_hard_residue(text)
    sc_findings = []
    ao_findings = []

    if args.check_level == 'full':
        sc_findings = detect_strong_contextual(text, args.profile)
        ao_findings = detect_advisory_only(text)

    # pass/fail 只由 hard-residue 决定
    pass_fail = 'fail' if hr_findings else 'pass'

    result = {
        'hard_residue': {
            'count': len(hr_findings),
            'items': hr_findings,
        },
        'strong_contextual': {
            'count': len(sc_findings),
            'items': sc_findings,
        },
        'advisory_only': {
            'count': len(ao_findings),
            'items': ao_findings,
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
            print(f'  [{f["pattern_id"]}] {f["pattern_name"]} @ {f["location"]}')
            print(f'    {f["excerpt"][:60]}')
        if args.check_level == 'full':
            print(f'strong-contextual: {len(sc_findings)} 个')
            for f in sc_findings:
                print(f'  [{f["pattern_id"]}] {f["pattern_name"]} @ {f["location"]} (聚集 {f["cluster_count"]}/{f["cluster_threshold"]})')
                print(f'    {f["excerpt"][:60]}')
            print(f'advisory-only: {len(ao_findings)} 个')
            for f in ao_findings:
                print(f'  [{f["pattern_id"]}] {f["pattern_name"]} @ {f["location"]}')
                print(f'    {f["excerpt"][:60]}')
        print(f'总体: {pass_fail}')

    # 退出码只由 hard-residue 决定
    if hr_findings:
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()
