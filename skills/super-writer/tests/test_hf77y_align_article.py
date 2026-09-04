"""77Y/OBS-370:align_outline_budget --article 修理(计数口径 + 导语区纳入)。

覆盖:
1. CJK/ASCII 混文计数与 validate_article_length.count_visible_chars 同口径
   (链接只计文本、代码计内容,不再「去空白全长」粗算);
2. 导语区(文首/H1 至第一个 ##)计为「（导语）」节纳入 actual 与预算分配,
   预算不再被正文节压占(输出清单在册 + 分配份额>0 + 合计=target)。
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = SKILL_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import align_outline_budget as aob  # noqa: E402
from validate_article_length import count_visible_chars  # noqa: E402

OUTLINE = """# 大纲

## 文章配置

- target_visible_chars：1000

## 第一节

- planned_chars：600
- minimum_chars：570
- maximum_chars：630
- weight_percent：60.0
- evidence_ids：[m1]

## 第二节

- planned_chars：400
- minimum_chars：380
- maximum_chars：420
- weight_percent：40.0
- evidence_ids：[m2]
"""


def _count_actual(atext: str) -> dict:
    """与 align_outline_budget main() --article 分支同构的实际统计
    (导语区 + 各 ## 节,count_visible_chars 口径)。"""
    heads = list(re.finditer(r"^##\s+(.+)$", atext, re.MULTILINE))
    actual = {}
    intro_body = atext[:heads[0].start()] if heads else atext
    intro_chars = count_visible_chars(intro_body)
    if intro_chars > 0:
        actual["（导语）"] = intro_chars
    for idx, hm in enumerate(heads):
        title = hm.group(1).strip()
        body = atext[hm.end(): heads[idx + 1].start()
                     if idx + 1 < len(heads) else len(atext)]
        actual[title] = count_visible_chars(body)
    return actual


def test_77y_align_article_counting_matches_count_visible_chars(tmp_path):
    """①CJK/ASCII 混文计数与 count_visible_chars 一致:链接只计链接文本
    (不计 URL),行内代码计内容——旧口径(去空白全长)含 URL,新口径不含。"""
    article = tmp_path / "article.md"
    article.write_text(
        "# 标题\n\n"
        "## 第一节\n\n"
        "看 [Claude 官方博客](https://www.anthropic.com/blog/v2?utm=x) 与 "
        "`pip install wxgzh` 的对比,数字 12345 ABC。\n"
        "第二段只有 ASCII words here。\n\n"
        "## 第二节\n\n"
        "中文段落,含半角 a1。\n",
        encoding="utf-8")
    outline = tmp_path / "outline.md"
    outline.write_text(OUTLINE, encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", str(_SCRIPTS / "align_outline_budget.py"),
         "--outline", str(outline), "--article", str(article),
         "--target-visible-chars", "1000", "--dry-run"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    info = json.loads(proc.stdout)
    atext = article.read_text(encoding="utf-8")
    heads = list(re.finditer(r"^##\s+(.+)$", atext, re.MULTILINE))
    # 输出留痕的 actual 与 count_visible_chars 逐节相等(同口径)
    for idx, hm in enumerate(heads):
        title = hm.group(1).strip()
        body = atext[hm.end(): heads[idx + 1].start()
                     if idx + 1 < len(heads) else len(atext)]
        assert info["actual"][title] == count_visible_chars(body)
    # 反证:第一节含长 URL——旧口径(去空白全长)会显著大于新口径
    old_style = len(re.sub(r"\s+", "", atext[heads[0].end(): heads[1].start()]))
    assert info["actual"]["第一节"] < old_style


def test_77y_align_article_intro_section_counted(tmp_path):
    """②导语区计入 actual:「（导语）」节在册,预算不再被压
    (导语按实测份额分得预算,new≥1,全节合计=target)。"""
    article = tmp_path / "article.md"
    article.write_text(
        "# 大标题\n\n这是导语段落,写足引子内容,「导语」不该被预算分配无视。"
        "再补几句让导语字数显著大于零,确保它在实际加权中占据真实份额。\n\n"
        "## 第一节\n\n正文一。\n\n## 第二节\n\n正文二。\n",
        encoding="utf-8")
    outline = tmp_path / "outline.md"
    outline.write_text(OUTLINE, encoding="utf-8")
    atext = article.read_text(encoding="utf-8")
    actual = _count_actual(atext)
    assert actual["（导语）"] > 0
    new_text, info, errors = aob.align_outline(
        outline.read_text(encoding="utf-8"), 1000, actual=actual)
    assert not errors
    titles = [s["title"] for s in info["sections"]]
    assert "（导语）" in titles, info["sections"]
    intro = next(s for s in info["sections"] if s["title"] == "（导语）")
    assert intro["new"] >= 1
    body_new = sum(s["new"] for s in info["sections"]
                   if s["title"] != "（导语）")
    assert intro["new"] + body_new == 1000
    assert body_new < 1000
    # 导语节无 planned 行:写回结果中 outline 预算行只属于两个正文节(零改坏)
    rewritten = aob.align_outline(
        outline.read_text(encoding="utf-8"), 1000, actual=actual)[0]
    assert "（导语）" not in rewritten  # 大纲文件本身不新增导语行
