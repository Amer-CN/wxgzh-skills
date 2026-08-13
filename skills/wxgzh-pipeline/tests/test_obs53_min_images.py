import json
from pathlib import Path
import pytest

from wxgzh_pipeline.stages import load_validator

validate_media_bindings = load_validator("validate_media_bindings")


def _files(tmp_path, count=2):
    man = tmp_path / "media_manifest.json"
    bnd = tmp_path / "article_image_bindings.json"
    assets = []
    body = []
    for i in range(count):
        aid = f"A-{i+1:03d}"
        url = f"https://mmbiz.qpic.cn/{aid}"
        sha = f"{i+1:064d}"
        assets.append({"asset_id": aid, "decision": "eligible", "sha256": sha,
                       "upload": {"status": "success", "remote_url": url}})
        body.append({"asset_id": aid, "sha256": sha})
    man.write_text(json.dumps({"assets": assets}), encoding="utf-8")
    bnd.write_text(json.dumps({"body_images": body}), encoding="utf-8")
    return man, bnd


def test_explicit_min_two_passes_and_reports_source(tmp_path):
    man, bnd = _files(tmp_path)
    code, report = validate_media_bindings.validate(man, bnd, 2, "validation_config.json")
    assert code == 0
    assert report["min_required"] == 2
    assert report["body_images_min_source"] == "validation_config.json"


def test_default_min_remains_six_but_shortfall_degrades(tmp_path):
    """76C:body_images_min 保留目标值 6,但少图不再 FAIL——降级留痕。"""
    man, bnd = _files(tmp_path)
    code, report = validate_media_bindings.validate(man, bnd)
    assert code == 0  # 76C 降级:不足不再阻断
    assert report["min_required"] == 6
    assert report["image_shortfall"] is True
    assert report["image_shortfall_count"] == 4
    assert "76C 降级" in report.get("note", "")

@pytest.mark.parametrize("value", [0, -1])
def test_min_less_than_one_rejected(tmp_path, value):
    man, bnd = _files(tmp_path)
    with pytest.raises(ValueError, match=">= 1"):
        validate_media_bindings.validate(man, bnd, value)
