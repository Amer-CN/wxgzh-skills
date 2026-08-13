"""档72B-2 OBS-225:exit-1 警告的 receipt 是有效 receipt(§0-6)。

问题:validate_receipt 把任一官方校验器 exit != 0 判为 receipt 无效,
verify_receipt 又以其为第一步 → exit-1 的 receipt 写下即无效 →
receipt_valid()/verify_receipt() 双假 → resume 视该阶段未执行并重跑
(OBS-217 叠加成死循环)。

修法(单一真源 R106):execmodel.validator_exit_acceptable /
WARNING_EXIT_ALLOWED 是唯一判定点;receipts.py 与 stages 3c 都消费它。

四条用例:
① exit-1 receipt → validate_receipt 返回空列表
② exit-1 receipt(落盘)→ verify_receipt 首元素 True
③ exit-1 全跑(不用 stop_after)→ COMPLETE 且 media_enrichment 已执行,
   resume 返回 ALREADY_COMPLETE 且 zh receipt 逐字不变(不被重跑)
④ exit-2 receipt → validate_receipt 仍报错(安全带:只放行 1)
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from wxgzh_pipeline import execmodel as EM
from wxgzh_pipeline.receipts import (
    load_receipt,
    receipt_path,
    validate_receipt,
    verify_receipt,
)
from wxgzh_pipeline.state import sha256_file

REPO_ROOT = Path(__file__).resolve().parents[1]

_OV_FIELDS = ("path", "sha256", "command", "exit_code", "stdout_sha256", "stderr_sha256")


def _shim(name: str) -> Path:
    p = EM.resolve_agent_validator(
        "zh-human-writing", f"scripts/{name}", "fake_live", REPO_ROOT)
    assert p.is_file(), p
    return p


def _ov(rel: str, exit_code: int) -> dict:
    p = _shim(Path(rel).name)
    return {
        "path": str(p),
        "sha256": sha256_file(p),
        "command": ["python", rel],
        "exit_code": exit_code,
        "stdout_sha256": hashlib.sha256(b"{}").hexdigest(),
        "stderr_sha256": hashlib.sha256(b"").hexdigest(),
    }


def _write_exit_receipt(tmp_path: Path, exit_code: int) -> dict:
    sd = tmp_path / "zh_human_writing"
    sd.mkdir(parents=True, exist_ok=True)
    (sd / "final_article.md").write_text("# article\n", encoding="utf-8")
    (sd / "fidelity_report.json").write_text("{}", encoding="utf-8")
    output_files = [sd / "final_article.md", sd / "fidelity_report.json"]
    receipt = {
        "stage": "zh_human_writing",
        "skill_name": "zh-human-writing",
        "skill_dir": str(_shim("fidelity_guard.py").parent),
        "skill_version": "0.1.0",
        "skill_root_sha256": "0" * 64,
        "invoked_entrypoint": str(_shim("fidelity_guard.py")),
        "entrypoint_path": None,
        "entrypoint_sha256": None,
        "input_files": [],
        "input_hashes": {},
        "output_files": [str(p) for p in output_files],
        "output_hashes": {p.name: sha256_file(p) for p in output_files},
        "validator_path": None,
        "validator_sha256": None,
        "validator_exit_code": 0,
        "official_validator": None,
        "official_validators": [
            _ov("scripts/fidelity_guard.py", exit_code),
            _ov("scripts/pattern_audit.py", 0),
            _ov("scripts/change_report.py", 0),
        ],
        "network_mode": "fake_live",
        "started_at": "2026-08-08T00:00:00Z",
        "ended_at": "2026-08-08T00:00:01Z",
        "elapsed_seconds": 1.0,
        "side_effects": [],
    }
    assert not validate_receipt(receipt) or exit_code == 2, validate_receipt(receipt)
    receipt_path(tmp_path, "zh_human_writing").write_text(
        json.dumps(receipt, ensure_ascii=False), encoding="utf-8")
    return receipt


def test_obs225_exit1_receipt_validate_ok(tmp_path):
    _write_exit_receipt(tmp_path, 1)
    r = load_receipt(tmp_path, "zh_human_writing")
    assert validate_receipt(r) == []


def test_obs225_exit1_receipt_verify_ok(tmp_path):
    _write_exit_receipt(tmp_path, 1)
    ok, mism, extra = verify_receipt(tmp_path, "zh_human_writing",
                                     skills_home=str(REPO_ROOT))
    assert ok is True, mism
    assert mism == []
    assert extra["skill_root_state"] == "OK"


def test_obs225_exit1_full_run_media_executes_and_no_rerun(orch, monkeypatch):
    monkeypatch.setenv("WXGZH_FAKE_FIDELITY_EXIT", "1")
    out = orch.run("t")
    assert out["status"] == "COMPLETE", out
    assert "media_enrichment" in out.get("completed_stages", []), out
    run_dir = Path(out["run_dir"])
    zh_receipt_file = receipt_path(run_dir, "zh_human_writing")
    before = zh_receipt_file.read_bytes()
    out2 = orch.resume(out["run_id"])
    # 若 exit-1 receipt 无效(修前行为),resume 会判定 zh 未执行并重跑,
    # 返回 COMPLETE 而非 ALREADY_COMPLETE,且 receipt 时间戳变化。
    assert out2["status"] == "ALREADY_COMPLETE", out2
    assert out2["verify"]["zh_human_writing"]["ok"] is True
    assert zh_receipt_file.read_bytes() == before


def test_obs225_exit2_receipt_still_invalid(tmp_path):
    _write_exit_receipt(tmp_path, 2)
    r = load_receipt(tmp_path, "zh_human_writing")
    errs = validate_receipt(r)
    assert any("official validator exit_code != 0 (2)" in e for e in errs), errs
