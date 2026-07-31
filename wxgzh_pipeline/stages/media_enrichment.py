"""Stage 4 — media-enrichment. Runs after freeze. Bindings must be eligible +
upload success + mmbiz + sha==manifest, >=6 images. Serial upload, no bypass.
"""
from __future__ import annotations

from pathlib import Path

from . import subskill_validator_sha, load_validator

STAGE = "media_enrichment"
STAGE_CONFIG = {
    "COPYRIGHT_POLICY": "ALLOW_UNLESS_EXPLICITLY_PROHIBITED", "USER_BLANKET_APPROVAL": True,
    "source_url_first": True, "upload_serial": True, "manifest_single_writer": True,
    "BODY_IMAGES_MIN": 6, "BODY_IMAGES_TARGET": 8, "no_orchestrator_bypass": True,
}


def stage_inputs(ctx, state):
    return {"final_article_sha256": state.final_article_sha256 or "",
            "final_article": "../zh_human_writing/final_article.md"}


def invoked_entrypoint(ctx):
    return "media-enrichment scripts/run_media_enrichment.py (wechat_image_host) + scripts/validate_media_manifest.py"


def side_effects(ctx, state):
    # Only LIVE performs a real serial upload to mmbiz. offline_fixture (copy) and
    # fake_live (wechat_audit, no network) declare NO real write side-effect.
    if ctx.network_mode == "live":
        return [{"type": "wechat_image_upload", "detail": "serial uploadimg to mmbiz.qpic.cn"}]
    detail = ("offline fixture — no real WeChat image upload"
              if ctx.network_mode == "offline_fixture"
              else f"{ctx.network_mode} wechat_audit — deterministic mmbiz URL, no network/upload")
    return [{"type": "none", "detail": detail,
             "simulated": ctx.network_mode in ("fake_live", "integration")}]


def content_validate(ctx, sd: Path, state):
    vpath, vsha = subskill_validator_sha(ctx, "media-enrichment", "scripts/validate_media_manifest.py")
    man = sd / "media_manifest.json"
    bnd = sd / "article_image_bindings.json"
    if not man.is_file() or not bnd.is_file():
        return 1, {"reason": "media_manifest.json or article_image_bindings.json missing"}, vpath, vsha
    mod = load_validator("validate_media_bindings")
    config_path = sd / "validation_config.json"
    body_images_min = 6
    body_images_min_source = "default"
    if config_path.is_file():
        import json
        config = json.loads(config_path.read_text(encoding="utf-8"))
        body_images_min = config.get("body_images_min", 6)
        body_images_min_source = str(config_path)
    code, report = mod.validate(
        man, bnd, body_images_min=body_images_min,
        body_images_min_source=body_images_min_source)
    # depends-on-freeze: bindings must reference the frozen article sha
    if state.final_article_sha256:
        txt = bnd.read_text(encoding="utf-8")
        report["references_frozen_article_sha"] = state.final_article_sha256 in txt
        if not report["references_frozen_article_sha"]:
            code = 1
            report["MEDIA_BINDINGS"] = "FAIL"
    return code, report, vpath, vsha


def post(ctx, sd, state, exit_code, report):
    if exit_code == 0:
        state.uploaded_image_count = report.get("body_image_count", 0)
        state.side_effects.append({"stage": "media_enrichment",
                                   "uploaded_image_count": state.uploaded_image_count,
                                   "real_upload": ctx.network_mode == "live"})


def run_live(ctx, state):
    from ..producers import produce
    return produce(ctx, STAGE, state)
