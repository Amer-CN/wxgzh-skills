"""档72B-1R OBS-214/224:fidelity_guard exit 1 是警告不是失败(§0-4 的可测化)。

§0-4 把 fidelity_guard.py 的 exit 1 从「非 0 即失败」中拆分出来:
exit 1 → official_validator_warnings,不抬升阶段 exit_code;
exit 2/3 → 仍进 official_validators_failed,阶段 STAGE_FAILED。

fake_live shim 通过 WXGZH_FAKE_FIDELITY_EXIT 注入口确定性模拟两种退出码。
注入口默认关闭(R104):未设环境变量时 shim 行为与原来逐字相同
(PASS + exit 0),该「默认关闭」断言由 test_obs223_shim_cli_contract.py
在剔除该键后运行 shim 守护。

exit=1 用例为什么用 stop_after 而不是全跑:
receipts.validate_receipt(不在 R99-A 授权范围)仍把「任一官方校验器
exit != 0」判为 receipt 无效,media_enrichment 的 must_run_after_verified
契约会因此拒绝 zh_human_writing 的 receipt(新发现,待后续档修)。
全跑会撞上这一层,与 §0-4 本身无关;stop_after 让本测试只验证
§0-4 的语义:exit 1 不失败 zh 阶段,exit 2 失败 zh 阶段。
"""
from __future__ import annotations

import json
from pathlib import Path

from wxgzh_pipeline.receipts import load_receipt


def _stage_result(run_dir: Path) -> dict:
    p = run_dir / "zh_human_writing" / "stage_result.json"
    return json.loads(p.read_text(encoding="utf-8"))


def test_obs214_fidelity_exit1_is_warning_not_failure(orch, monkeypatch):
    monkeypatch.setenv("WXGZH_FAKE_FIDELITY_EXIT", "1")
    out = orch.run("t", stop_after="zh_human_writing")
    # 若 §0-4 失效(exit 1 仍当失败),这里会是 STAGE_FAILED。
    assert out["status"] == "STOPPED_AFTER", out
    assert out.get("stage") == "zh_human_writing", out
    assert "zh_human_writing" in out.get("completed_stages", []), out
    # STOPPED_AFTER 返回不含 run_dir,按 paths 布局由 project_root + run_id 定位。
    run_dir = Path(orch.project_root) / ".temp" / "wxgzh-pipeline" / out["run_id"]
    stage = _stage_result(run_dir)
    assert stage["status"] == "success", stage
    report = stage["validator_report"]
    warnings = report.get("official_validator_warnings")
    assert warnings, f"缺少 official_validator_warnings: {report}"
    assert any(
        v.get("exit_code") == 1 and Path(v["path"]).name == "fidelity_guard.py"
        for v in warnings
    )
    assert "official_validators_failed" not in report
    # 阶段 exit_code 未被抬升:receipt 里 validator_exit_code 仍为 0。
    receipt = load_receipt(run_dir, "zh_human_writing")
    assert receipt["validator_exit_code"] == 0
    assert any(
        v.get("exit_code") == 1 and Path(v["path"]).name == "fidelity_guard.py"
        for v in receipt["official_validators"]
    )


def test_obs214_fidelity_exit2_is_still_failure(orch, monkeypatch):
    monkeypatch.setenv("WXGZH_FAKE_FIDELITY_EXIT", "2")
    out = orch.run("t")
    assert out["status"] == "STAGE_FAILED", out
    assert out.get("failed_stage") == "zh_human_writing", out
    report = _stage_result(Path(out["run_dir"]))["validator_report"]
    failed = report.get("official_validators_failed")
    assert failed, f"缺少 official_validators_failed: {report}"
    assert any(
        v.get("exit_code") == 2 and Path(v["path"]).name == "fidelity_guard.py"
        for v in failed
    )
    assert "official_validator_warnings" not in report
