#!/usr/bin/env python3
"""
change_report.py — zh-human-writing v1 变化统计脚本

对编辑前后的文本做量化对比，输出变化统计。不作审美判断。

用法:
    python change_report.py --original ORIGINAL.txt --edited EDITED.txt [OPTIONS]

选项:
    --original PATH        原文文件路径（必需）
    --edited PATH          编辑后文件路径（必需）
    --length-retention MODE 长度保持模式（strict/balanced/free，默认 balanced）
    --output FORMAT        输出格式（json/text，默认 json）
    --help                 显示帮助

退出码:
    0 — 成功
    3 — 错误（文件不存在、编码错误、参数错误）
"""

import argparse
import json
import re
import sys


class _P(argparse.ArgumentParser):
    """档72C-3/OBS-234:argparse 错误统一退出码 3。"""
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


def count_characters(text):
    """统计字符数（不含空白字符）。"""
    return len(re.sub(r'\s', '', text))


def count_all_characters(text):
    """统计全部字符数（含空白）。"""
    return len(text)


def split_sentences(text):
    """按句号、问号、叹号分句。"""
    # 保留分隔符
    sentences = re.split(r'(?<=[。！？!?])', text)
    # 过滤空句
    return [s.strip() for s in sentences if s.strip()]


def count_sentences(text):
    """统计句数。"""
    return len(split_sentences(text))


def split_paragraphs(text):
    """按空行分段。"""
    paragraphs = re.split(r'\n\s*\n', text)
    return [p.strip() for p in paragraphs if p.strip()]


def count_paragraphs(text):
    """统计段落数。"""
    return len(split_paragraphs(text))


def find_deleted_sentences(original, edited):
    """找出原文中有但终稿中没有的句子。"""
    orig_sents = set(s.strip() for s in split_sentences(original))
    edit_sents = set(s.strip() for s in split_sentences(edited))

    deleted = []
    for sent in orig_sents:
        if sent not in edit_sents:
            # 尝试部分匹配（句子可能被微调但仍保留大部分内容）
            # 如果原文句子中有 >50% 的内容在终稿中存在，不算删除
            if len(sent) > 10:
                # 检查句子的前半部分是否在终稿中
                prefix = sent[:len(sent)//2]
                if prefix in edited:
                    continue
            deleted.append(sent)
    return deleted


def extract_protected_spans_simple(text):
    """简单提取可能的 protected spans。"""
    spans = []
    # 数字
    spans.extend([(m.group(), 'number') for m in re.finditer(r'\d[\d,]*\.?\d*[%‰]?', text)])
    # URL
    spans.extend([(m.group(), 'url') for m in re.finditer(r'https?://[^\s<>"\']+', text)])
    # 代码块
    spans.extend([(m.group(), 'code') for m in re.finditer(r'```[^\n]*\n.*?```', text, re.DOTALL)])
    # 行内代码
    spans.extend([(m.group(), 'code') for m in re.finditer(r'`[^`]+`', text)])
    # 用户标记
    spans.extend([(m.group(), 'user_protected') for m in re.finditer(r'\[\[protected\]\].*?\[\[/protected\]\]', text, re.DOTALL)])
    return spans


def check_protected_span_changes(original, edited):
    """检查 protected spans 变化。"""
    orig_spans = extract_protected_spans_simple(original)
    edit_spans = extract_protected_spans_simple(edited)

    changes = []
    orig_contents = set(s[0] for s in orig_spans)
    edit_contents = set(s[0] for s in edit_spans)

    for content, category in orig_spans:
        if content not in edit_contents:
            changes.append({
                'category': category,
                'original': content[:100],
                'edited': '(missing)',
                'status': 'changed'
            })

    return changes


def main():
    parser = _P(
        description='zh-human-writing v1 变化统计脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--original', required=True, help='原文文件路径')
    parser.add_argument('--edited', required=True, help='编辑后文件路径')
    parser.add_argument('--length-retention', default='balanced',
                        choices=['strict', 'balanced', 'free'],
                        help='长度保持模式')
    parser.add_argument('--output', default='json', choices=['json', 'text'], help='输出格式')

    args = parser.parse_args()

    original = read_file(args.original)
    edited = read_file(args.edited)

    # 统计
    orig_chars = count_all_characters(original)
    edit_chars = count_all_characters(edited)
    orig_nonws = count_characters(original)
    edit_nonws = count_characters(edited)

    length_ratio = edit_chars / orig_chars if orig_chars > 0 else 0.0

    orig_sents = count_sentences(original)
    edit_sents = count_sentences(edited)

    orig_paras = count_paragraphs(original)
    edit_paras = count_paragraphs(edited)

    deleted = find_deleted_sentences(original, edited)

    span_changes = check_protected_span_changes(original, edited)

    # 阈值
    thresholds = {'strict': 0.90, 'balanced': 0.80, 'free': 0.00}
    threshold = thresholds.get(args.length_retention, 0.80)

    result = {
        'character_count': {
            'original': orig_chars,
            'edited': edit_chars,
            'change_ratio': round((edit_chars - orig_chars) / orig_chars, 4) if orig_chars > 0 else 0.0,
        },
        'sentence_count': {
            'original': orig_sents,
            'edited': edit_sents,
            'change': edit_sents - orig_sents,
        },
        'paragraph_count': {
            'original': orig_paras,
            'edited': edit_paras,
            'change': edit_paras - orig_paras,
        },
        'length_ratio': {
            'value': round(length_ratio, 4),
            'threshold': threshold,
            'meets_threshold': length_ratio >= threshold if threshold > 0 else True,
        },
        'deleted_sentences': {
            'count': len(deleted),
            'details': [{'text': s[:100], 'location': '', 'reason': '在终稿中未找到'} for s in deleted],
        },
        'protected_span_changes': {
            'count': len(span_changes),
            'details': span_changes,
        }
    }

    if args.output == 'json':
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f'字符数: {orig_chars} → {edit_chars} ({result["character_count"]["change_ratio"]*100:.1f}%)')
        print(f'句数: {orig_sents} → {edit_sents} (变化 {edit_sents - orig_sents})')
        print(f'段落数: {orig_paras} → {edit_paras} (变化 {edit_paras - orig_paras})')
        print(f'长度比例: {length_ratio:.4f} (阈值: {threshold})')
        print(f'删除整句数: {len(deleted)}')
        if deleted:
            print('  删除的句子:')
            for s in deleted:
                print(f'    - {s[:80]}')
        print(f'Protected spans 变化: {len(span_changes)}')
        if span_changes:
            for c in span_changes:
                print(f'  [{c["category"]}] {c["original"][:50]} → {c["edited"][:50]}')

    sys.exit(0)

if __name__ == '__main__':
    main()
