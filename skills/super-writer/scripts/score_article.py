#!/usr/bin/env python3
"""Deterministic preflight only; semantic scoring remains the Reviewer's job.

P3: Added burstiness diagnostic as non-blocking diagnostic.
No universal Chinese hard threshold. Only soft diagnostics.
blocking is always False. Handoff to humanizer.
"""
from pathlib import Path
import argparse, json, re, statistics

p = argparse.ArgumentParser()
p.add_argument('article')
p.add_argument('--json', action='store_true')
a = p.parse_args()
text = Path(a.article).read_text(encoding='utf-8')
paras = [x.strip() for x in re.split(r'\n\s*\n', text) if x.strip()]
heads = re.findall(r'^#{1,3}\s+.+$', text, re.M)
anchors = re.findall(r'\[编辑锚点(?:/[^：\]]+)?：.*?\]', text)
source_like = re.findall(r'https?://\S+|\[\^\d+\]|来源[：:]', text)
claims = re.findall(r'\b\d+(?:\.\d+)?%|\d{4}年|数据显示|研究表明', text)
duplicates = len(paras) - len(set(paras))

# ── Burstiness diagnostic (P3, non-blocking) ──

def compute_burstiness(text: str) -> dict:
    """Compute burstiness as a non-blocking diagnostic.

    No universal Chinese hard threshold.
    Only soft diagnostics based on pattern detection.
    Priority: personal corpus baseline > same-type baseline > generic default.
    """
    # Split into sentences by Chinese punctuation
    sentences = [s.strip() for s in re.split(r'[。！？!?；;\n]', text) if s.strip() and len(s.strip()) > 2]

    if len(sentences) < 4:
        return {
            "risk": "low",
            "evidence": ["句子数量不足，无法进行节奏诊断"],
            "blocking": False,
            "handoff_to": "humanizer",
            "note": "样本不足，仅作参考"
        }

    # Compute sentence lengths (in characters, excluding punctuation)
    lengths = [len(re.sub(r'[^\u4e00-\u9fff\w]', '', s)) for s in sentences]
    mean_len = statistics.mean(lengths) if lengths else 0
    stdev = statistics.stdev(lengths) if len(lengths) > 1 else 0
    cv = stdev / mean_len if mean_len > 0 else 0  # coefficient of variation

    evidence = []
    risk_score = 0

    # Check 1: Consecutive sentences with very similar length
    similar_runs = 0
    for i in range(len(lengths) - 1):
        if abs(lengths[i] - lengths[i + 1]) <= 3 and lengths[i] > 5:
            similar_runs += 1
    if similar_runs >= 4:
        evidence.append(f"连续 {similar_runs} 组句子长度差异不超过3字")
        risk_score += 2
    elif similar_runs >= 2:
        evidence.append(f"有 {similar_runs} 组相邻句子长度接近")
        risk_score += 1

    # Check 2: Consecutive paragraphs with identical sentence count
    para_sentence_counts = []
    for para in paras:
        para_sentences = [s for s in re.split(r'[。！？!?；;]', para) if s.strip()]
        para_sentence_counts.append(len(para_sentences))
    identical_para_runs = 0
    for i in range(len(para_sentence_counts) - 1):
        if para_sentence_counts[i] == para_sentence_counts[i + 1] and para_sentence_counts[i] > 0:
            identical_para_runs += 1
    if identical_para_runs >= 3:
        evidence.append(f"连续 {identical_para_runs + 1} 个段落的句子数量完全一致")
        risk_score += 2
    elif identical_para_runs >= 2:
        evidence.append(f"有 {identical_para_runs} 组相邻段落的句子数量一致")
        risk_score += 1

    # Check 3: All sections have identical internal structure
    sections = re.split(r'^#{1,3}\s+.+$', text, flags=re.M)
    sections = [s.strip() for s in sections if s.strip()]
    if len(sections) >= 3:
        section_para_counts = [len([p for p in s.split('\n\n') if p.strip()]) for s in sections]
        if len(set(section_para_counts)) == 1 and section_para_counts[0] > 0:
            evidence.append(f"所有 {len(sections)} 个章节均为 {section_para_counts[0]} 段")
            risk_score += 2

    # Check 4: Almost no variation in sentence length
    if cv < 0.2 and mean_len > 10:
        evidence.append(f"句长变异系数仅为 {cv:.2f}，长短句几乎没有变化")
        risk_score += 2
    elif cv < 0.3 and mean_len > 10:
        evidence.append(f"句长变异系数较低（{cv:.2f}）")
        risk_score += 1

    # Check 5: Too many consecutive single-sentence paragraphs
    single_sentence_paras = sum(1 for c in para_sentence_counts if c == 1)
    if single_sentence_paras > len(paras) * 0.6 and len(paras) > 5:
        evidence.append(f"{single_sentence_paras}/{len(paras)} 个段落为单句段")
        risk_score += 1

    # Check 6: Many consecutive sentences starting with the same pattern
    first_chars = [s[0] if s else '' for s in sentences]
    same_start_runs = 0
    for i in range(len(first_chars) - 2):
        if first_chars[i] == first_chars[i + 1] == first_chars[i + 2]:
            same_start_runs += 1
    if same_start_runs >= 2:
        evidence.append(f"有 {same_start_runs} 组连续3句以上以相同字开头")
        risk_score += 1

    # Determine risk level
    if risk_score >= 5:
        risk = "high"
    elif risk_score >= 3:
        risk = "medium"
    elif risk_score >= 1:
        risk = "low"
    else:
        risk = "low"

    if not evidence:
        evidence.append("未检测到明显的节奏问题")

    return {
        "risk": risk,
        "evidence": evidence,
        "blocking": False,
        "handoff_to": "humanizer",
        "stats": {
            "sentence_count": len(sentences),
            "mean_length": round(mean_len, 1),
            "stdev": round(stdev, 1),
            "cv": round(cv, 3),
        },
        "note": "非阻塞诊断。没有个人语料基线，只做软诊断。正式阈值需10-20篇人工定稿后计算。"
    }

burstiness = compute_burstiness(text)

checks = {
  'characters': len(text), 'paragraphs': len(paras), 'headings': len(heads),
  'editor_anchors': len(anchors), 'source_markers': len(source_like),
  'claim_markers': len(claims), 'duplicate_paragraphs': duplicates,
  'burstiness': burstiness,
  'warnings': []
}
if len(text) < 800: checks['warnings'].append('正文较短，确认是否符合任务')
if duplicates: checks['warnings'].append('存在完全重复段落')
if claims and not source_like: checks['warnings'].append('检测到数据/研究表述，但未发现来源标记')
if anchors: checks['warnings'].append('仍有编辑锚点，不能静默当作完成稿')
if burstiness['risk'] != 'low':
    checks['warnings'].append(f"节奏诊断: {burstiness['risk']} (非阻塞，交接给 humanizer)")
if a.json: print(json.dumps(checks, ensure_ascii=False, indent=2))
else:
    for k,v in checks.items():
        if k == 'burstiness':
            print(f'burstiness:')
            print(f'  risk: {v["risk"]}')
            print(f'  blocking: {v["blocking"]}')
            print(f'  handoff_to: {v["handoff_to"]}')
            for e in v['evidence']:
                print(f'  - {e}')
            if 'stats' in v:
                print(f'  stats: {v["stats"]}')
        else:
            print(f'{k}: {v}')
