"""OBS-73/OBS-83 content-fidelity guard tests (档51, hammer.3 semantics).

The guard inspects the BODY region only (hammer_para paragraphs + <pre> blocks);
EVERY intro paragraph — including the FIRST line — must be present IN FULL.
A cover-subtitle/oneliner occurrence does NOT count (档50 regression: the old
whole-HTML check passed while the first line lived only in the cover).
"""
from __future__ import annotations

from pathlib import Path

from wxgzh_pipeline.stages.gzh_design import (
    _body_plain_text,
    _intro_content_fidelity,
    _intro_paras,
)

MULTI_INTRO = """# 标题

第一行导语。

第二行导语段落。

第三行导语段落。

## 第一章

章节正文。
"""


def _html_with_body(paras: list[str]) -> str:
    body = "".join(
        f'<section style="margin:0 20px;"><p style="margin-bottom:16px;font-size:14px;'
        f'line-height:1.9;text-align:justify;color:#555555;"><span leaf="">{p}</span></p></section>'
        for p in paras)
    return f'<p style="font-size:24px;font-weight:900;">封面副标题占位</p>' + body + '<p>PART 01</p>'


class TestBodyPlainText:
    def test_only_body_paras_and_pre_are_extracted(self):
        html = ('<p style="font-size:24px;">封面不该出现</p>'
                '<section style="margin:0 20px;"><p style="margin-bottom:16px;font-size:14px;'
                'line-height:1.9;text-align:justify;color:#555;">正文段</p></section>'
                '<pre style="white-space:pre;">code  x</pre>'
                '<p>签名不该出现</p>')
        text = _body_plain_text(html)
        assert "正文段" in text and "codex" in text  # whitespace-normalized
        assert "封面不该出现" not in text and "签名不该出现" not in text


class TestContentFidelity:
    def test_all_paragraphs_including_first_in_body_passes(self):
        report = _intro_content_fidelity(MULTI_INTRO, _html_with_body(
            ["第一行导语。", "第二行导语段落。", "第三行导语段落。"]))
        assert report["ok"] is True
        assert report["intro_line_count"] == 3

    def test_first_line_only_in_cover_fails(self):
        # OBS-83: cover occurrence must NOT satisfy the first line
        html = ('<p style="font-size:24px;font-weight:900;">第一行导语。</p>'
                + _html_with_body(["第二行导语段落。", "第三行导语段落。"]))
        report = _intro_content_fidelity(MULTI_INTRO, html)
        assert report["ok"] is False
        assert "第一行导语。" in report["missing_text"]

    def test_first_line_200_chars_in_body_passes(self):
        md = "# T\n\n" + "甲" * 200 + "。\n\n## 一\n\n正文。\n"
        report = _intro_content_fidelity(md, _html_with_body(["甲" * 200 + "。"]))
        assert report["ok"] is True

    def test_missing_second_paragraph_fails_with_full_text(self):
        md = "# T\n\n第一行。\n\n被吞掉的第二段。\n\n## 一\n\n正文\n"
        report = _intro_content_fidelity(md, _html_with_body(["第一行。"]))
        assert report["ok"] is False
        assert "被吞掉的第二段。" in report["missing_text"]

    def test_html_entities_and_whitespace_normalized(self):
        md = "# T\n\n第一行 & 第二行。\n\n## 一\n\n正文\n"
        html = ('<section style="margin:0 20px;"><p style="margin-bottom:16px;font-size:14px;'
                'line-height:1.9;text-align:justify;color:#555;">第一行 &amp;  第二行。</p></section>')
        report = _intro_content_fidelity(md, html)
        assert report["ok"] is True


class TestRealHTMLRegression:
    """档50 first-line-only-in-cover HTML must FAIL under the new guard."""

    def test_run50_html_fails(self):
        # 档52:样本已冻结为 fixtures(原测试读 .temp 实时 RUN 目录;档52 按指令
        # 重跑 gzh_design 时该文件被新渲染器产物合法覆盖,旧渲染(首段仅封面)已
        # 无处可寻。fixture 用 hammer.2 渲染器(9596ecc)对同一冻结文章离线复现,
        # 语义逐字等同档50 产物(首段仅以 40 字 oneliner 出现于封面,正文缺失)。
        fixture = Path(__file__).resolve().parents[1] / "fixtures" / "regression_samples"
        md = (fixture / "run50-final_article.md").read_text(encoding="utf-8")
        html = (fixture / "run50-final-html-broken.html").read_text(encoding="utf-8")
        report = _intro_content_fidelity(md, html)
        assert report["ok"] is False
        assert "导语：多模型编排正在成为 AI 编程成本的关键杠杆" in report["missing_text"]


