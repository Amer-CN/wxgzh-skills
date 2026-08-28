"""77M/OBS-330: container/type enum sync guard + article pre-check tests."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
VSP = SCRIPT_DIR / "validate_single_product.py"
CATALOG = Path(__file__).resolve().parents[1] / "references" / "component-catalog.md"
RENDER_ARTICLE = Path(__file__).resolve().parents[2] / "gzh-design" / "scripts" / "render_article.py"


def _run_vsp(product, content):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(content)
        f.flush()
        result = subprocess.run(
            [sys.executable, str(VSP), "--product", product, "--file", f.name],
            capture_output=True, text=True, encoding="utf-8")
    import os
    os.unlink(f.name)
    return json.loads(result.stdout)


def test_container_type_sync_with_render_article():
    """77M/OBS-330: ALERT_TYPES/QUOTE_TYPES in VSP must match render_article.py."""
    sys.path.insert(0, str(SCRIPT_DIR))
    from validate_single_product import ALERT_TYPES, QUOTE_TYPES, CONTAINER_TYPES

    if RENDER_ARTICLE.is_file():
        import importlib.util
        spec = importlib.util.spec_from_file_location("_ra", RENDER_ARTICLE)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert ALERT_TYPES == mod.ALERT_TYPES, "ALERT_TYPES out of sync with render_article.py"
        assert QUOTE_TYPES == mod.QUOTE_TYPES, "QUOTE_TYPES out of sync with render_article.py"
        assert CONTAINER_TYPES == mod.CONTAINER_TYPES, "CONTAINER_TYPES out of sync"
    else:
        # gzh-design not in this repo tree; just check they exist
        assert ALERT_TYPES == frozenset({"note", "tip", "important", "warning", "caution"})
        assert QUOTE_TYPES == frozenset({"normal", "highlight", "sourced"})


def test_catalog_contains_container_section():
    """77M/OBS-330: component-catalog.md must document alert/quote type enums."""
    txt = CATALOG.read_text(encoding="utf-8")
    assert ":::alert" in txt, "catalog missing :::alert type enum"
    assert ":::quote" in txt, "catalog missing :::quote type enum"
    assert "ALERT_TYPES" in txt
    assert "QUOTE_TYPES" in txt


def test_article_invalid_alert_type_rejected():
    """77M/OBS-330: invalid alert type in article is rejected with catalog pointer."""
    article = ':::alert type="info"\nbody\n:::\n'
    result = _run_vsp("article", article)
    assert not result["valid"], "invalid alert type must fail"
    assert any("component-catalog.md" in e for e in result["errors"]), \
        "error must point to component-catalog.md"


def test_article_valid_alert_type_passes():
    """77M/OBS-330: valid alert type passes."""
    article = ':::alert type="warning"\nbody\n:::\n'
    result = _run_vsp("article", article)
    assert result["valid"], f"valid alert type must pass, got: {result['errors']}"
