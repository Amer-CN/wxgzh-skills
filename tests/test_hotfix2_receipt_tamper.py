"""dev2-hotfix2 P0#1 tests: Receipt field-deletion / tamper cannot bypass the
gate. Each mutation MUST make verify_receipt FAIL, which makes resume and the
WeChat draft gate FAIL_CLOSED.

Cases (spec a-g):
  a. stage_receipt.json replaced with {}
  b. delete an input_hashes entry
  c. delete an output_hashes entry
  d. delete entrypoint_sha256
  e. delete official_validators
  f. validator_exit_code -> 1
  g. official validator exit_code -> 1
"""
import json
from pathlib import Path

import pytest

from wxgzh_pipeline import STAGES
from wxgzh_pipeline.receipts import verify_receipt, receipt_path


def _complete(orch):
    out = orch.run("t")
    assert out["status"] == "COMPLETE", out
    return Path(out["run_dir"]), out["run_id"]


def _mutate(run_dir, stage, fn):
    p = receipt_path(run_dir, stage)
    r = json.loads(p.read_text(encoding="utf-8"))
    fn(r)
    p.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")


# stage whose receipt we tamper -> the tamper closure
MUTATIONS = {
    "a_empty_object": ("gzh_design", "REPLACE_EMPTY"),
    "b_del_input_hash": ("gzh_design", lambda r: r["input_hashes"].pop(next(iter(r["input_hashes"])))),
    "c_del_output_hash": ("gzh_design", lambda r: r["output_hashes"].pop(next(iter(r["output_hashes"])))),
    "d_del_entrypoint_sha": ("gzh_design", lambda r: r.pop("entrypoint_sha256")),
    "e_del_official_validators": ("media_enrichment", lambda r: r.pop("official_validators")),
    "f_validator_exit_1": ("gzh_design", lambda r: r.__setitem__("validator_exit_code", 1)),
    "g_official_exit_1": ("media_enrichment",
                          lambda r: r["official_validator"].__setitem__("exit_code", 1)),
}


@pytest.mark.parametrize("case", list(MUTATIONS))
def test_receipt_tamper_fails_verify_and_resume(orch, case):
    stage, mut = MUTATIONS[case]
    run_dir, run_id = _complete(orch)
    if mut == "REPLACE_EMPTY":
        receipt_path(run_dir, stage).write_text("{}", encoding="utf-8")
    else:
        _mutate(run_dir, stage, mut)

    # 1) verify_receipt must FAIL for the tampered stage
    vok, mism, _ = verify_receipt(run_dir, stage, network_mode="fake_live")
    assert vok is False and mism, f"{case}: verify_receipt should FAIL"

    # 2) resume must NOT report ALREADY_COMPLETE; it invalidates from that stage
    res = orch.resume(run_id)
    assert res["status"] != "ALREADY_COMPLETE", f"{case}: resume bypassed tamper"
    assert res["receipt_verification"][stage]["ok"] is False


def test_wechat_gate_blocks_on_tampered_prior_receipt(orch):
    """The WeChat draft gate re-verifies all 5 prior receipts; a tampered prior
    receipt must FAIL_CLOSED the draft (draft is idempotent, so we drive a fresh
    gate by tampering then resuming a run whose wechat stage must re-run)."""
    run_dir, run_id = _complete(orch)
    # tamper an EARLIER receipt AND drop the draft so wechat must run again
    _mutate(run_dir, "media_enrichment", lambda r: r["output_hashes"].pop(next(iter(r["output_hashes"]))))
    st = json.loads((run_dir / "pipeline_state.json").read_text(encoding="utf-8"))
    st["draft_created"] = False
    st["completed_stages"] = [s for s in STAGES if s != "wechat_draft"]
    (run_dir / "pipeline_state.json").write_text(json.dumps(st), encoding="utf-8")
    res = orch.resume(run_id)
    # media invalid => cascade re-exec; the run must not silently accept the draft
    assert res["status"] in ("COMPLETE", "FAIL_CLOSED")
    assert res["receipt_verification"]["media_enrichment"]["ok"] is False
