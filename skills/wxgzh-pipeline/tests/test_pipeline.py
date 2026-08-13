"""wxgzh-pipeline behavior tests (CLI/defaults, locking, state machine, media,
draft delta, resume). Offline only — no WeChat side effects.
Covers spec test items 1-15, 24-25.
"""
import hashlib
import json
from pathlib import Path

import pytest

from conftest import load_validator
from wxgzh_pipeline import cli, STAGES
from wxgzh_pipeline import skill_discovery as SD
from wxgzh_pipeline.state import load_state
from wxgzh_pipeline.receipts import load_receipt


# ---- 1. topic extraction ----
@pytest.mark.parametrize("phrase,topic", [
    ("发文：Claude Opus 5", "Claude Opus 5"),
    ("发文:OpenAI最新模型", "OpenAI最新模型"),
    ("  发文： 本周值得关注的开源模型 ", "本周值得关注的开源模型"),
])
def test_01_topic_extraction(phrase, topic):
    cmd = cli.parse_command(phrase)
    assert cmd["command"] == "fabu" and cmd["topic"] == topic


def test_cli_other_commands():
    assert cli.parse_command("续发")["command"] == "resume"
    assert cli.parse_command("续发：RUN-1")["run_id"] == "RUN-1"
    assert cli.parse_command("进度")["command"] == "progress"
    assert cli.parse_command("验收编排Skill")["command"] == "release_audit"
    assert cli.parse_command("随便说点啥")["command"] == "unknown"


# ---- 2 & 3. default profile fast_publish + default target is a draft ----
def test_02_03_defaults_and_draft(orch):
    out = orch.run("Claude Opus 5")
    assert out["status"] == "COMPLETE"
    st = load_state(Path(out["run_dir"]))
    assert st.profile == "fast_publish"
    assert st.draft_created is True
    assert st.formally_published is False


# ---- 4. formal publish capability does not exist ----
def test_04_no_formal_publish_capability(skill_root):
    needles = ["cgi-bin/freepublish", "freepublish/submit", "cgi-bin/message/mass",
               "mass/sendall", "cgi-bin/draft/delete"]
    hits = []
    for p in (skill_root / "wxgzh_pipeline").rglob("*.py"):
        txt = p.read_text(encoding="utf-8")
        hits += [(p.name, n) for n in needles if n in txt]
    assert hits == []


# ---- helpers for locking tests: build a tiny fake skill + lock ----
def _mk_skill(root: Path, version="1.0.0", extra=None):
    root.mkdir(parents=True, exist_ok=True)
    (root / "VERSION").write_text(f"version: {version}\n", encoding="utf-8")
    (root / "SKILL.md").write_text("# fake\n", encoding="utf-8")
    if extra:
        (root / extra).write_text("x", encoding="utf-8")


def _lock_for(home: Path, name: str):
    sha, _ = SD.compute_root_sha(home / name)
    ver = SD._read_version(home / name, name)
    return {"skills": {name: {"skill_name": name, "skill_version": ver,
                              "skill_root_sha256": sha, "required_files": ["SKILL.md"]}}}


# ---- 5. skill missing => fail ----
def test_05_skill_missing_fails(tmp_path):
    home = tmp_path / "skills"; home.mkdir()
    lock = {"skills": {"foo": {"skill_name": "foo", "skill_version": "1.0.0",
                               "skill_root_sha256": "deadbeef", "required_files": ["SKILL.md"]}}}
    ok, disc = SD.verify_all(home, lock)
    assert not ok and disc["foo"]["exists"] is False


# ---- 6. version mismatch => fail ----
def test_06_version_mismatch_fails(tmp_path):
    home = tmp_path / "skills"; _mk_skill(home / "foo", "1.0.0")
    lock = _lock_for(home, "foo")
    _mk_skill(home / "foo", "9.9.9")  # bump version after locking
    ok, disc = SD.verify_all(home, lock)
    assert not ok and disc["foo"]["version_ok"] is False


# ---- 7. root hash mismatch => fail ----
def test_07_hash_mismatch_fails(tmp_path):
    home = tmp_path / "skills"; _mk_skill(home / "foo", "1.0.0")
    lock = _lock_for(home, "foo")
    (home / "foo" / "new_file.txt").write_text("changed", encoding="utf-8")  # mutate tree
    ok, disc = SD.verify_all(home, lock)
    assert not ok and disc["foo"]["hash_ok"] is False


# ---- 8. stages cannot be skipped (fixed order, all present) ----
def test_08_no_stage_skip(orch):
    out = orch.run("t")
    assert out["completed_stages"] == STAGES  # exactly the fixed order, none skipped


# ---- 9. missing stage receipt => stage treated as not executed ----
def test_09_missing_receipt_fails(orch, tmp_path):
    v = load_validator("validate_stage_receipt")
    code, rep = v.validate(tmp_path / "nope.json")
    assert code == 1 and rep["STAGE_RECEIPT"] == "FAIL"


# ---- 10. resume does not rerun completed stages / recreate draft ----
def test_10_resume_no_rerun(orch):
    out = orch.run("t")
    run_dir = Path(out["run_dir"])
    r1 = load_receipt(run_dir, "gzh_design")["started_at"]
    res = orch.resume(run_dir.name)
    assert res["status"] == "ALREADY_COMPLETE" and res["draft_created"] is True
    r2 = load_receipt(run_dir, "gzh_design")["started_at"]
    assert r1 == r2  # receipt untouched => not rerun


