"""77A/OBS-309: 半角引号机械归一在 zh 阶段链上强制前置。

管线对 final_article.md 先跑 normalize_quotes.py（中文语境成对转全角、
单边留 WARNING 不硬改），再进 fidelity/pattern/change 校验。
"""
from pathlib import Path
from types import SimpleNamespace

from wxgzh_pipeline import producers as P


def test_zh_chain_normalizes_quotes_first(tmp_path):
    rd = tmp_path / "run"
    sd = rd / "zh_human_writing"
    sd.mkdir(parents=True)
    (sd / "final_article.md").write_text('他说"你好"。\n', encoding="utf-8")
    entries = P._agent_validator_args(
        "zh_human_writing", SimpleNamespace(run_dir=str(rd)), sd)
    assert entries[0][1] == "scripts/normalize_quotes.py"
    assert entries[0][2][0] == "--text"
    assert entries[0][2][-1] == str(sd / "final_article.md")


def test_zh_instruction_carries_hard_wording():
    instr = P.AGENT_INSTRUCTIONS["zh_human_writing"]
    assert "77A/OBS-309" in instr
    assert "成对转全角" in instr
    assert "单边落单不猜" in instr
