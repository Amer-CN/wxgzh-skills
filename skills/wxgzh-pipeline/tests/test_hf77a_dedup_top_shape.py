"""77A/OBS-307: deduplicated_items.json 顶层形状强制为数组。

dict/包装对象直接 FAIL_CLOSED，报错文案须指路 contracts/01_aihot.yaml。
"""
import json
from pathlib import Path
from types import SimpleNamespace

from wxgzh_pipeline.stages.aihot import content_validate

STAGE = "aihot"


def _run(tmp_path, payload):
    sd = tmp_path / STAGE
    sd.mkdir(parents=True)
    (sd / "deduplicated_items.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return content_validate(SimpleNamespace(), sd, SimpleNamespace())


def test_dict_top_shape_rejected_with_pointer(tmp_path):
    code, report, vpath, _vsha = _run(tmp_path, {"items": []})
    assert code == 1
    assert "AIHOT" in report
    assert "数组" in report["reason"]
    assert "01_aihot.yaml" in report["reason"]
    assert vpath.endswith("validate_stage_receipt.py")


def test_wrapped_items_object_rejected(tmp_path):
    code, report, _vpath, _vsha = _run(tmp_path, {"items": [{"id": "M-001"}]})
    assert code == 1
    assert "dict" in report["reason"] or "包装" in report["reason"]


def test_real_list_still_passes(tmp_path):
    code, report, _vpath, _vsha = _run(tmp_path, [{"id": "M-001", "source_url": "https://s/x"}])
    assert code == 0
    assert report.get("AIHOT") == "PASS"
