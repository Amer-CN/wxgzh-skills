#!/usr/bin/env python3
"""档71C-R2 OBS-145-150:组件载体判据分裂 + 锚实测导出 + 四名单。

判据(2b/2c/2d,单一来源写死在本文件):
  render_ok   全部必填槽哨兵出现在渲染 HTML 原文(只问渲染器,含属性)。
  anchor_ok   全部必填槽哨兵出现在 _body_plain_text(只问 pipeline 锚)。
  per_item_ok v2(2d):multi 槽组件给 N=3 输入,要求 N 个哨兵各自的最近
               <p style> 祖先起始偏移两两不同、且不同偏移数量 == N。
               ★已删除 _BASE_EL_COUNT/_measure_base_el_count 与魔数阈值 3
               (OBS-140/OBS-147 治本)。

四名单(5a/5b;OBS-160 口径,档71C-R4):
  QUARANTINED = {not render_ok}(语义收紧,注释写明变更与档号)
  MULTILINE_UNSUPPORTED = {render_ok 且 not struct_ok}(多行塌陷)
  ANCHOR_GAP = {render_ok 且 not anchor_ok}(不拦作者、不进 fail-closed)
  APPROVED_CARRIER = {render_ok 且 anchor_ok}
  ★语义说明:anchor_ok = 「JSON 锚与当前渲染器同步 + 哨兵确在其最近 <p> 内」。
  本档不声称「锚全量覆盖已证」;空集名单的反证物见 tests/fixtures/fake_*.py
  (R32:无反证物的结论只写「未观察到」)。

锚导出(3a):export_body_anchors_from_measurement(renderer) 对每个哨兵定位最近
  <p style="…"> 祖先,产出 style 串集合;找不到祖先记 NO_P_ANCHOR 并停机 S37。
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# 三名单快照(实测导出;测试以 R19 口径断言 == 现场导出,禁止赋值后自证)。
# OBS-145(档71C-R2):QUARANTINED 语义由「哨兵未进 final.html」收紧为「not render_ok」;
# 新增 ANCHOR_GAP = render_ok 且 not anchor_ok(渲染器吐字但 pipeline 锚缺口)。
# 实测导出快照(档71C-R3 实测):锚闭环(OBS-154)后 _COMPONENT_PARA_RES 从
# component_anchors.json 全量导出(条数以 component_anchors.json 现算为准,当前 17),9 类全部 render_ok+struct_ok+
# anchor_ok -> QUARANTINED/MULTILINE/ANCHOR_GAP 全空,APPROVED = 9 类全部。
# 测试以 R19 断言 == 现场导出,防快照过期。
QUARANTINED_COMPONENTS = frozenset()
MULTILINE_UNSUPPORTED_COMPONENTS = frozenset()
ANCHOR_GAP_COMPONENTS = frozenset()
APPROVED_CARRIER_COMPONENTS = frozenset({"alert", "code-compare", "dialogue",
                                         "footnotes", "gallery", "long-image",
                                         "media-text", "quote", "resources"})

# ── 4a(OBS-155):三张哨兵表从 component_slots.SLOTS 机械生成 ──
# 哨兵名 = S_<COMP>_<SLOT>;同一 (组件,槽) 多模式时追加模式后缀(type=note -> _NOTE,
# lang=有 -> _YES);multi 槽按 N=3 追加 _1.._N。禁止手写(4b 测试焊死与 SLOTS 对应)。
def _load_slots():
    """延迟 import component_slots(CLI 直跑时 repo 根由 main 注入 sys.path)。"""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from validators.component_slots import SLOTS
    return SLOTS


_SLOTS = _load_slots()


def _sentinel_name(comp: str, slot_name: str, mode: str, idx: int | None = None) -> str:
    base = f"S_{comp.upper().replace('-', '_')}_{slot_name.upper()}"
    suffix = ""
    if mode and mode != "默认" and "*" not in mode:
        if mode.startswith("type="):
            suffix = "_" + mode[5:].upper()
        elif mode.startswith("lang="):
            suffix = "_" + ("YES" if mode[5:] == "有" else "NO")
    if idx is not None:
        suffix += f"_{idx + 1}"
    return base + suffix


def _build_sentinel_tables() -> tuple[dict, dict, dict]:
    required: dict[str, list[str]] = {}
    optional: dict[str, list[str]] = {}
    url: dict[str, list[str]] = {}
    for cs in _SLOTS:
        comp = cs.component
        slot_entries: dict[str, list] = {}
        for s in cs.slots:
            slot_entries.setdefault(s.name, []).append(s)
        for slot_name, entries in slot_entries.items():
            s0 = entries[0]
            multi_n = 3 if s0.multi else None
            target = url if s0.url else (required if s0.required else optional)
            target.setdefault(comp, [])
            for e in entries:
                if multi_n is not None:
                    for i in range(multi_n):
                        n = _sentinel_name(comp, slot_name, e.mode, i)
                        if n not in target[comp]:
                            target[comp].append(n)
                else:
                    n = _sentinel_name(comp, slot_name, e.mode)
                    if n not in target[comp]:
                        target[comp].append(n)
    return required, optional, url


REQUIRED_SENTINELS, OPTIONAL_SENTINELS, URL_SENTINELS = _build_sentinel_tables()

# 每类最小样本(渲染到 HTML,覆盖全部必填槽)。模式用 mode 字段区分。
SLOT_SAMPLES: dict[str, list[dict]] = {
    "alert": [
        {"mode": "type=note", "block": ':::alert type="note"\nS_ALERT_BODY_NOTE 正文\n:::\n'},
        {"mode": "type=tip", "block": ':::alert type="tip"\nS_ALERT_BODY_TIP 正文\n:::\n'},
        {"mode": "type=important", "block": ':::alert type="important"\nS_ALERT_BODY_IMPORTANT 正文\n:::\n'},
        {"mode": "type=warning", "block": ':::alert type="warning" title="S_ALERT_TITLE"\nS_ALERT_BODY_WARNING 正文\n:::\n'},
        {"mode": "type=caution", "block": ':::alert type="caution"\nS_ALERT_BODY_CAUTION 正文\n:::\n'},
    ],
    "quote": [
        {"mode": "type=normal", "block": ':::quote type="normal"\nS_QUOTE_TEXT_NORMAL 引用\n:::\n'},
        {"mode": "type=highlight", "block": ':::quote type="highlight"\nS_QUOTE_TEXT_HIGHLIGHT 金句\n:::\n'},
        {"mode": "type=sourced", "block": ':::quote type="sourced" source="S_QUOTE_SOURCE_SOURCED"\nS_QUOTE_TEXT_SOURCED 引文\n:::\n'},
    ],
    "code-compare": [
        {"mode": "lang=无", "block": ':::code-compare title="S_CODE_COMPARE_TITLE_NO"\n@before\nS_CODE_COMPARE_BEFORE_NO 旧\n@end\n@after\nS_CODE_COMPARE_AFTER_NO 新\n@end\n:::\n'},
        {"mode": "lang=有", "block": ':::code-compare title="S_CODE_COMPARE_TITLE_YES"\n@before lang="python"\nS_CODE_COMPARE_BEFORE_YES 旧\n@end\n@after lang="python"\nS_CODE_COMPARE_AFTER_YES 新\n@end\n:::\n'},
    ],
    "media-text": [
        {"mode": "默认", "block": ':::media-text\n![S_MEDIA_TEXT_CAP](https://x.com/a.png)\nS_MEDIA_TEXT_EXP 解释\n:::\n'},
    ],
    "gallery": [
        {"mode": "默认", "block": ':::gallery title="S_GALLERY_TITLE"\n![S_GALLERY_CAPTION_1](https://x.com/1.png)\n![S_GALLERY_CAPTION_2](https://x.com/2.png)\n![S_GALLERY_CAPTION_3](https://x.com/3.png)\n:::\n'},
    ],
    "long-image": [
        {"mode": "默认", "block": ':::long-image image="https://x.com/S_LONG_IMAGE_IMAGE.png" caption="S_LONG_IMAGE_CAPTION"\n:::\n'},
    ],
    "resources": [
        {"mode": "默认", "block": ':::resources title="S_RESOURCES_TITLE"\n- [S_RESOURCES_LINK_TEXT_1](https://x.com/S_RESOURCES_URL_1)\n- [S_RESOURCES_LINK_TEXT_2](https://x.com/S_RESOURCES_URL_2)\n- [S_RESOURCES_LINK_TEXT_3](https://x.com/S_RESOURCES_URL_3)\n:::\n'},
    ],
    "footnotes": [
        {"mode": "默认", "block": ':::footnotes\n[^1]: S_FOOTNOTES_FN_TEXT_1 注释一\n[^2]: S_FOOTNOTES_FN_TEXT_2 注释二\n[^3]: S_FOOTNOTES_FN_TEXT_3 注释三\n:::\n'},
    ],
    "dialogue": [
        {"mode": "默认", "block": ':::dialogue title="S_DIALOGUE_TITLE"\n@user name="S_DIALOGUE_NAME_1": S_DIALOGUE_MSG_1 问题一\n@assistant name="S_DIALOGUE_NAME_2": S_DIALOGUE_MSG_2 回答二\n@user name="S_DIALOGUE_NAME_3": S_DIALOGUE_MSG_3 问题三\n:::\n'},
    ],
}

# per_item v2 输入(multi 槽组件 N=3)
PER_ITEM_V2: dict[str, list[str]] = {
    "gallery": ["S_GALLERY_CAPTION_1", "S_GALLERY_CAPTION_2", "S_GALLERY_CAPTION_3"],
    "resources": ["S_RESOURCES_LINK_TEXT_1", "S_RESOURCES_LINK_TEXT_2", "S_RESOURCES_LINK_TEXT_3"],
    "footnotes": ["S_FOOTNOTES_FN_TEXT_1", "S_FOOTNOTES_FN_TEXT_2", "S_FOOTNOTES_FN_TEXT_3"],
    "dialogue": ["S_DIALOGUE_MSG_1", "S_DIALOGUE_MSG_2", "S_DIALOGUE_MSG_3"],
}
PER_ITEM_V2_SAMPLES: dict[str, str] = {
    "gallery": ':::gallery title="S_GALLERY_TITLE"\n![S_GALLERY_CAPTION_1](https://x.com/1.png)\n![S_GALLERY_CAPTION_2](https://x.com/2.png)\n![S_GALLERY_CAPTION_3](https://x.com/3.png)\n:::\n',
    "resources": ':::resources title="S_RESOURCES_TITLE"\n- [S_RESOURCES_LINK_TEXT_1](https://x.com/1)\n- [S_RESOURCES_LINK_TEXT_2](https://x.com/2)\n- [S_RESOURCES_LINK_TEXT_3](https://x.com/3)\n:::\n',
    "footnotes": ':::footnotes\n[^1]: S_FOOTNOTES_FN_TEXT_1 注释一\n[^2]: S_FOOTNOTES_FN_TEXT_2 注释二\n[^3]: S_FOOTNOTES_FN_TEXT_3 注释三\n:::\n',
    "dialogue": ':::dialogue title="S_DIALOGUE_TITLE"\n@user: S_DIALOGUE_MSG_1 问题一\n@assistant: S_DIALOGUE_MSG_2 回答二\n@user: S_DIALOGUE_MSG_3 问题三\n:::\n',
}

# 1b(OBS-161,R33):显式豁免表 —— 差集哨兵 -> (理由, OBS 号)。
# S_CODE_COMPARE_LANG_YES: lang= 是 @before 行内属性,属性值不渲染进正文(R2 4a
#   已删 title lang 后缀),无文本锚,无法被样本触达(OBS-161)。
EXEMPT_SENTINELS: dict[str, tuple[str, str]] = {
    "S_CODE_COMPARE_LANG_YES": ("lang 属性值不进正文,无文本锚", "OBS-161"),
}

# 负样本(1d,OBS-145):未知 type / 缺 type,渲染不崩且 unknown_component_args 有记录。
_NEGATIVE_SAMPLES: dict[str, str] = {
    "alert-type-warn": ':::alert type="warn"\nSENTINEL_A1 正文\n:::\n',
    "quote-type-xxx": ':::quote type="xxx"\nSENTINEL_A1 金句\n:::\n',
    "alert-no-type": ':::alert title="提示"\nSENTINEL_A1 正文\n:::\n',
}

# 结构位换行载体归一化正则(1b 单一判据来源;字面 </p><p 与 </p>换行<p 同载体)。
_STRUCT_CARRIER_RE = re.compile(r"</p>\s*<p")


def sentinels_for(component: str, kinds=("required", "optional", "url")) -> list[str]:
    """OBS-153(R29):哨兵集合唯一来源。

    anchor_ok 与 export_body_anchors_from_measurement 必须调用本函数且传相同
    kinds(required+optional+url),禁止两处各写各的。URL 槽哨兵由调用方按 URL
    语义跳过(见 _URL_SENTINEL_SET)。
    """
    tables = {"required": REQUIRED_SENTINELS, "optional": OPTIONAL_SENTINELS,
              "url": URL_SENTINELS}
    out: list[str] = []
    for k in kinds:
        out.extend(tables[k].get(component, []))
    return out


_URL_SENTINEL_SET = frozenset(s for lst in URL_SENTINELS.values() for s in lst)


class SlotLookupMiss(ValueError):
    """3b(71C-R7):哨兵无法从 SLOTS 反查到 (slot_name, mode) 时抛此异常。

    与普通 ValueError 区分:main() 只捕获本异常,其它 ValueError 照常向上抛。
    """


def _lookup_slot(sentinel: str) -> tuple[str, str]:
    """OBS-172:从 SLOTS 反查哨兵对应的 (slot_name, mode);反查不中 -> ("SLOT_LOOKUP_MISS", "")."""
    for cs in _SLOTS:
        for slot in cs.slots:
            if slot.multi:
                for i in range(3):
                    if _sentinel_name(cs.component, slot.name, slot.mode, i) == sentinel:
                        return slot.name, slot.mode
            else:
                if _sentinel_name(cs.component, slot.name, slot.mode) == sentinel:
                    return slot.name, slot.mode
    return "SLOT_LOOKUP_MISS", ""


def _render_one(renderer: Path, out_dir: Path, block: str) -> tuple[int, str]:
    """CLI 渲染单个样本到 out_dir,返回 (returncode, final.html 文本)。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    mdp = out_dir / "a.md"
    mdp.write_text(f"# 标题\n\n## 章节\n\n{block}\n结尾。\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", str(renderer),
         "--article", str(mdp), "--output-dir", str(out_dir),
         "--theme", "smartisan"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=120)
    html_path = out_dir / "final.html"
    html = html_path.read_text(encoding="utf-8") if html_path.is_file() else ""
    return proc.returncode, html


