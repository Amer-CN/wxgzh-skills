"""OBS-88(档66):注入路径写作合同校验 —— 数字结构化 + 代码块保真。

背景:档 65 取证定位,vibe-coding-guide 注入 RUN 的数字丢失在 c 层——super_writer
构建 canonical_claim_registry 时未把文章中的数字对比(8→11 / 19→25 / 四→五)登记
为结构化 numbers/chart_group/metric_name/series_label,导致 media 图表零生成;
代码块缺失因写作无形态指示,15 条 deny/ask 拦截文案被转写为散文。

本模块在 Pipeline 侧提供两个校验(仅注入路径强制,由 stages/super_writer.py
content_validate 挂载):

1. `validate_registry_numbers`:文章正文出现的数字对比对必须被 registry claims
   结构化登记(每对要求起/终两个数据点:numbers.value + chart_group +
   metric_name + series_label 非空)。支持中文数字(四→五)。文章没有的对比对
   不要求(不伪造);文章有的而 registry 没登记 → FAIL_CLOSED。
2. `validate_codeblock_fidelity`:注入素材中的 deny/ask 拦截文案(guard-bash.sh
   的 deny/ask 拦截文案(实测 16 条,⛔/⚠️ 前缀模板在 _common.sh)至少 10 条必须以
   【载体块】逐字进入文章,且载体内必须出现 ⛔ 与 ⚠️ 模板前缀;改写/散文化不计数。

OBS-176(档71E)载体放宽的正当性:档 65 取证的原始意图是【防散文化】——原文:
「代码块缺失因写作无形态指示,15 条 deny/ask 拦截文案被转写为散文」;不是
【必须用代码块】。故载体集合 = fenced code block ∪ 已批准 A 组组件块
(:::<name> … :::,name 必须来自 validators/validate_component_visibility 的
APPROVED_CARRIER_COMPONENTS,R48:单一来源 import,禁止手抄组件名)。
载体块体以外的正文一律不计数(R47);MIN_DENY_ASK_COVERAGE 保持 10,不得降低。

两者都只读 RUN 产物,不修改任何文件。
"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

# 中文数字 → 阿拉伯(本次所需范围 1-99,含常见组合)
_CN_DIGITS = {"零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
              "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
_DENY_ASK_RE = re.compile(r"(?:deny|ask)\s+'([^']+)'")
# 数字对比对:从? X 单位? (扩到|到|→) Y 单位?
_PAIR_RE = re.compile(
    r"从?\s*([0-9一二三四五六七八九十百两]+)\s*([条个项张组]?)\s*"
    r"(?:扩到|变为|改成|到|→)\s*"
    r"([0-9一二三四五六七八九十百两]+)\s*([条个项张组]?)")
_FENCE_RE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)
MIN_NUMBER_PAIRS = 3        # 本次预期:19→25 / 8→11 / 四→五
MIN_DENY_ASK_COVERAGE = 10  # 16 条中至少 10 条逐字进入载体块


def _load_approved_carrier_components() -> frozenset[str]:
    """R48(OBS-176):已批准载体集合从 validators/validate_component_visibility
    单一来源 import,禁止手抄组件名常量。与 stages.load_validator / tests
    conftest 同机制(importlib 文件加载),避免包循环依赖。

    S63(档71E):import 失败(路径/循环依赖)→ 由调用方停机上报,禁止改手填常量绕过。
    """
    root = Path(__file__).resolve().parents[1]
    path = root / "validators" / "validate_component_visibility.py"
    spec = importlib.util.spec_from_file_location("validate_component_visibility", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"S63 OBS-176 cannot import validate_component_visibility from {path}")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # noqa: BLE001 —— 原样上抛供 S63 停机贴原文
        raise RuntimeError(
            f"S63 OBS-176 import validate_component_visibility failed: {exc!r}") from exc
    approved = getattr(module, "APPROVED_CARRIER_COMPONENTS", None)
    if not isinstance(approved, frozenset):
        raise RuntimeError(
            "S63 OBS-176 APPROVED_CARRIER_COMPONENTS missing/not frozenset: "
            f"{approved!r}")
    return approved


_APPROVED_CARRIER_COMPONENTS = _load_approved_carrier_components()


def cn_to_int(token: str) -> int | None:
    """中文数字 → int(1-99,含 十/十五/二十/二十五 等常见形式);失败返回 None。"""
    if not token:
        return None
    if token.isdigit():
        return int(token)
    if all(c in _CN_DIGITS for c in token):
        if len(token) == 1:
            return _CN_DIGITS[token]
        # 两位及以上:先按「X十Y」/「十X」解析
        if "十" in token:
            parts = token.split("十")
            tens = _CN_DIGITS.get(parts[0], 1) if parts[0] else 1
            ones = _CN_DIGITS.get(parts[1], 0) if len(parts) > 1 and parts[1] else 0
            return tens * 10 + ones
    return None


def extract_number_pairs(text: str) -> list[tuple[int, int, str]]:
    """从文章/素材文本提取数字对比对 (start, end, unit)。

    仅接受可解析的数字(阿拉伯或中文);解析失败的对忽略(不伪造)。"""
    pairs: list[tuple[int, int, str]] = []
    for m in _PAIR_RE.finditer(text or ""):
        start = cn_to_int(m.group(1))
        end = cn_to_int(m.group(3))
        if start is None or end is None or start == end:
            continue
        unit = m.group(2) or m.group(4) or ""
        pairs.append((start, end, unit))
    return pairs


def _registry_claims(registry_path: Path) -> list[dict]:
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    claims = data.get("claims") or data.get("canonical_claims") or []
    return [c for c in claims if isinstance(c, dict)]


def validate_registry_numbers(article_path: Path, registry_path: Path) -> tuple[bool, dict]:
    """文章中的数字对比对必须被 registry 结构化登记。

    每对 (start, end, unit) 要求 registry 存在两个 claims:一个
    numbers.value==start、一个 numbers.value==end(unit 一致或空),且
    chart_group / metric_name / series_label 全部非空。"""
    article = article_path.read_text(encoding="utf-8")
    pairs = extract_number_pairs(article)
    claims = _registry_claims(registry_path)

    def find_point(value: int, unit: str) -> dict | None:
        for c in claims:
            nums = c.get("numbers")
            if isinstance(nums, dict):
                nums = [nums]  # 兼容单对象
            if isinstance(nums, list):
                for n in nums:
                    if isinstance(n, dict) and n.get("value") == value:
                        u = n.get("unit", "")
                        # 文章简写对不带单位(如「8→11」)时,不要求 claim 单位一致;
                        # 文章带单位(如「8 条扩到 11 条」)时,要求单位一致。
                        if u == unit or not unit:
                            if (c.get("chart_group") and c.get("metric_name")
                                    and c.get("series_label")):
                                return c
        return None

    # 去重:同一 (start, end) 的多次出现(正文详述 + 简写总结)只算一对
    seen_pairs = set()
    unique_pairs = []
    for start, end, unit in pairs:
        key = (start, end)
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        unique_pairs.append((start, end, unit))

    registered = []
    missing = []
    for start, end, unit in unique_pairs:
        a = find_point(start, unit)
        b = find_point(end, unit)
        if a is not None and b is not None:
            registered.append({"start": start, "end": end, "unit": unit,
                               "chart_group": a["chart_group"]})
        else:
            missing.append({"start": start, "end": end, "unit": unit})
    if not pairs:
        # 文章无数字对比对:无登记要求,不伪造(缺数字时不要求任何 numbers)
        ok = True
    else:
        ok = not missing and len(registered) >= MIN_NUMBER_PAIRS
    return ok, {
        "pairs_in_article": [{"start": s, "end": e, "unit": u} for s, e, u in unique_pairs],
        "registered": registered,
        "missing": missing,
        "min_pairs": MIN_NUMBER_PAIRS,
        "OBS88_NUMBERS": "PASS" if ok else "FAIL",
    }


def extract_deny_ask_lines(items_path: Path) -> list[str]:
    """从注入 items 的 summary(shell 原文)提取 deny/ask 拦截文案(逐字)。"""
    items = json.loads(items_path.read_text(encoding="utf-8"))
    lines: list[str] = []
    for item in items if isinstance(items, list) else []:
        summary = item.get("summary", "") if isinstance(item, dict) else ""
        for m in _DENY_ASK_RE.finditer(summary or ""):
            text = m.group(1).strip()
            if text and text not in lines:
                lines.append(text)
    return lines


def _carrier_blocks(article_text: str) -> tuple[list[str], list[str]]:
    """OBS-176(档71E):返回【载体块体文本】列表与其载体类型清单。

    载体 = ① fenced code block(三反引号,沿用 _FENCE_RE,向后兼容)
            ∪ ② 已批准 A 组组件块:从 ':::<name>' 开标签行到配对 ':::' 收尾行之间
              的内容,<name> 必须在 APPROVED_CARRIER_COMPONENTS 内。

    组件块提取与安装侧 gzh-design render_article.py parse_article() 的
    in_component 状态机口径一致(逐行:strip 后以 ::: 开头的行进入/关闭组件块,
    块体 = 开关行之间的原文行);嵌套/未配对 ':::' 一律不计为载体(宁可漏,不可多)。

    返回 (block_texts, kinds):kinds 为命中的载体类型名(如 ["fence","alert"])。
    """
    blocks: list[str] = []
    kinds: list[str] = []
    # ① fenced code block
    for m in _FENCE_RE.finditer(article_text or ""):
        blocks.append(m.group(1))
        kinds.append("fence")
    # ② 已批准组件块(状态机与安装侧 parse_article in_component 同口径)
    in_component = False
    comp_name = ""
    buf: list[str] = []
    for ln in (article_text or "").replace("\r\n", "\n").split("\n"):
        st = ln.strip()
        if in_component:
            if st.startswith(":::"):
                if comp_name in _APPROVED_CARRIER_COMPONENTS:
                    blocks.append("\n".join(buf))
                    kinds.append(comp_name)
                buf = []
                in_component = False
            else:
                buf.append(ln)
            continue
        if st.startswith(":::"):
            in_component = True
            buf = []
            head = st[3:].strip()
            comp_name = head.split()[0] if head.split() else ""
            continue
    return blocks, kinds


def validate_codeblock_fidelity(article_path: Path, items_path: Path) -> tuple[bool, dict]:
    """≥10 条 deny/ask 文案必须以【载体块】(fenced code block ∪ 已批准 A 组
    组件块)逐字进入文章,且载体内必须出现 ⛔ 与 ⚠️ 模板前缀。

    OBS-176(档71E):covered / 前缀判定只在载体块体内进行(R47);载体内正文
    一律不计数;MIN_DENY_ASK_COVERAGE 保持 10。返回新增 carrier_kinds 与
    carrier_block_count。"""
    article = article_path.read_text(encoding="utf-8")
    blocks, kinds = _carrier_blocks(article)
    block_text = "\n".join(blocks)
    lines = extract_deny_ask_lines(items_path)
    covered = [line for line in lines if line in block_text]
    has_deny_prefix = "⛔" in block_text
    has_ask_prefix = "⚠️" in block_text
    ok = (len(covered) >= MIN_DENY_ASK_COVERAGE
          and has_deny_prefix and has_ask_prefix)
    return ok, {
        "deny_ask_total": len(lines),
        "covered_in_codeblocks": len(covered),
        "min_coverage": MIN_DENY_ASK_COVERAGE,
        "deny_prefix_present": has_deny_prefix,
        "ask_prefix_present": has_ask_prefix,
        "missing_lines": [l for l in lines if l not in covered],
        "carrier_kinds": sorted(set(kinds)),
        "carrier_block_count": len(blocks),
        "OBS88_CODEBLOCK": "PASS" if ok else "FAIL",
    }
