#!/usr/bin/env python3
"""Build the deterministic fake_live fixture used by the fake-agent for the three
agent-driven stages (aihot / super_writer / zh_human_writing). Executable stages
(media_enrichment / gzh_design / wechat_draft) are produced live by shims, so no
canned outputs are needed for them. No side effects; regenerates in place.

The frozen article has EXACTLY 6 `## ` chapters so the dynamic chapter/TOC gate
has a concrete, article-derived expectation. No reader-facing internal terms.
"""
from __future__ import annotations

import json
from pathlib import Path

FX = Path(__file__).resolve().parents[1] / "fixtures" / "fake_live_fixture"

CHAPTERS = [
    "缘起：一块旧显卡的第二次生命",
    "选型：为什么是它",
    "装机：踩过的三个坑",
    "驱动与环境：让它真正跑起来",
    "出图：第一张图的那一刻",
    "复盘：值不值得折腾",
]
ARTICLE = "# 把旧显卡折腾成本地画图机\n\n开篇导语，交代背景与动机。\n\n" + "\n\n".join(
    f"## {t}\n\n这一节讲述「{t}」的具体过程与结论，包含可核实的细节与数字。" for t in CHAPTERS
) + "\n"


def out(stage: str, name: str, text: str):
    p = FX / stage / "outputs" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")


def outj(stage: str, name: str, obj):
    out(stage, name, json.dumps(obj, ensure_ascii=False, indent=2))


# --- aihot ---
raw = [{"id": f"item-{i}", "title": f"素材 {i}", "url": f"https://example.com/{i}"} for i in range(1, 9)]
outj("aihot", "raw_items.json", raw)
outj("aihot", "deduplicated_items.json", raw[:6])
outj("aihot", "fetch_log.json", {"source": "aihot.virxact.com", "fetched": len(raw),
                                  "deduplicated": 6, "mode": "fake_live"})

# --- super_writer ---
out("super_writer", "article.md", ARTICLE)
out("super_writer", "outline.md", "\n".join(f"- {t}" for t in CHAPTERS) + "\n")
outj("super_writer", "canonical_claim_registry.json",
     {"claims": [{"id": f"C-{i:02d}", "text": f"事实 {i}", "source": f"https://example.com/{i}"}
                 for i in range(1, 7)]})
outj("super_writer", "full_mode_validator_report.json",
     {"exit": 0, "FULL_MODE_VALIDATOR_EXIT": 0, "length_mode": "long", "length_auto": True,
      "target_visible_chars": 5200, "chapters": len(CHAPTERS), "mode": "material_heavy_full_mode"})

# --- zh_human_writing --- (freeze target: same 6 chapters, no forbidden terms)
out("zh_human_writing", "final_article.md", ARTICLE)
outj("zh_human_writing", "fidelity_report.json",
     {"NEW_UNREGISTERED_FACTS": 0, "NUMBER_CHANGES": 0, "ATTRIBUTION_LOSS": 0,
      "QUALIFIER_LOSS": 0, "CLAIM_SEMANTIC_CHANGE": 0, "HARD_RESIDUE": 0})

print("fake_live fixture ->", FX)
print("chapters:", len(CHAPTERS))
