"""77N/OBS-335: VSP --product article ** bold ban mechanical check tests."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
VSP = SCRIPT_DIR / "validate_single_product.py"


def _run_vsp_article(content: str) -> dict:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(content)
        f.flush()
        result = subprocess.run(
            [sys.executable, str(VSP), "--product", "article", "--file", f.name],
            capture_output=True, text=True, encoding="utf-8")
    os.unlink(f.name)
    return json.loads(result.stdout)


def test_bold_marker_outside_fence_rejected_with_pointer():
    """77N/OBS-335: ** in body (fenced-outside) → FAIL pointing to 76Q/OBS-286."""
    result = _run_vsp_article("正文 **加粗** 残留。\n")
    assert not result["valid"], "bold marker must fail"
    assert any("76Q/OBS-286" in e and "**" in e for e in result["errors"]), result["errors"]


def test_clean_article_and_fenced_bold_pass():
    """77N/OBS-335: clean body passes; ** inside fenced code block is exempt."""
    result = _run_vsp_article("正文干净。\n\n```bash\n# comment ** not bold\n```\n")
    assert result["valid"], f"expected pass, got: {result['errors']}"
