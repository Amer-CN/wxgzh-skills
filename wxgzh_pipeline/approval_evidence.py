"""OBS-87(档61):批准信息链闸门 — Pipeline 侧,不碰被锁 skill。

背景(假绿第六例):media-enrichment discover 产物的 alt_text/caption 由
placement_planner 以 claim_text 派生(placement_planner.py L67-68/L84-85/L94-95:
alt_text = claim_text[:60]、caption = "图：" + claim_text[:40]),不是图片内容
描述。档 50 对 A-109 的「内容适配性」批准即被该派生文本误导——系统把文章自己
的论点贴在图片上当作图片描述,再请审核者判断相关性。任何图配任何文,在这套
机制下都必然显得相关。

本模块在 Pipeline 侧建立「批准前信息完备性」闸门,三件事:

1. 内容描述:资产必须携带可验证的 content_description(来自图片自身或其页面
   上下文,不得来自文章文本),否则如实标记「内容不明」且不得进入批准点。
2. 页面位置:资产必须能定位到源页面的章节(DOM 文档序前置标题),否则不得进入
   批准点。
3. rejected 资产不得写入/消费批准合同(档 50 A-107 类:decision=rejected 仍被
   批准并消费)。

与 OBS-82 的分界:OBS-82(档55)挡物理门槛(尺寸 <640x360);OBS-87 挡批准语义
门槛(decision 状态 + 信息完备性)。两者独立、都 FAIL_CLOSED。

口径说明(OBS-31 教训):本模块不做「生产派生值」,只做「检测派生痕迹」;
闸门的阻断力来自字段级要求——当前 manifest 无 content_description 字段,
六张真实资产全部无法进入批准点,直到 media-enrichment 侧(OBS-86/档62)补上
字段。即使派生检测漏判,字段缺失依然 FAIL_CLOSED,不存在双口径放行路径。

OBS-74 教训同源:同一份代码存在多个不同步的副本会腐烂;同一份证据自我循环
会造假。本闸门只读 RUN 产物,新增 approval_readiness.json,不修改任何被锁
skill、lock、台账与既有 RUN 文件。
"""
from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .state import sha256_file

# 与 placement_planner.py 派生逻辑对应的检测窗口(见模块 docstring 口径说明)
CLAIM_ALT_WINDOW = 60   # alt_text = claim_text[:60]
CLAIM_CAPTION_WINDOW = 40  # caption = "图：" + claim_text[:40]

# 可信的内容描述来源:必须来自图片自身或其页面上下文
ALLOWED_DESCRIPTION_SOURCES = frozenset(
    {"page_alt", "page_context", "human", "visual_analysis"})

# 页面位置解析允许的标题层级
_SECTION_HEADING_LEVELS = ("h1", "h2", "h3")
_IMAGE_ATTRS = ("src", "srcset", "data-src", "data-original", "data-lazy-src")
_FETCH_MAX_BYTES = 5 * 1024 * 1024


class ApprovalEvidenceError(Exception):
    """OBS-87 批准信息链闸门失败(fail-closed)。"""


