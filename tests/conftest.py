"""Conftest for media-enrichment tests."""

import sys
from pathlib import Path

# Add src to path
SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "src"))

FIXTURES_HTML = SKILL_ROOT / "fixtures" / "html"
FIXTURES_IMAGES = SKILL_ROOT / "fixtures" / "images"
SCHEMAS_DIR = SKILL_ROOT / "schemas"
EXAMPLES_DIR = SKILL_ROOT / "examples"