def _nearest_p_style(html: str, sentinel: str) -> str | None:
    """哨兵最近 <p style="…"> 祖先的 style 串;无祖先返回 None(NO_P_ANCHOR)。"""
    pos = html.find(sentinel)
    if pos < 0:
        return None
    ps = [m for m in re.finditer(r'<p style="([^"]*)"', html[:pos])]
    return ps[-1].group(1) if ps else None


def _p_open_offset(html: str, sentinel: str) -> int | None:
    """哨兵最近 <p 开标签的起始偏移;无 <p 祖先返回 None。"""
    pos = html.find(sentinel)
    if pos < 0:
        return None
    ps = [m for m in re.finditer(r"<p\b", html[:pos])]
    return ps[-1].start() if ps else None


def component_structure_check(renderer: Path, out_dir: Path) -> dict[str, dict]:
    """OBS-151(档71C-R3):四判据。

    render_ok / struct_ok / anchor_ok / per_item_ok(v2)。
    struct_ok(1a 恢复):对每个样本内相邻哨兵对,取两者之间的 HTML 片段,命中
    _STRUCT_CARRIER_RE 或含 <section 即判有载体;全部有载体 -> True;
    无相邻哨兵对的组件(单槽样本)视为无多行证据 -> True。docstring 口径与
    实现逐字一致(OBS-139)。
    anchor_ok(OBS-160):「JSON 锚与当前渲染器同步 + 哨兵确在其最近 <p> 内」,
    不声称锚全量覆盖已证;空集结论依赖 fake_offanchor 等反证物(R32)。
    """
    from wxgzh_pipeline.stages.gzh_design import _body_plain_text
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {}
    for name, samples in SLOT_SAMPLES.items():
        render_ok = True
        anchor_ok = True
        struct_ok = True
        for smp in samples:
            d = out_dir / f"{name}-{smp['mode']}"
            rc, html = _render_one(renderer, d, smp["block"])
            body = _body_plain_text(html)
            # 2b:render_ok 查必填槽 + URL 槽(渲染器吐字)。
            for sent in REQUIRED_SENTINELS.get(name, []) + URL_SENTINELS.get(name, []):
                if sent in smp["block"] and sent not in html:
                    render_ok = False
            # 2f/2a(OBS-153):anchor_ok 查 sentinels_for(name) 全部哨兵(required+
            # optional+url,与 export 同源同 kinds);URL 槽不在正文区,跳过。
            for sent in sentinels_for(name):
                if sent in smp["block"] and sent not in _URL_SENTINEL_SET and sent not in body:
                    anchor_ok = False
            # 1a(OBS-151):struct_ok —— 相邻哨兵对之间的 HTML 片段须有换行载体。
            # ★只取文本槽(REQUIRED+OPTIONAL);URL 槽在 img src 属性内,非文本行,
            # 不参与多行塌陷判据(与 anchor 判据口径一致,见 4c② 定案)。
            # ★按 HTML 中出现顺序排序(block 顺序 ≠ HTML 渲染顺序,如 quote source
            # 渲染在 text 之后;倒序对会得到空片段,误判塌陷)。
            present = sorted(
                [s for s in sentinels_for(name, ("required", "optional"))
                 if s in smp["block"] and s in html],
                key=lambda s: html.find(s))
            for i in range(len(present) - 1):
                p1 = html.find(present[i])
                p2 = html.find(present[i + 1])
                seg = html[p1:p2] if p1 >= 0 and p2 >= 0 else ""
                if not (_STRUCT_CARRIER_RE.search(seg) or "<section" in seg):
                    struct_ok = False
        per_item = None
        if name in PER_ITEM_V2:
            d = out_dir / f"{name}-n3"
            rc, html = _render_one(renderer, d, PER_ITEM_V2_SAMPLES[name])
            offsets = []
            for sent in PER_ITEM_V2[name]:
                style = _nearest_p_style(html, sent)
                if style is None:
                    offsets.append(None)
                    continue
                pos = html.find(sent)
                offsets.append((pos, style))
            valid = [o for o in offsets if o is not None]
            # 2d:最近 <p style> 祖先的「起始偏移」两两不同、不同偏移数量 == N。
            # 偏移 = 哨兵所在 <p> 开标签起始位置(同 style 的并列项也各占一偏移)。
            per_item = (len(valid) == len(PER_ITEM_V2[name])
                        and len({_p_open_offset(html, sent)
                                 for sent in PER_ITEM_V2[name]}) == len(PER_ITEM_V2[name]))
        result[name] = {"render_ok": render_ok, "struct_ok": struct_ok,
                        "anchor_ok": anchor_ok, "per_item_ok": per_item}
    return result


