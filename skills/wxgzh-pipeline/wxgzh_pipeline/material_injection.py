"""OBS-64(档64):素材注入正门(自有素材)。

背景:aihot 阶段是 agent 驱动的抓取阶段,无正式注入入口;事件 RUN
20260801T231452 曾以 agent 手写三文件的方式注入 18 条用户素材
(fetch_log.mode=user_materials_override),被定性为非受控通道(UNCONTROLLED)。
本模块提供正式 `--items-file` 注入入口:

1. schema 校验:注入 items 必须与 aihot 正常产出同构(缺字段 FAIL_CLOSED);
2. 来源留痕:每条素材必须携带 source_provenance(来源类型/原始标识/内容
   sha256),连同 items 文件 sha 写入 fetch_log(contract 哈希绑定,可追溯);
3. 注入标记:fetch_log.mode="items_file_injection" + injection 块,
   audit 中显式标记为「自有素材注入」,不得伪装成 aihot 检索结果;
4. 旧通道关闭:fetch_log.mode="user_materials_override" 由
   stages/aihot.py content_validate 判 FAIL(档64 起不可用)。

OBS-27(检索合同缺失)说明:注入路径不执行检索,「检索合同」语义不适用;
由注入证据链(来源留痕 + 注入标记 + items 文件 sha)替代,检索与注入
两条路径的产物同构,下游(registry/super_writer/media)无需区分。
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .state import sha256_file

INJECTION_MODE = "items_file_injection"
LEGACY_OVERRIDE_MODE = "user_materials_override"
ALLOWED_SOURCE_TYPES = ("local_file", "repo_path", "url")

# 与 aihot 正常产出同构的必填字段(缺任一即 FAIL_CLOSED)
REQUIRED_ITEM_FIELDS = (
    "id", "title", "source", "links", "source_url", "aihot_permalink",
)
REQUIRED_SOURCE_FIELDS = ("name",)
REQUIRED_LINKS_FIELDS = ("original", "aihot")
REQUIRED_PROVENANCE_FIELDS = ("source_type", "original_ref", "content_sha256")


class MaterialInjectionError(ValueError):
    """素材注入校验失败(fail-closed)。"""


def validate_items(items) -> list[dict]:
    """注入 items schema 校验:与 aihot 产出同构 + 来源留痕必填。"""
    if not isinstance(items, list) or not items:
        raise MaterialInjectionError(
            "material injection FAIL_CLOSED: items must be a non-empty list")
    out: list[dict] = []
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            raise MaterialInjectionError(
                f"material injection FAIL_CLOSED: item[{idx}] must be an object")
        missing = [f for f in REQUIRED_ITEM_FIELDS
                   if item.get(f) in (None, "")]
        if missing:
            raise MaterialInjectionError(
                f"material injection FAIL_CLOSED: item[{idx}] missing "
                f"required fields: {missing}")
        src = item.get("source")
        if not isinstance(src, dict):
            raise MaterialInjectionError(
                f"material injection FAIL_CLOSED: item[{idx}].source must be an object")
        if any(src.get(f) in (None, "") for f in REQUIRED_SOURCE_FIELDS):
            raise MaterialInjectionError(
                f"material injection FAIL_CLOSED: item[{idx}].source.name required")
        links = item.get("links")
        if not isinstance(links, dict):
            raise MaterialInjectionError(
                f"material injection FAIL_CLOSED: item[{idx}].links must be an object")
        if any(links.get(f) in (None, "") for f in REQUIRED_LINKS_FIELDS):
            raise MaterialInjectionError(
                f"material injection FAIL_CLOSED: item[{idx}].links.original/aihot required")
        prov = item.get("source_provenance")
        if not isinstance(prov, dict):
            raise MaterialInjectionError(
                f"material injection FAIL_CLOSED: item[{idx}] missing "
                "source_provenance (来源留痕必填)")
        if any(prov.get(f) in (None, "") for f in REQUIRED_PROVENANCE_FIELDS):
            raise MaterialInjectionError(
                f"material injection FAIL_CLOSED: item[{idx}].source_provenance "
                f"requires {REQUIRED_PROVENANCE_FIELDS}")
        if prov["source_type"] not in ALLOWED_SOURCE_TYPES:
            raise MaterialInjectionError(
                f"material injection FAIL_CLOSED: item[{idx}] source_type "
                f"{prov['source_type']!r} not in {ALLOWED_SOURCE_TYPES}")
        if not isinstance(prov["content_sha256"], str) or len(prov["content_sha256"]) != 64:
            raise MaterialInjectionError(
                f"material injection FAIL_CLOSED: item[{idx}] content_sha256 "
                "must be a 64-hex digest")
        out.append(item)
    return out


def build_fetch_log(items: list[dict], items_file: Path, run_id: str,
                    topic: str) -> dict:
    """构造注入版 fetch_log(contract 哈希绑定,audit 显式标记)。"""
    items_file = Path(items_file)
    return {
        "skill": "aihot",
        "topic": topic,
        "mode": INJECTION_MODE,
        "aihot_api_skipped": True,
        "reason": "自有素材注入(档64 正式入口 --items-file):不执行 AI HOT 检索,"
                  "注入事实显式标记,不伪装为检索结果",
        "injection": {
            "items_file": str(items_file),
            "items_file_sha256": sha256_file(items_file),
            "item_count": len(items),
            "provenance": [
                {
                    "id": item["id"],
                    "source_type": item["source_provenance"]["source_type"],
                    "original_ref": item["source_provenance"]["original_ref"],
                    "content_sha256": item["source_provenance"]["content_sha256"],
                }
                for item in items
            ],
        },
        "queries": [],
        "raw_count": len(items),
        "deduplicated_count": len(items),
        "dedup_notes": "注入素材按 id 唯一,不做合并;id 与 source_provenance 一一对应",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def write_injected_aihot(sd: Path, items_file: Path, run_id: str,
                         topic: str) -> dict:
    """写注入三文件(deduplicated_items / raw_items / fetch_log)。

    - 冻结 items 输入副本到 aihot/items_file.injected.json(审计留档);
    - raw_items.json 与 deduplicated_items.json 同构(注入无 API 原始响应,
      raw=注入清单本身,与正常路径的「原始抓取清单」语义一致)。
    """
    sd = Path(sd)
    items_file = Path(items_file)
    if not items_file.is_file():
        raise MaterialInjectionError(
            f"material injection FAIL_CLOSED: items file missing: {items_file}")
    try:
        items = json.loads(items_file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise MaterialInjectionError(
            f"material injection FAIL_CLOSED: items file unreadable: {exc}")
    items = validate_items(items)

    frozen = sd / "items_file.injected.json"
    frozen.write_bytes(items_file.read_bytes())
    (sd / "deduplicated_items.json").write_text(
        json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    (sd / "raw_items.json").write_text(
        json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    fetch_log = build_fetch_log(items, items_file, run_id, topic)
    (sd / "fetch_log.json").write_text(
        json.dumps(fetch_log, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "mode": INJECTION_MODE,
        "items_file": str(items_file),
        "items_file_sha256": fetch_log["injection"]["items_file_sha256"],
        "frozen_copy": str(frozen),
        "item_count": len(items),
    }
