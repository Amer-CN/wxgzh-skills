"""Stage 6 — WeChat draft. Reuses the existing stable implementation
(gzh-design/scripts/publish_wechat_draft.py). Creates ONE draft only.

This module contains NO formal-publish / mass-send / scheduled-send / delete
capability. In offline_fixture mode NO real WeChat API call is made — draft
delta is verified from desensitized before/after batchget snapshots.
"""
from __future__ import annotations

from pathlib import Path

from . import subskill_validator_sha, load_validator

STAGE = "wechat_draft"
STAGE_CONFIG = {"creates": "draft_only", "authorization": "发文：<选题> is the explicit authorization"}


def stage_inputs(ctx, state):
    return {"final_html": "../gzh_design/final.html",
            "requires_all_prior_receipts_valid": True}


def invoked_entrypoint(ctx):
    return ("REUSE gzh-design/scripts/publish_wechat_draft.py (cgi-bin/token, "
            "material/add_material cover, media/uploadimg, draft/add) + thin batchget wrapper — draft only")


def side_effects(ctx, state):
    if ctx.network_mode == "offline_fixture":
        return [{"type": "offline_mock", "detail": "no real WeChat API; draft delta from snapshot fixtures"}]
    return [{"type": "wechat_draft_add", "detail": "single draft/add; cover add_material; no publish"}]


def content_validate(ctx, sd: Path, state):
    vpath, vsha = subskill_validator_sha(ctx, "gzh-design", "scripts/publish_wechat_draft.py")
    before = sd / "draft_before.json"
    after = sd / "draft_after.json"
    if not before.is_file() or not after.is_file():
        return 1, {"reason": "draft_before.json / draft_after.json missing"}, vpath, vsha
    mod = load_validator("validate_draft_delta")
    code, report = mod.validate(before, after)
    return code, report, vpath, vsha


def post(ctx, sd, state, exit_code, report):
    if exit_code == 0:
        state.draft_created = True
        state.formally_published = False  # invariant; no code path sets True
        state.side_effects.append({"stage": "wechat_draft", "draft_created": True,
                                   "real_api": ctx.network_mode != "offline_fixture",
                                   "formally_published": False})


def run_live(ctx, state):
    # Documented live path (agent/orchestrator runtime). Draft-only; reuses the
    # audited module. NOT exercised during dev/tests (no real drafts).
    raise NotImplementedError(
        "live wechat_draft reuses gzh-design/scripts/publish_wechat_draft.py (draft only); "
        "dev/tests never create a real draft")
