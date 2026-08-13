#!/usr/bin/env python3
"""档71E OBS-175:配图章节亲和判据(独立 CLI + 测试,不挂主门禁)。

判据(3a):每张正文图,其在 final.html 中的插入位置所属章节,必须等于该图对应
数字对(chart_group 的 start/end 值)在 final_article.md 中【首次出现】的那个
## 章节。

排除项:封面图(hammer cover_breaking 组件,主题自带,不在 body_images)、
页脚图(footer_cta,同上)、社交卡片图(media 侧 og:image 源资产在
media_enrichment 即被 rejected,不会进入 body_images)。依据:三类都不来自
bindings.body_images;body_images 只含正文图,本判据只处理 body_images。

位置机制(S65,档71E 1a 取证):安装侧 gzh-design render_article.py render()
L222-253 用 _distribute() 按 img_queue 顺序 round-robin 分配章节,
bindings.placement(anchor/position/confidence) 完全不读 → 渲染器内不存在
可注入的位置控制点。故按档71E 3d 例外条款:本判据【不挂主门禁】,只保留
独立 CLI + 测试;第 6 步仍运行它并如实贴结果,FAIL 不阻塞但必须在 l 项写明。

bindings 缺 chart_group(现 RUN 实测为缺):不静默跳过 → 判 FAIL 并打印缺字段名;
caption/alt_text 中的数字对仅用于亲和差异的诊断输出(不改变 FAIL 结论)。

CLI:--article --html --bindings --out-dir;exit 0 = PASS,exit 1 = FAIL。
FAIL 时逐张打印【图文件名 / 图所在章节 / 数字线所在章节 / 差异】,
reason 常量 = OBS175_IMAGE_SECTION_AFFINITY=FAIL。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REASON = "OBS175_IMAGE_SECTION_AFFINITY=FAIL"

_CN_DIGITS = {"零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
              "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
_PAIR_RE = re.compile(
    r"从?\s*([0-9一二三四五六七八九十百两]+)\s*(?:条|个|项|张|组)?\s*"
    r"(?:扩到|变为|改成|到|→)\s*"
    r"([0-9一二三四五六七八九十百两]+)\s*(?:条|个|项|张|组)?")
_CAPTION_INT_RE = re.compile(r"(\d+)(?:\.0)?\s*条")


def _cn_to_int(token: str) -> int | None:
    if not token:
        return None
    if token.isdigit():
        return int(token)
    if all(c in _CN_DIGITS for c in token):
        if len(token) == 1:
            return _CN_DIGITS[token]
        if "十" in token:
            parts = token.split("十")
            tens = _CN_DIGITS.get(parts[0], 1) if parts[0] else 1
            ones = _CN_DIGITS.get(parts[1], 0) if len(parts) > 1 and parts[1] else 0
            return tens * 10 + ones
    return None


def _pair_in_text(text: str, start: int, end: int) -> bool:
    for m in _PAIR_RE.finditer(text):
        a = _cn_to_int(m.group(1))
        b = _cn_to_int(m.group(2))
        if a == start and b == end:
            return True
    return False


def _split_article_chapters(article: str) -> list[dict]:
    """按 '## ' 标题切分 final_article.md,返回 [{title, text, order}]。"""
    chapters: list[dict] = []
    cur_title = ""
    cur_lines: list[str] = []
    for ln in article.replace("\r\n", "\n").split("\n"):
        st = ln.strip()
        if st.startswith("## ") and not st.startswith("### "):
            if cur_title:
                chapters.append({"title": cur_title,
                                 "text": "\n".join(cur_lines)})
            cur_title = st[3:].strip()
            cur_lines = []
        else:
            cur_lines.append(ln)
    if cur_title:
        chapters.append({"title": cur_title, "text": "\n".join(cur_lines)})
    for i, ch in enumerate(chapters, 1):
        ch["order"] = i
    return chapters


def _first_occurrence_chapter(article: str, start: int, end: int) -> dict | None:
    """数字对 (start, end) 在 final_article.md 中【首次出现】的 ## 章节。"""
    for ch in _split_article_chapters(article):
        if _pair_in_text(ch["text"], start, end):
            return ch
    return None


def _image_section(html: str, img_pos: int, chapter_markers: list[tuple[int, str]]) -> str:
    """img_pos 所属章节:最近的前置章节边界。边界 = 该章标题在 HTML 中的
    【最后一次出现】(TOC 在前,章节标题组件在后)。无前置边界 → 正文外(intro)。"""
    best = None
    for pos, title in chapter_markers:
        if pos <= img_pos:
            best = title
        else:
            break
    return best or ""


