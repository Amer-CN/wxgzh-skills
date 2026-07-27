"""Stage executor + context. Each stage: writes stage_request.json, produces
outputs (offline_fixture copies canned outputs; live would invoke the real
sub-skill), runs a content validator whose exit code is embedded in the receipt,
then writes stage_result.json + stage_receipt.json. No stage may be skipped.
"""
from __future__ import annotations

import hashlib
import importlib.util
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from ..state import atomic_write_json, sha256_file
from ..receipts import build_receipt, write_receipt, now
from ..contracts import validate as schema_validate

SKILL_ROOT = Path(__file__).resolve().parents[2]

# stage -> discovery skill key (wechat_draft reuses gzh-design's publish module)
STAGE_SKILL = {
    "aihot": "aihot",
    "super_writer": "super-writer",
    "zh_human_writing": "zh-human-writing",
    "media_enrichment": "media-enrichment",
    "gzh_design": "gzh-design",
    "wechat_draft": "gzh-design",
}


class StageError(Exception):
    pass


@dataclass
class StageContext:
    run_dir: Path
    skills_home: Path
    discovery: dict
    network_mode: str = "offline_fixture"
    fixture_dir: Path | None = None
    env: dict = field(default_factory=dict)
    create_wechat_draft: bool = True

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

    # 2. produce outputs
    if ctx.network_mode == "offline_fixture":
        outputs = _copy_fixture_outputs(ctx, stage)
    else:
        outputs = module.run_live(ctx, state)  # documented; not exercised during dev

    # 3. content validation (exit code embedded in receipt)
    exit_code, vreport, vpath, vsha = module.content_validate(ctx, sd, state)

    # 4. receipt
    disc = ctx.discovery.get(skill, {})
    receipt = build_receipt(
        skill_name=stage, skill_dir=disc.get("skill_dir", str(Path(ctx.skills_home) / skill)),
        skill_version=disc.get("current_version") or disc.get("locked_version"),
        skill_root_sha256=disc.get("current_root_sha256") or disc.get("locked_root_sha256"),
        invoked_entrypoint=module.invoked_entrypoint(ctx),
        input_files=[sd / "stage_request.json"], output_files=outputs,
        validator_path=vpath, validator_sha256=vsha, validator_exit_code=exit_code,
        started_at=started, ended_at=now(),
        side_effects=module.side_effects(ctx, state),
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
