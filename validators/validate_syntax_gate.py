#!/usr/bin/env python3
"""档71B OBS-102/档71B'-C:未支持语法门禁 —— 判据来自渲染器实测行为(probe)。

作用对象:stage 03 产出的冻结文章 zh_human_writing/final_article.md。
执行时机:stage 05(gzh_design)内容校验阶段,渲染之后、放行之前。

★免悖论声明:判据来自 probe(对安装侧渲染器逐类实测);71C 接线后 probe 会
自动判定 ::: 为「支持」并放行;本门禁不含任何跨仓硬编码期望值(避免 OBS-98
形状),因此不与 71C/71D 构成不可满足集合。

★判据来源必须是渲染器实际行为,严禁硬编码「支持/不支持」清单:
  - 每类语法生成最小样本 md(骨架 + 控制行 + 哨兵);
  - 用生产调用方式(CLI 子进程)调用安装侧 gzh-design 渲染器;
  - 判「不支持」的两个条件,任一成立即不支持:
      ① 语法控制符原样出现在正文区文本中(R9:针与文本同一归一化;
         测量域=归一化正文区,与哨兵同源);
      ② 哨兵文本未完整出现在 final.html 的正文区。
  - ★正文区口径复用 wxgzh_pipeline/stages/gzh_design.py 的 _PARA_RE +
    _CODE_ROW_RE + _PRE_RE + _body_plain_text + _normalize_text(同源,禁止另写)。

OBS-114(高):探针针体无可匹配性自检 —— 不可匹配的针恒产出「支持」;
本档实例 = ulist/olist 的 token 含空格而测量域删除全部空白。通用修法 =
R9(针与文本同归一化 + 针体自检,见 3C-d 固化为 pytest 用例)。

OBS-115(中):ARTICLE_SCAN 曾用并集正则(r"^[-*]\s+"、r"\*\*|~~"),
探针只测其中一支,未测形态借用已测形态的结论;本档已拆分并补
ulist_star / strike 两类样本(拆分理由见 ARTICLE_SCAN 注释)。
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

# ── 语法目录(catalog,13 类 + 1 负对照,档71B'-C 第 3C-c 条逐字照用) ──────
CATALOG_VERSION = "v3"

# 样本统一骨架:标题 + 导语占位(无控制符) + 章节 + 控制行 + 结尾段落
_SKELETON = (
    "# 探针样本\n"
    "\n"
    "这是导语占位段落，不含任何控制符。\n"
    "\n"
    "## 章节一\n"
)

# (key, label, token, needle, 控制行模板)
#   token  = 该类原始控制符(仅用于报告与负对照诊断,不参与判定)
#   needle = 参与判定的针,必须是「经 _normalize_text 处理后仍可匹配」的形态
#            (含空白的 token 在归一化(删空白)后不可匹配,故 needle 用哨兵锚定形)
# SENTINEL_A1 放在控制行上(或围栏块内),SENTINEL_A2 放在紧随的普通段落。
CATALOG = [
    ("code_fence", "``` 代码围栏", "```", "```",
     "```text\nSENTINEL_A1\n```\n"),
    ("fence", "::: 围栏", ":::", ":::",
     ":::alert type=\"warn\" title=\"探针\"\nSENTINEL_A1\n:::\n"),
    ("h3", "### 及更深标题", "###", "###", "### SENTINEL_A1\n"),
    ("quote", "行首 > 引用", ">", ">", "> SENTINEL_A1\n"),
    ("ulist", "行首 - 无序列表", "- ", "-SENTINEL_A1", "- SENTINEL_A1\n"),
    ("ulist_star", "行首 * 无序列表", "* ", "*SENTINEL_A1", "* SENTINEL_A1\n"),
    ("olist", "行首 1. 有序列表", "1. ", "1.SENTINEL_A1", "1. SENTINEL_A1\n"),
    ("table", "| 表格", "|", "|SENTINEL_A1", "| SENTINEL_A1 | 值 |\n| --- | --- |\n"),
    ("bold", "** 加粗", "**", "**", "**SENTINEL_A1**\n"),
    ("strike", "~~ 删除线", "~~", "~~", "~~SENTINEL_A1~~\n"),
    ("inline_code", "行内反引号 `code`", "`", "`", "`SENTINEL_A1`\n"),
    ("fn_ref", "[^N] 脚注引用", "[^1]", "[^1]", "正文 SENTINEL_A1[^1] 结束。\n"),
    ("fn_def", "[^N]: 脚注定义", "[^1]:", "[^1]:", "[^1]: SENTINEL_A1\n"),
]

# 负对照:无控制行,只有骨架 + 两个哨兵
# 3C-c 要求:baseline 正文不得含上表任何 token 字符(含 - 与 * 与 "1."),
# 故导语占位段与结尾段均用纯中文/字母,无连字符、星号、数字点、竖线、引号。
BASELINE_SAMPLE = (
    "# 探针样本\n"
    "\n"
    "这是导语占位段落，不含任何控制符。\n"
    "\n"
    "## 章节一\n"
    "\n"
    "SENTINEL_A1 结尾普通段落。\n"
)

# 文章侧扫描用(与 catalog 的 key 对应)
# OBS-115:拆分并集正则 —— r"^[-*]\s+" 拆为 r"^-\s+" 与 r"^\*\s+",
# r"\*\*|~~" 拆为 r"\*\*" 与 r"~~";避免未测形态借用已测形态的结论。
ARTICLE_SCAN = {
    "code_fence": re.compile(r"^```", re.M),
    "fence": re.compile(r"^:::", re.M),
    "h3": re.compile(r"^#{3,}\s", re.M),
    "quote": re.compile(r"^>\s?", re.M),
    "ulist": re.compile(r"^-\s+", re.M),
    "ulist_star": re.compile(r"^\*\s+", re.M),
    "olist": re.compile(r"^\d+\.\s+", re.M),
    "table": re.compile(r"^\|", re.M),
    "bold": re.compile(r"\*\*", re.M),
    "strike": re.compile(r"~~", re.M),
    "inline_code": re.compile(r"`[^`\n]+`"),
    "fn_ref": re.compile(r"\[\^\d+\](?!:)"),
    "fn_def": re.compile(r"^\[\^\d+\]:", re.M),
}


# 正文区口径:复用 gzh_design(同源,禁止另写一套)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wxgzh_pipeline.stages.gzh_design import (  # noqa: E402
    _body_plain_text,
    _normalize_text,
)


def _renderer_sha256(renderer: Path) -> str:
    return hashlib.sha256(renderer.read_bytes()).hexdigest()


def _probe_single(renderer: Path, sample_md: str, out_dir: Path,
                 needle: str) -> dict:
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
    # R9:针与文本同一归一化。测量域=归一化正文区(与哨兵同源)。
    body = _body_plain_text(html)
    ctrl_visible = needle in body
    sentinel_missing = not ("SENTINEL_A1" in body and "SENTINEL_A2" in body)
    return {"exit_code": proc.returncode, "html_len": len(html),
            "ctrl_visible": ctrl_visible, "sentinel_missing": sentinel_missing,
            "unsupported": ctrl_visible or sentinel_missing}


def probe_syntax_support(renderer: Path, probe_dir: Path) -> dict:
    """对 13 类语法逐一 probe,返回 {key: {"label", "unsupported", ...}}。"""
    probe_dir.mkdir(parents=True, exist_ok=True)
    result = {}
    for key, label, _token, needle, control_line in CATALOG:
        out_dir = probe_dir / key
        out_dir.mkdir(parents=True, exist_ok=True)
        sample = _SKELETON + control_line + "SENTINEL_A2 结尾普通段落。\n"
        r = _probe_single(renderer, sample, out_dir, needle)
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


def needle_self_check() -> dict:
    """3C-d 针体可匹配性自检:每类 needle 必须出现在 _normalize_text(该类样本
    md 原文)中。必须调用同一个 _normalize_text 函数对象。"""
    out = {}
    for key, label, _token, needle, control_line in CATALOG:
        sample = _SKELETON + control_line + "SENTINEL_A2 结尾普通段落。\n"
        norm = _normalize_text(sample)
        out[key] = needle in norm
    return out


def validate_syntax_gate(article_path: Path, renderer: Path,
                         probe_dir: Path, cache_path: Path | None = None) -> tuple[int, dict]:
    """冻结文章中任何「不支持」语法 -> FAIL_CLOSED。"""
    article = article_path.read_text(encoding="utf-8")
    lines = article.splitlines()
    support = load_or_probe(renderer, probe_dir, cache_path)
    problems = []
    for key, label, _token, needle, _control_line in CATALOG:
        rx = ARTICLE_SCAN[key]
        hits = [(i + 1, ln) for i, ln in enumerate(lines) if rx.search(ln)]
        entry = support.get(key, {})
        unsupported = entry.get("unsupported", True)
        if unsupported:
            reasons = []
            if entry.get("ctrl_visible"):
                reasons.append("① 语法控制符原样出现在正文区文本")
            if entry.get("sentinel_missing"):
                reasons.append("② 哨兵文本未完整出现在正文区")
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
