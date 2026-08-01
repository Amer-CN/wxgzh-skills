"""档28 P0-2: verify_receipt skill-root THREE-STATE判定 + relock ledger chain.

States (live mode only):
  OK             receipt root == installed root -> normal resume
  SKILL_UPGRADED mismatch + FULL traceable relock chain in the ledger ->
                 not a tamper; stage marked 需重跑; matched entry_ids returned
  TAMPERED       mismatch without a chain (incl. missing/empty/malformed
                 ledger) -> strict FAIL, exactly as before
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from conftest import SKILL_ROOT
from wxgzh_pipeline import receipts
from wxgzh_pipeline.receipts import verify_receipt
from wxgzh_pipeline.skill_discovery import compute_root_sha

STAGE = "gzh_design"
SKILL = "gzh-design"
EXPECTED_OUTPUTS = ("final.html", "final_runtime.html",
                    "component_usage_report.json", "theme_identity_report.json")


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _fake_tree(root: Path, marker: str) -> str:
    """Build a fake installed skill tree; returns its runtime root sha."""
    d = root / SKILL
    (d / "scripts").mkdir(parents=True, exist_ok=True)
    (d / "scripts" / "render.py").write_text(f"print('{marker}')\\n", encoding="utf-8")
    (d / "SKILL.md").write_text(f"---\\nname: gzh-design\\nmarker: {marker}\\n---\\n",
                                encoding="utf-8")
    sha, _ = compute_root_sha(d)
    return sha


def _write_receipt(run_dir: Path, skill_dir: Path, root_sha: str) -> dict:
    stage_dir = run_dir / STAGE
    stage_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for name in EXPECTED_OUTPUTS:
        p = stage_dir / name
        p.write_text("v", encoding="utf-8")
        outputs.append(p)
    vsha = _sha("v")
    rec = receipts.build_receipt(
        stage=STAGE, skill_name=SKILL, skill_dir=skill_dir,
        skill_version="v-test", skill_root_sha256=root_sha,
        invoked_entrypoint="echo hi", input_files=[],
        output_files=outputs,
        validator_path=str(stage_dir / "final.html"),
        validator_sha256=vsha, validator_exit_code=0,
        started_at="2026-08-01T00:00:00Z", ended_at="2026-08-01T00:00:01Z",
        entrypoint_path=str(stage_dir / "final.html"),
        entrypoint_sha256=vsha,
        official_validator={"path": str(stage_dir / "final.html"), "sha256": vsha,
                            "command": "x", "exit_code": 0,
                            "stdout_sha256": _sha("so"), "stderr_sha256": _sha("se")},
        official_validators=[],
        network_mode="live",
    )
    receipts.write_receipt(run_dir, STAGE, rec)
    return rec


@pytest.fixture
def env(tmp_path, monkeypatch):
    """run_dir + skills_home + fake ledger; monkeypatches the ledger path."""
    run_dir = tmp_path / "run"
    skills_home = tmp_path / "skills_home"
    ledger = tmp_path / "skills.lock.history.json"
    monkeypatch.setattr(receipts, "_history_path", lambda: ledger)
    return {"run_dir": run_dir, "skills_home": skills_home, "ledger": ledger}


def _ledger(env, records):
    env["ledger"].write_text(json.dumps(records, ensure_ascii=False, indent=2),
                             encoding="utf-8")


def _rec(entry_id, old, new, skill=SKILL):
    return {"entry_id": entry_id, "skill": skill,
            "old_root_sha256": old, "new_root_sha256": new,
            "old_manifest_sha256": "m", "new_manifest_sha256": "m",
            "old_file_count": 1, "new_file_count": 1,
            "reason": "test", "recorded_at": "2026-08-01T00:00:00Z",
            "doctor_result": "PASS"}


# ── 三态:OK ────────────────────────────────────────────────────────────────
def test_state_ok(env):
    skills_home = env["skills_home"]
    cur = _fake_tree(skills_home, "current")
    _write_receipt(env["run_dir"], skills_home / SKILL, cur)
    ok, mism, extra = verify_receipt(env["run_dir"], STAGE,
                                     skills_home=skills_home, network_mode="live")
    assert ok is True and not mism
    assert extra["skill_root_state"] == "OK"
    assert extra["upgrade_entry_ids"] == []


# ── 三态:SKILL_UPGRADED(单跳) ──────────────────────────────────────────────
def test_state_skilled_upgraded_single_hop(env):
    skills_home = env["skills_home"]
    cur = _fake_tree(skills_home, "current")
    _write_receipt(env["run_dir"], skills_home / SKILL, "old" * 32)
    _ledger(env, [_rec("e-relock-1", "old" * 32, cur)])
    ok, mism, extra = verify_receipt(env["run_dir"], STAGE,
                                     skills_home=skills_home, network_mode="live")
    assert ok is True
    assert extra["skill_root_state"] == "SKILL_UPGRADED"
    assert extra["upgrade_entry_ids"] == ["e-relock-1"]
    assert not any("skill_root" in m for m in mism)


# ── 三态:SKILL_UPGRADED(多跳链) ────────────────────────────────────────────
def test_state_upgraded_multi_hop(env):
    skills_home = env["skills_home"]
    cur = _fake_tree(skills_home, "current")
    mid = _sha("mid")
    _write_receipt(env["run_dir"], skills_home / SKILL, "old" * 32)
    _ledger(env, [_rec("e1", "old" * 32, mid), _rec("e2", mid, cur)])
    ok, mism, extra = verify_receipt(env["run_dir"], STAGE,
                                     skills_home=skills_home, network_mode="live")
    assert ok is True
    assert extra["skill_root_state"] == "SKILL_UPGRADED"
    assert extra["upgrade_entry_ids"] == ["e1", "e2"]


# ── 三态:TAMPERED(链中断) ─────────────────────────────────────────────────
def test_state_tampered_broken_chain(env):
    skills_home = env["skills_home"]
    cur = _fake_tree(skills_home, "current")
    mid = _sha("mid")
    _write_receipt(env["run_dir"], skills_home / SKILL, "old" * 32)
    _ledger(env, [_rec("e1", "old" * 32, mid),   # old -> mid
                  _rec("e2", mid, _sha("other"))])  # mid -> other (current missing)
    ok, mism, extra = verify_receipt(env["run_dir"], STAGE,
                                     skills_home=skills_home, network_mode="live")
    assert ok is False
    assert extra["skill_root_state"] == "TAMPERED"
    assert extra["upgrade_entry_ids"] == []
    assert any("skill_root" in m for m in mism)


# ── 台账缺失/为空/非法 -> TAMPERED ─────────────────────────────────────────
def test_tampered_history_missing(env):
    skills_home = env["skills_home"]
    cur = _fake_tree(skills_home, "current")
    _write_receipt(env["run_dir"], skills_home / SKILL, "old" * 32)
    ok, mism, extra = verify_receipt(env["run_dir"], STAGE,
                                     skills_home=skills_home, network_mode="live")
    assert ok is False and extra["skill_root_state"] == "TAMPERED"


def test_tampered_history_empty(env):
    skills_home = env["skills_home"]
    cur = _fake_tree(skills_home, "current")
    _write_receipt(env["run_dir"], skills_home / SKILL, "old" * 32)
    _ledger(env, [])
    ok, mism, extra = verify_receipt(env["run_dir"], STAGE,
                                     skills_home=skills_home, network_mode="live")
    assert ok is False and extra["skill_root_state"] == "TAMPERED"


def test_tampered_history_malformed_json(env):
    skills_home = env["skills_home"]
    cur = _fake_tree(skills_home, "current")
    _write_receipt(env["run_dir"], skills_home / SKILL, "old" * 32)
    env["ledger"].write_text("not json at all", encoding="utf-8")
    ok, mism, extra = verify_receipt(env["run_dir"], STAGE,
                                     skills_home=skills_home, network_mode="live")
    assert ok is False and extra["skill_root_state"] == "TAMPERED"


def test_tampered_history_not_a_list(env):
    skills_home = env["skills_home"]
    cur = _fake_tree(skills_home, "current")
    _write_receipt(env["run_dir"], skills_home / SKILL, "old" * 32)
    env["ledger"].write_text('{"skills": []}', encoding="utf-8")
    ok, mism, extra = verify_receipt(env["run_dir"], STAGE,
                                     skills_home=skills_home, network_mode="live")
    assert ok is False and extra["skill_root_state"] == "TAMPERED"


# ── 台账被篡改成任意值,不得把 TAMPERED 洗成 SKILL_UPGRADED ────────────────
def test_tampered_history_arbitrary_values(env):
    """Junk records (wrong skill / wrong old / non-dict / cycle / fake chain)
    must NEVER turn a mismatch into SKILL_UPGRADED."""
    skills_home = env["skills_home"]
    cur = _fake_tree(skills_home, "current")
    _write_receipt(env["run_dir"], skills_home / SKILL, "old" * 32)
    junk = [
        _rec("wrong-skill", "old" * 32, cur, skill="super-writer"),  # wrong skill
        _rec("wrong-old", "x" * 64, cur),                            # old doesn't match
        _rec("reversed", cur, "old" * 32),                           # backwards
        {"entry_id": "non-dict"},                                    # malformed
        _rec("cycle-1", "old" * 32, _sha("mid")),
        _rec("cycle-2", _sha("mid"), "old" * 32),                    # cycle back
        _rec("missing-fields", None, cur),                           # bad old
    ]
    _ledger(env, junk)
    ok, mism, extra = verify_receipt(env["run_dir"], STAGE,
                                     skills_home=skills_home, network_mode="live")
    assert ok is False
    assert extra["skill_root_state"] == "TAMPERED"
    assert extra["upgrade_entry_ids"] == []


def test_tampered_cycle_in_chain(env):
    """A pure loop that can never reach the current root must be TAMPERED."""
    skills_home = env["skills_home"]
    cur = _fake_tree(skills_home, "current")
    _write_receipt(env["run_dir"], skills_home / SKILL, "old" * 32)
    a, b = _sha("a"), _sha("b")
    _ledger(env, [_rec("e1", "old" * 32, a), _rec("e2", a, b),
                  _rec("e3", b, a)])            # loop a<->b, no path to cur
    ok, mism, extra = verify_receipt(env["run_dir"], STAGE,
                                     skills_home=skills_home, network_mode="live")
    assert ok is False and extra["skill_root_state"] == "TAMPERED"


def test_upgraded_chain_with_loop_noise(env):
    """A genuine chain that reaches current is accepted even if the ledger
    also contains an unrelated loop (arbitrary extra records never break a
    real, complete chain)."""
    skills_home = env["skills_home"]
    cur = _fake_tree(skills_home, "current")
    _write_receipt(env["run_dir"], skills_home / SKILL, "old" * 32)
    a, b = _sha("a"), _sha("b")
    _ledger(env, [_rec("e1", "old" * 32, a), _rec("e2", a, b),
                  _rec("e3", b, a),            # loop noise
                  _rec("e4", b, cur)])         # real hop to current
    ok, mism, extra = verify_receipt(env["run_dir"], STAGE,
                                     skills_home=skills_home, network_mode="live")
    assert ok is True
    assert extra["skill_root_state"] == "SKILL_UPGRADED"
    assert extra["upgrade_entry_ids"] == ["e1", "e2", "e4"]
