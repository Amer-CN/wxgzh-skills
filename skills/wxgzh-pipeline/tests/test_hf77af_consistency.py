"""77AF consistency checker tests (tmp fixtures only, no history RUN touch)."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT))


def _load_verifier():
    spec = importlib.util.spec_from_file_location(
        "wxgzh_verify_report_consistency_77af",
        SKILL_ROOT / "scripts" / "verify_report_consistency.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


V = _load_verifier()

STAGES_6 = ["aihot", "super_writer", "zh_human_writing",
            "media_enrichment", "gzh_design", "wechat_draft"]

EXPECTED = {
    "aihot": ["raw_items.json", "deduplicated_items.json", "fetch_log.json"],
    "super_writer": ["generation-profile.yaml", "writing-brief.md",
                     "material-readiness.yaml", "material-ingestion-report.json",
                     "material-ledger.yaml", "evidence-map.md",
                     "canonical_claim_registry.json", "core-card.md", "outline.md",
                     "semantic-map.yaml", "article.md", "editor-report.md",
                     "handoff.yaml", "full_mode_validator_report.json"],
    "zh_human_writing": ["final_article.md", "fidelity_report.json"],
    "media_enrichment": ["media_manifest.json", "article_image_bindings.json",
                         "upload_events.json"],
    "gzh_design": ["final.html", "final_runtime.html",
                   "component_usage_report.json", "theme_identity_report.json"],
    "wechat_draft": ["draft_before.json", "draft_after.json",
                     "draft_creation_result.json"],
}

SKILL_OF = {"aihot": "aihot", "super_writer": "super-writer",
            "zh_human_writing": "zh-human-writing",
            "media_enrichment": "media-enrichment", "gzh_design": "gzh-design",
            "wechat_draft": "gzh-design"}


def _sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _make_receipts(run_dir: Path) -> None:
    for st in STAGES_6:
        sd = run_dir / st
        sd.mkdir(parents=True, exist_ok=True)
        out_paths = []
        hashes = {}
        for name in EXPECTED[st]:
            fp = sd / name
            if not fp.exists():  # 真实内容已由构建步骤写入的，按现状取哈希
                fp.write_bytes(("# " + st + "/" + name + "\n").encode())
            out_paths.append(str(fp))
            hashes[name] = _sha_bytes(fp.read_bytes())
        receipt = {
            "stage": st, "skill_name": SKILL_OF[st],
            "skill_dir": str(SKILL_ROOT.parent / SKILL_OF[st]),
            "skill_version": "0.0.0-test", "skill_root_sha256": "0" * 64,
            "invoked_entrypoint": "test", "entrypoint_path": None,
            "entrypoint_sha256": None, "input_files": [], "input_hashes": {},
            "output_files": out_paths, "output_hashes": hashes,
            "validator_path": None, "validator_sha256": None,
            "validator_exit_code": 0, "official_validator": None,
            "official_validators": [], "network_mode": "offline_fixture",
            "started_at": "2026-09-13T00:00:00Z",
            "ended_at": "2026-09-13T00:00:01Z", "elapsed_seconds": 1.0,
            "side_effects": [],
        }
        _write(sd / "stage_receipt.json",
               json.dumps(receipt, ensure_ascii=False))


def _pattern_stdout(ai_tone=2, advisory=3, strong=0, hard=0, stat=1) -> dict:
    def _items(n, prefix):
        return [{"rule_id": prefix + "-" + str(i)} for i in range(n)]
    hi = _items(strong, "SC")
    return {
        "hard_residue": {"count": hard, "items": _items(hard, "HR")},
        "strong_contextual": {"count": strong, "high_confidence": hi,
                              "low_confidence": []},
        "advisory_only": {"count": advisory, "items": _items(advisory, "AO")},
        "statistical": {"count": stat, "items": _items(stat, "ST")},
        "ai_tone": {"count": ai_tone, "items": _items(ai_tone, "LT")},
        "overall": {"pass_fail": "pass", "description": "test"},
    }


def _fidelity_report(total=13, passes=13, fails=0, warnings=0,
                     with_pattern=False, with_six=False) -> dict:
    d = {"total_checks": total, "passes": passes, "fails": fails,
         "warnings": warnings, "fail_details": [], "warning_details": [],
         "rolled_back": [], "pending_confirmation": [],
         "NEW_UNREGISTERED_FACTS": 0, "NUMBER_CHANGES": 0,
         "ATTRIBUTION_LOSS": 0, "QUALIFIER_LOSS": 0,
         "CLAIM_SEMANTIC_CHANGE": 0, "HARD_RESIDUE": 0,
         "gates": {"NEW_UNREGISTERED_FACTS": 0, "NUMBER_CHANGES": 0,
                   "ATTRIBUTION_LOSS": 0, "QUALIFIER_LOSS": 0,
                   "CLAIM_SEMANTIC_CHANGE": 0, "HARD_RESIDUE": 0}}
    if with_pattern:
        d["pattern_audit"] = {"overall": "pass", "hard_residue_count": 0,
                              "ai_tone_count": 0,
                              "statistical_review_only": ["ST-005"]}
    if with_six:
        d["six_family_changes"] = {"a1": 0, "a2": 0, "a3": 0,
                                   "a4": 0, "a5": 0, "a6": 0}
    return d


def _guard_stdout(total=13, passes=13, fails=0, warnings=0) -> dict:
    return _fidelity_report(total, passes, fails, warnings)


def _handoff_text(dims=(4, 5, 4, 4, 4), total=21) -> str:
    a, b, c, d_, e = dims
    return ("handoff:\n  title_candidates:\n    - T1\n"
            "  title_selection_reason: \"T1=" + "x" + "，" + "点击欲望 "
            + str(a) + "，" + "事实匹配 " + str(b) + "，" + "人群匹配 "
            + str(c) + "，" + "差异化 " + str(d_) + "，" + "长期价值 "
            + str(e) + "，" + "风险标记：" + "无。" + "推荐结构："
            + "主标题选候选一（总分 " + str(total) + "）。\"\n")


def _wall_text(entries=(("aihot", 10.0), ("super_writer", 20.0))) -> str:
    total = sum(v for _, v in entries)
    stages = [[k, v] for k, v in entries]
    return json.dumps({"stage_wall_total_seconds": total,
                       "run_wall_seconds": total + 0.5,
                       "delta_seconds": -0.5, "stages": stages},
                      ensure_ascii=False)


def _media_files(run_dir: Path, landed_basis: str, request_basis: str,
                 with_provenance: bool = False, n: int = 2) -> None:
    md = run_dir / "media_enrichment"
    approvals, reqs, rassets, man_assets = [], [], [], []
    for i in range(n):
        aid = "A-" + str(i).zfill(3)
        url = "https://example.com/" + str(i) + ".jpg"
        ap = {"approval_id": "AP-" + str(i), "approved_scope": "single_asset",
              "approved_at": "2026-09-13T00:00:00Z", "approved_by": "auto_rule",
              "asset_id": aid, "material_id": "mat-001",
              "source_page_url": "https://aihot.news/items/x",
              "resolved_original_url": url, "asset_sha256": "0" * 64,
              "asset_identity_sha256": "1" * 64,
              "discovery_manifest_sha256": "2" * 64,
              "approval_evidence_sha256": "3" * 64,
              "approval_readiness_sha256": "4" * 64, "basis": landed_basis}
        if with_provenance:
            ap["basis_provenance"] = V.MECHANICAL_PROVENANCE_FALLBACK
        approvals.append(ap)
        reqs.append({"approval_id": "AP-" + str(i),
                     "approved_scope": "single_asset",
                     "approved_at": "2026-09-13T00:00:00Z",
                     "approved_by": "auto_rule", "asset_id": aid,
                     "asset_identity_sha256": "1" * 64,
                     "asset_sha256": "0" * 64,
                     "basis": request_basis,
                     "discovery_manifest_sha256": "2" * 64,
                     "material_id": "mat-001",
                     "resolved_original_url": url,
                     "source_page_url": "https://aihot.news/items/x",
                     "approval_evidence_sha256": "3" * 64})
        rassets.append({"asset_id": aid, "decision": "eligible",
                        "approvable": True, "approvable_blockers": []})
        man_assets.append({"asset_id": aid, "decision": "eligible",
                           "asset_approval_consumed": True, "reasons": []})
    _write(md / "copyright_approval.json",
           json.dumps({"schema_version": "1.0", "run_id": run_dir.name,
                       "generated_at": "2026-09-13T00:00:00Z",
                       "approvals": approvals}, ensure_ascii=False))
    _write(md / "media_continuation_request.json",
           json.dumps({"article": {"path": "../zh/final_article.md",
                                   "sha256": "0" * 64},
                       "asset_approvals": reqs}, ensure_ascii=False))
    _write(md / "approval_readiness.json",
           json.dumps({"schema_version": "1.0", "run_id": run_dir.name,
                       "assets": rassets}, ensure_ascii=False))
    man_path = md / "media_manifest.json"
    _write(man_path, json.dumps({"assets": man_assets, "warnings": []},
                                ensure_ascii=False))


def _build_clean_run(run_dir: Path) -> None:
    zh = run_dir / "zh_human_writing"
    pa = _pattern_stdout()
    _write(zh / "pattern_audit.stdout.json",
           json.dumps(pa, ensure_ascii=False))
    _write(zh / "fidelity_report.json",
           json.dumps(_fidelity_report(), ensure_ascii=False))
    _write(zh / "fidelity_guard.stdout.json",
           json.dumps(_guard_stdout(), ensure_ascii=False))
    _write(zh / "final_article.md", "# test\n")
    sw = run_dir / "super_writer"
    _write(sw / "handoff.yaml", _handoff_text())
    _write(run_dir / "wall_self_check.json", _wall_text())
    basis = "auto_rule lane(test): basis-t"
    _media_files(run_dir, basis, basis, with_provenance=False)
    _make_receipts(run_dir)  # 内容全部落盘后生成回执，哈希取终态内容


def _status(report: dict, name: str) -> str:
    for c in report["checks"]:
        if c["name"] == name:
            return c["status"]
    raise AssertionError("check missing: " + name)


def test_77af_clean_synthetic_run_passes(tmp_path):
    rd = tmp_path / "run-clean"
    _build_clean_run(rd)
    rep = V.verify_run(rd)
    assert rep["overall"] == "PASS", rep
    assert all(c["status"] == "PASS" for c in rep["checks"]), rep


def test_77af_forged_title_total_fails(tmp_path):
    rd = tmp_path / "run-forge-title"
    _build_clean_run(rd)
    hp = rd / "super_writer" / "handoff.yaml"
    hp.write_text(_handoff_text(dims=(4, 5, 4, 4, 4), total=99),
                  encoding="utf-8")
    rep = V.verify_run(rd)
    assert rep["overall"] == "FAIL", rep
    assert _status(rep, "title_scores") == "FAIL"


def test_77af_forged_wall_total_fails(tmp_path):
    rd = tmp_path / "run-forge-wall"
    _build_clean_run(rd)
    d = json.loads((rd / "wall_self_check.json").read_text(encoding="utf-8"))
    d["stage_wall_total_seconds"] = 999999.0
    (rd / "wall_self_check.json").write_text(
        json.dumps(d, ensure_ascii=False), encoding="utf-8")
    rep = V.verify_run(rd)
    assert rep["overall"] == "FAIL", rep
    assert _status(rep, "wall_sums") == "FAIL"


def test_77af_forged_fidelity_numbers_fail(tmp_path):
    rd = tmp_path / "run-forge-fid"
    _build_clean_run(rd)
    fp = rd / "zh_human_writing" / "fidelity_report.json"
    d = json.loads(fp.read_text(encoding="utf-8"))
    d["passes"] = 1
    fp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    rep = V.verify_run(rd)
    assert rep["overall"] == "FAIL", rep
    assert _status(rep, "fidelity_numbers_gates") == "FAIL"


def test_77af_pattern_advisory_omission_fails(tmp_path):
    rd = tmp_path / "run-adv"
    _build_clean_run(rd)
    zh = rd / "zh_human_writing"
    pa = _pattern_stdout(ai_tone=18, advisory=36, strong=2, hard=0)
    (zh / "pattern_audit.stdout.json").write_text(
        json.dumps(pa, ensure_ascii=False), encoding="utf-8")
    fr = _fidelity_report(with_pattern=True, with_six=False)
    (zh / "fidelity_report.json").write_text(
        json.dumps(fr, ensure_ascii=False), encoding="utf-8")
    rep = V.verify_run(rd)
    assert _status(rep, "pattern_audit_counts") == "FAIL", rep
    assert rep["overall"] == "FAIL", rep


def test_77af_six_family_contradiction_fails(tmp_path):
    rd = tmp_path / "run-six"
    _build_clean_run(rd)
    zh = rd / "zh_human_writing"
    pa = _pattern_stdout(ai_tone=18, advisory=36, strong=2, hard=0)
    (zh / "pattern_audit.stdout.json").write_text(
        json.dumps(pa, ensure_ascii=False), encoding="utf-8")
    fr = _fidelity_report(with_pattern=True, with_six=True)
    fr["six_family_changes"] = {"k1": 2, "k2": 2, "k3": 1,
                                "k4": 0, "k5": 0, "k6": 0}
    (zh / "fidelity_report.json").write_text(
        json.dumps(fr, ensure_ascii=False), encoding="utf-8")
    rep = V.verify_run(rd)
    assert _status(rep, "fidelity_numbers_gates") == "FAIL", rep
    assert rep["overall"] == "FAIL", rep


def test_77af_basis_pre77ad_consistent_passes(tmp_path):
    rd = tmp_path / "run-basis-old"
    _build_clean_run(rd)
    rep = V.verify_run(rd)
    assert _status(rep, "approval_basis") == "PASS", rep


def test_77af_basis_77ad_request_handfilled_fails(tmp_path):
    rd = tmp_path / "run-basis-new"
    _build_clean_run(rd)
    fn, load_contract, prov, lerr = V._load_mechanical_fn()
    assert lerr is None, lerr
    contract = load_contract()
    rd_map = {"asset_id": "A-000", "decision": "eligible",
              "approvable": True, "approvable_blockers": []}
    asset = SimpleNamespace(decision="eligible", copyright_status="",
                            resolved_original_url="https://example.com/0.jpg")
    expected = fn("live", {}, contract, rd_map, asset)
    assert expected, "mechanical should bless synthetic asset"
    _media_files(rd, expected, "auto_rule lane(hand-filled): xxx",
                 with_provenance=True, n=2)
    rep = V.verify_run(rd)
    assert _status(rep, "approval_basis") == "FAIL", rep
    assert rep["overall"] == "FAIL", rep


def test_77af_basis_77ad_fully_mechanical_passes(tmp_path):
    rd = tmp_path / "run-basis-ok"
    _build_clean_run(rd)
    fn, load_contract, prov, lerr = V._load_mechanical_fn()
    assert lerr is None, lerr
    contract = load_contract()
    asset = SimpleNamespace(decision="eligible", copyright_status="",
                            resolved_original_url="https://example.com/0.jpg")
    rd_map = {"asset_id": "A-000", "decision": "eligible",
              "approvable": True, "approvable_blockers": []}
    expected = fn("live", {}, contract, rd_map, asset)
    assert expected
    _media_files(rd, expected, expected, with_provenance=True, n=2)
    rep = V.verify_run(rd)
    assert _status(rep, "approval_basis") == "PASS", rep


def test_77af_drift_only_classifier():
    assert V._is_drift_only([]) is True
    assert V._is_drift_only(["entrypoint hash mismatch"]) is True
    assert V._is_drift_only(["official_validator script missing: x"]) is True
    assert V._is_drift_only(["output hash mismatch: final_article.md"]) is False
    assert V._is_drift_only(["entrypoint hash mismatch",
                             "output missing: a.json"]) is False
