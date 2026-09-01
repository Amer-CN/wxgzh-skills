#!/usr/bin/env python3
"""ai_tone_calibration.py — frozen-run AI-tone calibration (77R/OBS-344).

Runs the six vendored AI-tone operator families over every frozen RUN's
super_writer/article.md and appends one JSONL row per RUN. No rewriting, no
network access, no WeChat side effects.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
SKILLS_ROOT = SKILL_ROOT.parent
DEFAULT_PATTERN_AUDIT = SKILLS_ROOT / "zh-human-writing" / "scripts" / "pattern_audit.py"
DEFAULT_OUTPUT = SKILL_ROOT / "audit" / "quality" / "ai-tone-calibration.jsonl"


def _load_pattern_audit(path: Path):
    if not path.is_file():
        raise FileNotFoundError(f"pattern_audit.py not found: {path}")
    spec = importlib.util.spec_from_file_location("ai_tone_pattern_audit", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    required = ("AI_TONE_FAMILIES", "detect_ai_tone_families", "mask_non_prose")
    if any(not hasattr(module, name) for name in required):
        raise ValueError(f"pattern_audit module lacks 77R operators: {path}")
    return module


def _default_runs_root() -> Path:
    project_root = os.environ.get("WXGZH_PROJECT_ROOT")
    if project_root:
        return Path(project_root) / ".temp" / "wxgzh-pipeline"
    return Path.cwd() / ".temp" / "wxgzh-pipeline"


def _model_from_run_id(run_id: str) -> str:
    match = re.match(r"^\d{8}T\d{6}-(.+)$", run_id)
    if not match:
        return "unknown"
    parts = match.group(1).split("-")
    if len(parts) > 1 and re.fullmatch(r"[0-9a-z]{6}", parts[-1]):
        parts = parts[:-1]
    return "-".join(parts) if parts else "unknown"


def _families(findings: list[dict]) -> dict[str, int]:
    counts = {family_id: 0 for family_id in ("LT-001", "LT-002", "LT-003",
                                             "LT-004", "LT-005", "LT-006")}
    for finding in findings:
        family_id = finding.get("rule_id")
        if family_id in counts:
            counts[family_id] += 1
    return counts


def _records(runs_root: Path, pattern_audit, run_filter: str | None):
    for article in sorted(runs_root.glob("*/super_writer/article.md")):
        run_dir = article.parent.parent
        run_id = run_dir.name
        if run_filter and run_filter not in run_id:
            continue
        text = article.read_text(encoding="utf-8", errors="replace")
        masked = pattern_audit.mask_non_prose(text)
        findings = pattern_audit.detect_ai_tone_families(
            masked, text, "essay", [])
        yield {
            "calibrated_at": datetime.now(timezone.utc).isoformat(),
            "run_id": run_id,
            "model": _model_from_run_id(run_id),
            "article_sha256": hashlib.sha256(article.read_bytes()).hexdigest(),
            "hanzi": len(re.findall(r"[一-鿿]", masked)),
            "families": _families(findings),
            "ai_tone_count": len(findings),
        }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-root", default=None,
                        help="frozen pipeline RUN root; defaults to <project>/.temp/wxgzh-pipeline")
    parser.add_argument("--output", default=None,
                        help="JSONL output path; defaults to pipeline audit/quality")
    parser.add_argument("--pattern-audit", default=None,
                        help="pattern_audit.py path; defaults to sibling zh-human-writing")
    parser.add_argument("--run-filter", default=None,
                        help="substring filter for RUN_ID")
    args = parser.parse_args(argv)

    runs_root = Path(args.runs_root) if args.runs_root else _default_runs_root()
    output = Path(args.output) if args.output else DEFAULT_OUTPUT
    pattern_path = (Path(args.pattern_audit) if args.pattern_audit
                    else DEFAULT_PATTERN_AUDIT)
    pattern_audit = _load_pattern_audit(pattern_path)
    if not runs_root.is_dir():
        parser.error(f"runs root not found: {runs_root}")

    rows = list(_records(runs_root, pattern_audit, args.run_filter))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("a", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    totals = {family_id: 0 for family_id in ("LT-001", "LT-002", "LT-003",
                                             "LT-004", "LT-005", "LT-006")}
    for row in rows:
        for family_id, count in row["families"].items():
            totals[family_id] += count
    print(json.dumps({
        "runs": len(rows), "runs_root": str(runs_root), "output": str(output),
        "totals": totals,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
