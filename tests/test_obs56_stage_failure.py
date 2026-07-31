import json
from types import SimpleNamespace

import pytest

from wxgzh_pipeline.stages import (
    StageContext,
    StageError,
    _write_stage_failure,
    execute_stage,
)


def test_stage_failure_record_contains_streams_and_scrubs_argv(tmp_path):
    secret = "unit-test-secret-value"
    token = "unit-test-access-token"
    _write_stage_failure(
        tmp_path,
        "wechat_draft",
        {
            "command": [
                "python", "entry.py", "--app-secret", secret,
                f"https://example.invalid/?access_token={token}",
            ],
            "exit_code": 7,
            "stdout": f"stdout access_token={token}",
            "stderr": f"stderr secret={secret}",
            "elapsed_seconds": 1.25,
        },
        "entry.py",
    )

    record = json.loads((tmp_path / "stage_failure.json").read_text(encoding="utf-8"))
    serialized = json.dumps(record, ensure_ascii=False)
    assert record["exit_code"] == 7
    assert record["request_elapsed_seconds"] == 1.25
    assert "stdout" in record["stdout_tail"]
    assert "stderr" in record["stderr_tail"]
    assert secret not in serialized
    assert token not in serialized
    assert "<REDACTED>" in serialized


def test_execute_stage_writes_failure_before_raising(tmp_path, monkeypatch):
    import wxgzh_pipeline.stages as stages

    monkeypatch.setitem(stages.STAGE_SKILL, "obs56_test", "gzh-design")
    module = SimpleNamespace(
        STAGE="obs56_test",
        STAGE_CONFIG={},
        stage_inputs=lambda ctx, state: {},
        run_live=lambda ctx, state: ([], {
            "entrypoint_path": "entry.py",
            "entry_run": {
                "command": ["python", "entry.py"],
                "exit_code": 9,
                "stdout": "plain stdout",
                "stderr": "plain stderr",
                "elapsed_seconds": 0.5,
            },
        }),
    )
    ctx = StageContext(
        run_dir=tmp_path,
        skills_home=tmp_path,
        discovery={},
        network_mode="live",
    )
    state = SimpleNamespace(run_id="obs56-run")

    with pytest.raises(StageError):
        execute_stage(ctx, module, state)

    record = json.loads(
        (tmp_path / "obs56_test" / "stage_failure.json").read_text(encoding="utf-8"))
    assert record["exit_code"] == 9
    assert record["stdout_tail"] == "plain stdout"
    assert record["stderr_tail"] == "plain stderr"


def test_successful_stage_does_not_emit_stage_failure(tmp_path, monkeypatch):
    import wxgzh_pipeline.stages as stages

    monkeypatch.setitem(stages.STAGE_SKILL, "obs56_success", "gzh-design")
    monkeypatch.setattr(stages, "schema_validate", lambda obj, schema: [])
    monkeypatch.setattr(
        stages, "enforce_contract",
        lambda *args, **kwargs: (True, {"CONTRACT": "PASS"}))
    monkeypatch.setattr(stages, "build_receipt", lambda **kwargs: {})
    monkeypatch.setattr(stages, "write_receipt", lambda *args, **kwargs: None)
    module = SimpleNamespace(
        STAGE="obs56_success",
        STAGE_CONFIG={},
        stage_inputs=lambda ctx, state: {},
        run_live=lambda ctx, state: ([], {
            "entrypoint_path": "entry.py",
            "entry_run": {
                "command": ["python", "entry.py"],
                "exit_code": 0,
                "stdout": "ok",
                "stderr": "",
                "elapsed_seconds": 0.1,
            },
        }),
        content_validate=lambda ctx, sd, state: (0, {}, None, None),
        side_effects=lambda ctx, state: [],
        invoked_entrypoint=lambda ctx: "entry.py",
        post=lambda ctx, sd, state, exit_code, report: None,
    )
    ctx = StageContext(
        run_dir=tmp_path,
        skills_home=tmp_path,
        discovery={},
        network_mode="live",
    )
    state = SimpleNamespace(run_id="obs56-success")

    result = execute_stage(ctx, module, state)

    assert result["status"] == "success"
    assert not (tmp_path / "obs56_success" / "stage_failure.json").exists()
