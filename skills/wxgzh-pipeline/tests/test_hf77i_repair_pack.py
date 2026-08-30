"""77I repair-pack focused tests."""

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from wxgzh_pipeline import agent_handshake as AH
from wxgzh_pipeline import producers as PR
from wxgzh_pipeline.stages import zh_human_writing as ZW

SW_ROOT = Path(__file__).resolve().parents[2] / "super-writer"
sys.path.insert(0, str(SW_ROOT / "scripts"))
import validate_single_product as VSP  # noqa: E402


def _clean_audit():
    return {
        "hard_residue": {"count": 0, "items": []},
        "strong_contextual": {"count": 0, "high_confidence": [], "low_confidence": []},
        "advisory_only": {"count": 0, "items": []},
    }


def test_obs319_missing_fidelity_gates_default_zero(tmp_path):
    sd = tmp_path / "zh_human_writing"
    sd.mkdir()
    (sd / "final_article.md").write_text("正常句子。", encoding="utf-8")
    (sd / "fidelity_report.json").write_text("{}", encoding="utf-8")
    (sd / "pattern_audit.stdout.json").write_text(
        json.dumps(_clean_audit()), encoding="utf-8")
    code, report, _, _ = ZW.content_validate(
        SimpleNamespace(skills_home=str(tmp_path)), sd, SimpleNamespace())
    assert code == 0, report
    assert set(report["zero_gate_defaults"]) == set(ZW._ZERO_GATES)


def test_obs319_explicit_fidelity_violation_still_rejects(tmp_path):
    sd = tmp_path / "zh_human_writing"
    sd.mkdir()
    (sd / "final_article.md").write_text("正常句子。", encoding="utf-8")
    (sd / "fidelity_report.json").write_text(
        json.dumps({"NUMBER_CHANGES": 1}), encoding="utf-8")
    (sd / "pattern_audit.stdout.json").write_text(
        json.dumps(_clean_audit()), encoding="utf-8")
    code, report, _, _ = ZW.content_validate(
        SimpleNamespace(skills_home=str(tmp_path)), sd, SimpleNamespace())
    assert code == 1
    assert report["gates"]["NUMBER_CHANGES"] == 1


def _registry(material):
    url = material["source_url"]
    return {
        "claims": [{"claim_id": "C-01", "claim_text": "text",
                    "material_id": material["material_id"],
                    "source_url": url, "source_excerpt": "excerpt"}],
        "materials": [material],
    }


def test_obs320_missing_material_media_fields_rejected(tmp_path):
    material = {"material_id": "M-01", "dedup_id": "d-1",
                "source_url": "https://s.example/a"}
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(_registry(material), ensure_ascii=False),
                    encoding="utf-8")
    errors, _ = VSP.check_registry(path)
    joined = "\n".join(errors)
    assert "缺必填字段 `title`" in joined
    assert "缺必填字段 `aihot_permalink`" in joined
    assert "77I/OBS-320" in joined


def test_obs320_material_permalink_must_match_dedup(tmp_path):
    material = {"material_id": "M-01", "dedup_id": "d-1",
                "title": "title", "aihot_permalink": "https://wrong.example/a",
                "source_url": "https://s.example/a"}
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(_registry(material), ensure_ascii=False),
                    encoding="utf-8")
    dedup = tmp_path / "dedup.json"
    dedup.write_text(json.dumps([{"id": "d-1",
                                  "source_url": "https://s.example/a",
                                  "aihot_permalink": "https://aihot.example/a",
                                  "links": {"original": "https://o.example/a"}}]),
                     encoding="utf-8")
    errors, _ = VSP.check_registry(path, dedup=dedup)
    joined = "\n".join(errors)
    assert "aihot_permalink" in joined
    assert "77I/OBS-320" in joined


def test_obs320_complete_registry_fields_pass(tmp_path):
    material = {"material_id": "M-01", "dedup_id": "d-1",
                "title": "title", "aihot_permalink": "https://aihot.example/a",
                "source_url": "https://s.example/a"}
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(_registry(material), ensure_ascii=False),
                    encoding="utf-8")
    dedup = tmp_path / "dedup.json"
    dedup.write_text(json.dumps([{"id": "d-1",
                                  "source_url": "https://s.example/a",
                                  "aihot_permalink": "https://aihot.example/a",
                                  "links": {"original": "https://o.example/a"}}]),
                     encoding="utf-8")
    errors, _ = VSP.check_registry(path, dedup=dedup)
    assert errors == []


def test_obs322_title_playbook_fail_blocks_and_points_to_playbook(tmp_path):
    handoff = {"handoff": {
        "schema_version": "2.2",
        "prose_craft_applied": True,
        "prose_craft_version": "1.0",
        "formatter": {"cover": {"kicker": "深度观察"}},
        "title_candidates": ["标题一", "标题二", "标题三"],
        "hook_line": "hook",
        "selected_title": "标题一",
        "title_selection_reason": "选择标题一",
    }}
    path = tmp_path / "handoff.yaml"
    yaml_text = "\n".join([
        "handoff:",
        "  schema_version: '2.2'",
        "  prose_craft_applied: true",
        "  prose_craft_version: '1.0'",
        "  formatter:",
        "    cover:",
        "      kicker: 深度观察",
        "  title_candidates:",
        "    - 标题一",
        "    - 标题二",
        "    - 标题三",
        "  hook_line: hook",
        "  selected_title: 标题一",
        "  title_selection_reason: 选择标题一",
    ])
    path.write_text(yaml_text, encoding="utf-8")
    errors, checks = VSP.check_handoff(path)
    assert errors and "references/title-playbook.md" in errors[0]
    warnings = checks["title_playbook_errors"]
    assert any("分组覆盖不足" in warning for warning in warnings)
    assert any("缺五维评分" in warning for warning in warnings)
    assert any("缺风险标记" in warning for warning in warnings)


def test_obs321_resume_reuses_frozen_request(tmp_path, monkeypatch):
    sd = tmp_path / "super_writer"
    sd.mkdir()
    ctx = SimpleNamespace(run_dir=tmp_path, network_mode="live",
                          skills_home=tmp_path, env={}, fake_agent=None)
    state = SimpleNamespace(run_id="run-1", topic="topic",
                            final_article_sha256=None, items_file=None)
    expected = ["out.txt"]
    (sd / "stage_request.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(PR, "_upstream_hashes", lambda ctx, stage: {})
    monkeypatch.setattr(PR, "_skill_identity",
                        lambda ctx, stage: {"skill_name": "super-writer"})
    monkeypatch.setattr(PR, "_contract_sha", lambda stage: "contract")
    monkeypatch.setattr(PR, "_agent_validator_args", lambda stage, ctx, sd: [])

    original_write = AH.write_request
    calls = []

    def spy_write(*args, **kwargs):
        calls.append((args, kwargs))
        return original_write(*args, **kwargs)

    monkeypatch.setattr(AH, "write_request", spy_write)

    outputs, meta = PR._agent(ctx, "super_writer", sd, expected, expected, state)
    assert meta["handshake"]["HANDSHAKE"] == "AWAITING_AGENT"
    assert len(calls) == 1

    (sd / "out.txt").write_text("output", encoding="utf-8")
    AH.write_ack(sd, "super_writer", expected)
    request_before = (sd / AH.REQUEST_FILE).read_bytes()

    outputs, meta = PR._agent(ctx, "super_writer", sd, expected, expected, state)
    assert meta["handshake"]["HANDSHAKE"] == "PASS"
    assert len(calls) == 1
    assert (sd / AH.REQUEST_FILE).read_bytes() == request_before
