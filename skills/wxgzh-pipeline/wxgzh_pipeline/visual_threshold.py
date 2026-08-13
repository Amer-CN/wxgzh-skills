"""OBS-89/档67/档68:视觉内容门槛分级 + 同数据重复检测。

背景:技术文(代码密集型)的媒体形态与新闻综述不同——正文以代码块为主体,
可批准候选常少于 6 张新闻配图。档 67 引入两级客观判据(判据全部从冻结产物
final_article.md 计算,无人工标记字段、无环境开关、无 profile 判据),同时
实现 OBS-89 同数据图表去重。档 68 正式启用分级,依据留痕见 compute_visual_tier
返回的 evidence 字段(替换档 67 的浏览器高度几何估算)。

分级判据(全部可从产物客观计算):
1. code_blocks = final_article.md 中成对 ``` 围栏且含 >=1 行非空内容的代码块数;
2. code_dense  = code_blocks >= 2(独立理由:单代码块可能是引用性片段,不足以
   定义文章形态;>=2 说明文章以代码/命令为主体,属技术文);
3. 非 code_dense  -> body_images_min = 6(默认不变,新闻综述门槛不降低);
   code_dense     -> body_images_min = 3(最低可见性基线)
                      且要求 images + code_blocks >= 5(视觉内容达标)。

代码块权重 1:1 的独立依据(档68 正式启用,替换旧 250px 几何估算):
- 依据一:1a 深色代码块是 references/common-components.md 的默认组件,规范原文
  声明「适配所有主题」——它是本 skill 的官方视觉单元,不是临时排版。
- 依据二:2026-08-05 00:27–00:37 用户在微信编辑器内人工预览实测,深色卡片、圆角、
  顶栏、红黄绿三圆点、语言标签全部保留未被剥离——代码块在最终平台上确为独立
  视觉单元。
- 依据三:用户历史文章长期使用该组件形态且呈现正确(用户 2026-08-04 22:41 陈述)。
- 视觉锚点下限 5:3000+ 字长文约每 600-800 字需要一个视觉锚点(图片或代码块,
  可读性基线),3950 字文章 -> >=5 个锚点,5 为保守下界。

OBS-89 同数据去重:生成图表按 chart_group + 其 claim_ids 对应的 numbers 集合
(排序后的 (value, unit) 元组)分组;同组仅保留一张,其余标记 duplicate_of 且
approvable=false。确定性规则:优先 bar 形态(从 content_description 解析
「生成图表(<type>)」,解析失败回退最小 asset_id)。依据:数据点为 2 个版本对比
时,bar 是单指标多版本对比的基础形态,comparison 的并列增强在仅 2 个数据点时
与 bar 视觉信息等价(无信息增量);保留 bar 确定性、可审计,不由人工挑选。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

CODE_DENSE_MIN_BLOCKS = 2       # >=2 个代码块 => 代码密集型(技术文)
CODE_DENSE_IMAGE_MIN = 3        # 代码密集型文章的正文图下限
NEWS_IMAGE_MIN = 6              # 非代码密集型(新闻综述)门槛,不得降低
CODE_DENSE_VISUAL_UNITS = 5     # 代码密集型文章视觉锚点下限(图片 + 代码块)

# 档68:视觉分级正式启用的三条依据(替换档67 的 250px/211px 浏览器高度估算)。
# 必须随 readiness 的 visual_tier 块与 stage_result.VISUAL_TIER 一并留痕。
VISUAL_TIER_EVIDENCE = [
    "依据一:references/common-components.md 1a 深色代码块为默认组件,规范声明「适配所有主题」——官方视觉单元,非临时排版。",
    "依据二:2026-08-05 00:27–00:37 微信编辑器人工预览实测,深色卡片/圆角/顶栏/三圆点/语言标签全部保留未被剥离。",
    "依据三:用户历史文章长期使用该组件形态且呈现正确(用户 2026-08-04 22:41 陈述)。",
]

_FENCE_RE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)
_CHART_TYPE_RE = re.compile(r"^生成图表\((\w+)\)")


def count_code_blocks(article_text: str) -> int:
    """final_article.md 中成对 ``` 围栏且含 >=1 行非空内容的代码块数。"""
    if not article_text:
        return 0
    blocks = _FENCE_RE.findall(article_text)
    return sum(1 for b in blocks if any(line.strip() for line in b.splitlines()))


def compute_visual_tier(article_text: str) -> dict:
    """从冻结文章计算视觉门槛分级(客观判据,无人工输入)。"""
    code_blocks = count_code_blocks(article_text)
    code_dense = code_blocks >= CODE_DENSE_MIN_BLOCKS
    return {
        "code_blocks": code_blocks,
        "code_dense": code_dense,
        "body_images_min": CODE_DENSE_IMAGE_MIN if code_dense else NEWS_IMAGE_MIN,
        "visual_units_min": CODE_DENSE_VISUAL_UNITS if code_dense else None,
        "evidence": list(VISUAL_TIER_EVIDENCE),
        "criterion": (
            "code_dense(>=2 fenced blocks) => body_images>=3 且 images+code_blocks>=5"
            if code_dense
            else "news(0-1 fenced blocks) => body_images>=6,门槛不降低"),
    }


def effective_body_images_min(tier: dict, config_value: int | None) -> int:
    """有效图片下限:分级值;若存在 validation_config.json,取其 max(分级值, 配置值)
    ——分级值是文章类型的客观下限,配置(人工)不得把新闻类压到 6 以下。"""
    tier_min = int(tier.get("body_images_min", NEWS_IMAGE_MIN))
    if config_value is None:
        return tier_min
    return max(tier_min, config_value)


def _chart_data_key(asset: dict, claims_by_id: dict) -> tuple | None:
    """生成图表的分组键:(chart_group, 排序后的 (value, unit) 元组)。"""
    if asset.get("asset_origin") != "generated":
        return None
    group = None
    points: list[tuple] = []
    for cid in asset.get("claim_ids") or []:
        claim = claims_by_id.get(cid)
        if not isinstance(claim, dict):
            return None
        if group is None:
            group = claim.get("chart_group") or ""
        elif (claim.get("chart_group") or "") != group:
            return None
        nums = claim.get("numbers")
        if isinstance(nums, dict):
            nums = [nums]
        if not isinstance(nums, list):
            return None
        for n in nums:
            if not isinstance(n, dict) or n.get("value") is None:
                return None
            points.append((n.get("value"), n.get("unit", "")))
    if group is None or not points:
        return None
    return (group, tuple(sorted(points)))


def _chart_type(asset: dict) -> str | None:
    desc = asset.get("content_description") or ""
    m = _CHART_TYPE_RE.match(desc)
    return m.group(1) if m else None


def dedup_same_data_charts(records: list[dict], assets_by_id: dict,
                           registry_path: Path) -> list[dict]:
    """OBS-89:同 chart_group + 同 numbers 的生成图表,最多一张可批准。

    确定性规则:优先 bar 形态(content_description 解析);同形态/解析失败时
    回退最小 asset_id。其余标记 duplicate_of 且 approvable=false。"""
    if not registry_path.is_file():
        return records
    try:
        reg = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return records
    claims_by_id = {c.get("claim_id"): c for c in reg.get("claims", [])
                    if isinstance(c, dict)}

    key_by_aid: dict[str, tuple | None] = {}
    for aid, asset in assets_by_id.items():
        key_by_aid[aid] = _chart_data_key(asset, claims_by_id)

    # 只对可分组(同数据)的生成图表做去重
    groups: dict[tuple, list[str]] = {}
    for rec in records:
        key = key_by_aid.get(rec["asset_id"])
        if key is None:
            continue
        if rec.get("decision") not in ("review_required", "eligible"):
            continue
        groups.setdefault(key, []).append(rec["asset_id"])

    duplicate_of: dict[str, str] = {}
    for key, aids in groups.items():
        if len(aids) < 2:
            continue
        # 确定性保留:bar 优先,其次最小 asset_id
        def _rank(aid: str) -> tuple:
            t = _chart_type(assets_by_id.get(aid, {}))
            return (0 if t == "bar" else 1, aid)
        keep = min(aids, key=_rank)
        for aid in aids:
            if aid != keep:
                duplicate_of[aid] = keep

    if not duplicate_of:
        return records

    out = []
    for rec in records:
        dup = duplicate_of.get(rec["asset_id"])
        if dup is not None:
            rec["duplicate_of"] = dup
            rec["approvable"] = False
            rec["approvable_blockers"].append(
                f"OBS-89: 与 {dup} 同 chart_group 同 numbers,仅保留确定性形态(bar),"
                "同数据重复不得进入批准合同")
        else:
            rec.setdefault("duplicate_of", None)
        out.append(rec)
    return out