# ---- 11. final_article change invalidates downstream (freeze) ----
def test_11_article_freeze_invalidates_downstream(orch):
    v = load_validator("validate_article_freeze")
    fa = orch.fixture_dir / "zh_human_writing" / "outputs" / "final_article.md"
    good = hashlib.sha256(fa.read_bytes()).hexdigest()
    code_ok, _ = v.validate(fa, good)
    code_bad, rep = v.validate(fa, "0" * 64)
    assert code_ok == 0 and code_bad == 1 and rep["final_article_unchanged"] is False


# ---- 12. fewer than 6 images degrades with shortfall (76C) ----
def test_12_min_images_blocks(tmp_path):
    v = load_validator("validate_media_bindings")
    man = {"assets": [{"asset_id": f"A-{i}", "decision": "eligible", "sha256": str(i),
                       "upload": {"status": "success", "remote_url": "https://mmbiz.qpic.cn/x"}} for i in range(5)]}
    bnd = {"body_images": [{"asset_id": f"A-{i}", "sha256": str(i),
                            "wechat_remote_url": "https://mmbiz.qpic.cn/x"} for i in range(5)]}
    mp, bp = tmp_path / "m.json", tmp_path / "b.json"
    mp.write_text(json.dumps(man), encoding="utf-8"); bp.write_text(json.dumps(bnd), encoding="utf-8")
    code, rep = v.validate(mp, bp)
    # 76C: 图片数量不再是发文限制条件,不足时降级留痕,不再阻断。
    assert code == 0 and rep["min_met"] is False
    assert rep["image_shortfall"] is True and rep["image_shortfall_count"] == 1
    assert "blocking_reason" not in rep


# ---- 13. non-eligible (e.g. social share card) image cannot be bound ----
def test_13_non_eligible_binding_rejected(tmp_path):
    v = load_validator("validate_media_bindings")
    man = {"assets": [{"asset_id": "A-0", "decision": "rejected",  # social_share_card => rejected
                       "sha256": "s0", "upload": {"status": "skipped"}}]
                      + [{"asset_id": f"A-{i}", "decision": "eligible", "sha256": f"s{i}",
                          "upload": {"status": "success", "remote_url": "http://mmbiz.qpic.cn/x"}} for i in range(1, 7)]}
    bnd = {"body_images": [{"asset_id": f"A-{i}", "sha256": f"s{i}",
                            "wechat_remote_url": "http://mmbiz.qpic.cn/x"} for i in range(7)]}
    mp, bp = tmp_path / "m.json", tmp_path / "b.json"
    mp.write_text(json.dumps(man), encoding="utf-8"); bp.write_text(json.dumps(bnd), encoding="utf-8")
    code, rep = v.validate(mp, bp)
    assert code == 1 and any("A-0" in p for p in rep["problems"])


# ---- 14. image upload is serial (config) ----
def test_14_upload_serial():
    from wxgzh_pipeline.stages import media_enrichment as me
    assert me.STAGE_CONFIG["upload_serial"] is True
    assert me.STAGE_CONFIG["manifest_single_writer"] is True


# ---- 15. orchestrator must not bypass media-enrichment (no direct uploadimg) ----
def test_15_no_orchestrator_bypass(skill_root):
    from wxgzh_pipeline.stages import media_enrichment as me
    assert me.STAGE_CONFIG["no_orchestrator_bypass"] is True
    # the orchestrator itself performs no image upload endpoint call
    orch_src = (skill_root / "wxgzh_pipeline" / "orchestrator.py").read_text(encoding="utf-8")
    assert "media/uploadimg" not in orch_src


# ---- 24 & 25. draft delta: AFTER=BEFORE+1 and old drafts preserved ----
def test_24_25_draft_delta(tmp_path):
    v = load_validator("validate_draft_delta")
    before = {"total_count": 2, "drafts": [{"fingerprint": "a"}, {"fingerprint": "b"}]}
    after_ok = {"total_count": 3, "drafts": [{"fingerprint": "a"}, {"fingerprint": "b"}, {"fingerprint": "c"}]}
    after_lost = {"total_count": 3, "drafts": [{"fingerprint": "a"}, {"fingerprint": "c"}, {"fingerprint": "d"}]}
    bp = tmp_path / "b.json"; bp.write_text(json.dumps(before), encoding="utf-8")
    okp = tmp_path / "ok.json"; okp.write_text(json.dumps(after_ok), encoding="utf-8")
    lostp = tmp_path / "lost.json"; lostp.write_text(json.dumps(after_lost), encoding="utf-8")
    c1, r1 = v.validate(bp, okp)
    c2, r2 = v.validate(bp, lostp)
    assert c1 == 0 and r1["AFTER_eq_BEFORE_plus_1"] and r1["OLD_DRAFTS_PRESERVED"]
    assert c2 == 1 and r2["OLD_DRAFTS_PRESERVED"] is False


# ---- full run emits delivery + manifest + formally_published False ----
def test_full_run_delivery(orch):
    out = orch.run("Claude Opus 5")
    run_dir = Path(out["run_dir"])
    dv = load_validator("validate_delivery")
    code, rep = dv.validate(run_dir)
    assert code == 0 and rep["formally_published_false"] and rep["all_stage_receipts_present"]
