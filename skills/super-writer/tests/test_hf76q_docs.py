"""76Q/OBS-287 文档税打包测试:registry dict 形状 / dedup-id ↔ material_id 映射 /
claim-material source_url 逐字一致(含锚点)三条规则在 material-ingestion.md 落档。
"""
from __future__ import annotations

from pathlib import Path

DOC = Path(__file__).resolve().parents[1] / "references" / "material-ingestion.md"


def test_docs_registry_dict_shape_declared():
    text = DOC.read_text(encoding="utf-8")
    assert "canonical_claim_registry" in text
    assert "顶层必须是 **对象（dict）**" in text
    assert "禁止数组" in text
    assert "76Q/OBS-287" in text


def test_docs_registry_example_has_claims_and_materials():
    text = DOC.read_text(encoding="utf-8")
    assert '"claims": [' in text and '"materials": [' in text
    for field in ("claim_id", "claim_text", "material_id", "source_url",
                  "source_excerpt", "dedup_id", "provenance"):
        assert field in text, f"示例缺字段 {field}"


def test_docs_dedup_material_mapping_rule():
    text = DOC.read_text(encoding="utf-8")
    assert "dedup-id ↔ material_id 映射" in text
    assert "deduplicated_items.json" in text
    assert "逐字一致" in text


def test_docs_source_url_verbatim_rule():
    text = DOC.read_text(encoding="utf-8")
    assert "逐字完全相等" in text
    assert "#anchor" in text
    assert "validate_single_product.py --product registry" in text
