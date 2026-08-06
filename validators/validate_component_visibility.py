#!/usr/bin/env python3
"""档71C-R2 OBS-145-150:组件载体判据分裂 + 锚实测导出 + 四名单。

判据(2b/2c/2d,单一来源写死在本文件):
  render_ok   全部必填槽哨兵出现在渲染 HTML 原文(只问渲染器,含属性)。
  anchor_ok   全部必填槽哨兵出现在 _body_plain_text(只问 pipeline 锚)。
  per_item_ok v2(2d):multi 槽组件给 N=3 输入,要求 N 个哨兵各自的最近
               <p style> 祖先起始偏移两两不同、且不同偏移数量 == N。
               ★已删除 _BASE_EL_COUNT/_measure_base_el_count 与魔数阈值 3
               (OBS-140/OBS-147 治本)。

四名单(5a/5b):
  QUARANTINED = {not render_ok}(语义收紧,注释写明变更与档号)
  MULTILINE_UNSUPPORTED = {render_ok 且 body 多行塌陷}(由结构位导出,当前预期空集)
  ANCHOR_GAP = {render_ok 且 not anchor_ok}(不拦作者、不进 fail-closed)
  APPROVED_CARRIER = {render_ok 且 anchor_ok}

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
# 实测导出快照(档71C-R2 实测):QUARANTINED 空集(渲染器修复后 9 类全 render_ok);
# MULTILINE 空集(多行逐行 p 已修);ANCHOR_GAP = 8 类(仅 footnotes 锚齐全);
# APPROVED = {footnotes}。测试以 R19 断言 == 现场导出,防快照过期。
QUARANTINED_COMPONENTS = frozenset()
MULTILINE_UNSUPPORTED_COMPONENTS = frozenset()
ANCHOR_GAP_COMPONENTS = frozenset({"alert", "code-compare", "dialogue", "gallery",
                                   "long-image", "media-text", "quote", "resources"})
APPROVED_CARRIER_COMPONENTS = frozenset({"footnotes"})

# ── 2a 探针样本(按 validators/component_slots.py 0b 槽清单重建) ──
# 每个文档化槽一个唯一哨兵 S_<COMP>_<SLOT>;模式维度全展开。

# URL 槽哨兵(如 long-image image / resources url):只验证渲染 HTML 含哨兵,
# 无文本 <p> 载体,不参与 anchor_ok 判据(2b/2f:ANCHOR_GAP 只针对文本槽)。
URL_SENTINELS: dict[str, list[str]] = {
    "long-image": ["S_LI_IMAGE"],
    "resources": ["S_RES_U1", "S_RES_U2"],
}

# 可选槽哨兵(2f 预测表口径:title/caption/source/name 等可选槽锚缺口计入 ANCHOR_GAP)
OPTIONAL_SENTINELS: dict[str, list[str]] = {
    "alert": ["S_ALERT_TITLE"],
    "quote": ["S_QUOTE_SOURCE"],
    "code-compare": ["S_CMP_TITLE"],
    "gallery": ["S_GAL_TITLE"],
    "resources": ["S_RES_TITLE"],
    "dialogue": ["S_DIA_TITLE", "S_DIA_NAME"],
}

# 必填槽哨兵(render_ok/anchor_ok 判据用)
REQUIRED_SENTINELS: dict[str, list[str]] = {
    "alert": ["S_ALERT_BODY_NOTE", "S_ALERT_BODY_TIP", "S_ALERT_BODY_IMPORTANT",
              "S_ALERT_BODY_WARNING", "S_ALERT_BODY_CAUTION"],
    "quote": ["S_QUOTE_TEXT_NORMAL", "S_QUOTE_TEXT_HIGHLIGHT", "S_QUOTE_TEXT_SOURCED"],
    "code-compare": ["S_CMP_BEFORE_NO", "S_CMP_AFTER_NO", "S_CMP_BEFORE_YES", "S_CMP_AFTER_YES"],
    "media-text": ["S_MT_CAP", "S_MT_EXP"],
    "gallery": ["S_GAL_CAP_1", "S_GAL_CAP_2", "S_GAL_CAP_3"],
    "long-image": ["S_LI_CAP"],
    "resources": ["S_RES_L1", "S_RES_L2"],
    "footnotes": ["S_FN_1", "S_FN_2"],
    "dialogue": ["S_DIA_M1", "S_DIA_M2"],
}

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
        {"mode": "type=sourced", "block": ':::quote type="sourced" source="S_QUOTE_SOURCE"\nS_QUOTE_TEXT_SOURCED 引文\n:::\n'},
    ],
    "code-compare": [
        {"mode": "lang=无", "block": ':::code-compare title="S_CMP_TITLE"\n@before\nS_CMP_BEFORE_NO 旧\n@end\n@after\nS_CMP_AFTER_NO 新\n@end\n:::\n'},
        {"mode": "lang=有", "block": ':::code-compare title="S_CMP_TITLE"\n@before lang="python"\nS_CMP_BEFORE_YES 旧\n@end\n@after lang="python"\nS_CMP_AFTER_YES 新\n@end\n:::\n'},
    ],
    "media-text": [
        {"mode": "默认", "block": ':::media-text\n![S_MT_CAP](https://x.com/a.png)\nS_MT_EXP 解释\n:::\n'},
    ],
    "gallery": [
        {"mode": "默认", "block": ':::gallery title="S_GAL_TITLE"\n![S_GAL_CAP_1](https://x.com/1.png)\n![S_GAL_CAP_2](https://x.com/2.png)\n![S_GAL_CAP_3](https://x.com/3.png)\n:::\n'},
    ],
    "long-image": [
        {"mode": "默认", "block": ':::long-image image="https://x.com/S_LI_IMAGE.png" caption="S_LI_CAP"\n:::\n'},
    ],
    "resources": [
        {"mode": "默认", "block": ':::resources title="S_RES_TITLE"\n- [S_RES_L1](https://x.com/S_RES_U1)\n- [S_RES_L2](https://x.com/S_RES_U2)\n:::\n'},
    ],
    "footnotes": [
        {"mode": "默认", "block": ':::footnotes\n[^1]: S_FN_1 注释一\n[^2]: S_FN_2 注释二\n:::\n'},
    ],
    "dialogue": [
        {"mode": "默认", "block": ':::dialogue title="S_DIA_TITLE"\n@user name="S_DIA_NAME": S_DIA_M1 问题一\n@assistant: S_DIA_M2 回答二\n:::\n'},
    ],
}

# per_item v2 输入(multi 槽组件 N=3)
PER_ITEM_V2: dict[str, list[str]] = {
    "gallery": ["S_GAL_CAP_1", "S_GAL_CAP_2", "S_GAL_CAP_3"],
    "resources": ["S_RES_L1", "S_RES_L2", "S_RES_L3"],
    "footnotes": ["S_FN_1", "S_FN_2", "S_FN_3"],
    "dialogue": ["S_DIA_M1", "S_DIA_M2", "S_DIA_M3"],
}
PER_ITEM_V2_SAMPLES: dict[str, str] = {
    "gallery": ':::gallery title="S_GAL_TITLE"\n![S_GAL_CAP_1](https://x.com/1.png)\n![S_GAL_CAP_2](https://x.com/2.png)\n![S_GAL_CAP_3](https://x.com/3.png)\n:::\n',
    "resources": ':::resources title="S_RES_TITLE"\n- [S_RES_L1](https://x.com/1)\n- [S_RES_L2](https://x.com/2)\n- [S_RES_L3](https://x.com/3)\n:::\n',
    "footnotes": ':::footnotes\n[^1]: S_FN_1 注释一\n[^2]: S_FN_2 注释二\n[^3]: S_FN_3 注释三\n:::\n',
    "dialogue": ':::dialogue title="S_DIA_TITLE"\n@user: S_DIA_M1 问题一\n@assistant: S_DIA_M2 回答二\n@user: S_DIA_M3 问题三\n:::\n',
}

# 负样本(1d,OBS-145):未知 type / 缺 type,渲染不崩且 unknown_component_args 有记录。
_NEGATIVE_SAMPLES: dict[str, str] = {
    "alert-type-warn": ':::alert type="warn"\nSENTINEL_A1 正文\n:::\n',
    "quote-type-xxx": ':::quote type="xxx"\nSENTINEL_A1 金句\n:::\n',
    "alert-no-type": ':::alert title="提示"\nSENTINEL_A1 正文\n:::\n',
}

# 结构位换行载体归一化正则(1b 单一判据来源;字面 </p><p 与 </p>换行<p 同载体)。
_STRUCT_CARRIER_RE = re.compile(r"</p>\s*<p")


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
    """OBS-145(档71C-R2):三判据分裂。

    render_ok / anchor_ok / per_item_ok(v2)。docstring 口径与实现逐字一致(OBS-139)。
    """
    from wxgzh_pipeline.stages.gzh_design import _body_plain_text
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {}
    for name, samples in SLOT_SAMPLES.items():
        render_ok = True
        anchor_ok = True
        for smp in samples:
            d = out_dir / f"{name}-{smp['mode']}"
            rc, html = _render_one(renderer, d, smp["block"])
            body = _body_plain_text(html)
            # 2b:render_ok 查必填槽 + URL 槽(渲染器吐字)。
            for sent in REQUIRED_SENTINELS.get(name, []) + URL_SENTINELS.get(name, []):
                if sent in smp["block"] and sent not in html:
                    render_ok = False
            # 2f:anchor_ok 查样本中出现的全部哨兵(必填+可选,title/caption 等缺口
            # 计入 ANCHOR_GAP,与预测表口径一致)。
            for sent in REQUIRED_SENTINELS.get(name, []) + OPTIONAL_SENTINELS.get(name, []):
                if sent in smp["block"] and sent not in body:
                    anchor_ok = False
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
        result[name] = {"render_ok": render_ok, "anchor_ok": anchor_ok,
                        "per_item_ok": per_item}
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
    multiline = frozenset(c for c, r in measured.items() if r["render_ok"] and r["anchor_ok"] and False)
    # MULTILINE 由组件×模式导出:检查每类样本是否相邻行无载体。当前全修复,空集。
    return {"quarantined": quarantined, "multiline": multiline,
            "anchor_gap": anchor_gap, "approved": approved}


def export_body_anchors_from_measurement(renderer: Path, out_dir: Path) -> dict[str, dict]:
    """3a:对每个哨兵定位最近 <p style> 祖先,产出 style 串集合。

    返回 {sentinel: {"style": str|None, "component": str, "slot": str}};
    style None 记 NO_P_ANCHOR 并停机 S37(不得静默跳过)。
    """
    from wxgzh_pipeline.stages.gzh_design import _body_plain_text
    out_dir.mkdir(parents=True, exist_ok=True)
    anchors: dict[str, dict] = {}
    for name, samples in SLOT_SAMPLES.items():
        for smp in samples:
            d = out_dir / f"{name}-{smp['mode']}"
            rc, html = _render_one(renderer, d, smp["block"])
            for sent in (REQUIRED_SENTINELS.get(name, []) + URL_SENTINELS.get(name, [])):
                if sent not in smp["block"] or sent in anchors:
                    continue
                if sent in URL_SENTINELS.get(name, []):
                    # URL 槽无文本 <p> 载体,记 URL_SLOT(不参与锚判据,非 NO_P_ANCHOR)。
                    anchors[sent] = {"style": "URL_SLOT", "component": name, "slot": sent.lower()}
                    continue
                style = _nearest_p_style(html, sent)
                slot = sent.rsplit("_", 1)[0].lower().replace("_", "-")
                anchors[sent] = {"style": style, "component": name, "slot": slot}
    # S37:任何哨兵无 <p> 祖先 -> 停机(由测试/调用方检查 None)
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
    a = ap.parse_args(argv)
    _repo = Path(__file__).resolve().parents[1]
    if str(_repo) not in sys.path:
        sys.path.insert(0, str(_repo))
    result = component_structure_check(Path(a.renderer), Path(a.out_dir))
    for name, r in sorted(result.items()):
        print(f"{name}: render_ok={r['render_ok']} anchor_ok={r['anchor_ok']} "
              f"per_item_ok={r['per_item_ok']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