def export_lists_from_measurement(measured: dict[str, dict]) -> dict[str, frozenset]:
    """四名单实测导出(R20):
    QUARANTINED = {not render_ok};MULTILINE = {render_ok 且多行塌};
    ANCHOR_GAP = {render_ok 且 not anchor_ok};APPROVED = {render_ok 且 anchor_ok}。
    MULTILINE 由结构位(相邻哨兵无换行载体)导出;当前渲染器多行已修复,预期空集。"""
    quarantined = frozenset(c for c, r in measured.items() if not r["render_ok"])
    anchor_gap = frozenset(c for c, r in measured.items()
                           if r["render_ok"] and not r["anchor_ok"])
    approved = frozenset(c for c, r in measured.items()
                         if r["render_ok"] and r["anchor_ok"])
    # 1b(OBS-152):multiline = {c : render_ok 且 not struct_ok}。
    multiline = frozenset(c for c, r in measured.items()
                          if r["render_ok"] and not r["struct_ok"])
    return {"quarantined": quarantined, "multiline": multiline,
            "anchor_gap": anchor_gap, "approved": approved}


def export_body_anchors_from_measurement(renderer: Path, out_dir: Path) -> dict[str, dict]:
    """3a:对每个哨兵定位最近 <p style> 祖先,产出 style 串集合。

    返回 {sentinel: {"style": str|None, "component": str, "slot": str, "mode": str}};
    style None 记 NO_P_ANCHOR 并停机 S37(不得静默跳过)。slot/mode 来自 SLOTS 反查,
    反查不中 slot="SLOT_LOOKUP_MISS" 并在收尾 raise(OBS-163/档71C-R6)。
    """
    from wxgzh_pipeline.stages.gzh_design import _body_plain_text
    out_dir.mkdir(parents=True, exist_ok=True)
    anchors: dict[str, dict] = {}
    for name, samples in SLOT_SAMPLES.items():
        for smp in samples:
            d = out_dir / f"{name}-{smp['mode']}"
            rc, html = _render_one(renderer, d, smp["block"])
            for sent in sentinels_for(name):
                if sent not in smp["block"] or sent in anchors:
                    continue
                # 2a(OBS-172):从 SLOTS 反查真实 (slot_name, mode) 三元组(单一来源);
                # 反查不中 -> slot="SLOT_LOOKUP_MISS" 由调用方 FAIL,禁止静默空串。
                slot_name, slot_mode = _lookup_slot(sent)
                if sent in _URL_SENTINEL_SET:
                    # URL 槽无文本 <p> 载体,记 URL_SLOT(不参与锚判据,非 NO_P_ANCHOR)。
                    anchors[sent] = {"style": "URL_SLOT", "component": name,
                                     "slot": slot_name, "mode": slot_mode}
                    continue
                style = _nearest_p_style(html, sent)
                anchors[sent] = {"style": style, "component": name,
                                 "slot": slot_name, "mode": slot_mode}
    # S37:任何哨兵无 <p> 祖先 -> 停机(由测试/调用方检查 None)
    # 4c(OBS-163):SLOT_LOOKUP_MISS 真失败 —— 反查不中的哨兵收集后 raise。
    miss = sorted(s for s, info in anchors.items() if info.get("slot") == "SLOT_LOOKUP_MISS")
    if miss:
        raise SlotLookupMiss(f"SLOT_LOOKUP_MISS: {miss}")
    return anchors