def load_claim_texts(run_dir: Path) -> list[str]:
    """从 canonical_claim_registry.json 读全部 claim_text(与 _build_media_request
    同一文件、同一语义)。取不到即 FAIL_CLOSED。"""
    reg_p = Path(run_dir) / "super_writer" / "canonical_claim_registry.json"
    if not reg_p.is_file():
        raise ApprovalEvidenceError(
            "approval evidence FAIL_CLOSED: canonical_claim_registry.json missing")
    try:
        reg = json.loads(reg_p.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise ApprovalEvidenceError(
            f"approval evidence FAIL_CLOSED: canonical registry malformed: {exc}")
    claims = reg.get("claims") or reg.get("canonical_claims") or []
    texts = [str(c.get("claim_text", "")) for c in claims if isinstance(c, dict)]
    if not texts:
        raise ApprovalEvidenceError(
            "approval evidence FAIL_CLOSED: canonical registry has no claims")
    return texts


def is_claim_derived_text(alt_text: str | None, caption: str | None,
                          claim_texts: list[str]) -> bool:
    """检测 alt_text/caption 是否与 placement_planner 的 claim 派生模式吻合。

    派生模式:alt_text == claim_text[:60];caption == "图：" + claim_text[:40]。
    检测是保守的:文本是某条 claim 的前缀(≤窗口长度)即判派生,宁可多标
    「内容不明」也不放行自证文本。"""
    alt = (alt_text or "").strip()
    cap = (caption or "").strip()
    for ct in claim_texts:
        ct = (ct or "").strip()
        if not ct:
            continue
        if alt and len(alt) <= CLAIM_ALT_WINDOW and ct.startswith(alt):
            return True
        if cap.startswith("图："):
            body = cap[2:]
            if body and len(body) <= CLAIM_CAPTION_WINDOW and ct.startswith(body):
                return True
    return False


def assess_content(asset: dict, claim_texts: list[str]) -> dict:
    """对单张资产做内容描述评估。返回:
      {"kind", "description", "source", "verified"}
    kind: verified / claim_derived / empty / unverifiable
    「内容不明」不是放行理由也不是拒绝理由,它是必须呈现给批准者的事实;
    但「缺少可验证内容描述」使资产不得进入批准点(第5条)。"""
    alt = asset.get("alt_text")
    caption = asset.get("caption")
    desc = asset.get("content_description")
    desc_source = asset.get("content_description_source")

    if isinstance(desc, str) and desc.strip():
        if desc_source not in ALLOWED_DESCRIPTION_SOURCES:
            return {"kind": "unverifiable",
                    "description": "内容不明(存在 content_description 但来源字段无效或缺失,无法验证)",
                    "source": desc_source, "verified": False}
        if is_claim_derived_text(desc, None, claim_texts):
            return {"kind": "claim_derived",
                    "description": "内容不明(content_description 为文章 claim 派生文本,非图片内容描述)",
                    "source": desc_source, "verified": False}
        return {"kind": "verified", "description": desc.strip(),
                "source": desc_source, "verified": True}

    if is_claim_derived_text(alt, caption, claim_texts):
        return {"kind": "claim_derived",
                "description": "内容不明(alt_text/caption 为文章 claim 派生文本,非图片内容描述)",
                "source": None, "verified": False}
    if not alt and not caption:
        return {"kind": "empty",
                "description": "内容不明(无任何内容描述)",
                "source": None, "verified": False}
    return {"kind": "unverifiable",
            "description": "内容不明(存在文本但来源无法验证,且缺少 content_description 字段)",
            "source": None, "verified": False}


def fetch_html(url: str, timeout: int = 20) -> str | None:
    """抓取源页面 HTML 用于位置解析。失败返回 None(位置未知 -> 不得进入批准点,
    属 fail-closed,不允许降级为本地推断)。"""
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 (OBS-87 approval-readiness)"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read(_FETCH_MAX_BYTES)
        return data.decode("utf-8", "ignore")
    except Exception:
        return None


def _image_attrs_text(node) -> str:
    return " ".join(str(node.get(attr, "") or "") for attr in _IMAGE_ATTRS)


def _matches_image(attrs_text: str, url: str) -> bool:
    if url in attrs_text:
        return True
    filename = url.rstrip("/").split("/")[-1]
    return bool(filename) and filename in attrs_text


def extract_section_map(html: str, image_urls: list[str]) -> dict[str, dict]:
    """DOM 文档序:每张图取其前最近 h1/h2/h3 文本。与档 60 取证方法一致。

    返回 {image_url: {"heading": str, "level": str}};页面里找不到的图不出现。"""
    from bs4 import BeautifulSoup
    targets = [u for u in image_urls if u]
    if not targets:
        return {}
    soup = BeautifulSoup(html or "", "html.parser")
    last_heading: tuple[str, str] | None = None
    found: dict[str, dict] = {}
    for node in soup.find_all([*_SECTION_HEADING_LEVELS, "img"]):
        if node.name in _SECTION_HEADING_LEVELS:
            text = node.get_text(strip=True)
            if text:
                last_heading = (node.name, text)
        elif node.name == "img":
            attrs = _image_attrs_text(node)
            for url in targets:
                if url not in found and _matches_image(attrs, url):
                    if last_heading is not None:
                        found[url] = {"heading": last_heading[1],
                                      "level": last_heading[0]}
                    else:
                        found[url] = {"heading": "", "level": ""}
    return found


def build_approval_readiness(
    run_dir: Path,
    claim_texts: list[str] | None = None,
    html_provider: Callable[[str], str | None] | None = None,
) -> dict:
    """构建批准前信息完备性报告(批准清单呈现物 + 闸门输入)。

    - 读 discover/media_manifest.json(取不到即 FAIL_CLOSED)
    - 每个资产:内容描述评估 + 页面位置解析 + 可批准性
    - approvable = decision ∈ {review_required, eligible}
                  且 content.verified 且 page_position.known
    - html_provider 可注入(测试用);默认 fetch_html。"""
    run_dir = Path(run_dir)
    manifest_path = run_dir / "media_enrichment" / "discover" / "media_manifest.json"
    if not manifest_path.is_file():
        raise ApprovalEvidenceError(
            "approval evidence FAIL_CLOSED: discover media_manifest.json missing")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise ApprovalEvidenceError(
            f"approval evidence FAIL_CLOSED: invalid discover media_manifest: {exc}")
    assets = manifest.get("assets") or []
    if not isinstance(assets, list):
        raise ApprovalEvidenceError(
            "approval evidence FAIL_CLOSED: discover manifest assets invalid")

    if claim_texts is None:
        claim_texts = load_claim_texts(run_dir)
    provider = html_provider or fetch_html

    # OBS-86(档62)联动:manifest 已带 page_position(提取层产出,章节归属)
    # 时优先直接消费,不再重抓页面;仅对缺字段的旧 manifest 回退到页面解析。
    # 闸门语义不变:位置必须 known 才可批准。
    def _manifest_position(asset: dict) -> dict | None:
        pos = asset.get("page_position")
        if isinstance(pos, dict) and pos.get("known") is True and pos.get("heading"):
            return {"known": True, "heading": str(pos["heading"]),
                    "level": str(pos.get("level") or "")}
        if isinstance(pos, dict) and pos.get("known") is False:
            return {"known": False, "heading": None, "level": None}
        return None

    # 按 source_page_url 分组抓取一次,缓存(仅缺 manifest 位置字段的资产)
    page_cache: dict[str, str | None] = {}
    by_page: dict[str, list[dict]] = {}
    for asset in assets:
        if not isinstance(asset, dict) or not asset.get("asset_id"):
            continue
        # rejected 资产不抓取页面位置(仍出现在 readiness 记录中,呈现为不可批准)
        if asset.get("decision") not in ("review_required", "eligible"):
            continue
        if _manifest_position(asset) is not None:
            continue
        src = asset.get("source_page_url")
        if src:
            by_page.setdefault(str(src), []).append(asset)
    for src, page_assets in by_page.items():
        if src not in page_cache:
            page_cache[src] = provider(src)
        html = page_cache[src]
        if not html:
            continue
        section_map = extract_section_map(
            html, [str(a.get("resolved_original_url") or "") for a in page_assets])
        for asset in page_assets:
            url = str(asset.get("resolved_original_url") or "")
            if url in section_map:
                asset["_obs87_section"] = section_map[url]

    records = []
    for asset in sorted(assets, key=lambda a: str(a.get("asset_id", ""))):
        if not isinstance(asset, dict) or not asset.get("asset_id"):
            continue
        aid = asset["asset_id"]
        decision = asset.get("decision", "")
        content = assess_content(asset, claim_texts)
        section = asset.get("_obs87_section")
        manifest_pos = _manifest_position(asset)
        if manifest_pos is not None:
            position_known = bool(manifest_pos.get("known"))
            pos_heading = manifest_pos.get("heading")
            pos_level = manifest_pos.get("level")
        else:
            position_known = isinstance(section, dict) and bool(section.get("heading"))
            pos_heading = section["heading"] if position_known else None
            pos_level = section["level"] if position_known else None
        blockers = []
        if decision not in ("review_required", "eligible"):
            blockers.append(f"decision={decision} — 非可批准状态,不得写入批准合同")
        if not content["verified"]:
            blockers.append("缺少可验证内容描述(" + content["kind"] + ")")
        if not position_known:
            blockers.append("页面位置未知")
        records.append({
            "asset_id": aid,
            "decision": decision,
            "content": content,
            "page_position": (
                {"known": True, "heading": pos_heading, "level": pos_level}
                if position_known else {"known": False, "heading": None, "level": None}),
            "approvable": not blockers,
            "approvable_blockers": blockers,
        })
    summary = {
        "total": len(records),
        "approvable": sum(1 for r in records if r["approvable"]),
        "blocked": sum(1 for r in records if not r["approvable"]),
    }
    return {
        "schema_version": "1.0",
        "run_id": str(manifest.get("run_id", "")),
        "discovery_manifest_sha256": str(manifest.get("discovery_manifest_sha256", "")),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "gate": {
            "content_description_required": True,
            "page_position_required": True,
            "claim_derived_text_never_accepted": True,
        },
        "assets": records,
        "summary": summary,
    }


def enforce_approval_readiness(
    readiness_path: Path,
    readiness: dict,
    approvals: list[dict],
) -> None:
    """消费端闸门:批准合同中的每个 single_asset 记录必须:

    1. 携带 approval_readiness_sha256 且等于当前 approval_readiness.json 的
       sha256 —— 旧合同(档49/50 的 AP-…-001/002)缺该字段,自动失效;
    2. 目标资产在 readiness 中 approvable(内容可验证 + 位置已知
       + decision 非 rejected)—— 六张电车图与 A-107 类全部被拦。"""
    if not readiness_path.is_file():
        raise ApprovalEvidenceError(
            "approval evidence FAIL_CLOSED: approval_readiness.json missing")
    actual_sha = sha256_file(readiness_path)
    by_id = {r["asset_id"]: r for r in readiness.get("assets", [])}
    for appr in approvals:
        aid = appr.get("asset_id")
        ref = appr.get("approval_readiness_sha256")
        if not ref or not isinstance(ref, str) or ref.lower() != actual_sha.lower():
            raise ApprovalEvidenceError(
                f"approval evidence FAIL_CLOSED: approval for {aid} does not "
                "reference current approval_readiness.json (missing/stale "
                "approval_readiness_sha256) — 旧批准合同自动失效,不得复用")
        rec = by_id.get(aid)
        if rec is None:
            raise ApprovalEvidenceError(
                f"approval evidence FAIL_CLOSED: approved asset {aid} absent "
                "from approval readiness")
        if not rec["approvable"]:
            detail = "; ".join(rec["approvable_blockers"]) or "not approvable"
            raise ApprovalEvidenceError(
                f"approval evidence FAIL_CLOSED: asset {aid} not approvable "
                f"under OBS-87 gate ({detail})")
