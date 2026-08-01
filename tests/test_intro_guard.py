"""档40 OBS-73 — Pipeline-side intro content-loss guard tests.

The guard mirrors gzh-design/scripts/render_article.py parse_article() L79-104
(locked skill). The three archived RUN articles must ALL FAIL (any PASS means
the mirror is misaligned -> stop and report, per 档40 spec); one compliant
input must PASS.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from wxgzh_pipeline.stages.gzh_design import _INTRO_MAX_LEN, _intro_guard_report

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNS = REPO_ROOT / "audit" / "runs"
RUN1_ARTICLE = RUNS / "20260731T135947-ai-bbg4al" / "stages" / "zh_human_writing" / "final_article.md"
RUN2_ARTICLE = RUNS / "20260801T182628-topic-ui5f7p" / "stages" / "zh_human_writing" / "final_article.md"
EVENT_ARTICLE = (RUNS / "20260801T231452-vibe-coding-guide-v2-1-1vg6jx"
                 / "zh_human_writing" / "final_article.md")


def _report_of(path: Path) -> dict:
    assert path.is_file(), f"archived article missing: {path}"
    return _intro_guard_report(path.read_text(encoding="utf-8"))


def _reference_parse_article(md: str) -> str:
    """Independent replica of gzh-design render_article.py L79-104 (kept in the
    test to prove the guard's first-line selection matches the locked renderer)."""
    lines = md.replace("\r\n", "\n").split("\n")
    title = ""
    intro = ""
    chapters = []
    cur = None
    for ln in lines:
        st = ln.strip()
        if not title and st.startswith("# ") and not st.startswith("## "):
            title = st[2:].strip()
            continue
        if st.startswith("## ") and not st.startswith("### "):
            cur = {"title": st[3:].strip(), "paras": []}
            chapters.append(cur)
            continue
        if st.startswith("#"):
            continue
        if not st:
            continue
        if cur is None:
            if not intro:
                intro = st
            continue
        cur["paras"].append(st)
    return intro


@pytest.mark.parametrize("article", [RUN1_ARTICLE, RUN2_ARTICLE, EVENT_ARTICLE],
                         ids=["run1-bbg4al", "run2-topic-ui5f7p", "event-vibe-coding-guide"])
def test_archived_run_articles_all_fail(article):
    report = _report_of(article)
    assert report["ok"] is False
    assert report["intro_line_count"] > 1 or report["intro_char_count"] > _INTRO_MAX_LEN
    assert report["dropped_text"], "FAIL must carry the full dropped text"
    assert report["guidance"].startswith("首个 ## 之前只能有一行且不超过 40 字")


def test_run1_two_intro_paragraphs_fails_with_second_paragraph_text():
    report = _report_of(RUN1_ARTICLE)
    assert report["intro_line_count"] == 2
    assert report["intro_char_count"] > 0
    # the dropped full text is para2 of RUN1 (the material round-up)
    assert "本轮AI HOT素材把这种变化摆在了一起" in report["dropped_text"]
    assert "正在成为安全流程里的行动者" in report["dropped_text"]


def test_run2_single_198_char_intro_fails_with_truncation_tail():
    report = _report_of(RUN2_ARTICLE)
    assert report["intro_line_count"] == 1
    assert report["intro_char_count"] == 198
    assert "出了问题找谁" in report["dropped_text"]


def test_event_run_eight_intro_paragraphs_fails():
    report = _report_of(EVENT_ARTICLE)
    assert report["intro_line_count"] == 8
    for marker in ("说的是我做的 vibe-coding-guide", "今天先认个账",
                   "那不叫安全气囊", "这次，纸条是真的变成锁了"):
        assert marker in report["dropped_text"]


def test_guard_intro_matches_reference_parse_article():
    for article in (RUN1_ARTICLE, RUN2_ARTICLE, EVENT_ARTICLE):
        md = article.read_text(encoding="utf-8")
        report = _intro_guard_report(md)
        reference_intro = _reference_parse_article(md)
        assert report["intro_char_count"] == len(reference_intro)
        if report["intro_line_count"] == 1:
            assert report["dropped_text"] == reference_intro[_INTRO_MAX_LEN:]


def test_compliant_single_short_intro_passes():
    md = "# 示例标题\n\n合规导语。\n\n## 第一节\n\n正文。\n"
    report = _intro_guard_report(md)
    assert report["ok"] is True
    assert report["intro_line_count"] == 1
    assert report["intro_char_count"] <= _INTRO_MAX_LEN
    assert report["dropped_text"] == ""


def test_blank_and_heading_lines_are_skipped_like_parse_article():
    # blank lines / extra H1 / H3 before the first H2 must not count as intro lines
    md = "# 标题\n\n\n### 小节标题\n\n导语。\n\n# 重复标题\n\n## 第一章\n\n正文。\n"
    report = _intro_guard_report(md)
    assert report["ok"] is True
    assert report["intro_line_count"] == 1
    assert report["intro_char_count"] == 3
