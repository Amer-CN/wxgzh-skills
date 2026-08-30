"""77P/OBS-339: cover strike and subtitle single-line budget gates."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import validate_single_product as VSP  # noqa: E402


def _handoff(strike_assumption=None, hook_line="钩子") -> str:
    import json
    sa = ""
    if strike_assumption is not None:
        sa = f"      strike_assumption: {json.dumps(strike_assumption, ensure_ascii=False)}\n"
    return f"""handoff:
  schema_version: "2.2"
  prose_craft_applied: true
  prose_craft_version: "1.0"
  title_candidates: ["A", "B"]
  hook_line: {json.dumps(hook_line, ensure_ascii=False)}
  selected_title: "A"
  title_selection_reason: "具体"
  formatter:
    cover:
      kicker: null
      strike: null
{sa}      tags: null
"""


def test_strike_assumption_over_single_line_budget_fails(tmp_path):
    p = tmp_path / "handoff.yaml"
    p.write_text(_handoff("这是一句被故意写成十九个中文汉字的划线旧认知"), encoding="utf-8")
    errors, checks = VSP.check_handoff(p)
    assert errors
    assert any("strike_assumption" in error and "18" in error for error in errors)
    assert checks["strike_assumption"] == "这是一句被故意写成十九个中文汉字的划线旧认知"


def test_subtitle_sources_use_single_line_budget(tmp_path):
    handoff = tmp_path / "handoff.yaml"
    handoff.write_text(_handoff(hook_line="这个副标题兜底文案被故意写成二十一个中文汉字长度"),
                       encoding="utf-8")
    hook_errors, _ = VSP.check_handoff(handoff)
    assert any("hook_line" in error and "20" in error for error in hook_errors)

    article = tmp_path / "article.md"
    article.write_text("# 标题\n\n" + "这个导语副标题被故意写成二十一个中文汉字长度\n\n## 第一章\n\n正文。\n",
                       encoding="utf-8")
    intro_errors, checks = VSP.check_article(article)
    assert any("article: 封面副标题" in error and "20" in error for error in intro_errors)
    assert checks["cover_subtitle_source"] == "article.intro"
