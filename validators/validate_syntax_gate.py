#!/usr/bin/env python3
"""档71B OBS-102:未支持语法门禁 —— 判据来自渲染器实测行为(probe)。

作用对象:stage 03 产出的冻结文章 zh_human_writing/final_article.md。
执行时机:stage 05(gzh_design)内容校验阶段,渲染之后、放行之前。

★免悖论声明:判据来自 probe(对安装侧渲染器逐类实测);71C 接线后 probe 会
自动判定 ::: 为「支持」并放行;本门禁不含任何跨仓硬编码期望值(避免 OBS-98
形状),因此不与 71C/71D 构成不可满足集合。

★判据来源必须是渲染器实际行为,严禁硬编码「支持/不支持」清单:
  - 每类语法生成最小样本 md(H1 + 一个 ## 章节 + 该语法 3-5 行),语法内文本
    使用可唯一定位的哨兵串(SENTINEL_A1 / SENTINEL_A2);
  - 用生产调用方式(CLI 子进程)调用安装侧 gzh-design 渲染器;
  - 判「不支持」的两个条件,任一成立即不支持:
      ① 语法控制符原样出现在 final.html 的可见文本中;
      ② 哨兵文本未完整出现在 final.html 的正文区。
  - ★正文区口径复用 wxgzh_pipeline/stages/gzh_design.py 的 _PARA_RE + _PRE_RE
    + _body_plain_text(同源,禁止另写一套)。
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

# ── 语法目录(catalog,10 类,档71B 第 4b 条逐字照用) ──────────────
CATALOG_VERSION = "v1"
CATALOG = [
    # (key, label, 检测用控制符, 样本 md 模板)
    ("fence", "::: 围栏", ":::", "# 标题\n\n## 章节\n\n```\nSENTINEL_A1\nSENTINEL_A2\n```\n"),
    ("fn_ref", "[^N] 脚注引用", "[^1]", "# 标题\n\n## 章节\n\n正文 SENTINEL_A1[^1] 继续\n\n[^1]: SENTINEL_A2 定义\n"),
    ("fn_def", "[^N]: 脚注定义", "[^1]:", "# 标题\n\n## 章节\n\n[^1]: SENTINEL_A1 定义行\n[^2]: SENTINEL_A2 定义行\n"),
    ("h3", "### 及更深标题", "###", "# 标题\n\n## 章节\n\n### SENTINEL_A1 三级标题\n### SENTINEL_A2 更深\n"),
    ("quote", "行首 > 引用", ">", "# 标题\n\n## 章节\n\n> SENTINEL_A1 引用一行\n> SENTINEL_A2 引用二行\n"),
    ("ulist", "行首 - 无序列表", "- ", "# 标题\n\n## 章节\n\n- SENTINEL_A1 项一\n- SENTINEL_A2 项二\n"),
    ("olist", "行首 1. 有序列表", "1. ", "# 标题\n\n## 章节\n\n1. SENTINEL_A1 步一\n2. SENTINEL_A2 步二\n"),
    ("table", "| 表格", "|", "# 标题\n\n## 章节\n\n| SENTINEL_A1 | SENTINEL_A2 |\n|---|---|\n| 甲 | 乙 |\n"),
    ("bold", "** 加粗 或 ~~ 删除线", "**", "# 标题\n\n## 章节\n\n**SENTINEL_A1** 与 ~~SENTINEL_A2~~\n"),
    ("inline_code", "行内反引号 `code`", "`", "# 标题\n\n## 章节\n\n`SENTINEL_A1` 与 `SENTINEL_A2`\n"),
]

# 文章侧扫描用(与 catalog 的 key 对应,检测冻结文章中是否出现该类语法)
ARTICLE_SCAN = {
    "fence": re.compile(r"^:::", re.M),
    "fn_ref": re.compile(r"\[\^\d+\](?!:)"),
    "fn_def": re.compile(r"^\[\^\d+\]:", re.M),
    "h3": re.compile(r"^#{3,}\s", re.M),
    "quote": re.compile(r"^>\s?", re.M),
    "ulist": re.compile(r"^[-*]\s+", re.M),
    "olist": re.compile(r"^\d+\.\s+", re.M),
    "table": re.compile(r"^\|", re.M),
    "bold": re.compile(r"\*\*|~~"),
    "inline_code": re.compile(r"`[^`\n]+`"),
}


def _renderer_sha256(renderer: Path) -> str:
    return hashlib.sha256(renderer.read_bytes()).hexdigest()


def _probe_single(renderer: Path, sample_md: str, out_dir: Path,
                 ctrl: str) -> dict:
    """对单个语法样本运行渲染器,返回 (ctrl_visible, sentinel_missing)。"""
    md_path = out_dir / "sample.md"
    md_path.write_text(sample_md, encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", str(renderer),
         "--article", str(md_path), "--output-dir", str(out_dir),
         "--theme", "smartisan"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=120)
    html_path = out_dir / "final.html"
    html = html_path.read_text(encoding="utf-8") if html_path.is_file() else ""
    # ① 语法控制符原样出现在可见文本(逐类检测其专有控制符)
    visible = re.sub(r"<[^>]+>", "", html)
    import html as _html_mod
    visible = _html_mod.unescape(visible)
    ctrl_visible = ctrl in visible
    # 正文区口径:复用 gzh_design._body_plain_text(同源)
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from wxgzh_pipeline.stages.gzh_design import _body_plain_text
    body = _body_plain_text(html)
    sentinel_missing = not ("SENTINEL_A1" in body and "SENTINEL_A2" in body)
    return {"exit_code": proc.returncode, "html_len": len(html),
            "ctrl_visible": ctrl_visible, "sentinel_missing": sentinel_missing,
            "unsupported": ctrl_visible or sentinel_missing}


def probe_syntax_support(renderer: Path, probe_dir: Path) -> dict:
    """对 10 类语法逐一 probe,返回 {key: {"label", "unsupported", ...}}。"""
    probe_dir.mkdir(parents=True, exist_ok=True)
    result = {}
    for key, label, ctrl, sample in CATALOG:
        out_dir = probe_dir / key
        out_dir.mkdir(parents=True, exist_ok=True)
        r = _probe_single(renderer, sample, out_dir, ctrl)
        result[key] = {"label": label, **r}
    return result


def load_or_probe(renderer: Path, probe_dir: Path, cache_path: Path | None = None) -> dict:
    """probe 结果可按「渲染器文件 sha256 + catalog 版本」缓存;禁止跨 RUN 复用
    (缓存路径由调用方控制在 RUN 目录内)。"""
    sha = _renderer_sha256(renderer)
    if cache_path is not None and cache_path.is_file():
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            if (cached.get("renderer_sha256") == sha
                    and cached.get("catalog_version") == CATALOG_VERSION):
                return cached["result"]
        except (OSError, ValueError):
            pass
    result = probe_syntax_support(renderer, probe_dir)
    if cache_path is not None:
        cache_path.write_text(json.dumps(
            {"renderer_sha256": sha, "catalog_version": CATALOG_VERSION,
             "result": result}, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def validate_syntax_gate(article_path: Path, renderer: Path,
                         probe_dir: Path, cache_path: Path | None = None) -> tuple[int, dict]:
    """冻结文章中任何「不支持」语法 -> FAIL_CLOSED。

    报告给出语法类别 + 行号 + 原文片段 + probe 依据(哪一条判定条件命中)。
    """
    article = article_path.read_text(encoding="utf-8")
    lines = article.splitlines()
    support = load_or_probe(renderer, probe_dir, cache_path)
    problems = []
    for key, label, ctrl, _sample in CATALOG:
        rx = ARTICLE_SCAN[key]
        hits = [(i + 1, ln) for i, ln in enumerate(lines) if rx.search(ln)]
        if not hits:
            continue
        entry = support.get(key, {})
        unsupported = entry.get("unsupported", True)
        reasons = []
        if entry.get("ctrl_visible"):
            reasons.append("① 语法控制符原样出现在 final.html 可见文本")
        if entry.get("sentinel_missing"):
            reasons.append("② 哨兵文本未完整出现在 final.html 正文区")
        if unsupported:
            for lineno, text in hits[:5]:
                problems.append({
                    "category": label, "line": lineno,
                    "snippet": text.strip()[:120],
                    "probe_reason": "；".join(reasons) if reasons else "probe 判定不支持",
                })
    ok = not problems
    return (0 if ok else 1), {
        "OBS102_SYNTAX_GATE": "PASS" if ok else "FAIL",
        "catalog_version": CATALOG_VERSION,
        "renderer_sha256": _renderer_sha256(renderer),
        "probe_summary": {k: {"label": v["label"], "unsupported": v["unsupported"]}
                          for k, v in support.items()},
        "hits": problems,
        "guidance": "冻结文章含渲染器不支持的语法;请改写为支持的语法(或等待 71C 接线)。",
    }


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="OBS-102 syntax gate (probe-driven)")
    ap.add_argument("--article", required=True)
    ap.add_argument("--renderer", required=True)
    ap.add_argument("--probe-dir", required=True)
    ap.add_argument("--cache", default=None)
    a = ap.parse_args(argv)
    code, report = validate_syntax_gate(
        Path(a.article), Path(a.renderer), Path(a.probe_dir),
        Path(a.cache) if a.cache else None)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