def _chapter_markers(html: str, chapters: list[dict]) -> list[tuple[int, str]]:
    markers: list[tuple[int, str]] = []
    for ch in chapters:
        last = -1
        for m in re.finditer(re.escape(ch["title"]), html):
            last = m.start()
        if last >= 0:
            markers.append((last, ch["title"]))
    markers.sort()
    return markers


def _image_number_pair(entry: dict) -> tuple[dict | None, list[str]]:
    """从 bindings 条目取数字对。返回 (pair_or_None, 问题清单)。

    chart_group 缺失是硬失败(3c 边界),即使 caption 回退能算出数字对,
    缺字段本身仍判 FAIL(问题清单保留;pair 只用于亲和差异诊断)。"""
    problems: list[str] = []
    cg = entry.get("chart_group")
    pair: dict | None = None
    if isinstance(cg, dict):
        start = cg.get("start")
        end = cg.get("end")
        if isinstance(start, int) and isinstance(end, int):
            pair = {"start": start, "end": end, "source": "chart_group"}
        else:
            problems.append("missing field: chart_group.start/end")
    elif cg is None:
        problems.append("missing field: chart_group")
    if pair is None:
        # 诊断回退:从 caption/alt_text 提取数字对(不改变 FAIL 结论)
        caption = entry.get("caption") or entry.get("alt_text") or ""
        ints = [int(x) for x in _CAPTION_INT_RE.findall(caption)]
        uniq = sorted(set(ints))
        if len(uniq) == 2:
            pair = {"start": uniq[0], "end": uniq[1], "source": "caption_fallback"}
        elif uniq:
            problems.append(f"caption numbers ambiguous: {uniq}")
        else:
            problems.append("no numbers in caption/alt_text")
    return pair, problems


def validate_affinity(article_path: Path, html_path: Path,
                      bindings_path: Path) -> dict:
    article = article_path.read_text(encoding="utf-8")
    html = html_path.read_text(encoding="utf-8")
    bindings = json.loads(bindings_path.read_text(encoding="utf-8"))
    images = bindings.get("body_images", [])
    chapters = _split_article_chapters(article)
    markers = _chapter_markers(html, chapters)

    per_image: list[dict] = []
    ok = True
    for entry in images:
        asset_id = entry.get("asset_id") or "?"
        sha = entry.get("sha256", "")[:8]
        fname = entry.get("file_name") or f"{asset_id}_{sha}.png"
        img_pos = html.find(entry.get("remote_url", "")) if entry.get("remote_url") else -1
        if img_pos < 0:
            per_image.append({"asset_id": asset_id, "file_name": fname,
                              "ok": False, "reason": "image url not found in html"})
            ok = False
            continue
        section = _image_section(html, img_pos, markers)
        pair, problems = _image_number_pair(entry)
        if pair is None:
            per_image.append({"asset_id": asset_id, "file_name": fname,
                              "image_section": section,
                              "number_section": None, "ok": False,
                              "reason": "; ".join(problems)})
            ok = False
            continue
        num_ch = _first_occurrence_chapter(article, pair["start"], pair["end"])
        if num_ch is None:
            per_image.append({"asset_id": asset_id, "file_name": fname,
                              "image_section": section,
                              "number_section": None, "ok": False,
                              "reason": (f"numbers {pair['start']}→{pair['end']} "
                                         "not found in any ## chapter")})
            ok = False
            continue
        same = section == num_ch["title"]
        diag = "" if same else ("section mismatch: 图在「%s」,数字线在「%s」"
                                % (section, num_ch["title"]))
        reason = "; ".join([p for p in problems if p] + ([diag] if diag else []))
        per_image.append({
            "asset_id": asset_id, "file_name": fname,
            "image_section": section, "number_section": num_ch["title"],
            "number_pair": [pair["start"], pair["end"]],
            "number_source": pair["source"], "same_chapter": same, "ok": same and not problems,
            "reason": reason,
        })
        if not same or problems:
            ok = False
    return {"ok": ok, "reason": REASON, "per_image": per_image,
            "chapter_count": len(chapters), "image_count": len(images)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="OBS-175 配图章节亲和判据(独立 CLI)")
    ap.add_argument("--article", required=True)
    ap.add_argument("--html", required=True)
    ap.add_argument("--bindings", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rep = validate_affinity(Path(a.article), Path(a.html), Path(a.bindings))
    for img in rep["per_image"]:
        line = (f"[{'PASS' if img['ok'] else 'FAIL'}] {img['file_name']} "
                f"| 图所在章节={img.get('image_section') or '-'} "
                f"| 数字线所在章节={img.get('number_section') or '-'} "
                f"| 差异={img.get('reason') or '无'}")
        print(line, file=sys.stdout)
    (out / "validate_image_section_affinity.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    if not rep["ok"]:
        print(f"{REASON}", file=sys.stdout)
        return 1
    print("OBS175_IMAGE_SECTION_AFFINITY=PASS", file=sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
