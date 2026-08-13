"""Stage 4 — media-enrichment. Runs after freeze. Bindings must be eligible +
upload success + mmbiz + sha==manifest, >=6 images. Serial upload, no bypass.
"""
from __future__ import annotations

from pathlib import Path
import json

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

    # 档67:视觉内容门槛分级(客观判据,从冻结文章计算,无人工字段/开关/profile)。
    # 代码密集型文章(>=2 个 fenced code block)图片下限降为 3,但要求
    # 图片 + 代码块 >= 5 视觉单元;新闻综述(0-1 代码块)门槛保持 6 不降低。
    # 档68:正式启用,三条依据随 VISUAL_TIER 留痕(见 visual_threshold.VISUAL_TIER_EVIDENCE)。
    from ..visual_threshold import compute_visual_tier, effective_body_images_min
    article_path = Path(ctx.run_dir) / "zh_human_writing" / "final_article.md"
    article_text = (article_path.read_text(encoding="utf-8", errors="ignore")
                    if article_path.is_file() else "")
    tier = compute_visual_tier(article_text)

    config_path = sd / "validation_config.json"
    body_images_min = None
    config_value = None
    if config_path.is_file():
        import json
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config_value = config.get("body_images_min")
    body_images_min = effective_body_images_min(tier, config_value)
    body_images_min_source = (
        f"visual_tier(档67){' (max of config ' + str(config_path) + ')' if config_value is not None else ''}")
    code, report = mod.validate(
        man, bnd, body_images_min=body_images_min,
        body_images_min_source=body_images_min_source)
    # 档67:代码密集型文章须「视觉内容达标」——图片 + 代码块 >= 5 视觉单元,
    # 通过理由必须是视觉内容达标,不是图片数量豁免。档68:依据留痕并入 VISUAL_TIER。
    if tier.get("code_dense"):
        visual_units = int(report.get("body_image_count", 0) or 0) + int(tier["code_blocks"])
        report["VISUAL_TIER"] = {
            "code_blocks": tier["code_blocks"],
            "code_dense": True,
            "body_images_min": body_images_min,
            "visual_units": visual_units,
            "visual_units_min": tier["visual_units_min"],
            "visual_content_met": visual_units >= tier["visual_units_min"],
            "evidence": list(tier.get("evidence") or []),
            "reason": "视觉内容达标(图片 + 代码块视觉单元),非图片数量豁免",
        }
        # 76C:视觉内容门槛同降级——不足时留痕,不阻断(图片数量不再是
        # 发文限制条件;用户裁决 2026-08-11)。
        if not report["VISUAL_TIER"]["visual_content_met"]:
            report["image_shortfall"] = True
            report["image_shortfall_count"] = max(0, tier["visual_units_min"] - visual_units)
            report["note"] = (report.get("note") or "") + (
                f" 视觉单元 {visual_units} < {tier['visual_units_min']}(code-dense),少图交付留痕(76C 降级)")
    else:
        report["VISUAL_TIER"] = {
            "code_blocks": tier["code_blocks"],
            "code_dense": False,
            "body_images_min": body_images_min,
            "visual_units_min": None,
            "evidence": list(tier.get("evidence") or []),
            "note": "新闻综述/非代码密集型:门槛保持 6,不降低",
        }
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
        # 76C:少图交付留痕(不静默)——image_shortfall 进 state/final_delivery
        if report.get("image_shortfall"):
            state.image_shortfall = int(report.get("image_shortfall_count", 0) or 0)
            state.side_effects.append({"stage": "media_enrichment",
                                       "image_shortfall": True,
                                       "image_shortfall_count": state.image_shortfall,
                                       "actual_images": report.get("body_image_count"),
                                       "note": "生图兜底后仍不足,少图交付(76C 降级)"})
        # 76D/OBS-259:WebP→JPEG 转码记录进 side_effects(manifest.transcodes 留痕)。
        try:
            man_p = Path(sd) / "media_manifest.json"
            if man_p.is_file():
                man = json.loads(man_p.read_text(encoding="utf-8"))
                tcs = man.get("transcodes") or []
                if tcs:
                    state.side_effects.append({"stage": "media_enrichment",
                                               "webp_transcodes": list(tcs)})
        except (OSError, ValueError):
            pass


def run_live(ctx, state):
    from ..producers import produce
    return produce(ctx, STAGE, state)
