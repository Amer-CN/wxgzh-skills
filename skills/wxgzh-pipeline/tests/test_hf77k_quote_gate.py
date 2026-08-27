"""77K repair-pack focused tests."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


NORMALIZE = load_module(
    REPO / "skills/zh-human-writing/scripts/normalize_quotes.py",
    "test_hf77k_normalize_quotes")
VSP = load_module(
    REPO / "skills/super-writer/scripts/validate_single_product.py",
    "test_hf77k_validate_single_product")
RENDER_ROOT = REPO / "skills/gzh-design/scripts"


def test_obs326_directive_quotes_are_untouched_and_body_still_normalized():
    text = ':::alert type="information" title="价格对照"\n他说"你好"。\n:::\n'
    result, warnings = NORMALIZE.normalize_text(text)
    assert result.splitlines()[0] == ':::alert type="information" title="价格对照"'
    assert "他说“你好”。" in result
    assert ":::" in result
    assert warnings == []


def test_obs326_attribute_line_inside_component_is_machine_syntax():
    text = '起点"前"\n:::alert\nsource="https://example.com/a"\n:::\n终点"后"\n'
    result, _ = NORMALIZE.normalize_text(text)
    assert 'source="https://example.com/a"' in result
    assert "终点“后”" in result


def test_obs326_malformed_component_argument_warns_and_does_not_silently_default(tmp_path):
    article = tmp_path / "article.md"
    out = tmp_path / "render"
    article.write_text(
        "# 标题\n\n## 章节\n\n"
        ':::alert type="information title="价格对照"\n'
        "提示正文。\n"
        ":::\n",
        encoding="utf-8")
    proc = subprocess.run([
        sys.executable, "-X", "utf8", str(RENDER_ROOT / "render_article.py"),
        "--article", str(article), "--output-dir", str(out),
        "--theme", "smartisan", "--date", "2026.08",
    ], capture_output=True, text=True, encoding="utf-8", errors="replace")
    report = json.loads((out / "component_usage_report.json").read_text(encoding="utf-8"))
    warnings = report["components"]["component_argument_warnings"]
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert any(row["component"] == "alert" and row.get("head") for row in warnings)


def test_obs327_handoff_null_is_honest_only_when_not_applied(tmp_path):
    path = tmp_path / "handoff.yaml"
    good = """handoff:
  schema_version: "2.2"
  prose_craft_applied: false
  prose_craft_version: null
  title_candidates: ["A", "B", "C"]
  hook_line: "hook"
  selected_title: "A"
  title_selection_reason: "具体"
  formatter:
    cover:
      kicker: "深度观察"
"""
    path.write_text(good, encoding="utf-8")
    errors, checks = VSP.check_handoff(path)
    assert errors == []
    assert checks["prose_craft_version"] is None

    path.write_text(good.replace("applied: false", "applied: true"), encoding="utf-8")
    errors, checks = VSP.check_handoff(path)
    assert checks["prose_craft_version"] is None
    assert errors == ["handoff: 缺必填字段 `handoff.prose_craft_version`"]


def test_obs328_article_placeholder_is_blocked_before_render(tmp_path):
    path = tmp_path / "article.md"
    path.write_text("本文开始。\n[编辑锚点] 补证据。\n", encoding="utf-8")
    errors, checks = VSP.check_article(path)
    joined = "\n".join(errors)
    assert "[编辑锚点" in joined
    assert "77K/OBS-328" in joined

    path.write_text("本文已完成事实核对。\n", encoding="utf-8")
    errors, checks = VSP.check_article(path)
    assert errors == []
    assert checks["chars"] > 0
def test_obs328_article_precheck_is_in_official_ack_chain(tmp_path):
    from types import SimpleNamespace
    sys.path.insert(0, str(REPO / "skills/wxgzh-pipeline"))
    from wxgzh_pipeline import producers as PR
    sd = tmp_path / "super_writer"; sd.mkdir()
    (sd / "generation-profile.yaml").write_text(
        "mode: full\narticle_mode: medium\nlength_mode: medium\n"
        "target_visible_chars: 3000\nacceptable_min: 2500\nacceptable_max: 4000\n")
    ctx = SimpleNamespace(run_dir=tmp_path, network_mode="live", skills_home=tmp_path)
    precheck = next(item for item in PR._agent_validator_args("super_writer", ctx, sd)
                     if item[1].endswith("validate_single_product.py") and "article" in item[2])
    assert precheck[2][1] == "article" and str(sd / "article.md") == precheck[2][-1]

