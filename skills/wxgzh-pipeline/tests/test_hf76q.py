"""76Q 生产暴露修理包测试。

- 任务 1/OBS-284:zh 验收门读 pattern_audit 分组——FT-001 advisory(疑似专名
  降级)命中不阻断、仅留痕 forbidden_term_advisory;strong 命中语义不变仍拒;
  pattern_audit.stdout.json 缺失/解析失败时回退旧 text.count(fail-closed)。
- 任务 3/OBS-286:语法门 bold 探针是渲染器能力探测(unsupported 属正确报告,
  非误判)——契约由源码断言固定;渲染器零改动。
- 任务 4/OBS-287:pipeline sw 指令引用 registry dict / dedup 映射 / source_url
  逐字一致契约。
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import wxgzh_pipeline.producers as PR
from wxgzh_pipeline.stages import zh_human_writing as ZW

from conftest import SKILL_ROOT


def _mk_stage(tmp_path, article_text: str, pa: dict | None) -> Path:
    sd = Path(tmp_path)
    (sd / "final_article.md").write_text(article_text, encoding="utf-8")
    (sd / "fidelity_report.json").write_text(json.dumps(
        {g: 0 for g in ZW._ZERO_GATES}, ensure_ascii=False), encoding="utf-8")
    if pa is not None:
        (sd / "pattern_audit.stdout.json").write_text(
            json.dumps(pa, ensure_ascii=False), encoding="utf-8")
    return sd


def _ft_finding(rule_group: str, span: str) -> dict:
    if rule_group == "advisory_only":
        return {"rule_id": "FT-001", "group": "advisory_only", "severity": "advisory",
                "span_text": span}
    return {"rule_id": "FT-001", "group": "strong_contextual", "severity": "strong",
            "span_text": span}


def test_obs284_advisory_ft_passes_and_flagged():
    """FT-001 advisory(疑似专名降级)命中 → 过门,forbidden_term_advisory 留痕。"""
    import tempfile
    tmp = Path(tempfile.mkdtemp())
    sd = _mk_stage(tmp, "Luma Agents 上线了。", {
        "hard_residue": {"count": 0, "items": []},
        "strong_contextual": {"count": 0, "high_confidence": [], "low_confidence": []},
        "advisory_only": {"count": 1, "items": [
            _ft_finding("advisory_only", "Luma Agents 上线了。")]},
    })
    ctx = SimpleNamespace(skills_home=str(tmp))
    code, report, _, _ = ZW.content_validate(ctx, sd, SimpleNamespace())
    assert code == 0, report
    assert report["pattern_audit_report"] == "ok"
    assert report["forbidden_term_hits"] == {}
    assert report["forbidden_term_advisory"] == {"Agent": 1}


def test_obs284_strong_ft_still_rejects():
    """FT-001 strong(普通命中)命中 → 仍拒,语义不变。"""
    import tempfile
    tmp = Path(tempfile.mkdtemp())
    sd = _mk_stage(tmp, "这款智能体助手很好用。", {
        "hard_residue": {"count": 0, "items": []},
        "strong_contextual": {"count": 1, "high_confidence": [
            _ft_finding("strong_contextual", "这款智能体助手很好用。")],
            "low_confidence": []},
        "advisory_only": {"count": 0, "items": []},
    })
    ctx = SimpleNamespace(skills_home=str(tmp))
    code, report, _, _ = ZW.content_validate(ctx, sd, SimpleNamespace())
    assert code == 1, report
    assert report["forbidden_term_hits"].get("智能体助手") == 1
    assert "Agent" not in report["forbidden_term_hits"]


def test_obs284_non_ft_internal_terms_still_reject():
    """非 FT-001 内部词(写作残留)仍 text.count 阻断。"""
    import tempfile
    tmp = Path(tempfile.mkdtemp())
    sd = _mk_stage(tmp, "本次抓取的内容见素材库。", {
        "hard_residue": {"count": 0, "items": []},
        "strong_contextual": {"count": 0, "high_confidence": [], "low_confidence": []},
        "advisory_only": {"count": 0, "items": []},
    })
    ctx = SimpleNamespace(skills_home=str(tmp))
    code, report, _, _ = ZW.content_validate(ctx, sd, SimpleNamespace())
    assert code == 1
    assert "素材库" in report["forbidden_term_hits"]


def test_obs284_missing_pa_report_falls_back_fail_closed():
    """pattern_audit.stdout.json 缺失 → 回退旧 text.count,含 Agent 仍拒(fail-closed)。"""
    import tempfile
    tmp = Path(tempfile.mkdtemp())
    sd = _mk_stage(tmp, "Luma Agents 上线了。", None)
    ctx = SimpleNamespace(skills_home=str(tmp))
    code, report, _, _ = ZW.content_validate(ctx, sd, SimpleNamespace())
    assert code == 1
    assert report["pattern_audit_report"] == "missing"
    assert report["forbidden_term_hits"].get("Agent") == 1


def test_obs284_syntax_gate_bold_probe_is_capability_probe():
    """OBS-286:语法门 bold 探针=渲染器能力探测,unsupported 属正确报告而非误判。"""
    text = (SKILL_ROOT / "validators" / "validate_syntax_gate.py").read_text(
        encoding="utf-8")
    assert '("bold", "** 加粗"' in text
    assert "unsupported" in text
    # 判据来自 probe(对安装侧渲染器逐类实测),不是规则硬编码
    assert "probe" in text.lower()


def test_obs287_super_writer_instruction_cites_registry_contract():
    instr = PR.AGENT_INSTRUCTIONS["super_writer"]
    assert "76Q/OBS-287" in instr
    assert "claims,materials" in instr
    assert "dedup_id" in instr and "逐字一致" in instr
    assert "含锚点原样一致" in instr
    assert "76Q/OBS-285" in instr and "双层包裹" in instr
    assert "76Q/OBS-286" in instr and "** 加粗标记" in instr


def test_obs287_contract_file_declares_registry_shape():
    text = (SKILL_ROOT / "contracts" / "02_super_writer.yaml").read_text(
        encoding="utf-8")
    assert "76Q/OBS-287" in text
    assert "claims" in text and "materials" in text
    assert "dedup_id" in text and "source_url" in text