def build_component_para_regexes(anchors: dict[str, dict]) -> list[str]:
    """3b:从 3a 锚实测导出生成组件段落锚正则(style 串去重后转 <p style="..."> 锚)。

    URL_SLOT 不参与(无文本载体);返回排重后的 style 串列表(供测试焊死
    gzh_design._COMPONENT_PARA_RES 快照 == 现场导出,防手抄锚自证)。
    """
    styles = []
    for info in anchors.values():
        s = info.get("style")
        if not s or s == "URL_SLOT":
            continue
        if s not in styles:
            styles.append(s)
    return sorted(styles)


def _block_effective_lines(body: str) -> int:
    """块体内有效文本行数(忽略空行与纯控制行)。"""
    n = 0
    for ln in body.splitlines():
        s = ln.strip()
        if not s:
            continue
        if s.startswith("@") and ":" in s:
            continue
        n += 1
    return n


def multiline_gate(article_text: str) -> list[dict]:
    """2.6c:MULTILINE_UNSUPPORTED 组件的 ::: 块体有效文本行 >=2 -> 命中。"""
    hits = []
    lines = article_text.splitlines()
    in_block = False
    cur_name = ""
    cur_start = 0
    buf: list[str] = []
    for i, ln in enumerate(lines):
        st = ln.strip()
        if in_block:
            if st.startswith(":::"):
                n = _block_effective_lines("\n".join(buf))
                if cur_name in MULTILINE_UNSUPPORTED_COMPONENTS and n >= 2:
                    hits.append({"name": cur_name, "start_line": cur_start,
                                "end_line": i + 1, "line_count": n})
                in_block = False
                buf = []
            else:
                buf.append(ln)
            continue
        if st.startswith(":::"):
            in_block = True
            cur_start = i + 1
            head = st[3:].strip()
            cur_name = head.split()[0] if head.split() else ""
            buf = []
    return hits