# ── OBS-120(档71C-2):导语区 ::: 组件块排除 + 未知组件 FAIL_CLOSED ──

def test_obs120_intro_alert_block_passes():
    """① 导语区含 :::alert -> 守卫 PASS(组件块被排除)。"""
    md = "# 标题\n\n:::alert type=\"warn\"\n风险提示内容\n:::\n这是导语正文。\n\n## 第一章\n"
    html = ('<p style="margin-bottom:16px;font-size:14px;line-height:1.9;'
            'text-align:justify;">这是导语正文。</p>')
    g = _intro_content_fidelity(md, html)
    assert g["ok"] is True, g


def test_obs120_intro_missing_text_still_fails():
    """② 导语区正常文字缺失 -> 仍 FAIL(旧能力不退化)。"""
    md = "# 标题\n\n这是导语正文。\n\n## 第一章\n"
    html = '<p style="margin-bottom:16px;font-size:14px;line-height:1.9;text-align:justify;">不相关内容</p>'
    g = _intro_content_fidelity(md, html)
    assert g["ok"] is False
    assert "这是导语正文" in g["missing_text"]


def test_obs120_unknown_component_fail_closed(tmp_path):
    """③ unknown_count=1 的 usage 报告 -> FAIL_CLOSED 且 reason 命中。"""
    import json
    from wxgzh_pipeline.stages import gzh_design as gd
    sd = tmp_path / "gzh_design"
    sd.mkdir(parents=True, exist_ok=True)
    (sd / "final.html").write_text("<p>x</p>", encoding="utf-8")
    (sd / "component_usage_report.json").write_text(json.dumps({
        "components": {"unknown": [{"name": "unknown-comp", "head": ":::unknown-comp"}],
                       "unknown_count": 1},
    }), encoding="utf-8")
    class Ctx:
        run_dir = tmp_path
        network_mode = "live"
        skills_home = tmp_path
        env = {}
    class State:
        final_article_sha256 = None
    # 直接调用 content_validate:unknown 应在 final.html 检查后、OBS-73 前触发
    import types
    # 语法门禁在真实渲染器存在时才跑;此处直接验证未知组件逻辑(构造 usage 报告)
    from validators.validate_component_visibility import quarantine_gate
    code, report, vp, vs = gd.content_validate(
        types.SimpleNamespace(run_dir=tmp_path, network_mode="live",
                              skills_home=r"F:\AIXM\wxgzh\.agents\skills", env={}),
        sd, State())
    assert code == 1
    assert "COMPONENT_UNKNOWN" in report.get("reason", "")
    assert "unknown-comp" in str(report.get("unknown_components", []))


# ── OBS-119(档71C-2 C路线):隔离组件 fail-closed + 恒等断言 ──

def test_obs119_quarantined_component_fails(tmp_path):
    """用到隔离组件(code-compare) -> quarantine_gate 命中 + 行号正确。"""
    from validators.validate_component_visibility import quarantine_gate
    md = "# 标题\n\n## 章节\n\n:::code-compare\n@before\nx\n@end\n:::\n"
    hits = quarantine_gate(md)
    assert hits and hits[0]["name"] == "code-compare"
    assert hits[0]["line"] == 5  # :::code-compare 行


def test_obs119_approved_component_not_triggered(tmp_path):
    """只用批准组件(alert) -> 不触发隔离门禁。"""
    from validators.validate_component_visibility import quarantine_gate
    md = "# 标题\n\n## 章节\n\n:::alert type=\"warn\"\n内容\n:::\n"
    hits = quarantine_gate(md)
    assert hits == []


# ── OBS-129/132(档71C-2 收尾):多行不支持组件门禁 ──

def test_obs129_multiline_alert_fails():
    """alert 多段 -> multiline_gate 命中。"""
    from validators.validate_component_visibility import multiline_gate
    md = "# 标题\n\n## 章节\n\n:::alert type=\"warn\"\nS1\nS2\nS3\n:::\n"
    hits = multiline_gate(md)
    assert hits and hits[0]["name"] == "alert" and hits[0]["line_count"] == 3


def test_obs129_single_line_alert_not_triggered():
    """alert 单段 -> 不触发。"""
    from validators.validate_component_visibility import multiline_gate
    md = "# 标题\n\n## 章节\n\n:::alert type=\"warn\"\nS1\n:::\n"
    hits = multiline_gate(md)
    assert hits == []
