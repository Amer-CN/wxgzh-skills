"""OBS-86(档62):claim 章节对齐判定。

背景(档60 取证):ithome 聚合页的全部图片都在页面正文容器(post_content)内,
纯 DOM 容器判定无法区分「本素材相关章节的图」与「同页其他新闻章节的图」。
发现是 claim 驱动的(materials 带 selected_claim_ids),因此正文边界判定在
容器语义之外必须叠加「章节对齐」维度:图片所属章节标题与素材 claim 文本
不匹配的,视为跨章节图,在下载前排除。

判定依据:词元交集(非字母数字切分;拉丁词元长度≥3,中文连续串长度≥2)。
章节标题与任一 claim 文本共享 ≥3 个词元,或 claim 前 20 字出现在标题中,
即判对齐。阈值以档 60 六张真实图/章节实测校准:
- 章节#2(OpenAI 降价)与 claim C-06 共享 OpenAI/GPT-5.6/Luna/模型/费用/下调 ≥3 -> 对齐
- 章节#4(小米)/#14(比亚迪大汉)/#18(海獭)/#20(特斯拉)/#3(携程)共享 0-1 个 -> 不对齐
"""
from __future__ import annotations

import re

_MIN_CLAIM_PREFIX = 20   # claim_text[:20] 出现在标题中即对齐
_SHARED_TOKEN_THRESHOLD = 3
_LATIN_MIN_LEN = 3
_CJK_MIN_LEN = 2


def tokenize(text: str) -> set[str]:
    """非字母数字切分;拉丁词元保留长度≥3,中文连续串保留长度≥2。"""
    tokens: set[str] = set()
    for part in re.split(r"[^0-9A-Za-z\u4e00-\u9fff]+", text or ""):
        if not part:
            continue
        if re.fullmatch(r"[A-Za-z0-9]+", part):
            if len(part) >= _LATIN_MIN_LEN:
                tokens.add(part.lower())
        else:
            for run in re.findall(r"[\u4e00-\u9fff]{2,}", part):
                tokens.add(run)
    return tokens


def section_matches_claims(section_heading: str, claim_texts: list[str]) -> bool:
    """章节标题是否与任一 claim 对齐(保守:无法判定时返回 False 即排除)。"""
    if not section_heading or not claim_texts:
        return False
    heading = (section_heading or "").strip()
    heading_tokens = tokenize(heading)
    for ct in claim_texts:
        ct = (ct or "").strip()
        if not ct:
            continue
        core = ct[:_MIN_CLAIM_PREFIX]
        if core and core in heading:
            return True
        shared = len(heading_tokens & tokenize(ct))
        if shared >= _SHARED_TOKEN_THRESHOLD:
            return True
    return False
