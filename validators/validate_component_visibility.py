#!/usr/bin/env python3
"""档71C-2 C路线 OBS-119:组件载体以实测可见性为唯一事实源。

component_body_visibility_check:对 A 组 9 类各构造最小文章,把哨兵 SENTINEL_A1
放进该组件正文槽,CLI 子进程调用安装侧渲染器,断言 SENTINEL_A1 出现在
_body_plain_text(final.html) 中。

component_structure_check(OBS-133,档71C-2A'):结构位落成可执行探针 —— 三行哨兵
SENTINEL_S1/S2/S3,判据 text_ok + struct_ok + per_item_ok 单一来源写死在此。

2d'(档71C-2):类 B(哨兵未进 final.html)组件一律不补 pipeline 锚(R15),
只能进 QUARANTINED_COMPONENTS + fail-closed 门禁。修复归 71C-R。

OBS-133(档71C-2A'):三名单(QUARANTINED / MULTILINE_UNSUPPORTED /
APPROVED_CARRIER)一律由 component_structure_check 现场实测导出,禁止手填(R20);
模块常量 = 实测导出结果的快照,测试以 R19 口径(常量 vs 现场实测)断言一致。
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# 类 B(2d' 实测:哨兵未进 final.html)——渲染器缺陷,不补锚,隔离 + fail-closed。
# gzh-design 修复后须回归 test_component_visibility 并移回 APPROVED。
# OBS-124:code-compare @before/@after 只取同一行,续行代码丢失且 lang="..." 串入正文。
# OBS-125:long-image 文档 image=/caption= 与实现 url/cap 双不匹配,图与说明双丢。
QUARANTINED_COMPONENTS = frozenset({"code-compare", "long-image"})

# 组件×模式隔离 —— 该组件单段可用,块体 ≥2 行有效文本即失败。
# OBS-129:alert 多行块体塌成单 <p>(行间仅字面 \n,无 <br>/</p><p 载体)。
# OBS-132:quote 同单槽结构(blockquote 单 <p>),多行塌陷(2.6d 实测确认)。
# OBS-133:media-text 同单槽塌陷(2.7 矩阵实测,位2=False),由实测导出自动入列。
MULTILINE_UNSUPPORTED_COMPONENTS = frozenset({"alert", "quote", "media-text"})

# 可见且保结构(文本位+结构位双真)的组件。模块级真常量 = 实测导出快照,
# 测试以 R19 口径(import 后未修改的常量 vs 现场实测)断言一致,禁止赋值后自证。
APPROVED_CARRIER_COMPONENTS = frozenset({"gallery", "resources", "footnotes", "dialogue"})

# 单段可见性样本(位1,哨兵 SENTINEL_A1 放组件正文槽)。
_COMPONENT_SAMPLES = {
    "alert": ":::alert type=\"warn\"\nSENTINEL_A1\n:::\n",
    "quote": ":::quote\nSENTINEL_A1\n:::\n",
    "code-compare": ":::code-compare\n@before lang=\"python\"\nSENTINEL_A1\n@end\n:::\n",
    "media-text": ":::media-text\n![图](https://x.com/a.png)\nSENTINEL_A1\n:::\n",
    "gallery": ":::gallery title=\"图集\"\n![SENTINEL_A1](https://x.com/1.png)\n:::\n",
    "long-image": ":::long-image image=\"https://x.com/1.png\" caption=\"SENTINEL_A1\"\n:::\n",
    "resources": ":::resources title=\"参考\"\n- [SENTINEL_A1](https://x.com)\n:::\n",
    "footnotes": ":::footnotes\n[^1]: SENTINEL_A1 注释\n:::\n",
    "dialogue": ":::dialogue title=\"问答\"\n@user: SENTINEL_A1\n:::\n",
}

# 结构位样本(OBS-133 第 1 步 1c):三行哨兵,文档语法 + 实现能解析,双满足。
_MULTI_SAMPLES = {
    "alert": ":::alert type=\"warn\"\nSENTINEL_S1 第一行\nSENTINEL_S2 第二行\nSENTINEL_S3 第三行\n:::\n",
    "quote": ":::quote\nSENTINEL_S1 第一行\nSENTINEL_S2 第二行\nSENTINEL_S3 第三行\n:::\n",
    "code-compare": ":::code-compare\n@before lang=\"python\"\nSENTINEL_S1\n@end\n@after lang=\"python\"\nSENTINEL_S2\n@end\n:::\n",
    "media-text": ":::media-text\n![图](https://x.com/a.png)\nSENTINEL_S1 第一行\nSENTINEL_S2 第二行\nSENTINEL_S3 第三行\n:::\n",
    "gallery": ":::gallery title=\"图集\"\n![SENTINEL_S1](https://x.com/1.png)\n![SENTINEL_S2](https://x.com/2.png)\n![SENTINEL_S3](https://x.com/3.png)\n:::\n",
    "long-image": ":::long-image image=\"https://x.com/1.png\" caption=\"SENTINEL_S1\"\n:::\n",
    "resources": ":::resources title=\"参考\"\n- [SENTINEL_S1](https://x.com/1)\n- [SENTINEL_S2](https://x.com/2)\n- [SENTINEL_S3](https://x.com/3)\n:::\n",
    "footnotes": ":::footnotes\n[^1]: SENTINEL_S1 注释一\n[^2]: SENTINEL_S2 注释二\n[^3]: SENTINEL_S3 注释三\n:::\n",
    "dialogue": ":::dialogue title=\"问答\"\n@user: SENTINEL_S1 问题一\n@assistant: SENTINEL_S2 回答二\n@user: SENTINEL_S3 问题三\n:::\n",
}

# per_item(位3):3 项输入 —— gallery 3 图 / resources 3 链 / footnotes 3 条 / dialogue 3 轮。
_PER_ITEM_INPUTS = {
    "gallery": ":::gallery title=\"图集\"\n![SENTINEL_S1](https://x.com/1.png)\n![SENTINEL_S2](https://x.com/2.png)\n![SENTINEL_S3](https://x.com/3.png)\n:::\n",
    "resources": ":::resources title=\"参考\"\n- [SENTINEL_S1](https://x.com/1)\n- [SENTINEL_S2](https://x.com/2)\n- [SENTINEL_S3](https://x.com/3)\n:::\n",
    "footnotes": ":::footnotes\n[^1]: SENTINEL_S1 注释一\n[^2]: SENTINEL_S2 注释二\n[^3]: SENTINEL_S3 注释三\n:::\n",
    "dialogue": ":::dialogue title=\"问答\"\n@user: SENTINEL_S1 问题一\n@assistant: SENTINEL_S2 回答二\n@user: SENTINEL_S3 问题三\n:::\n",
}

# 结构位换行载体归一化正则(第 1 步 1b 单一判据来源;字面 </p><p 与 </p>\n<p
# 视为同一载体 —— 两者都是段落边界)。
_STRUCT_CARRIER_RE = re.compile(r"</p>\s*<p")

# 无组件基线 HTML 的 <p+<section 元素计数(per_item 增量判断,与组件产物同渲染
# 器同主题;由 component_structure_check 首次调用时实测填充)。
_BASE_EL_COUNT = 0
_BASE_EL_COUNT_MEASURED = False


def _measure_base_el_count(renderer: Path, out_dir: Path) -> None:
    """CLI 渲染无组件基线文章,实测 <p+<section 元素计数(per_item 判据的零点)。"""
    global _BASE_EL_COUNT, _BASE_EL_COUNT_MEASURED
    if _BASE_EL_COUNT_MEASURED:
        return
    d = out_dir / "_baseline"
    d.mkdir(parents=True, exist_ok=True)
    mdp = d / "a.md"
    mdp.write_text("# 标题\n\n## 章节\n\n普通段落。\n结尾。\n", encoding="utf-8")
    out = d / "out"
    out.mkdir(exist_ok=True)
    subprocess.run(
        [sys.executable, "-X", "utf8", str(renderer),
         "--article", str(mdp), "--output-dir", str(out), "--theme", "smartisan"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=120)
    html = (out / "final.html").read_text(encoding="utf-8") if (out / "final.html").is_file() else ""
    _BASE_EL_COUNT = html.count("<p") + html.count("<section")
    _BASE_EL_COUNT_MEASURED = True


def _body_plain_text_import():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from wxgzh_pipeline.stages.gzh_design import _body_plain_text
    return _body_plain_text


def component_body_visibility_check(renderer: Path, out_dir: Path) -> dict[str, bool]:
    """对 A 组 9 类逐一 CLI 渲染,断言哨兵出现在正文区。返回 {name: visible}。"""
    from wxgzh_pipeline.stages.gzh_design import _body_plain_text
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {}
    for name, block in _COMPONENT_SAMPLES.items():
        md = f"# 标题\n\n## 章节\n\n{block}\n结尾。\n"
        d = out_dir / name
        d.mkdir(exist_ok=True)
        mdp = d / "a.md"
        mdp.write_text(md, encoding="utf-8")
        out = d / "out"
        out.mkdir(exist_ok=True)
        proc = subprocess.run(
            [sys.executable, "-X", "utf8", str(renderer),
             "--article", str(mdp), "--output-dir", str(out), "--theme", "smartisan"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=120)
        html_path = out / "final.html"
        html = html_path.read_text(encoding="utf-8") if html_path.is_file() else ""
        result[name] = "SENTINEL_A1" in _body_plain_text(html)
    return result


def component_structure_check(renderer: Path, out_dir: Path) -> dict[str, dict]:
    """OBS-133(档71C-2A' 第 1 步):结构位落成可执行探针。

    对 A 组 9 类各构造最小文章(三行哨兵 SENTINEL_S1/S2/S3 放该组件正文槽),
    CLI 子进程调用安装侧渲染器,返回每类:
      text_ok      三行哨兵全部出现在 _body_plain_text(final.html)
      struct_ok    text_ok 且 相邻哨兵位置之间存在换行载体 —— 归一化正则
                   r"</p>空白*<p"(等价 </p>\\s*<p) | r"<br..." | r"<section..."
                   ★口径:字面 </p><p 与 </p>换行<p 视为同一载体(段落边界)。
      per_item_ok  构造 3 项输入,重复出现的 <p 或 <section 计数 >= 3;
                   无多项输入槽的组件返回 None。

    三类判据全部写死在本函数(单一来源),测试/名单导出/矩阵 JSON 一律调用本函数。
    """
    from wxgzh_pipeline.stages.gzh_design import _body_plain_text
    out_dir.mkdir(parents=True, exist_ok=True)
    _measure_base_el_count(renderer, out_dir)
    result = {}
    for name, block in _MULTI_SAMPLES.items():
        d = out_dir / name
        d.mkdir(exist_ok=True)
        mdp = d / "a.md"
        mdp.write_text(f"# 标题\n\n## 章节\n\n{block}\n结尾。\n", encoding="utf-8")
        out = d / "out"
        out.mkdir(exist_ok=True)
        proc = subprocess.run(
            [sys.executable, "-X", "utf8", str(renderer),
             "--article", str(mdp), "--output-dir", str(out), "--theme", "smartisan"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=120)
        html_path = out / "final.html"
        html = html_path.read_text(encoding="utf-8") if html_path.is_file() else ""
        body = _body_plain_text(html)
        text_ok = all(s in body for s in ("SENTINEL_S1", "SENTINEL_S2", "SENTINEL_S3"))
        struct_ok = False
        if text_ok:
            ok = []
            for i in range(2):
                p1 = html.find(f"SENTINEL_S{i + 1}")
                p2 = html.find(f"SENTINEL_S{i + 2}")
                seg = html[p1:p2] if p1 >= 0 and p2 >= 0 else ""
                ok.append(bool(_STRUCT_CARRIER_RE.search(seg))
                          or "<br" in seg or "<section" in seg)
            struct_ok = all(ok)
        per_item = None
        if name in _PER_ITEM_INPUTS:
            d3 = out_dir / f"{name}-n"
            d3.mkdir(exist_ok=True)
            mdp3 = d3 / "a.md"
            mdp3.write_text(f"# 标题\n\n## 章节\n\n{_PER_ITEM_INPUTS[name]}\n结尾。\n",
                            encoding="utf-8")
            out3 = d3 / "out"
            out3.mkdir(exist_ok=True)
            subprocess.run(
                [sys.executable, "-X", "utf8", str(renderer),
                 "--article", str(mdp3), "--output-dir", str(out3), "--theme", "smartisan"],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=120)
            html3 = (out3 / "final.html").read_text(encoding="utf-8") \
                if (out3 / "final.html").is_file() else ""
            per_item = (html3.count("<p") + html3.count("<section")) - _BASE_EL_COUNT >= 3
        result[name] = {"text_ok": text_ok, "struct_ok": struct_ok,
                        "per_item_ok": per_item}
    return result


def export_lists_from_measurement(measured: dict[str, dict]) -> dict[str, frozenset]:
    """OBS-133 第 3 步:三名单由实测导出(R20)。

    QUARANTINED      == {c : not text_ok}
    MULTILINE        == {c : text_ok and not struct_ok}
    APPROVED         == {c : text_ok and struct_ok}
    """
    q = frozenset(c for c, r in measured.items() if not r["text_ok"])
    m = frozenset(c for c, r in measured.items()
                  if r["text_ok"] and not r["struct_ok"])
    a = frozenset(c for c, r in measured.items()
                  if r["text_ok"] and r["struct_ok"])
    return {"quarantined": q, "multiline": m, "approved": a}


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
    """2.6c:MULTILINE_UNSUPPORTED 组件的 ::: 块体有效文本行 >=2 -> 命中。

    返回 [{name, start_line, end_line, line_count}]。
    """
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
    """2h':final_article.md 中出现 QUARANTINED 组件的 ::: 块 -> 返回命中清单。

    每项含 {name, line}(源稿行号)。调用方(第 5 阶段)据此 return 1。
    """
    hits = []
    lines = article_text.splitlines()
    in_block = False
    cur_name = ""
    cur_start = 0
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
            cur_name = name
            cur_start = i + 1
    return hits


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="OBS-119 component visibility / structure check")
    ap.add_argument("--renderer", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    # CLI 直跑时确保能 import pipeline(_body_plain_text 在 stages 内)。
    _repo = Path(__file__).resolve().parents[1]
    if str(_repo) not in sys.path:
        sys.path.insert(0, str(_repo))
    result = component_structure_check(Path(a.renderer), Path(a.out_dir))
    for name, r in sorted(result.items()):
        print(f"{name}: text_ok={r['text_ok']} struct_ok={r['struct_ok']} "
              f"per_item_ok={r['per_item_ok']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
