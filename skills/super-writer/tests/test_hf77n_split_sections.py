"""77N/OBS-334: split_sections fenced code block skip tests."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_article_length import split_sections  # noqa: E402


def test_fenced_hash_comment_not_treated_as_heading():
    """77N/OBS-334: fenced bash `#` comments must not become sections."""
    article = (
        "## 第二节：评测\n"
        "正文。\n"
        "```bash\n"
        "npm i -g cline\n"
        "# 进入 Cline 后输入:\n"
        "/model\n"
        "# 然后选择 Hy4 preview\n"
        "```\n"
        "## 第三节：生态\n"
        "正文。\n"
    )
    titles = [s["title"] for s in split_sections(article)]
    assert titles == ["第二节：评测", "第三节：生态"], titles


def test_real_headings_still_split_sections():
    """77N/OBS-334: genuine headings outside fences still split."""
    article = "# H1\n甲。\n\n## H2\n乙。\n\n### H3\n丙。\n"
    titles = [s["title"] for s in split_sections(article)]
    assert titles == ["H1", "H2", "H3"], titles
