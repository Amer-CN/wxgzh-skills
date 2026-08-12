"""76D/OBS-257/258:封面标题链路与草稿标题接线。

- gzh 调用携带 --title(handoff.selected_title,缺省回落 title_candidates[0]);
- 终稿无导语且 handoff.hook_line 存在时携带 --subtitle 兜底;
- wechat_draft 标题 = selected_title(缺省回落 title_candidates[0],再回落 topic);
- 无 handoff 标题字段时行为与现状一致(不传 --title / 标题取 topic)。
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import wxgzh_pipeline.producers as PR

from conftest import SKILL_ROOT


class _Ctx:
    def __init__(self, run_dir, skills_home=None):
        self.run_dir = str(run_dir)
        self.skills_home = str(skills_home or SKILL_ROOT)
        self.env = {}
        self.network_mode = "fake_live"


def _mk_run(tmp_path, handoff_text: str, article_text: str = "# H1 原标题\n\n导语。\n## 第一章\n\n正文。\n") -> Path:
    sw = tmp_path / "super_writer"
    sw.mkdir(parents=True, exist_ok=True)
    (sw / "handoff.yaml").write_text(handoff_text, encoding="utf-8")
    zh = tmp_path / "zh_human_writing"
    zh.mkdir(parents=True, exist_ok=True)
    (zh / "final_article.md").write_text(article_text, encoding="utf-8")
    return tmp_path


HANDOFF_SELECTED = """handoff:
  schema_version: "2.2"
  selected_title: "选定标题"
  title_candidates: ["候选标题A", "候选标题B"]
  hook_line: "钩子句"
  formatter:
    cover:
      kicker: "实测观察"
"""

HANDOFF_CANDIDATES_ONLY = """handoff:
  schema_version: "2.2"
  title_candidates: ["候选标题A"]
"""


def test_gzh_args_carry_selected_title(tmp_path):
    rd = _mk_run(tmp_path, HANDOFF_SELECTED)
    ctx = _Ctx(rd)
    sd = rd / "gzh_design"
    sd.mkdir()
    args = PR._entry_args(ctx, "gzh_design", sd, None, None)
    assert "--title" in args and args[args.index("--title") + 1] == "选定标题"
    # 有导语时不传 --subtitle
    assert "--subtitle" not in args


def test_gzh_args_fall_back_to_candidates(tmp_path):
    rd = _mk_run(tmp_path, HANDOFF_CANDIDATES_ONLY)
    ctx = _Ctx(rd)
    sd = rd / "gzh_design"
    sd.mkdir()
    args = PR._entry_args(ctx, "gzh_design", sd, None, None)
    assert "--title" in args and args[args.index("--title") + 1] == "候选标题A"


def test_gzh_args_subtitle_hook_when_no_intro(tmp_path):
    rd = _mk_run(tmp_path, HANDOFF_SELECTED,
                 article_text="## 第一章\n\n正文。\n")
    ctx = _Ctx(rd)
    sd = rd / "gzh_design"
    sd.mkdir()
    args = PR._entry_args(ctx, "gzh_design", sd, None, None)
    assert "--subtitle" in args and args[args.index("--subtitle") + 1] == "钩子句"


def test_gzh_args_no_title_without_handoff_title(tmp_path):
    rd = _mk_run(tmp_path, "handoff:\n  schema_version: \"2.2\"\n")
    ctx = _Ctx(rd)
    sd = rd / "gzh_design"
    sd.mkdir()
    args = PR._entry_args(ctx, "gzh_design", sd, None, None)
    assert "--title" not in args and "--subtitle" not in args


def test_wechat_title_uses_selected_title(tmp_path):
    rd = _mk_run(tmp_path, HANDOFF_SELECTED)
    from wxgzh_pipeline.state import PipelineState
    st = PipelineState(run_id="r1", topic="主题")
    ctx = _Ctx(rd)
    title = PR._wechat_title(ctx, st)
    assert title == "选定标题"


def test_wechat_title_falls_back_to_topic(tmp_path):
    rd = _mk_run(tmp_path, "handoff:\n  schema_version: \"2.2\"\n")
    from wxgzh_pipeline.state import PipelineState
    st = PipelineState(run_id="r1", topic="主题")
    ctx = _Ctx(rd)
    title = PR._wechat_title(ctx, st)
    assert title == "主题"
