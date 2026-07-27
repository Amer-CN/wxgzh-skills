"""dev5 doc test: DOCUMENTED_ENTRY_EXISTS.

Every scripts/*.py path referenced in SKILL.md / README.md must exist,
and the phantom entry scripts/media_enrichment.py must not be referenced.
"""

import re
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]

DOC_FILES = ["SKILL.md", "README.md"]
SCRIPT_REF_RE = re.compile(r"scripts/([A-Za-z0-9_]+\.py)")


class TestDocumentedEntryExists:
    def test_documented_entry_exists(self):
        """DOCUMENTED_ENTRY_EXISTS: all referenced script entries exist on disk."""
        missing = []
        referenced = set()
        for doc in DOC_FILES:
            text = (SKILL_ROOT / doc).read_text(encoding="utf-8")
            for m in SCRIPT_REF_RE.finditer(text):
                referenced.add(m.group(1))
                if not (SKILL_ROOT / "scripts" / m.group(1)).exists():
                    missing.append(f"{doc} -> scripts/{m.group(1)}")
        assert referenced, "docs must reference at least one script entry"
        assert missing == [], f"documented entries missing on disk: {missing}"

    def test_phantom_entry_not_referenced(self):
        for doc in DOC_FILES:
            text = (SKILL_ROOT / doc).read_text(encoding="utf-8")
            assert "scripts/media_enrichment.py" not in text, \
                f"{doc} still references the non-existent scripts/media_enrichment.py"

    def test_real_entry_documented(self):
        skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        assert "scripts/run_media_enrichment.py" in skill_text
        assert (SKILL_ROOT / "scripts" / "run_media_enrichment.py").exists()
