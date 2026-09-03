"""77X/OBS-364:input_contract Step 3 追加 3f supplemental 分流测试。

与 validate_media_manifest.py REQUEST_MATERIAL_PERMALINK_LANE 同口径:
①supplemental + aihot_permalink=null 通过(无站内页属预期);
②supplemental + 外站 permalink 拒(error 含 77X/OBS-364)。
normal/缺省不新增门槛(77W 口径),不在本档断言范围。
"""
import json
from pathlib import Path

from media_enrichment.input_contract import compute_file_sha256, validate_request


def _request_with_supplemental(permalink) -> dict:
    return {
        "schema_version": "1.0", "run_id": "test-77x-supplemental",
        "article": {"path": "article.md", "sha256": "a" * 64},
        "materials": [{
            "material_id": "M-SUP", "aihot_permalink": permalink,
            "source_url": "https://example.org/sup", "title": "T",
            "selected_claim_ids": ["C-01"], "provenance": "supplemental",
        }],
        "claims": [{"claim_id": "C-01", "claim_text": "A", "material_id": "M-SUP",
                    "source_url": "https://example.org/sup", "source_excerpt": "A"}],
        "config": {"network_mode": "offline_fixture", "upload_mode": "dry_run"},
    }


def _write_and_validate(tmp_path: Path, request: dict):
    article = tmp_path / "article.md"
    article.write_text("test", encoding="utf-8")
    request["article"]["sha256"] = compute_file_sha256(article)
    req_path = tmp_path / "request.json"
    req_path.write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")
    return validate_request(req_path)


def test_supplemental_null_permalink_passes(tmp_path):
    """①supplemental + permalink=null:通过(无站内页应填 null)。"""
    result = _write_and_validate(
        tmp_path, _request_with_supplemental(None))
    assert result.valid, f"Errors: {result.errors}"


def test_supplemental_offsite_permalink_rejected(tmp_path):
    """②supplemental + 外站 permalink:拒,error 含 77X/OBS-364。"""
    result = _write_and_validate(
        tmp_path, _request_with_supplemental("https://huggingface.co/blog"))
    assert not result.valid
    assert any("77X/OBS-364" in e for e in result.errors)
    assert any("无站内页应填 null" in e for e in result.errors)
