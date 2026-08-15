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


def test_super_writer_instructions_guide_behavior():
    """76G-R/OBS-265:super_writer 握手指令必须含两条行为层引导——
    ① prose_craft_applied 如实填写(执行 R1–R9 才许 true);② Phase 6 标题选定必做
    (selected_title/title_selection_reason 必填)。"""
    src = (SKILL_ROOT / "wxgzh_pipeline" / "producers.py").read_text(encoding="utf-8")
    assert "prose_craft_applied" in src and "R1–R9" in src
    assert "执行了 R1–R9 自检才许填" in src
    assert "Phase 6" in src and "标题选定" in src
    assert "selected_title 与 title_selection_reason 必填" in src


def test_webp_cover_transcoded_to_jpeg(tmp_path):
    """76G-R:封面本地 WebP 转 JPEG(微信 40113 实证);非 WebP 原样。"""
    from PIL import Image
    webp = tmp_path / "cover.webp"
    Image.new("RGB", (800, 450), (200, 90, 30)).save(webp, "WEBP")
    out = PR._webp_cover_to_jpeg(webp, tmp_path)
    assert out != webp and out.suffix == ".jpg"
    with Image.open(out) as im:
        assert im.format == "JPEG"
    png = tmp_path / "cover.png"
    Image.new("RGB", (800, 450), (30, 90, 200)).save(png, "PNG")
    assert PR._webp_cover_to_jpeg(png, tmp_path) == png


def test_aihot_instructions_contain_oow_fetch_procedure():
    """76H/OBS-267:aihot 握手指令必须含超窗取料顺序(日报/快照/事件回溯/官方源/手动注入)。"""
    src = (SKILL_ROOT / "wxgzh_pipeline" / "producers.py").read_text(encoding="utf-8")
    assert "/api/v1/dailies/" in src
    assert "selected/snapshot" in src
    assert "hot-topics" in src and "stories" in src
    assert "supplemental" in src and "items_file_injection" in src


def test_gzh_args_use_frozen_bindings(tmp_path):
    """76X-R/用户裁决:图注下线——gzh 直传媒体冻结 bindings(不再生成 captioned 副本)。"""
    rd = tmp_path
    (rd / "media_enrichment").mkdir(parents=True)
    (rd / "gzh_design").mkdir()
    (rd / "media_enrichment" / "article_image_bindings.json").write_text(
        json.dumps({"body_images": []}), encoding="utf-8")
    ctx = _Ctx(rd)
    sd = rd / "gzh_design"
    args = PR._entry_args(ctx, "gzh_design", sd, None, None)
    bp = args[args.index("--bindings") + 1]
    assert bp.endswith("article_image_bindings.json")
    assert "captioned" not in bp

def test_76xr_gzh_args_no_captioned_copy(tmp_path):
    """76X-R:gzh 阶段不再生成 captioned bindings 副本——直传媒体冻结 bindings。"""
    rd = tmp_path
    (rd / "media_enrichment").mkdir(parents=True)
    (rd / "gzh_design").mkdir()
    (rd / "media_enrichment" / "article_image_bindings.json").write_text(
        json.dumps({"body_images": []}), encoding="utf-8")
    ctx = _Ctx(rd)
    sd = rd / "gzh_design"
    args = PR._entry_args(ctx, "gzh_design", sd, None, None)
    bp = args[args.index("--bindings") + 1]
    assert bp.endswith("article_image_bindings.json"), bp
    assert "captioned" not in bp
    # producers 中不再有图注合成函数
    src = (SKILL_ROOT / "wxgzh_pipeline" / "producers.py").read_text(encoding="utf-8")
    assert "_captioned_bindings_path" not in src
    assert "_caption_type" not in src