def quarantine_gate(article_text: str) -> list[dict]:
    """2h':final_article.md 中出现 QUARANTINED 组件的 ::: 块 -> 返回命中清单。"""
    hits = []
    lines = article_text.splitlines()
    in_block = False
    for i, ln in enumerate(lines):
        st = ln.strip()
        if in_block:
            if st.startswith(":::"):
                in_block = False
            continue
        if st.startswith(":::"):
            head = st[3:].strip()
            name = head.split()[0] if head.split() else ""
            if name in QUARANTINED_COMPONENTS:
                hits.append({"name": name, "line": i + 1})
            in_block = True
    return hits


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="OBS-145 component structure check (v2)")
    ap.add_argument("--renderer", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--emit-anchors", default=None,
                    help="3a(OBS-154):把锚导出落成 validators/component_anchors.json")
    a = ap.parse_args(argv)
    # 1a(OBS-167):统一 out = Path(a.out_dir),后续全部改用 out(缺失明细分支
    # 曾用未定义 out_dir 而崩溃)。
    out = Path(a.out_dir)
    _repo = Path(__file__).resolve().parents[1]
    if str(_repo) not in sys.path:
        sys.path.insert(0, str(_repo))
    result = component_structure_check(Path(a.renderer), out)
    for name, r in sorted(result.items()):
        print(f"{name}: render_ok={r['render_ok']} struct_ok={r['struct_ok']} "
              f"anchor_ok={r['anchor_ok']} per_item_ok={r['per_item_ok']}")
    # 2c/4a(OBS-153/162):逐条打印 组件 | 真正缺失哨兵(sent not in body) | style。
    from wxgzh_pipeline.stages.gzh_design import _body_plain_text
    try:
        anchors = export_body_anchors_from_measurement(Path(a.renderer), out)
    except SlotLookupMiss as _ve:
        # 3b:只捕获 SlotLookupMiss(其它 ValueError 照常向上抛)。
        print(f"ERROR: {_ve}")
        return 1
    # 3a(OBS-154):落成 component_anchors.json(五列 + renderer sha + 生成时间)。
    if a.emit_anchors:
        import hashlib
        import json as _json
        from datetime import datetime, timezone
        rows = []
        for sent, info in sorted(anchors.items()):
            # 2b(OBS-172):直接消费源头函数的结果(单一来源,R29),不再重复反查。
            comp = info["component"]
            slot_name = info.get("slot", "")
            mode = info.get("mode", "")
            rows.append({"sentinel": sent, "component": comp,
                         "slot": slot_name, "mode": mode,
                         "style": info["style"]})
        payload = {
            "renderer_sha256": hashlib.sha256(Path(a.renderer).read_bytes()).hexdigest(),
            "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "anchors": rows,
        }
        Path(a.emit_anchors).write_text(
            _json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[emit-anchors] wrote {len(rows)} rows -> {a.emit_anchors}")
    print("--- 缺失哨兵明细(组件 | 哨兵 | style;仅 sent not in body) ---")
    for name, r in sorted(result.items()):
        if not (r["render_ok"] and not r["anchor_ok"]):
            continue
        for smp in SLOT_SAMPLES[name]:
            d = out / f"{name}-{smp['mode']}"
            html = (d / "final.html").read_text(encoding="utf-8") \
                if (d / "final.html").is_file() else ""
            body = _body_plain_text(html)
            for sent in sentinels_for(name):
                if sent in _URL_SENTINEL_SET or sent not in smp["block"]:
                    continue
                if sent in body:
                    continue  # 4a:真 missing 过滤(sent not in body 才打印)
                info = anchors.get(sent)
                style = info["style"] if info else "NO_P_ANCHOR"
                print(f"{name} | {sent} | {style}")
    return 0


if __name__ == "__main__":
    sys.exit(main())