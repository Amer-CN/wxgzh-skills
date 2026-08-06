#!/usr/bin/env python3
"""档71C-2 C路线 OBS-119:组件载体以实测可见性为唯一事实源。

component_body_visibility_check:对 A 组 9 类各构造最小文章,把哨兵 SENTINEL_A1
放进该组件正文槽,CLI 子进程调用安装侧渲染器,断言 SENTINEL_A1 出现在
_body_plain_text(final.html) 中。

2d'(档71C-2):类 B(哨兵未进 final.html)组件一律不补 pipeline 锚(R15),
只能进 QUARANTINED_COMPONENTS + fail-closed 门禁。修复归 71C-R。

2g' 恒等断言:APPROVED_CARRIER_COMPONENTS == 现场实测可见集合(测试现场计算);
APPROVED ∪ QUARANTINED == 安装侧 _COMPONENT_BUILDERS 键集合且交集为空。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# 类 B(2d' 实测:哨兵未进 final.html)——渲染器缺陷,不补锚,隔离 + fail-closed。
# gzh-design 修复后须回归 test_component_visibility 并移回 APPROVED。
# OBS-124:code-compare @before/@after 只取同一行,续行代码丢失且 lang="..." 串入正文。
# OBS-125:long-image 文档 image=/caption= 与实现 url/cap 双不匹配,图与说明双丢。
QUARANTINED_COMPONENTS = frozenset({"code-compare", "long-image"})

# 2.6(档71C-2 收尾):组件×模式隔离 —— 该组件单段可用,块体 ≥2 行有效文本即失败。
# OBS-129:alert 多行块体塌成单 <p>(行间仅字面 \n,无 <br>/</p><p 载体)。
# OBS-132:quote 同单槽结构(blockquote 单 <p>),多行塌陷(2.6d 实测确认)。
# gzh-design 修复后须回归 test_component_visibility 并移回 APPROVED。
MULTILINE_UNSUPPORTED_COMPONENTS = frozenset({"alert", "quote"})

# 可见集合由 component_body_visibility_check 现场实测得出;与 QUARANTINED 并集
# 必须等于安装侧 _COMPONENT_BUILDERS 键集合(见 tests/test_obs119_visibility.py)。
APPROVED_CARRIER_COMPONENTS: frozenset[str] = frozenset()  # 测试运行时填充

_COMPONENT_SAMPLES = {
    "alert": ":::alert type=\"warn\"\nSENTINEL_A1\n:::\n",
    "quote": ":::quote\nSENTINEL_A1\n:::\n",
    "code-compare": ":::code-compare\n@before lang=\"python\"\nSENTINEL_A1\n@end\n:::\n",
    "media-text": ":::media-text\n![图](https://x.com/a.png)\nSENTINEL_A1\n:::\n",
    "gallery": ":::gallery title=\"图集\"\n![SENTINEL_A1](https://x.com/1.png)\n:::\n",
    "long-image": ":::long-image image=\"https://x.com/1.png\" caption=\"SENTINEL_A1\"\n:::\n",
    "resources": ":::resources title=\"参考\"\n- [SENTINEL_A1](https://x.com)\n:::\n",
    "footnotes": "正文[^1]\n\n[^1]: SENTINEL_A1 注释\n:::\n",
    "dialogue": ":::dialogue title=\"问答\"\n@user: SENTINEL_A1\n:::\n",
}


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
    ap = argparse.ArgumentParser(description="OBS-119 component visibility check")
    ap.add_argument("--renderer", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    result = component_body_visibility_check(Path(a.renderer), Path(a.out_dir))
    for name, visible in sorted(result.items()):
        print(f"{name}: {'visible' if visible else 'INVISIBLE'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
