#!/usr/bin/env python3
"""Media Enrichment CLI — main entry point.

Orchestrates: validate → fetch → extract → decode → download → inspect →
dedup → classify → generate charts → upload → placement → manifest.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from urllib.parse import urlsplit
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "src"))

from media_enrichment import __version__ as SKILL_VERSION
from media_enrichment.input_contract import validate_request
from media_enrichment.page_fetcher import fetch_page, scan_no_repost

# 76F/OBS-275:已知不可抓域名(原文页动态渲染)——短超时 + 立即跳过,
# 记 discovery_side_effects,不拖整段;aihot 站内页 / img-proxy / 官方源不受影响。
SHORT_TIMEOUT_DOMAINS = {"x.com", "twitter.com"}
SHORT_TIMEOUT_SECONDS = 5
DEFAULT_FETCH_TIMEOUT = 15
FETCH_WORKERS = 4


def _host_of(url: str) -> str:
    try:
        from urllib.parse import urlsplit
        return (urlsplit(url or "").hostname or "").lower()
    except Exception:
        return ""


def _fetch_material_pages(mat: dict, network_mode: str, fixture_dir,
                          short_domains=frozenset(SHORT_TIMEOUT_DOMAINS)) -> dict:
    """76F:单素材三连抓取(站内页优先 → source 兜底+no-repost → permalink),
    供 ThreadPoolExecutor 并行;返回结果字典,主循环按素材顺序串行消费,
    保证资产 id 顺序稳定。x.com/twitter.com 原文页短超时(5s)失败即跳过。"""
    material_id = mat.get("material_id", "")
    permalink = (mat.get("aihot_permalink") or "").strip()
    source_url = (mat.get("source_url") or "").strip()
    internal_url = (mat.get("aihot_internal_url") or "").strip()
    page_url = ""
    fetch_result = None
    extraction = None
    page_kind = ""
    no_repost_hits: list[str] = []
    fallback_page = ""
    fallback_fetch = None
    fallback_extraction = None
    fetched: set[str] = set()
    side_effects: list[dict] = []
    src_is_short = _host_of(source_url) in short_domains

    # ① AI HOT 站内页优先(76C pool 通道同源;links.aihot 直出 HTML)
    if internal_url and internal_url != source_url:
        fr_in = fetch_page(internal_url, mode=network_mode, fixture_dir=fixture_dir,
                           timeout=DEFAULT_FETCH_TIMEOUT)
        fetched.add(internal_url)
        if fr_in.success:
            ex_in = extract_images(fr_in.content, page_url=internal_url)
            if ex_in.candidates:
                page_url, fetch_result, extraction, page_kind = (
                    internal_url, fr_in, ex_in, "aihot_internal")
            else:
                fallback_page = internal_url
                fallback_fetch = fr_in
                fallback_extraction = ex_in
        # 站内页无候选的 warning 由主循环按 page_kind/fallback 语义补(保持原输出)

    # ② 原始来源页:无论主用页为何都抓取做 no-repost 扫描(规则保留);
    #    已知不可抓域名短超时,失败即跳过并留痕,不拖整段。
    if source_url and source_url not in fetched:
        fr_src = fetch_page(source_url, mode=network_mode, fixture_dir=fixture_dir,
                            timeout=SHORT_TIMEOUT_SECONDS if src_is_short
                            else DEFAULT_FETCH_TIMEOUT)
        fetched.add(source_url)
        if fr_src.success:
            no_repost_hits = scan_no_repost(fr_src.content)
            if not page_url:
                ex_src = extract_images(fr_src.content, page_url=source_url)
                if ex_src.candidates:
                    page_url, fetch_result, extraction, page_kind = (
                        source_url, fr_src, ex_src, "source_url")
                else:
                    fallback_page = fallback_page or source_url
                    fallback_fetch = fallback_fetch or fr_src
                    fallback_extraction = fallback_extraction or ex_src
        elif src_is_short:
            side_effects.append({
                "material_id": material_id, "url": source_url,
                "skipped_reason": "short_timeout_domain:" + _host_of(source_url),
                "duration_ms": fr_src.duration_ms})
        # source 失败且站内页有候选:不额外 warning(原逻辑仅在无 page_url 时提示)

    # ③ aihot_permalink 兜底(追溯链)
    if not page_url and permalink and permalink not in fetched:
        fr_p = fetch_page(permalink, mode=network_mode, fixture_dir=fixture_dir,
                          timeout=DEFAULT_FETCH_TIMEOUT)
        fetched.add(permalink)
        if fr_p.success:
            ex_p = extract_images(fr_p.content, page_url=permalink)
            if ex_p.candidates:
                page_url, fetch_result, extraction, page_kind = (
                    permalink, fr_p, ex_p, "aihot_permalink")
            else:
                fallback_page = fallback_page or permalink
                fallback_fetch = fallback_fetch or fr_p
                fallback_extraction = fallback_extraction or ex_p

    if not page_url and fallback_page:
        page_url = fallback_page
        fetch_result = fallback_fetch
        extraction = fallback_extraction
        page_kind = "fallback_no_candidates"

    return {"material_id": material_id, "internal_url": internal_url,
            "page_url": page_url, "fetch_result": fetch_result,
            "extraction": extraction, "page_kind": page_kind,
            "no_repost_hits": no_repost_hits,
            "fallback_page": fallback_page, "fallback_fetch": fallback_fetch,
            "fallback_extraction": fallback_extraction, "side_effects": side_effects}


from media_enrichment.image_extractor import extract_images
from media_enrichment.section_align import section_matches_claims
from media_enrichment.proxy_decoder import decode_proxy_url
from media_enrichment.url_security import is_safe_url
from media_enrichment.downloader import download_image
from media_enrichment.image_inspector import inspect_image
from media_enrichment.image_deduplicator import deduplicate_asset, DedupState
from media_enrichment.image_classifier import classify_image
from media_enrichment.chart_generator import build_chart_specs, generate_chart
from media_enrichment.uploader import (
    transcode_webp_to_jpeg,
    create_uploader, normalize_wechat_url, scan_for_secrets, timed_upload,
)
from media_enrichment.placement_planner import find_anchors
from media_enrichment.manifest_builder import ManifestBuilder, AssetRecord
from media_enrichment.asset_approval import (
    approval_mismatches,
    freeze_discovery_manifest,
    stable_asset_identity,
    verify_discovery_manifest,
    write_discovery_manifest,
)


def _source_content_description(candidate, material_title: str | None = None):
    """档HF-4/OBS-245 + 76I/OBS-269:源图内容描述——img alt/title(page_alt) >
    父元素/兄弟节点可读文本(context_text,剥离 HTML) > 既有 page_context
    (meta 通道 og:title/og:description) > 素材标题兜底。

    以「<img」开头的裸 HTML 片段一律判不可读(直接丢弃),触发下一级回填。
    严禁用文章 claim 文本填充(OBS-87 的墙,下游 claim 派生判定照旧)。"""
    text = (candidate.alt or candidate.title or "").strip()
    if text:
        return text, "page_alt"
    ctx_text = (candidate.context_text or "").strip()
    if ctx_text:
        return ctx_text, "page_context"
    ctx = (candidate.context or "").strip()
    if ctx and not ctx.startswith("<img"):
        return ctx, "page_context"
    if material_title and material_title.strip():
        return material_title.strip(), "page_context"
    return None, None


# 77W/OBS-357:审批车道(approved_by)合法枚举与依据要求。
APPROVED_BY_LANES = ("user", "auto_rule", "auto_approve")


def _user_action_evidence(approval: dict, request: dict) -> bool:
    """77W/OBS-357:user 车道用户动作证据存在性检查(校验=证据存在性,
    不改既有 user_images 注入行为)。证据=user_images.json 含该资产
    material_id/source_url(:308/:470 既有通道),或 approval 记录自带
    approval_evidence_sha256(审批留痕在案)。"""
    material_id = approval.get("material_id") or ""
    source_page_url = approval.get("source_page_url") or ""
    for ui in (request.get("user_images") or []):
        if not isinstance(ui, dict):
            continue
        if material_id and ui.get("material_id") == material_id:
            return True
        if source_page_url and ui.get("source_url") == source_page_url:
            return True
    return bool((approval.get("approval_evidence_sha256") or "").strip())


def _approval_lane_error(approval: dict, request: dict) -> str | None:
    """77W/OBS-357:审批车道校验——返回错误文案,None=通过。"""
    lane = approval.get("approved_by")
    if lane not in APPROVED_BY_LANES:
        return (f"77W/OBS-357: approved_by 枚举外值 {lane}，"
                "合法=user/auto_rule/auto_approve"
                "（指路 schemas/media_enrichment_request.schema.json）")
    if lane in ("auto_rule", "auto_approve") and not (approval.get("basis") or "").strip():
        return "77W/OBS-357: auto_* 车道必须带 basis 依据"
    if lane == "user" and not _user_action_evidence(approval, request):
        return ("user 车道无用户动作证据（user_images.json / approval_evidence 缺失），"
                "拒绝记账 user（77W/OBS-357）")
    return None


def main():
    parser = argparse.ArgumentParser(description="Media Enrichment Skill")
    parser.add_argument("--request", required=True)
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--fixture-dir", default=None)
    parser.add_argument(
        "--phase", choices=("discover", "continue"), default="discover",
        help="discover never uploads; continue requires --discovery-manifest and stable approvals",
    )
    parser.add_argument("--discovery-manifest", default=None)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Validate input
    print("[media-enrichment] Validating input contract...")
    validation = validate_request(args.request)
    if not validation.valid:
        print("[media-enrichment] Input validation FAILED:")
        for err in validation.errors:
            print(f"  ERROR: {err}")
        builder = ManifestBuilder(
            run_id="validation_failed",
            request_sha256=validation.request_sha256 or "",
            article_sha256=validation.article_sha256 or "",
            claims_total=0, materials_total=0,
        )
        builder.errors = list(validation.errors)
        builder.warnings = list(validation.warnings)
        builder.write(str(output_dir / "media_manifest.json"))
        sys.exit(1)

    request = validation.request
    config = request.get("config", {})
    print(f"[media-enrichment] Input validation PASSED")

    article_path = request.get("article", {}).get("path", "")
    article_sha256 = request.get("article", {}).get("sha256", "")
    builder = ManifestBuilder(
        run_id=request.get("run_id", "unknown"),
        request_sha256=validation.request_sha256 or "",
        article_sha256=article_sha256,
        claims_total=len(request.get("claims", [])),
        materials_total=len(request.get("materials", [])),
    )

    dedup_state = DedupState()
    requested_upload_mode = config.get("upload_mode", "dry_run")
    upload_mode = "dry_run" if args.phase == "discover" else requested_upload_mode
    # dev2-hotfix2: serial upload event log (proves no overlap, one attempt/asset)
    upload_events: list = []
    existing_upload_events: dict[str, dict] = {}
    if args.phase == "continue":
        events_path = output_dir / "upload_events.json"
        if events_path.is_file():
            try:
                prior_events = json.loads(
                    events_path.read_text(encoding="utf-8")).get("events", [])
                upload_events.extend(prior_events)
                for event in prior_events:
                    if (event.get("status") == "success"
                            and event.get("url")
                            and normalize_wechat_url(event.get("url"))):
                        existing_upload_events[event["asset_id"]] = event
            except (OSError, ValueError, TypeError):
                builder.errors.append("existing upload_events.json is invalid")

    # Validate upload_mode. Discovery is side-effect-free regardless of request.
    try:
        create_uploader(requested_upload_mode)
        uploader = create_uploader(upload_mode)
    except ValueError as exc:
        builder.errors.append(str(exc))
        builder.write(str(output_dir / "media_manifest.json"))
        print(f"[media-enrichment] ERROR: {exc}")
        sys.exit(1)

    discovery_side_effects: list[dict] = []
    materials = request.get("materials", [])
    claims = request.get("claims", [])
    materials_by_id = {m["material_id"]: m for m in materials}
    network_mode = config.get("network_mode", "live")
    fixture_dir = args.fixture_dir or str(SKILL_ROOT / "fixtures" / "html")
    # hotfix5 P0#3: approvals are considered only in the continue phase and are
    # matched to a stable identity after discovery and content hashing complete.
    asset_approvals = {ap["asset_id"]: ap for ap in request.get("asset_approvals", [])}
    consumed_asset_approvals: set[str] = set()
    discovery_records: list[dict] = []
    pending_uploads: list[tuple[AssetRecord, str, object, str]] = []
    # offline image "downloads" read from a sibling images/ fixture dir (no network)
    fixture_images_dir = Path(fixture_dir).parent / "images"

    # OBS-42: continuation consumes the exact bytes persisted by discovery.
    # It never re-fetches source pages or re-downloads approved assets.
    if args.phase == "continue":
        if not args.discovery_manifest:
            builder.errors.append("continue phase requires --discovery-manifest")
        else:
            frozen_path = Path(args.discovery_manifest)
            discover_manifest_path = frozen_path.parent / "media_manifest.json"
            try:
                approved_discovery = json.loads(frozen_path.read_text(encoding="utf-8"))
                discovery_file_valid, _ = verify_discovery_manifest(approved_discovery)
                if not discovery_file_valid:
                    builder.errors.append(
                        "approval_identity_mismatch: discovery manifest sha256 invalid")
                discover_manifest = json.loads(
                    discover_manifest_path.read_text(encoding="utf-8"))
                discovered_assets = {
                    item["asset_id"]: item for item in discover_manifest.get("assets", [])
                }
                discovered_asset_records = {
                    asset_id: AssetRecord(**item)
                    for asset_id, item in discovered_assets.items()
                }
                for record in discovered_asset_records.values():
                    builder.add_asset(record)
                frozen_records = {
                    item["asset_id"]: item
                    for item in approved_discovery.get("assets", [])
                }
                discovery_records.extend(approved_discovery.get("assets", []))
                images_root = (frozen_path.parent / "images").resolve()
                material_approved_ids = {
                    asset_id for asset_id, frozen in frozen_records.items()
                    if frozen.get("asset_origin") != "generated"
                    and (materials_by_id.get(frozen["material_id"], {})
                         .get("copyright_review", {}).get("status") == "known_allowed")
                }
                # 76C/OBS-255:user_provided 资产免版权审批(用户供图责任自负,
                # user_images.json 即批准依据),计入 upload_candidate_ids。
                user_granted_ids = {
                    asset_id for asset_id, frozen in frozen_records.items()
                    if frozen.get("asset_origin") == "user_provided"
                }
                # 档HF-4/OBS-246:守卫语义修正——不再用「候选数 > 显式
                # single_asset 批准数」计数比较(纯 material 车道被误杀,HF-2
                # lane1/lane2 实证);改为:每个上传候选(冻结清单中 decision 可
                # 批准的非 generated 资产)必须有批准依据(single_asset 或
                # material/source_url),存在无依据候选即 FAIL_CLOSED 并列明。
                frozen_candidates = {
                    asset_id for asset_id, rec in discovered_asset_records.items()
                    if rec.asset_origin != "generated"
                    and rec.decision in ("review_required", "eligible")
                }
                # 76R/OBS-289:自动放行——auto_approve 开启且单图证据链齐全
                # (observable_content 可读 + page_position 已知 + sha256 + 非黑名单
                # + 非 restricted)时,资产视为已自动批准(approved_by=auto_approve),
                # 计入批准依据,不再 FAIL_CLOSED。
                auto_approved_ids = set()
                if config.get("auto_approve") and network_mode != "live":
                    _bl_aa = [d.lower() for d in (config.get("domain_blacklist") or [])]
                    for _aid, _rec in discovered_asset_records.items():
                        if _rec.asset_origin == "generated" or _rec.copyright_status == "restricted":
                            continue
                        _host_aa = (urlsplit(_rec.resolved_original_url or "").hostname or "").lower()
                        if any(_host_aa == d or _host_aa.endswith("." + d) for d in _bl_aa):
                            continue
                        if not ((_rec.content_description or "").strip()
                                and not (_rec.content_description or "").lstrip().startswith("<img")
                                and (_rec.page_position or {}).get("known") is True
                                and _rec.sha256
                                and _rec.duplicate_of is None):
                            continue
                        _rec.copyright_status = "known_allowed"
                        _rec.approved_by = "auto_approve"
                        _rec.approved_scope = "auto"
                        _rec.approved_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                        _rec.auto_approved = True
                        _rec.reasons.append("auto_approved: evidence chain complete (76R/OBS-289)")
                        auto_approved_ids.add(_aid)
                unbacked = sorted(
                    aid for aid in frozen_candidates
                    if aid not in asset_approvals and aid not in material_approved_ids
                    and aid not in user_granted_ids and aid not in auto_approved_ids)
                if unbacked:
                    builder.errors.append(
                        "upload candidates without approval basis (FAIL_CLOSED): "
                        + ", ".join(unbacked))
                    upload_candidate_ids = set()
                else:
                    upload_candidate_ids = (set(asset_approvals) | material_approved_ids
                                           | user_granted_ids | auto_approved_ids)

                for asset_id in sorted(upload_candidate_ids):
                    approval = asset_approvals.get(asset_id)
                    frozen = frozen_records.get(asset_id)
                    discovered = discovered_assets.get(asset_id)
                    if frozen is None or discovered is None:
                        builder.errors.append(
                            f"approval_identity_mismatch: {asset_id} missing from frozen discovery")
                        continue

                    if approval is not None:
                        mismatches = approval_mismatches(
                            approval, frozen,
                            approved_discovery["discovery_manifest_sha256"],
                        )
                        if mismatches:
                            builder.errors.append(
                                f"approval_identity_mismatch: {asset_id}: "
                                + ", ".join(sorted(mismatches)))
                            continue

                    # 76C/OBS-255:user_provided 资产无对应 material(来源登记即依据),跳过检查
                    if frozen.get("asset_origin") != "user_provided":
                        material = materials_by_id.get(frozen["material_id"])
                        # 76J/OBS-270:绑定一致性认可站内页通道——source_page_url 与
                        # material 的 aihot_internal_url(站内页)相等即一致,与
                        # links.original(source_url)同等合法;无站内页字段的素材行为不变。
                        source_ok = (material is not None
                                     and (material.get("source_url") == frozen["source_page_url"]
                                          or (material.get("aihot_internal_url") or "")
                                          == frozen["source_page_url"]))
                        if not source_ok:
                            builder.errors.append(
                                f"approval_identity_mismatch: {asset_id} material/source changed")
                            continue

                    local_value = discovered.get("local_path")
                    if not local_value:
                        builder.errors.append(
                            f"approval_identity_mismatch: {asset_id} missing discovery local_path")
                        continue
                    local_path = Path(local_value).resolve()
                    allowed_roots = [images_root]
                    if frozen.get("asset_origin") == "generated":
                        allowed_roots.append((frozen_path.parent / "charts").resolve())
                    if (not any(local_path.is_relative_to(r) for r in allowed_roots)
                            or not local_path.is_file()):
                        builder.errors.append(
                            f"approval_identity_mismatch: {asset_id} local file outside discovery images")
                        continue

                    resolved_url = frozen["resolved_original_url"]
                    sec_check = None
                    if frozen.get("asset_origin") != "generated":
                        sec_check = is_safe_url(
                            resolved_url, require_dns=(network_mode == "live"))
                    if sec_check is not None and not sec_check.safe:
                        builder.errors.append(
                            f"URL security: {asset_id}: {', '.join(sec_check.reasons)}")
                        continue

                    inspection = inspect_image(
                        str(local_path), max_pixels=config.get("max_pixels", 40_000_000))
                    if inspection.sha256 != frozen["asset_sha256"]:
                        builder.errors.append(
                            f"approval_identity_mismatch: {asset_id} frozen sha256 mismatch")
                        continue
                    identity_sha256 = stable_asset_identity(
                        frozen["material_id"], frozen["source_page_url"],
                        resolved_url, inspection.sha256,
                    )
                    if identity_sha256 != frozen["asset_identity_sha256"]:
                        builder.errors.append(
                            f"approval_identity_mismatch: {asset_id} stable identity mismatch")
                        continue

                    asset = discovered_asset_records[asset_id]
                    asset.local_path = str(local_path)
                    asset.sha256 = inspection.sha256
                    asset.perceptual_hash = inspection.perceptual_hash
                    asset.mime_type = inspection.mime_type
                    asset.width = inspection.width
                    asset.height = inspection.height
                    asset.file_size = inspection.file_size
                    asset.quality_status = "pass" if inspection.is_valid else "fail"
                    asset.asset_identity_sha256 = identity_sha256
                    if approval is None and asset.copyright_status != "restricted":
                        asset.copyright_status = "known_allowed"
                    pending_uploads.append((
                        asset, str(local_path), inspection,
                        discovered.get("extraction_method") or "img.src"))
                    builder.downloads_succeeded += 1
            except (OSError, ValueError, KeyError, TypeError) as exc:
                builder.errors.append(
                    f"approval_identity_mismatch: cannot load frozen discovery assets: {exc}")

    max_images_per_material = config.get("max_images_per_material", 3)
    max_total_images = config.get("max_total_images", 12)
    # 76E/OBS-260:discovery 预算与最终入文数分离——max_total_images 只约束
    # 最终进入文章的上传图数;discovery 用独立预算(默认 max(24, 3×max_total)),
    # rejected/头像/重复图不再消耗中止条件,不得再出现「因预算截断跳过后续
    # 素材页」的行为。
    discovery_budget = int(config.get("discovery_budget") or max(24, max_total_images * 3))
    total_assets_added = 0
    # 76E/OBS-260:预算只统计非 rejected 资产(eligible/review_required)——rejected/
    # 头像/重复图不消耗中止条件,不得因预算截断跳过后续素材页。
    accepted_assets_added = 0
    asset_counter = 0

    # 76C/OBS-255:用户供图注入——user_images.json 直链清单(user_provided,
    # 免版权审批,用户供图责任自负,登记来源链接)。仅 discover 纳入候选。
    for ui in (request.get("user_images") or []):
        if accepted_assets_added >= discovery_budget:
            break
        url = (ui.get("url") or "").strip()
        if not url:
            continue
        asset_counter += 1
        asset_id = f"A-{asset_counter:03d}"
        _host = (urlsplit(url).hostname or "").lower()
        _bl = [d.lower() for d in (config.get("domain_blacklist") or [])]
        sec = is_safe_url(url, require_dns=(network_mode == "live"))
        if not sec.safe or any(_host == d or _host.endswith("." + d) for d in _bl):
            builder.add_asset(AssetRecord(
                asset_id=asset_id, asset_origin="user_provided", material_ids=[], claim_ids=[],
                source_page_url=ui.get("source_url") or "", discovered_url=url, resolved_original_url=url,
                extraction_method="user_provided", decode_method="none",
                decision="rejected", reasons=[f"user image rejected: {'URL security' if not sec.safe else 'domain blacklisted: ' + _host} (76C)"],
                quality_status="fail", relevance_status="irrelevant",))
            continue
        dl = download_image(url, output_dir / "images",
                              max_bytes=config.get("max_download_bytes", 15728640),
                              mode=network_mode, fixture_dir=fixture_images_dir)
        if not dl.success:
            builder.add_asset(AssetRecord(
                asset_id=asset_id, asset_origin="user_provided", material_ids=[], claim_ids=[],
                source_page_url=ui.get("source_url") or "", discovered_url=url, resolved_original_url=url,
                extraction_method="user_provided", decode_method="none",
                decision="rejected", reasons=[f"download failed: {dl.error}"],
                quality_status="fail", relevance_status="irrelevant",))
            continue
        inspection = inspect_image(dl.local_path, max_pixels=config.get("max_pixels", 40_000_000))
        identity_sha256 = stable_asset_identity("user-provided", ui.get("source_url") or "", url, inspection.sha256)
        dim_ok = (inspection.is_valid and inspection.width >= config.get("min_width", 480)
                  and inspection.height >= config.get("min_height", 200))
        decision = "eligible" if dim_ok else "review_required"
        caption = ui.get("caption") or ""
        asset = AssetRecord(
            asset_id=asset_id, asset_origin="user_provided", material_ids=[], claim_ids=[],
            source_page_url=ui.get("source_url") or "", discovered_url=url, resolved_original_url=url,
            extraction_method="user_provided", decode_method="none", local_path=dl.local_path,
            sha256=inspection.sha256, perceptual_hash=inspection.perceptual_hash,
            mime_type=inspection.mime_type, width=inspection.width, height=inspection.height,
            file_size=inspection.file_size, quality_status="pass" if inspection.is_valid else "fail",
            relevance_status="relevant" if decision == "eligible" else "uncertain",
            copyright_status="user_granted", copyright_risk="low", decision=decision,
            reasons=["user provided image — 免版权审批,用户供图责任自负 (76C/OBS-255)"],
            caption=caption, alt_text=caption,
            content_description=caption or "用户供图", content_description_source="user_provided",
            page_region="user_provided",
            # 77G/OBS-317: user description/source URL is the lane's position evidence.
            page_position={"known": True, "heading": caption or "用户供图",
                           "level": "user-evidence"},
            asset_identity_sha256=identity_sha256,
            upload={"mode": upload_mode, "status": "not_uploaded", "remote_url": None, "response_sha256": None},
        )
        pending_uploads.append((asset, dl.local_path, inspection, "user_provided"))
        discovery_records.append({
            "asset_id": asset_id, "asset_origin": "user_provided",
            "material_id": "user-provided", "source_page_url": ui.get("source_url") or "", "resolved_original_url": url,
            "asset_sha256": inspection.sha256, "asset_identity_sha256": identity_sha256,
        })
        builder.add_asset(asset)
        total_assets_added += 1
        if asset.decision != "rejected":
            accepted_assets_added += 1
        print(f"  User image {asset_id}: {url} — {decision}")

    # 76F/OBS-275:页面抓取有界并行(worker=4)——抓取阶段并行、资产构建串行
    # (asset_id 顺序稳定);x.com/twitter.com 原文页短超时跳过已留痕。
    from concurrent.futures import ThreadPoolExecutor
    _short_domains = frozenset(config.get("short_timeout_domains")
                               or SHORT_TIMEOUT_DOMAINS)
    fetch_results: dict[str, dict] = {}
    if args.phase != "continue":
        with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as _pool:
            _done = list(_pool.map(
                lambda _m: _fetch_material_pages(
                    _m, network_mode, fixture_dir, _short_domains),
                materials))
        fetch_results = {r["material_id"]: r for r in _done}

    for mat in ([] if args.phase == "continue" else materials):
        material_id = mat["material_id"]
        permalink = mat.get("aihot_permalink", "")
        source_url = mat.get("source_url", "")
        material_image_count = 0
        # Get copyright status from material's copyright_review
        copyright_review = mat.get("copyright_review", {})
        mat_copyright_status = copyright_review.get("status", "unknown")

        print(f"\n[media-enrichment] Processing material {material_id}: {permalink}")

        if accepted_assets_added >= discovery_budget:
            builder.warnings.append(f"discovery_budget ({discovery_budget}) reached — skipping {material_id}")
            print(f"  SKIP: discovery_budget reached")
            continue

        builder.pages_requested += 1
        # 76F/OBS-275:抓取已在并行阶段完成(_fetch_material_pages),此处按素材
        # 顺序消费结果——资产 id 顺序稳定;站内页优先语义不变。
        fr = fetch_results.get(material_id) or _fetch_material_pages(
            mat, network_mode, fixture_dir, _short_domains)
        internal_url = fr["internal_url"]
        page_url = fr["page_url"]
        fetch_result = fr["fetch_result"]
        extraction = fr["extraction"]
        page_kind = fr["page_kind"]
        no_repost_hits = fr["no_repost_hits"]
        fallback_page = fr["fallback_page"]
        fallback_fetch = fr["fallback_fetch"]
        fallback_extraction = fr["fallback_extraction"]
        discovery_side_effects.extend(fr["side_effects"])
        # 保持原 warning 语义:站内页无候选回退 source;source 失败且无主用页。
        if (internal_url and internal_url != source_url and not page_url
                and fr["fallback_page"] == internal_url):
            builder.warnings.append(
                f"{material_id}: aihot internal page has no image candidates "
                "— falling back to source page")
        if (source_url and not page_url and fetch_result is not None
                and not fetch_result.success):
            builder.warnings.append(
                f"{material_id}: source_url fetch failed — falling back to "
                f"aihot_permalink ({str(fetch_result.error)[:120]})")
        if not page_url and fallback_page:
            page_url = fallback_page
            fetch_result = fallback_fetch
            extraction = fallback_extraction
            page_kind = "fallback_no_candidates"
            print(f"  Fetched via {page_kind}: page has no image candidates")

        if not page_url:
            err = (fetch_result.error if fetch_result and not fetch_result.success
                   else "all page fetches failed")
            builder.errors.append(f"Failed to fetch page for {material_id}: {err}")
            print(f"  FETCH FAILED: {err}")
            continue

        builder.pages_fetched += 1
        print(f"  Fetched via {page_kind}: {fetch_result.status_code}")

        # 原始页 no-repost 命中 → 素材全部候选 restricted(含站内页来源图)
        if no_repost_hits:
            mat_copyright_status = "restricted"
            builder.warnings.append(
                f"{material_id}: explicit no-repost statement on source page "
                f"({'/'.join(no_repost_hits)}) — images restricted")
        # OBS-86(档62):正文边界判定后处理——素材 claim 文本(章节对齐用)
        # 与排除统计。peripheral 图已在提取阶段被排除(下载前,零请求)。
        material_claim_texts = [
            c.get("claim_text", "") for c in claims
            if c.get("claim_id") in (mat.get("selected_claim_ids") or [])
        ]
        if extraction.excluded:
            builder.warnings.append(
                f"{material_id}: excluded {len(extraction.excluded)} peripheral "
                f"images before download (OBS-86)")
        builder.candidates_discovered += len(extraction.candidates)
        print(f"  Candidates: {len(extraction.candidates)}")

        for candidate in extraction.candidates:
            if accepted_assets_added >= discovery_budget:
                builder.warnings.append(f"discovery_budget ({discovery_budget}) reached — stopping discovery")
                break
            if material_image_count >= max_images_per_material:
                builder.warnings.append(f"max_images_per_material ({max_images_per_material}) reached for {material_id}")
                break

            asset_counter += 1
            asset_id = f"A-{asset_counter:03d}"
            effective_copyright = mat_copyright_status

            decode_result = decode_proxy_url(candidate.url)
            resolved_url = decode_result.decoded_url

            sec_check = is_safe_url(resolved_url, require_dns=(network_mode == "live"))
            if not sec_check.safe:
                asset = AssetRecord(
                    asset_id=asset_id, asset_origin="source",
                    material_ids=[material_id], claim_ids=mat.get("selected_claim_ids", []),
                    aihot_permalink=permalink, source_page_url=page_url,
                    discovered_url=candidate.url, resolved_original_url=resolved_url,
                    extraction_method=candidate.extraction_method, decode_method=decode_result.decode_method,
                    decision="rejected", reasons=[f"URL security: {', '.join(sec_check.reasons)}"],
                    quality_status="fail", relevance_status="irrelevant",
                )
                builder.add_asset(asset)
                continue

            # OBS-86(档62):跨章节图下载前排除——仅对多章节结构(h2/h3)生效:
            # 聚合页正文容器内的其他新闻章节图与本素材 claim 不对齐,不下载、
            # 不发第三方请求;位置仍记录供审计。h1 单篇页无跨章节歧义,不做
            # 该门(其相关性属 OBS-87 批准闸门与素材层 OBS-29 职责)。
            if (candidate.section_level in ("h2", "h3")
                    and candidate.section_heading and material_claim_texts):
                if not section_matches_claims(candidate.section_heading, material_claim_texts):
                    asset = AssetRecord(
                        asset_id=asset_id, asset_origin="source",
                        material_ids=[material_id], claim_ids=mat.get("selected_claim_ids", []),
                        aihot_permalink=permalink, source_page_url=page_url,
                        discovered_url=candidate.url, resolved_original_url=resolved_url,
                        extraction_method=candidate.extraction_method, decode_method=decode_result.decode_method,
                        decision="rejected",
                        reasons=[f"cross-section image (section: {candidate.section_heading[:60]}) does not match any selected claim — excluded before download (OBS-86)"],
                        quality_status="fail", relevance_status="irrelevant",
                        page_region=candidate.page_region,
                        page_position={"known": True, "heading": candidate.section_heading,
                                       "level": candidate.section_level},
                    )
                    builder.add_asset(asset)
                    continue

            # 76C/OBS-248:来源域名黑名单(可配置,首批 ithome.com / img.ithome.com)
            # ——水印广告图,用户两次手动删除的域名,意图明确;命中即拒。
            _host = (urlsplit(resolved_url).hostname or "").lower()
            _bl = [d.lower() for d in (config.get("domain_blacklist") or [])]
            if any(_host == d or _host.endswith("." + d) for d in _bl):
                asset = AssetRecord(
                    asset_id=asset_id, asset_origin="source",
                    material_ids=[material_id], claim_ids=mat.get("selected_claim_ids", []),
                    aihot_permalink=permalink, source_page_url=page_url,
                    discovered_url=candidate.url, resolved_original_url=resolved_url,
                    extraction_method=candidate.extraction_method, decode_method=decode_result.decode_method,
                    decision="rejected", reasons=[f"domain blacklisted: {_host} (76C/OBS-248)"],
                    quality_status="fail", relevance_status="irrelevant",
                )
                builder.add_asset(asset)
                continue

            images_dir = output_dir / "images"
            download_result = download_image(resolved_url, images_dir,
                                              max_bytes=config.get("max_download_bytes", 15728640),
                                              mode=network_mode, fixture_dir=fixture_images_dir)
            if not download_result.success:
                asset = AssetRecord(
                    asset_id=asset_id, asset_origin="source",
                    material_ids=[material_id], claim_ids=mat.get("selected_claim_ids", []),
                    aihot_permalink=permalink, source_page_url=page_url,
                    discovered_url=candidate.url, resolved_original_url=resolved_url,
                    extraction_method=candidate.extraction_method, decode_method=decode_result.decode_method,
                    decision="rejected", reasons=[f"download failed: {download_result.error}"],
                    quality_status="fail",
                )
                builder.add_asset(asset)
                continue

            builder.downloads_succeeded += 1

            inspection = inspect_image(download_result.local_path,
                                        max_pixels=config.get("max_pixels", 40_000_000))

            dedup_result = deduplicate_asset(
                asset_id=asset_id, sha256=inspection.sha256,
                original_url=resolved_url, perceptual_hash=inspection.perceptual_hash,
                width=inspection.width, height=inspection.height, state=dedup_state,
            )

            if dedup_result.is_duplicate:
                asset = AssetRecord(
                    asset_id=asset_id, asset_origin="source",
                    material_ids=[material_id], claim_ids=mat.get("selected_claim_ids", []),
                    discovered_url=candidate.url, resolved_original_url=resolved_url,
                    sha256=inspection.sha256,
                    decision="rejected", reasons=[dedup_result.dedup_reason],
                    duplicate_of=dedup_result.duplicate_of,
                    dedup_method=dedup_result.dedup_method,
                    quality_status="pass" if inspection.is_valid else "fail",
                )
                builder.add_asset(asset)
                continue

            identity_sha256 = stable_asset_identity(
                material_id, page_url, resolved_url, inspection.sha256,
            )
            discovery_record = {
                "asset_id": asset_id,
                "asset_origin": "source",
                "material_id": material_id,
                "source_page_url": page_url,
                "resolved_original_url": resolved_url,
                "asset_sha256": inspection.sha256,
                "asset_identity_sha256": identity_sha256,
            }
            discovery_records.append(discovery_record)

            classification = classify_image(
                url=resolved_url, inspection=inspection,
                min_width=config.get("min_width", 640), min_height=config.get("min_height", 360),
                context=candidate.context, copyright_status=effective_copyright,
                extraction_method=candidate.extraction_method,
                # 76G-R/OBS-263:站内页图与素材同源即相关(站内内容已筛选)
                internal_page=(page_kind == "aihot_internal"),
            )

            content_desc, content_desc_source = _source_content_description(
                candidate, material_title=mat.get("title"))
            # 档HF-4/OBS-247:meta 通道图原始 HTML 无 DOM 位置——推文页=内容单元
            # 本身,页级主图位置即页面(page-meta 语义,审核方裁定);取不到页面
            # title 则 known=false。
            # 76G-R/OBS-262:站内页图源证据形态——站内页(aihot_internal)为单篇
            # 内容单元,页内 img 无章节上下文时位置即页面(page-meta,与 og:image
            # 的审核方裁定同源);三项证据=站内页 URL + 页内位置 + img-proxy 原始
            # URL 追溯(readiness 认可,不再因位置未知拦站内页图)。
            if (candidate.extraction_method in ("og:image", "twitter:image")
                    or page_kind == "aihot_internal"):
                if extraction.page_title:
                    page_pos = {"known": True, "heading": extraction.page_title,
                                "level": "page-meta"}
                else:
                    page_pos = {"known": False, "heading": None, "level": None}
            elif candidate.section_heading:
                page_pos = {"known": True, "heading": candidate.section_heading,
                            "level": candidate.section_level}
            else:
                page_pos = {"known": False, "heading": None, "level": None}
            asset = AssetRecord(
                asset_id=asset_id, asset_origin="source",
                material_ids=[material_id], claim_ids=mat.get("selected_claim_ids", []),
                aihot_permalink=permalink, source_page_url=page_url,
                discovered_url=candidate.url, resolved_original_url=resolved_url,
                extraction_method=candidate.extraction_method, decode_method=decode_result.decode_method,
                local_path=download_result.local_path, sha256=inspection.sha256,
                perceptual_hash=inspection.perceptual_hash, mime_type=inspection.mime_type,
                width=inspection.width, height=inspection.height, file_size=inspection.file_size,
                quality_status="pass" if inspection.is_valid else "fail",
                relevance_status="relevant" if classification.decision == "eligible" else "uncertain",
                copyright_status=effective_copyright,
                copyright_risk="high" if classification.decision == "rejected" else "medium",
                asset_identity_sha256=identity_sha256,
                decision=classification.decision,
                reasons=classification.rejection_reasons or classification.relevance_reasons,
                page_region=candidate.page_region,
                # 76G 增补/OBS-266:视频封面资产标记(证据链走站内页形态,视频本体不下载)
                video_poster=candidate.video_poster,
                page_position=page_pos,
                content_description=content_desc,
                content_description_source=content_desc_source,
            )
            pending_uploads.append((asset, download_result.local_path, inspection, candidate.extraction_method))
            builder.add_asset(asset)
            total_assets_added += 1
            if asset.decision != "rejected":
                accepted_assets_added += 1
            material_image_count += 1

    # 76C/OBS-254:discover 扩池——全池潜力源(pool_items,来自 aihot
    # deduplicated_items)补充抓取;每条素材除 source_url 外,优先抓 links.aihot
    # 站内页(渲染好的直出 HTML,可绕开 X 等平台动态渲染)。来源扩池的图仍按
    # 既有 OBS-86 规则做 claim 相关性绑定,只放行与文章相关者。
    pool_items = request.get("pool_items") or []
    # 76R/OBS-291:continue 阶段不重抓 pool——discover 已抓取并冻结,
    # 继续只消费冻结清单(asset_discovery_manifest.json),避免重复登记。
    if args.phase == "continue":
        pool_items = []
    pool_fetch_limit = int(config.get("pool_fetch_limit", 30))
    pool_fetched = 0
    # 76R/OBS-291:pool-fetch ID 规范化——iid(dedup id) ↔ canonical material_id(M-XX)
    # 映射表。凡归属已选素材的池内图(含池内重复图)一律映射回 M-XX 登记,
    # 禁止裸 iid 入库;映射不到的资产才独立登记并如实标注来源。
    iid_to_material = {}
    for _m in materials:
        _did = _m.get("dedup_id") or _m.get("id")
        if _did:
            iid_to_material[_did] = _m.get("material_id", "")
    # 76R/OBS-291:不再跳过「已选素材」——池内 iid 有映射即归属对应 M-XX(审批
    # 覆盖到),无映射才独立登记;两条路径都需处理,故取消旧 skip。
    all_claim_texts = [c.get("claim_text", "") for c in claims]
    _bl = [d.lower() for d in (config.get("domain_blacklist") or [])]
    pool_image_count = 0
    for item in pool_items:
        if accepted_assets_added >= discovery_budget or pool_fetched >= pool_fetch_limit:
            break
        iid = item.get("id", "")
        if not iid:
            continue
        permalink = item.get("aihot_permalink", "")
        source_url = item.get("source_url", "")
        links = item.get("links") or {}
        # 图源潜力:summary/links 含图片 URL 或站内页(优先);有图片线索则最多
        # 抓两页(站内页 + 原页),否则只抓站内页。
        img_hint = bool(re.search(r"https?://[^\s\"']+\.(?:png|jpe?g|gif|webp)",
                               (item.get("summary") or "") + json.dumps(links, ensure_ascii=False), re.I))
        page_candidates = []
        if links.get("aihot"):
            page_candidates.append(("aihot_permalink", links["aihot"]))
        if source_url and source_url != permalink and img_hint:
            page_candidates.append(("source_url", source_url))
        for kind, page_url in page_candidates:
            if accepted_assets_added >= discovery_budget or pool_fetched >= pool_fetch_limit:
                break
            fr = fetch_page(page_url, mode=network_mode, fixture_dir=fixture_dir,
                            timeout=SHORT_TIMEOUT_SECONDS if _host_of(page_url) in _short_domains
                            else DEFAULT_FETCH_TIMEOUT)
            pool_fetched += 1
            if not fr.success:
                continue
            extraction = extract_images(fr.content, page_url=page_url)
            print(f"  Pool {iid} via {kind}: {len(extraction.candidates)} candidates")
            for candidate in extraction.candidates:
                if accepted_assets_added >= discovery_budget:
                    break
                if pool_image_count >= max_images_per_material:
                    break
                asset_counter += 1
                asset_id = f"A-{asset_counter:03d}"
                decode_result = decode_proxy_url(candidate.url)
                resolved_url = decode_result.decoded_url
                sec = is_safe_url(resolved_url, require_dns=(network_mode == "live"))
                _host = (urlsplit(resolved_url).hostname or "").lower()
                if not sec.safe or any(_host == d or _host.endswith("." + d) for d in _bl):
                    builder.add_asset(AssetRecord(
                        asset_id=asset_id, asset_origin="source", material_ids=[iid_to_material.get(iid) or iid], claim_ids=[],
                        aihot_permalink=permalink, source_page_url=page_url,
                        discovered_url=candidate.url, resolved_original_url=resolved_url,
                        extraction_method=candidate.extraction_method, decode_method=decode_result.decode_method,
                        decision="rejected", reasons=[f"pool image rejected: {'URL security' if not sec.safe else 'domain blacklisted: ' + _host} (76C)"],
                        quality_status="fail", relevance_status="irrelevant",))
                    continue
                # OBS-86 语义不变:多章节页做 claim 相关性绑定,只放行与文章相关者
                if (candidate.section_level in ("h2", "h3")
                        and candidate.section_heading and all_claim_texts):
                    if not section_matches_claims(candidate.section_heading, all_claim_texts):
                        builder.add_asset(AssetRecord(
                            asset_id=asset_id, asset_origin="source", material_ids=[iid_to_material.get(iid) or iid], claim_ids=[],
                            aihot_permalink=permalink, source_page_url=page_url,
                            discovered_url=candidate.url, resolved_original_url=resolved_url,
                            extraction_method=candidate.extraction_method, decode_method=decode_result.decode_method,
                            decision="rejected", reasons=[f"pool cross-section image (section: {candidate.section_heading[:60]}) does not match any selected claim (OBS-86)"],
                            quality_status="fail", relevance_status="irrelevant",
                            page_region=candidate.page_region, page_position={"known": True, "heading": candidate.section_heading, "level": candidate.section_level},))
                        continue
                images_dir = output_dir / "images"
                dl = download_image(resolved_url, images_dir, max_bytes=config.get("max_download_bytes", 15728640),
                                    mode=network_mode, fixture_dir=fixture_images_dir)
                if not dl.success:
                    builder.add_asset(AssetRecord(
                        asset_id=asset_id, asset_origin="source", material_ids=[iid_to_material.get(iid) or iid], claim_ids=[],
                        aihot_permalink=permalink, source_page_url=page_url,
                        discovered_url=candidate.url, resolved_original_url=resolved_url,
                        extraction_method=candidate.extraction_method, decode_method=decode_result.decode_method,
                        decision="rejected", reasons=[f"download failed: {dl.error}"],
                        quality_status="fail", relevance_status="irrelevant",))
                    continue
                inspection = inspect_image(dl.local_path, max_pixels=config.get("max_pixels", 40_000_000))
                identity_sha256 = stable_asset_identity(iid_to_material.get(iid) or iid, page_url, resolved_url, inspection.sha256)
                classification = classify_image(
                    url=resolved_url, inspection=inspection,
                    min_width=config.get("min_width", 480), min_height=config.get("min_height", 200),
                    context=candidate.context, copyright_status="unknown",
                    internal_page=(kind == "aihot_permalink"),
                    extraction_method=candidate.extraction_method,)
                asset = AssetRecord(
                    asset_id=asset_id, asset_origin="source", material_ids=[iid_to_material.get(iid) or iid], claim_ids=[],
                    aihot_permalink=permalink, source_page_url=page_url,
                    discovered_url=candidate.url, resolved_original_url=resolved_url,
                    extraction_method=candidate.extraction_method, decode_method=decode_result.decode_method,
                    local_path=dl.local_path, sha256=inspection.sha256,
                    perceptual_hash=inspection.perceptual_hash, mime_type=inspection.mime_type,
                    width=inspection.width, height=inspection.height, file_size=inspection.file_size,
                    quality_status="pass" if inspection.is_valid else "fail",
                    relevance_status="relevant" if classification.decision == "eligible" else "uncertain",
                    copyright_status="unknown", copyright_risk="medium", decision=classification.decision,
                    reasons=classification.rejection_reasons or classification.relevance_reasons,
                    asset_identity_sha256=identity_sha256,
                    content_description=candidate.context or "", content_description_source="page_alt",
                    video_poster=candidate.video_poster,
                    page_region=candidate.page_region, page_position={"known": False, "heading": None, "level": None},
                    upload={"mode": upload_mode, "status": "not_uploaded", "remote_url": None, "response_sha256": None},
                )
                pending_uploads.append((asset, dl.local_path, inspection, candidate.extraction_method))
                discovery_records.append({
                    "asset_id": asset_id, "asset_origin": "source", "material_id": iid_to_material.get(iid) or iid,
                    "source_page_url": page_url, "resolved_original_url": resolved_url,
                    "asset_sha256": inspection.sha256, "asset_identity_sha256": identity_sha256,
                })
                builder.add_asset(asset)
                total_assets_added += 1
                if asset.decision != "rejected":
                    accepted_assets_added += 1
                pool_image_count += 1
                print(f"  Pool {asset_id}: {resolved_url} — {classification.decision}")

    # OBS-71(档63):生成图表纳入批准链——决策 review_required、版权 unknown、
    # 计入数量上限、内容描述来自图表 spec(数据来源,非 claim 派生填充),
    # 与源图走同一批准路径。仅 discover 生成;continue 从冻结清单重建,
    # 图表必须有显式 single_asset 批准才会上传。禁止任何 known_allowed 硬编码。
    def _generate_charts() -> None:
        """discover 阶段生成图表(决策 review_required,需显式批准)。"""
        nonlocal asset_counter, total_assets_added, accepted_assets_added
        print(f"\n[media-enrichment] Generating charts (discover only)...")
        claims_with_numbers = [c for c in claims if c.get("numbers")]
        if claims_with_numbers:
            plan = build_chart_specs(claims_with_numbers, materials_by_id)
            for w in plan.warnings:
                builder.warnings.append(w)
                print(f"  WARN: {w}")
            for i, spec in enumerate(plan.specs):
                if accepted_assets_added >= discovery_budget:
                    builder.warnings.append(
                        f"discovery_budget ({discovery_budget}) reached — chart skipped (OBS-71)")
                    break
                chart_path = output_dir / "charts" / f"chart-{i+1:03d}.png"
                chart_result = generate_chart(spec, chart_path)
                if chart_result.success:
                    asset_counter += 1
                    asset_id = f"A-{asset_counter:03d}"
                    material_ids = sorted({dp.material_id for dp in spec.data_points})
                    claim_ids = sorted({dp.claim_id for dp in spec.data_points})
                    src_page = materials_by_id.get(material_ids[0], {}).get("source_url") or ""
                    resolved_url = f"{src_page}#chart-{chart_result.sha256[:12]}"
                    identity_sha256 = stable_asset_identity(
                        material_ids[0], src_page, resolved_url, chart_result.sha256)
                    desc = (f"生成图表({spec.chart_type})「{spec.title or ''}」,"
                            f"数据来源:{spec.source_note or 'canonical claim numbers'}")
                    asset = AssetRecord(
                        asset_id=asset_id, asset_origin="generated",
                        material_ids=material_ids, claim_ids=claim_ids,
                        extraction_method="generated", decode_method="none",
                        source_page_url=src_page,
                        discovered_url=f"generated://chart/{chart_result.sha256}",
                        resolved_original_url=resolved_url,
                        local_path=chart_result.chart_path, sha256=chart_result.sha256,
                        perceptual_hash=chart_result.inspection.perceptual_hash if chart_result.inspection else None,
                        mime_type="image/png",
                        width=chart_result.inspection.width if chart_result.inspection else None,
                        height=chart_result.inspection.height if chart_result.inspection else None,
                        file_size=chart_result.inspection.file_size if chart_result.inspection else None,
                        quality_status="pass", relevance_status="uncertain",
                        copyright_status="unknown", copyright_risk="medium",
                        asset_identity_sha256=identity_sha256,
                        decision="review_required",
                        reasons=["generated chart — requires explicit single_asset approval before upload (OBS-71)"],
                        caption=spec.caption or spec.title, alt_text=spec.caption or spec.title,
                        content_description=desc, content_description_source="generated",
                        page_region="generated",
                        placement={"anchor": spec.title.strip() or (spec.chart_group + chr(183) + spec.metric_name), "position": "after", "confidence": 0.9},
                        page_position={"known": True, "heading": spec.title.strip() or (spec.chart_group + chr(183) + spec.metric_name), "level": "article-anchor"},
                        upload={"mode": upload_mode, "status": "not_uploaded",
                                "remote_url": None, "response_sha256": None},
                    )
                    pending_uploads.append((asset, chart_result.chart_path,
                                            chart_result.inspection, "generated"))
                    discovery_records.append({
                        "asset_id": asset_id, "asset_origin": "generated",
                        "material_id": material_ids[0],
                        "source_page_url": src_page,
                        "resolved_original_url": resolved_url,
                        "asset_sha256": chart_result.sha256,
                        "asset_identity_sha256": identity_sha256,
                    })
                    builder.add_asset(asset)
                    total_assets_added += 1
                    if asset.decision != "rejected":
                        accepted_assets_added += 1
                    print(f"  Chart {i+1}: {chart_path} ({spec.chart_type}) — review_required")
                else:
                    builder.warnings.append(f"Chart generation failed: {chart_result.error}")
        else:
            builder.warnings.append("No claims with numbers — no charts generated")

    if args.phase != "continue":
        _generate_charts()

    # Freeze discovery before any source upload can occur. Discovery mode writes
    # the manifest and stops at classification; continue mode compares a freshly
    # resolved discovery against the user-approved frozen manifest.


    # the manifest and stops at classification; continue mode compares a freshly
    # resolved discovery against the user-approved frozen manifest.
    current_discovery = freeze_discovery_manifest(discovery_records)
    discovery_path = output_dir / "asset_discovery_manifest.json"
    write_discovery_manifest(discovery_path, current_discovery)
    current_discovery_sha = current_discovery["discovery_manifest_sha256"]

    approved_discovery = None
    approved_records: dict[str, dict] = {}
    discovery_file_valid = False
    if args.phase == "continue":
        if not args.discovery_manifest:
            builder.errors.append("continue phase requires --discovery-manifest")
        else:
            try:
                approved_discovery = json.loads(
                    Path(args.discovery_manifest).read_text(encoding="utf-8"))
                discovery_file_valid, approved_sha = verify_discovery_manifest(approved_discovery)
                if not discovery_file_valid:
                    builder.errors.append("approval_identity_mismatch: discovery manifest sha256 invalid")
                approved_records = {
                    item["asset_id"]: item for item in approved_discovery.get("assets", [])
                }
            except (OSError, ValueError, KeyError, TypeError) as exc:
                builder.errors.append(f"approval_identity_mismatch: cannot read discovery manifest: {exc}")

        current_by_id = {item["asset_id"]: item for item in discovery_records}
        for asset, local_path, inspection, extraction_method in pending_uploads:
            approval = asset_approvals.get(asset.asset_id)
            frozen = approved_records.get(asset.asset_id)
            mismatches: list[str] = []

            # hotfix6/hotfix4 approval precedence:
            #   restricted/no-repost > material/source_url > stable single_asset > unknown.
            # A stable approval may upgrade only an otherwise-unknown source asset;
            # it can never override an explicit restricted/no-repost decision.
            if approval is not None and asset.copyright_status == "restricted":
                asset.reasons.append(
                    "restricted/no-repost overrides single_asset approval")
            elif approval is not None and asset.copyright_status != "known_allowed":
                if not discovery_file_valid or frozen is None:
                    mismatches.append("discovery_manifest")
                else:
                    mismatches.extend(approval_mismatches(
                        approval, frozen,
                        approved_discovery["discovery_manifest_sha256"],
                    ))
                    fresh = current_by_id.get(asset.asset_id)
                    if fresh is None:
                        mismatches.append("fresh_discovery")
                    else:
                        for field_name in (
                            "material_id", "source_page_url", "resolved_original_url",
                            "asset_sha256", "asset_identity_sha256",
                        ):
                            if fresh.get(field_name) != frozen.get(field_name):
                                mismatches.append(f"fresh_{field_name}")
                if mismatches:
                    asset.approval_identity_mismatch = sorted(set(mismatches))
                    asset.reasons.append(
                        "approval_identity_mismatch: " + ", ".join(asset.approval_identity_mismatch))
                else:
                    # 77W/OBS-357:审批车道校验(single_asset 搬运块前 fail-fast)——
                    # 车道非法即记账 error(退出码 FAIL 路径),不消费批准、不改写
                    # 版权状态,资产维持不可上传;历史 auto_approve 遗留值合法。
                    lane_error = _approval_lane_error(approval, request)
                    if lane_error is not None:
                        builder.errors.append(lane_error)
                        continue
                    consumed_asset_approvals.add(asset.asset_id)
                    asset.discovery_manifest_sha256 = approval["discovery_manifest_sha256"]
                    asset.approval_id = approval["approval_id"]
                    asset.approved_scope = approval["approved_scope"]
                    asset.approved_by = approval["approved_by"]
                    asset.approved_at = approval["approved_at"]
                    asset.approval_evidence_sha256 = approval["approval_evidence_sha256"]
                    asset.asset_approval_consumed = True
                    asset.copyright_status = "known_allowed"

            # 档HF-4R/OBS-246:重分类块从 single_asset 的 elif 分支内 dedent
            # 到 for 循环体层级(与 if/elif 平级)——material/source_url 批准
            # (approval=None 但 copyright_status=known_allowed)与 single_asset
            # 批准自此真正共用同一块重跑分类逻辑;decision 可转 eligible。
            # restricted/no-repost(copyright_status != known_allowed)永不可
            # 被覆盖(优先级不变)。
            if asset.copyright_status == "known_allowed" and asset.decision in (
                    "review_required", "rejected"):
                classification = classify_image(
                    url=asset.resolved_original_url, inspection=inspection,
                    min_width=config.get("min_width", 640),
                    min_height=config.get("min_height", 360),
                    context="", copyright_status="known_allowed",
                    extraction_method=extraction_method,
                    internal_page=((asset.source_page_url or "").startswith(
                        "https://aihot.virxact.com/")),
                )
                asset.decision = classification.decision
                asset.relevance_status = (
                    "relevant" if classification.decision == "eligible" else "uncertain")
                asset.copyright_risk = (
                    "high" if classification.decision == "rejected" else "medium")
                asset.reasons = (
                    classification.rejection_reasons or classification.relevance_reasons)

            # 76R/OBS-289:媒体审批自动放行模式(默认关)——WXGZH_MEDIA_AUTO_APPROVE=1
            # 且单图证据链齐全(observable_content 可读 + page_position 已知 + sha256 在册
            # + 感知去重通过 + 非黑名单域名)时自动批准并完整入账;任一要素缺失或命中
            # 红旗(restricted/no-repost、黑名单、证据断链)仍硬停等人工。
            auto_approve_enabled = bool(config.get(
                "auto_approve", False)) and network_mode != "live"
            if (auto_approve_enabled
                    and asset.copyright_status not in ("known_allowed", "restricted")
                    and asset.decision == "review_required"
                    and asset.quality_status == "pass"
                    and asset.duplicate_of is None
                    and (asset.content_description or "").strip()
                    and not (asset.content_description or "").lstrip().startswith("<img")
                    and (asset.page_position or {}).get("known") is True
                    and asset.sha256):
                _host_aa = (urlsplit(asset.resolved_original_url or "").hostname or "").lower()
                if not any(_host_aa == d or _host_aa.endswith("." + d) for d in _bl):
                    asset.copyright_status = "known_allowed"
                    asset.approved_by = "auto_approve"
                    asset.approved_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    asset.approved_scope = "auto"
                    asset.auto_approved = True
                    asset.reasons.append("auto_approved: evidence chain complete (76R/OBS-289)")

            # Material/source_url approval is represented by the material's
            # copyright_review.status=known_allowed and needs no per-asset approval.
            # All approval modes still require a valid frozen discovery manifest
            # in continue, plus the normal quality/relevance/dedup gates.
            if (discovery_file_valid
                    and asset.copyright_status == "known_allowed"
                    and asset.decision == "eligible"
                    and asset.quality_status == "pass"
                    and asset.relevance_status == "relevant"
                    and asset.duplicate_of is None):
                prior = existing_upload_events.get(asset.asset_id)
                if prior is not None:
                    asset.upload = {
                        "mode": prior.get("mode", upload_mode),
                        "status": "success",
                        "remote_url": prior["url"],
                        "response_sha256": prior.get("response_sha256"),
                    }
                    upload_events.append({
                        "asset_id": asset.asset_id,
                        "mode": prior.get("mode", upload_mode),
                        "status": "skipped_already_uploaded",
                        "started_at": prior.get("started_at"),
                        "ended_at": prior.get("ended_at"),
                        "start_monotonic": prior.get("start_monotonic"),
                        "end_monotonic": prior.get("end_monotonic"),
                        "http_status": prior.get("http_status"),
                        "wechat_errcode": prior.get("wechat_errcode"),
                        "wechat_errmsg": prior.get("wechat_errmsg"),
                        "request_elapsed_seconds": 0.0,
                        "endpoint_path": prior.get("endpoint_path"),
                        "request_attempt_index": prior.get("request_attempt_index"),
                        "media_id": prior.get("media_id"),
                        "url": prior["url"],
                        "source_event": "existing_success_event",
                    })
                else:
                    # 76D/OBS-259:上传前 WebP→JPEG 自动转码(微信 40005 实证);
                    # 转码成功用新路径上传并留痕,转码失败 fail-closed(不上传)。
                    upload_path, tinfo, terr = transcode_webp_to_jpeg(local_path)
                    if terr:
                        builder.errors.append(
                            f"upload blocked for {asset.asset_id}: {terr}")
                        asset.upload = {"mode": upload_mode, "status": "failed",
                                        "remote_url": None, "response_sha256": None}
                        continue
                    if tinfo is not None:
                        tinfo = dict(tinfo, asset_id=asset.asset_id)
                        builder.transcodes.append(tinfo)
                    upload_result = timed_upload(
                        uploader, upload_events, upload_path, asset.asset_id,
                        copyright_status=asset.copyright_status,
                    )
                    asset.upload = {
                        "mode": upload_mode, "status": upload_result.status,
                        "remote_url": upload_result.remote_url,
                        "response_sha256": upload_result.response_sha256,
                    }
                    if upload_result.status != "success":
                        builder.errors.append(
                            f"upload failed for {asset.asset_id}: "
                            f"{upload_result.error or 'no success response'}")

    for aid in sorted(set(asset_approvals) - consumed_asset_approvals):
        builder.warnings.append(f"asset_approval for {aid} NOT consumed")


    # Placement
    article_full_path = Path(args.request).parent / article_path if article_path else None
    if article_full_path and article_full_path.exists():
        claim_texts = [c.get("claim_text", "") for c in claims if c.get("claim_text")]
        placements = find_anchors(article_full_path, claim_texts)
        for asset in builder.assets:
            if asset.decision in ("eligible", "review_required") and asset.claim_ids:
                for cid in asset.claim_ids:
                    claim = next((c for c in claims if c["claim_id"] == cid), None)
                    if claim:
                        placement = placements.get(claim.get("claim_text", ""))
                        if placement and placement.anchor:
                            # 77F/OBS-181: generated 图表已由 spec 直出 placement.anchor+page_position,
                            # 不再被 find_anchors 文本匹配(claim_text[:30])覆盖;直出锚点即过闸(e.g. i2z69i A-087)
                            if asset.asset_origin == "generated":
                                continue
                            asset.placement = {"anchor": placement.anchor, "position": placement.position, "confidence": placement.confidence}
                            # OBS-71:图表位置=拟绑定章节锚点(文章内位置,非页面位置)
                            if asset.asset_origin == "generated" and placement.anchor:
                                asset.page_position = {"known": True,
                                                       "heading": placement.anchor,
                                                       "level": "article-anchor"}
                            # dev5: generated charts keep their group-level caption/alt —
                            # a single claim text must never represent a multi-point chart
                            if asset.asset_origin != "generated":
                                asset.caption = placement.caption
                                asset.alt_text = placement.alt_text
    else:
        builder.warnings.append("Article file not found for placement planning")

    # Secrets scan
    manifest = builder.build()
    secrets = [f for f in scan_for_secrets(manifest) if f.split(":")[-1].strip() not in {"secrets_detected", "secret_scan_passed", "no_secrets_found"}]
    if secrets:
        builder.errors.extend([f"SECRET_DETECTED: {s}" for s in secrets])
        manifest = builder.build()
    manifest["gate"]["secrets_detected"] = len(secrets) > 0
    manifest["discovery_side_effects"] = discovery_side_effects

    manifest_path = output_dir / "media_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2, sort_keys=True)

    # dev7-hotfix1: emit article_image_bindings.json — the FINAL binding of body
    # images to their uploaded WeChat-host URLs (pure projection of the manifest;
    # never mutates the article, never uploads). Downstream gzh-design consumes it
    # and validate_media_manifest.py --bindings checks it per asset.
    from media_enrichment.article_bindings import write_bindings
    bindings_path = output_dir / "article_image_bindings.json"
    # 76G-R:绑定按 max_total_images 截断最终入文图数(76C 语义)
    write_bindings(manifest, bindings_path,
                   max_images=config.get("max_total_images"))

    # dev2-hotfix2: persist the serial upload event log for downstream audit
    events_path = output_dir / "upload_events.json"
    with open(events_path, "w", encoding="utf-8") as f:
        json.dump({"schema_version": "1.0", "serial": True,
                   "events": upload_events}, f, ensure_ascii=False, indent=2)

    # OBS-43: Pipeline's stage contract reads required outputs at the stage root,
    # while two-phase execution keeps its canonical continue copies in continue/.
    if args.phase == "continue" and output_dir.name == "continue":
        for output_path in (manifest_path, bindings_path, events_path):
            (output_dir.parent / output_path.name).write_bytes(output_path.read_bytes())

    print(f"\n[media-enrichment] Manifest: {manifest_path}")
    print(f"[media-enrichment] Bindings: {bindings_path}")
    print(f"  Assets: {len(builder.assets)}")
    print(f"  Eligible: {sum(1 for a in builder.assets if a.decision == 'eligible')}")
    print(f"  Review: {sum(1 for a in builder.assets if a.decision == 'review_required')}")
    print(f"  Rejected: {sum(1 for a in builder.assets if a.decision == 'rejected')}")
    print(f"  Errors: {len(builder.errors)}")
    print(f"  Warnings: {len(builder.warnings)}")

    sys.exit(1 if builder.errors else 0)


if __name__ == "__main__":
    main()
