"""Stage executor + context. Each stage: writes stage_request.json, produces
outputs (offline_fixture copies canned outputs; live would invoke the real
sub-skill), runs a content validator whose exit code is embedded in the receipt,
then writes stage_result.json + stage_receipt.json. No stage may be skipped.
"""
from __future__ import annotations

import hashlib
import importlib.util
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from ..state import atomic_write_json, sha256_file
from ..receipts import build_receipt, write_receipt, now
from ..contracts import validate as schema_validate
from ..contracts import enforce_contract
from ..execmodel import STAGE_SKILL  # single source of truth (dev2-hotfix2)

SKILL_ROOT = Path(__file__).resolve().parents[2]


class StageError(Exception):
    pass


_SENSITIVE_ARG = re.compile(
    r"(?i)(access[_-]?token|app[_-]?secret|secret|password|authorization|api[_-]?key)")
_SENSITIVE_QUERY = re.compile(
    r"(?i)(access_token|wechat_app_secret|app_secret|secret|appsecret|password|api_key)"
    r"([\"']?\s*[:=]\s*[\"']?)([^&\s,}\"']+)")


def _scrub_text(value) -> str:
    return _SENSITIVE_QUERY.sub(r"\1\2<REDACTED>", str(value or ""))


def _scrub_argv(argv) -> list[str]:
    result = []
    hide_next = False
    for raw in argv or []:
        item = str(raw)
        if hide_next:
            result.append("<REDACTED>")
            hide_next = False
        elif item.startswith("--") and "=" in item:
            key, value = item.split("=", 1)
            result.append(f"{key}=<REDACTED>" if _SENSITIVE_ARG.search(key) else _scrub_text(item))
        else:
            result.append(_scrub_text(item))
            hide_next = item.startswith("--") and bool(_SENSITIVE_ARG.search(item))
    return result


def _write_stage_failure(sd: Path, stage: str, entry_run: dict, entry_path) -> None:
    command = entry_run.get("command") or []
    atomic_write_json(sd / "stage_failure.json", {
        "stage": stage,
        "entry": str(entry_path or ""),
        "exit_code": entry_run.get("exit_code"),
        "stdout_tail": _scrub_text(entry_run.get("stdout", "")[-2000:]),
        "stderr_tail": _scrub_text(entry_run.get("stderr", "")[-2000:]),
        "request_elapsed_seconds": entry_run.get(
            "elapsed_seconds", entry_run.get("elapsed")),
        "argv": _scrub_argv(command),
        "recorded_at": now(),
    })


class StageAwait(Exception):
    """Raised when an agent-driven stage is waiting for the agent to fulfill its
    handshake (live mode, no ACK yet). Not a failure — a clean pause."""
    pass


class MediaApprovalAwait(Exception):
    """Raised after real media discovery while awaiting a frozen stable approval."""

    def __init__(self, discovery_manifest: str, approval_file: str):
        super().__init__("awaiting stable media asset approval")
        self.discovery_manifest = discovery_manifest
        self.approval_file = approval_file


@dataclass
class StageContext:
    run_dir: Path
    skills_home: Path
    discovery: dict
    network_mode: str = "offline_fixture"
    fixture_dir: Path | None = None
    env: dict = field(default_factory=dict)
    create_wechat_draft: bool = True
    fake_agent: object = None

    def stage_dir(self, stage: str) -> Path:
        d = Path(self.run_dir) / stage
        d.mkdir(parents=True, exist_ok=True)
        return d


def load_validator(name: str):
    """Import a wxgzh-pipeline validator module by file name (no package needed)."""
    path = SKILL_ROOT / "validators" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_val_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def subskill_validator_sha(ctx: StageContext, skill: str, rel: str | None) -> tuple[str | None, str | None]:
    if not rel:
        return None, None
    p = Path(ctx.skills_home) / skill / rel
    return (str(p), sha256_file(p)) if p.is_file() else (str(p), None)


def _copy_fixture_outputs(ctx: StageContext, stage: str) -> list[Path]:
    src = Path(ctx.fixture_dir) / stage / "outputs"
    dst = ctx.stage_dir(stage)
    copied = []
    if src.is_dir():
        for p in sorted(src.rglob("*")):
            if p.is_file():
                rel = p.relative_to(src)
                target = dst / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(p, target)
                copied.append(target)
    return copied


