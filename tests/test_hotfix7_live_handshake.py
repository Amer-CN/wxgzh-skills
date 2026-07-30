"""hotfix7 regressions for OBS-22 and OBS-23."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from wxgzh_pipeline import agent_handshake as AH
from wxgzh_pipeline.ack_cli import main as ack_main
from wxgzh_pipeline.execmodel import AGENT_EXPECTED_OUTPUTS, SUPER_WRITER_AGENT_OUTPUTS
from wxgzh_pipeline import producers as P

from conftest import FAKE_FIXTURE

LOCKED_SUPER_WRITER_VALIDATOR_SHA256 = (
    "f2f878b14a94692fd301db197a612923cf2d9b5a8d38825b4169fe372e3d9a92"
)


def _real_super_writer_root() -> Path:
    explicit = os.environ.get("WXGZH_REAL_SUPER_WRITER_ROOT")
    if explicit:
        root = Path(explicit)
    else:
        skills_home = os.environ.get("WXGZH_REAL_SKILLS_HOME")
        if not skills_home:
            raise AssertionError(
                "set WXGZH_REAL_SUPER_WRITER_ROOT or WXGZH_REAL_SKILLS_HOME"
            )
        root = Path(skills_home) / "super-writer"
    validator = root / "scripts" / "validate_article_length.py"
    assert validator.is_file(), f"locked Super Writer validator missing: {validator}"
    actual = hashlib.sha256(validator.read_bytes()).hexdigest()
    assert actual == LOCKED_SUPER_WRITER_VALIDATOR_SHA256, (
        f"locked Super Writer validator sha256 mismatch: {actual}"
    )
    return root


def _request(sd: Path, stage="aihot", outputs=None, run_dir=None):
    outputs = outputs or ["one.json", "two.json"]
    sd.mkdir(parents=True)
    upstream = {}
    if run_dir:
        upstream_path = run_dir / "upstream.json"
        upstream_path.write_text("{}", encoding="utf-8")
        upstream = {"upstream.json": AH.sha256_file(upstream_path)}
    AH.write_request(sd, stage, stage.replace("_", "-"), "test", outputs, {},
                     run_id="run-1", upstream_hashes=upstream)
    for name in outputs:
        (sd / name).write_text(json.dumps({"name": name}), encoding="utf-8")
    return outputs


def test_ack_cli_normal_agent_id_and_unicode_space_path(tmp_path, capsys):
    sd = tmp_path / "中文 目录" / "aihot"
    outputs = _request(sd)
    assert ack_main(["--stage-dir", str(sd), "--agent-id", "agent-7"]) == 0
    ack = json.loads(capsys.readouterr().out)
    assert ack["agent_id"] == "agent-7"
    assert ack["produced_files"] == sorted(outputs)
    assert set(ack["produced_hashes"]) == set(outputs)


def test_ack_cli_rejects_missing_output(tmp_path):
    sd = tmp_path / "aihot"
    outputs = _request(sd)
    (sd / outputs[-1]).unlink()
    assert ack_main(["--stage-dir", str(sd)]) == 1
    assert not (sd / AH.ACK_FILE).exists()


def test_ack_invalid_after_output_request_and_upstream_drift(tmp_path):
    run_dir = tmp_path / "run"
    sd = run_dir / "aihot"
    outputs = _request(sd, run_dir=run_dir)
    AH.write_ack_from_request(sd)
    assert AH.verify_ack(sd, "aihot", outputs, run_dir=run_dir)[0]
    (sd / outputs[0]).write_text("tamper", encoding="utf-8")
    assert not AH.verify_ack(sd, "aihot", outputs, run_dir=run_dir)[0]
    (sd / outputs[0]).write_text(json.dumps({"name": outputs[0]}), encoding="utf-8")
    AH.write_ack_from_request(sd)
    req = json.loads((sd / AH.REQUEST_FILE).read_text(encoding="utf-8"))
    req["inputs"]["changed"] = True
    (sd / AH.REQUEST_FILE).write_text(json.dumps(req), encoding="utf-8")
    assert not AH.verify_ack(sd, "aihot", outputs, run_dir=run_dir)[0]
    AH.write_request(sd, "aihot", "aihot", "test", outputs, {}, run_id="run-1",
                     upstream_hashes={"upstream.json": AH.sha256_file(run_dir / "upstream.json")})
    AH.write_ack_from_request(sd)
    (run_dir / "upstream.json").write_text('{"changed":true}', encoding="utf-8")
    ok, report = AH.verify_ack(sd, "aihot", outputs, run_dir=run_dir)
    assert not ok and report["upstream_drift"] == ["upstream.json"]


@pytest.mark.parametrize("stage", ["aihot", "super_writer", "zh_human_writing"])
def test_ack_cli_supports_all_agent_stages(tmp_path, stage):
    sd = tmp_path / stage
    outputs = _request(sd, stage=stage, outputs=AGENT_EXPECTED_OUTPUTS[stage])
    assert ack_main(["--stage-dir", str(sd)]) == 0
    assert AH.verify_ack(sd, stage, outputs)[0]


def test_super_writer_expected_outputs_are_complete_and_bound():
    assert SUPER_WRITER_AGENT_OUTPUTS == [
        "generation-profile.yaml", "writing-brief.md", "material-readiness.yaml",
        "material-ingestion-report.json", "material-ledger.yaml", "evidence-map.md",
        "canonical_claim_registry.json", "core-card.md", "outline.md",
        "semantic-map.yaml", "article.md", "editor-report.md",
        "full_mode_validator_report.json",
    ]


def test_super_writer_validator_command_has_complete_full_mode_paths(tmp_path):
    sd = tmp_path / "super_writer"
    sd.mkdir()
    for name in SUPER_WRITER_AGENT_OUTPUTS:
        (sd / name).write_text("x", encoding="utf-8")
    (sd / "generation-profile.yaml").write_text(yaml.safe_dump({
        "article_mode": "long", "target_visible_chars": 5000,
        "acceptable_min": 4500, "acceptable_max": 6500,
    }), encoding="utf-8")
    ctx = SimpleNamespace(run_dir=tmp_path)
    validators = P._agent_validator_args("super_writer", ctx, sd)
    argv = next(args for _, rel, args in validators if rel.endswith("validate_article_length.py"))
    for flag in ("--article", "--outline", "--full-mode", "--generation-profile",
                 "--brief", "--material-readiness", "--material-ledger",
                 "--material-report", "--evidence-map", "--core-card",
                 "--semantic-map", "--editor-report", "--article-mode",
                 "--target-visible-chars", "--acceptable-min", "--acceptable-max", "--json"):
        assert flag in argv
    assert argv[argv.index("--article-mode") + 1] == "long"
    assert argv[argv.index("--target-visible-chars") + 1] == "5000"


def test_super_writer_policy_reads_declared_profile_without_article_inference(tmp_path):
    sd = tmp_path / "super_writer"
    sd.mkdir()
    with pytest.raises(ValueError):
        P._super_writer_policy(sd)
    (sd / "generation-profile.yaml").write_text(yaml.safe_dump({
        "article_mode": "long", "target_visible_chars": 4512,
        "acceptable_min": 4500, "acceptable_max": 6500,
    }), encoding="utf-8")
    policy = P._super_writer_policy(sd)
    assert policy["target_visible_chars"] == 4512
    # The parser reads only the declared profile; it never opens article.md.
    assert "article" not in policy


def _real_validator(stage_dir: Path, mode="long", target=4512, minimum=4500, maximum=6500):
    ctx = SimpleNamespace(run_dir=stage_dir.parent)
    argv = next(args for _, rel, args in P._agent_validator_args("super_writer", ctx, stage_dir)
                if rel.endswith("validate_article_length.py"))
    for flag, value in (("--article-mode", mode), ("--target-visible-chars", target),
                        ("--acceptable-min", minimum), ("--acceptable-max", maximum)):
        argv[argv.index(flag) + 1] = str(value)
    validator = _real_super_writer_root() / "scripts" / "validate_article_length.py"
    return subprocess.run([sys.executable, "-X", "utf8", str(validator), *argv],
                          capture_output=True, text=True, encoding="utf-8")


def test_cross_repo_real_full_mode_long_pass(tmp_path):
    sd = tmp_path / "super_writer"
    shutil.copytree(FAKE_FIXTURE / "super_writer" / "outputs", sd)
    run = _real_validator(sd)
    assert run.returncode == 0, run.stdout + run.stderr
    assert json.loads(run.stdout)["passed"] is True


def test_cross_repo_medium_overlong_uses_declared_policy(tmp_path):
    sd = tmp_path / "super_writer"
    shutil.copytree(FAKE_FIXTURE / "super_writer" / "outputs", sd)
    # Keep all three artifacts consistent with a declared medium policy.
    profile = yaml.safe_load((sd / "generation-profile.yaml").read_text(encoding="utf-8"))
    profile.update(article_mode="medium", length_mode="medium", target_visible_chars=3000,
                   acceptable_min=2500, acceptable_max=4000)
    (sd / "generation-profile.yaml").write_text(yaml.safe_dump(profile, allow_unicode=True), encoding="utf-8")
    for name in ("writing-brief.md", "outline.md"):
        text = (sd / name).read_text(encoding="utf-8")
        text = text.replace("article_mode：long", "article_mode：medium")
        text = text.replace("length_mode：long", "length_mode：medium")
        text = text.replace("target_visible_chars：4512", "target_visible_chars：3000")
        text = text.replace("acceptable_min：4500", "acceptable_min：2500")
        text = text.replace("acceptable_max：6500", "acceptable_max：4000")
        if name == "outline.md":
            text = text.replace("planned_total_chars：4512", "planned_total_chars：3000")
        (sd / name).write_text(text, encoding="utf-8")
    run = _real_validator(sd, mode="medium", target=3000, minimum=2500, maximum=4000)
    result = json.loads(run.stdout)
    assert result["target_visible_chars"] == 3000
    assert result["visible_chars_no_whitespace"] == 4512
    assert result["length_status"] == "above_max"
    assert result["warnings"]


def test_cross_repo_missing_full_mode_artifact_fails(tmp_path):
    sd = tmp_path / "super_writer"
    shutil.copytree(FAKE_FIXTURE / "super_writer" / "outputs", sd)
    (sd / "core-card.md").unlink()
    run = _real_validator(sd)
    assert run.returncode != 0
    assert any("core-card.md" in error for error in json.loads(run.stdout)["errors"])


def test_pipeline_stage_fails_when_agent_full_mode_output_missing(tmp_path, skills_home):
    from wxgzh_pipeline.orchestrator import Orchestrator
    fixture = tmp_path / "fixture"
    shutil.copytree(FAKE_FIXTURE, fixture)
    (fixture / "super_writer" / "outputs" / "core-card.md").unlink()
    orch = Orchestrator(project_root=tmp_path / "project", network_mode="fake_live",
                        skills_home=skills_home, fixture_dir=fixture)
    out = orch.run("missing product")
    assert out["status"] == "STAGE_FAILED"
    assert out["failed_stage"] == "super_writer"


def test_corrupt_policy_fails_closed_but_runs_material_and_semantic(tmp_path, skills_home):
    from wxgzh_pipeline.orchestrator import Orchestrator
    fixture = tmp_path / "fixture"
    shutil.copytree(FAKE_FIXTURE, fixture)
    (fixture / "super_writer" / "outputs" / "generation-profile.yaml").write_text(
        "article_mode: long\n", encoding="utf-8")
    orch = Orchestrator(project_root=tmp_path / "project", network_mode="fake_live",
                        skills_home=skills_home, fixture_dir=fixture)
    out = orch.run("corrupt policy")
    assert out["status"] == "STAGE_FAILED" and out["failed_stage"] == "super_writer"
    receipt = json.loads((Path(out["run_dir"]) / "super_writer" / "stage_receipt.json").read_text(encoding="utf-8"))
    validators = receipt["official_validators"]
    assert validators[0]["exit_code"] == 2 and "generation-profile" in validators[0]["error"]
    paths = [item["path"] for item in validators[1:]]
    assert any(str(path).endswith("material_ingestion.py") for path in paths)
    assert any(str(path).endswith("validate_semantic_map.py") for path in paths)


def test_pipeline_rejects_agent_report_different_from_official(tmp_path, skills_home, monkeypatch):
    from wxgzh_pipeline.orchestrator import Orchestrator
    fixture = tmp_path / "fixture"
    shutil.copytree(FAKE_FIXTURE, fixture)
    real_run = P.run_script

    def divergent_runner(script, args, **kwargs):
        result = real_run(script, args, **kwargs)
        if str(script).endswith("validate_article_length.py"):
            body = json.loads(result["stdout"])
            body["target_visible_chars"] = 9999
            result["stdout"] = json.dumps(body, ensure_ascii=False)
            import hashlib
            result["stdout_sha256"] = hashlib.sha256(result["stdout"].encode("utf-8")).hexdigest()
        return result

    monkeypatch.setattr(P, "run_script", divergent_runner)
    orch = Orchestrator(project_root=tmp_path / "project", network_mode="fake_live",
                        skills_home=skills_home, fixture_dir=fixture)
    out = orch.run("report mismatch")
    assert out["status"] == "STAGE_FAILED"
    assert out["failed_stage"] == "super_writer"
