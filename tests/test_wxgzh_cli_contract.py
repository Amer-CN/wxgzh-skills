#!/usr/bin/env python3
"""wxgzh-pipeline dev2-hotfix1 CLI contract test.

The wxgzh-pipeline orchestrator subprocess-executes THESE super-writer validators
during the super_writer stage (material ingestion / article length full-mode /
semantic map). This test locks the exact CLI flags the orchestrator relies on, so
a future change here can't silently break the pipeline's real invocation.
"""
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"

CONTRACT = {
    "material_ingestion.py": ["--ledger", "--output"],
    "validate_article_length.py": ["--article", "--full-mode"],
    "validate_semantic_map.py": ["--article", "--semantic-map"],
}


def test_validators_exist():
    for name in CONTRACT:
        assert (SCRIPTS / name).is_file(), f"missing validator {name}"


def test_cli_flags_declared():
    for name, flags in CONTRACT.items():
        src = (SCRIPTS / name).read_text(encoding="utf-8")
        for flag in flags:
            assert f"'{flag}'" in src or f'"{flag}"' in src, f"{name} must accept {flag}"


def test_validators_help_runs():
    """argparse --help must exit 0 and mention the contract flags (proves real CLI)."""
    for name, flags in CONTRACT.items():
        proc = subprocess.run([sys.executable, "-X", "utf8", str(SCRIPTS / name), "--help"],
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=60)
        assert proc.returncode == 0, f"{name} --help failed: {proc.stderr[:300]}"
        for flag in flags:
            assert flag in proc.stdout, f"{name} --help missing {flag}"