def execute_stage(ctx: StageContext, module, state) -> dict:
    """Run one stage via its module hooks. Returns stage_result dict."""
    stage = module.STAGE
    skill = STAGE_SKILL[stage]
    sd = ctx.stage_dir(stage)
    started = now()

    # 1. stage_request.json (schema-validated)
    request = {
        "run_id": state.run_id, "stage": stage, "skill_name": skill,
        "inputs": module.stage_inputs(ctx, state), "network_mode": ctx.network_mode,
        "config": getattr(module, "STAGE_CONFIG", {}),
    }
    req_errs = schema_validate(request, "stage_request")
    if req_errs:
        raise StageError(f"{stage}: invalid stage_request: {req_errs}")
    atomic_write_json(sd / "stage_request.json", request)

    # 2. produce outputs by network mode
    meta = {}
    if ctx.network_mode == "offline_fixture":
        outputs = _copy_fixture_outputs(ctx, stage)
        if stage == "gzh_design":
            # unit-test mode execution evidence: fixture copy, honestly labeled;
            # NEVER reported as an official gzh-design call.
            atomic_write_json(sd / "gzh_execution_evidence.json", {
                "simulated": True, "mode": "offline_fixture", "fixture_copy": True,
                "official_gzh_call": False})
    else:
        outputs, meta = module.run_live(ctx, state)  # real: handshake / subprocess / wechat
        if meta.get("await_media_approval"):
            raise MediaApprovalAwait(
                meta.get("discovery_manifest", ""), meta.get("approval_file", ""))
        if meta.get("await_agent"):
            raise StageAwait(f"{stage}: awaiting agent handshake (no ACK yet)")
        if meta.get("handshake_failed"):
            raise StageError(f"{stage}: agent handshake verification failed: {meta.get('handshake')}")
        er = meta.get("entry_run")
        if er and er.get("exit_code") not in (0, None):
            _write_stage_failure(sd, stage, er, meta.get("entrypoint_path"))
            raise StageError(
                f"{stage}: entrypoint subprocess failed (exit {er['exit_code']}): "
                f"{_scrub_text(er.get('stderr'))}")
        if stage == "gzh_design":
            official = ctx.network_mode in ("live", "integration")
            ev = {"simulated": not official, "mode": ctx.network_mode,
                  "official_gzh_call": official,
                  "render_entry_path": meta.get("entrypoint_path"),
                  "entry_path": meta.get("entrypoint_path"),
                  "entry_sha256": meta.get("entrypoint_sha256"),
                  "command": (meta.get("entry_run") or {}).get("command"),
                  "exit_code": (meta.get("entry_run") or {}).get("exit_code")}
            if official:
                # real install-source proof (P0#1): recompute the installed runtime
                # hashes AND read the EXTERNAL install receipt generated at install
                # time (<skills_home>/.install-receipts/gzh-design.json — never inside
                # the skill tree, so no commit/hash self-reference). Theme identity
                # three-way compares recomputed == receipt == lock; a missing or
                # mismatched receipt leaves install_source_commit None => FAIL.
                from ..skill_discovery import (_file_sha,
                                               compute_root_sha,
                                               compute_runtime_manifest_sha,
                                               read_install_receipt)
                gdir = Path(ctx.skills_home) / "gzh-design"
                comp = gdir / "scripts" / "generate_hammer_upgrade_samples.py"
                render_entry = Path(meta.get("entrypoint_path"))
                ev["entry_sha256"] = _file_sha(render_entry)
                ev["component_source_path"] = str(comp)
                root_sha, _ = compute_root_sha(gdir)
                man_sha, _ = compute_runtime_manifest_sha(gdir)
                ev["installed_root_sha256"] = root_sha
                ev["installed_runtime_manifest_sha256"] = man_sha
                receipt = read_install_receipt(ctx.skills_home, "gzh-design")
                if receipt:
                    ev["install_source_commit"] = receipt.get("full_commit_sha")
                    ev["install_receipt_root_sha256"] = receipt.get("installed_runtime_root_sha256")
                    ev["install_receipt_manifest_sha256"] = receipt.get("installed_runtime_manifest_sha256")
                    ev["install_receipt_repository_url"] = receipt.get("repository_url")
                else:
                    ev["install_source_commit"] = None
            atomic_write_json(sd / "gzh_execution_evidence.json", ev)

    # 3. content validation (in-repo real validators)
    exit_code, vreport, vpath, vsha = module.content_validate(ctx, sd, state)

    # 3b. YAML contract enforcement (FULL consumption of contracts/*.yaml, P0#7)
    declared_side_effects = module.side_effects(ctx, state)
    cok, creport = enforce_contract(stage, sd, ctx=ctx, state=state,
                                    side_effects=declared_side_effects)
    vreport = dict(vreport)
    vreport["contract"] = creport
    if not cok and exit_code == 0:
        exit_code = 1

    # 3c. official sub-skill validator(s) (REAL subprocess) must also pass
    ov = meta.get("official_validator")
    if ov is not None and ov.get("exit_code") not in (0, None):
        vreport["official_validator_failed"] = ov
        if exit_code == 0:
            exit_code = 1
    ovs = meta.get("official_validators") or []
    failed_ovs = []
    warn_ovs = []
    for v in ovs:
        if v.get("exit_code") not in (0, None):
            # 0-4(72B-1/OBS-214):fidelity_guard.py exit 1 =「有事项需人工确认」警告,
            # 不抬升 exit_code;exit 2/3 仍失败。判据:fidelity_guard 的 warning 判据是
            # 否定/条件/因果/不确定词四组约 40 词出现次数必须完全相等(FS-003/FS-004
            # 单元级契约);这是「警告」与「失败」两个退出码的语义拆分,不是放松门禁。
            if (Path(v.get("path") or "").name == "fidelity_guard.py") and v.get("exit_code") == 1:
                warn_ovs.append(v)
            else:
                failed_ovs.append(v)
    if warn_ovs:
        vreport["official_validator_warnings"] = warn_ovs
    if failed_ovs:
        vreport["official_validators_failed"] = failed_ovs
        if exit_code == 0:
            exit_code = 1

    # 4. receipt — bind REAL upstream inputs + optional inputs (P0#2), recompute
    #    all hashes, record entrypoint + official validator cmd/exit/stdout-stderr.
    #    offline_fixture is a copy-only sanity mode (no producers) so it binds only
    #    the stage_request; real exec modes bind the true upstream files.
    from ..execmodel import UPSTREAM_INPUTS, OPTIONAL_INPUTS
    input_files = [sd / "stage_request.json"]
    if ctx.network_mode != "offline_fixture":
        upstream = list(UPSTREAM_INPUTS.get(stage, []))
        if ctx.network_mode == "fake_live" and stage == "media_enrichment":
            upstream = [rel for rel in upstream if rel in (
                "zh_human_writing/final_article.md",
                "super_writer/canonical_claim_registry.json",
                "aihot/deduplicated_items.json",
                "media_enrichment/media_discovery_request.json",
            )]
        input_files += [Path(ctx.run_dir) / rel for rel in upstream]
        for rel in OPTIONAL_INPUTS.get(stage, []):
            p = Path(ctx.run_dir) / rel
            if p.is_file():
                input_files.append(p)
    disc = ctx.discovery.get(skill, {})
    receipt = build_receipt(
        stage=stage, skill_name=skill,
        skill_dir=disc.get("skill_dir", str(Path(ctx.skills_home) / skill)),
        skill_version=disc.get("current_version") or disc.get("locked_version"),
        skill_root_sha256=disc.get("current_root_sha256") or disc.get("locked_root_sha256"),
        invoked_entrypoint=meta.get("invoked_entrypoint") or module.invoked_entrypoint(ctx),
        input_files=input_files, output_files=outputs,
        validator_path=vpath, validator_sha256=vsha, validator_exit_code=exit_code,
        started_at=started, ended_at=now(),
        side_effects=declared_side_effects,
        entrypoint_path=meta.get("entrypoint_path"), entrypoint_sha256=meta.get("entrypoint_sha256"),
        official_validator=ov, official_validators=ovs, network_mode=ctx.network_mode,
    )
    write_receipt(ctx.run_dir, stage, receipt)

    status = "success" if exit_code == 0 else "failed"
    result = {"run_id": state.run_id, "stage": stage, "status": status,
              "outputs": {p.name: sha256_file(p) for p in outputs if p.is_file()},
              "validator_report": vreport, "errors": [] if exit_code == 0 else [vreport]}
    res_errs = schema_validate(result, "stage_result")
    if res_errs:
        raise StageError(f"{stage}: invalid stage_result: {res_errs}")
    atomic_write_json(sd / "stage_result.json", result)

    # 5. stage-specific post gate + state update
    module.post(ctx, sd, state, exit_code, vreport)
    if exit_code != 0:
        raise StageError(f"{stage}: content validator failed (exit {exit_code}): {vreport}")
    return result
