"""77E/OBS-313:registry 一致性机械预检测试。

R1 registry 内同 URL 双 ID / R2 dedup links.original 空 / R3 registry↔dedup id 冲突 /
R4 dedup 内同 URL 双 ID / R5 ledger↔registry 双通道 URL 对齐。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_DIR / "scripts"))

import validate_single_product as VSP  # noqa: E402


def _reg(materials):
    return {"claims": [{"claim_id": "C-01", "claim_text": "t", "material_id": "M-01",
                        "source_url": materials[0]["source_url"], "source_excerpt": "e"}],
            "materials": materials}


def _mat(mid, url, did="d-1"):
    return {"material_id": mid, "dedup_id": did, "source_url": url}


def _dedup(items):
    return [{"id": it["id"], "source_url": it["source_url"],
             "links": {"original": it.get("original", "https://o.example/x")}}
            for it in items]


def _write(tmp, name, obj):
    p = tmp / name
    p.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    return p


def test_registry_duplicate_url_two_ids_rejected(tmp_path):
    reg = _reg([_mat("M-01", "https://s.example/a"), _mat("M-02", "https://s.example/a", "d-2")])
    p = _write(tmp_path, "registry.json", reg)
    errs, _ = VSP.check_registry(p)
    joined = "\n".join(errs)
    assert "同 URL 双 ID" in joined and "77E/OBS-313" in joined, joined


def test_dedup_links_original_null_rejected(tmp_path):
    reg = _reg([_mat("M-01", "https://s.example/a")])
    reg_p = _write(tmp_path, "registry.json", reg)
    dedup = _write(tmp_path, "dedup.json", _dedup([{"id": "d-1", "source_url": "https://s.example/a",
                                                    "original": None}]))
    errs, _ = VSP.check_registry(reg_p, dedup=dedup)
    joined = "\n".join(errs)
    assert "links.original" in joined and "禁止 null" in joined, joined


def test_registry_dedup_id_conflict_rejected_and_clean_pass(tmp_path):
    # 冲突:dedup 同 URL id=d-9 ≠ registry dedup_id=d-1
    reg = _reg([_mat("M-01", "https://s.example/a", "d-1")])
    reg_p = _write(tmp_path, "registry.json", reg)
    dedup_bad = _write(tmp_path, "dedup_bad.json",
                       _dedup([{"id": "d-9", "source_url": "https://s.example/a"}]))
    errs, _ = VSP.check_registry(reg_p, dedup=dedup_bad)
    joined = "\n".join(errs)
    assert "dedup_id" in joined and "77E/OBS-313" in joined, joined
    # 干净形态全过
    dedup_ok = _write(tmp_path, "dedup_ok.json",
                      _dedup([{"id": "d-1", "source_url": "https://s.example/a"}]))
    errs2, _ = VSP.check_registry(reg_p, dedup=dedup_ok)
    assert errs2 == [], errs2


def test_ledger_registry_dual_channel_mismatch_rejected(tmp_path):
    reg = _reg([_mat("M-01", "https://s.example/a")])
    reg_p = _write(tmp_path, "registry.json", reg)
    ledger = tmp_path / "ledger.yaml"
    ledger.write_text(
        "material_ledger:\n  materials:\n"
        "    - id: mat-001\n      source_url: \"https://s.example/OTHER\"\n",
        encoding="utf-8")
    errs, _ = VSP.check_registry(reg_p, ledger=ledger)
    joined = "\n".join(errs)
    assert "双通道" in joined and "77E/OBS-313" in joined, joined
    # 对齐形态过
    ledger2 = tmp_path / "ledger2.yaml"
    ledger2.write_text(
        "material_ledger:\n  materials:\n"
        "    - id: mat-001\n      source_url: \"https://s.example/a\"\n",
        encoding="utf-8")
    errs2, _ = VSP.check_registry(reg_p, ledger=ledger2)
    assert errs2 == [], errs2
