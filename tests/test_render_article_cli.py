"""OBS-78: CLI-level (subprocess) regression tests for scripts/render_article.py.

These tests run the REAL production invocation path — `python render_article.py`
as a child process — never importlib/direct-import + main() calls. That is the
whole point: the 档45R2 defect (defs after the __main__ guard) crashed the CLI
while every importlib-style test stayed green.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
RENDER = SKILL_ROOT / "scripts" / "render_article.py"


def _run_cli(article_text: str, bindings=None, theme="smartisan", timeout=300):
    td = Path(tempfile.mkdtemp(prefix="render-cli-"))
    article = td / "article.md"
    article.write_text(article_text, encoding="utf-8")
    cmd = [sys.executable, "-X", "utf8", str(RENDER),
           "--article", str(article), "--output-dir", str(td), "--theme", theme]
    if bindings is not None:
        bp = td / "bindings.json"
        bp.write_text(json.dumps(bindings), encoding="utf-8")
        cmd += ["--bindings", str(bp)]
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)
    html = (td / "final.html").read_text(encoding="utf-8") if (td / "final.html").is_file() else ""
    return proc, html


def _assert_no_traceback(proc):
    assert proc.returncode == 0, proc.stdout + proc.stderr
    for marker in ("NameError", "AttributeError", "KeyError", "Traceback"):
        assert marker not in proc.stderr, f"stderr contains {marker}:\n{proc.stderr}"


MULTI_INTRO = """# 标题

第一行导语。

第二行导语段落。

第三行导语段落。

## 第一章

章节正文。

## 第二章

结尾。
"""

FENCED = """# 标题

导语。

## 第一章

正文段落。

```
rm -rf /tmp/x
git push --force origin main
    indented line
```

结束段落。
"""


class TestCliProductionPath:
    def test_multi_intro_paragraphs_cli(self):
        proc, html = _run_cli(MULTI_INTRO)
        _assert_no_traceback(proc)
        assert "第二行导语段落。" in html
        assert "第三行导语段落。" in html
        assert html.rindex("第二行导语段落。") < html.rindex("PART 01")

    def test_fenced_code_block_cli(self):
        proc, html = _run_cli(FENCED)
        _assert_no_traceback(proc)
        import html as _h
        import html as _h
        assert "```" not in html
        assert "rm -rf /tmp/x" in _h.unescape(html).replace("\xa0", " ")
        assert "git push --force origin main" in _h.unescape(html).replace("\xa0", " ")
        # OBS-90:缩进以 &nbsp; 保留(unescape 后逐字一致)
        assert "    indented line" in _h.unescape(html).replace("\xa0", " ")

    def test_minimal_call_without_bindings_cli(self):
        proc, html = _run_cli("# T\n\n导语。\n\n## 一\n\n正文。\n")
        _assert_no_traceback(proc)
        assert "<section" in html

    def test_stderr_clean_for_all_themes(self):
        for theme in ("smartisan", "hammer", "锤子风格"):
            proc, html = _run_cli(MULTI_INTRO, theme=theme)
            _assert_no_traceback(proc)
