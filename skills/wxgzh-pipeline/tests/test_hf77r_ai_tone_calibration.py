"""77R/OBS-344 calibration and instruction guardrail tests."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from wxgzh_pipeline import producers as PR

REPO = Path(__file__).resolve().parents[3]
CALIBRATION = REPO / "skills" / "wxgzh-pipeline" / "scripts" / "ai_tone_calibration.py"
PATTERN_AUDIT = REPO / "skills" / "zh-human-writing" / "scripts" / "pattern_audit.py"


def test_ai_tone_calibration_appends_run_model_family_row(tmp_path):
    run_root = tmp_path / "runs"
    article_dir = run_root / "20260831T120000-glm-5-3-flash-testab" / "super_writer"
    article_dir.mkdir(parents=True)
    (article_dir / "article.md").write_text(
        "# 标题\n\n正文足够长。\n\n它像一位智慧的导师，会指出盲点。\n",
        encoding="utf-8")
    output = tmp_path / "ai-tone-calibration.jsonl"
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", str(CALIBRATION),
         "--runs-root", str(run_root), "--output", str(output),
         "--pattern-audit", str(PATTERN_AUDIT)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=60)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1
    assert rows[0]["run_id"] == "20260831T120000-glm-5-3-flash-testab"
    assert rows[0]["model"] == "glm-5-3-flash"
    assert rows[0]["families"]["LT-002"] == 1


def test_zh_instruction_has_six_families_and_do_not_guardrails():
    instr = PR.AGENT_INSTRUCTIONS["zh_human_writing"]
    for anchor in (
        "77R/OBS-342", "pattern_audit.ai_tone", "段首零回指", "拟人喻体",
        "起首语", "编号小标题", "顿号", "五式译文句式", "handoff.prose_craft",
        "禁为“人味”调句长", "禁删设问/比喻", "禁补单字虚词",
    ):
        assert anchor in instr, anchor
