"""档71C-R5 OBS-167/168:CLI 缺失明细(真过滤 + 不崩溃)。

用 subprocess 跑 CLI:
- fake_offanchor 下 returncode==0 + stdout 含明细段 + 明细行数 == 现场计算;
- 真渲染器下明细段 0 行。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from conftest import SKILL_ROOT

sys.path.insert(0, str(SKILL_ROOT))
import validators.validate_component_visibility as vcv

CLI = SKILL_ROOT / "validators" / "validate_component_visibility.py"
FAKE_OFFANCHOR = SKILL_ROOT / "tests" / "fixtures" / "fake_offanchor.py"


def _expected_missing_count(renderer: Path, out_dir: Path) -> int:
    """现场计算缺失哨兵数(用同一批 sentinels_for + _body_plain_text)。"""
    from wxgzh_pipeline.stages.gzh_design import _body_plain_text
    measured = vcv.component_structure_check(renderer, out_dir / "struct")
    anchors = vcv.export_body_anchors_from_measurement(renderer, out_dir / "anchors")
    n = 0
    for name, r in measured.items():
        if not (r["render_ok"] and not r["anchor_ok"]):
            continue
        for smp in vcv.SLOT_SAMPLES[name]:
            d = out_dir / "struct" / f"{name}-{smp['mode']}"
            html = (d / "final.html").read_text(encoding="utf-8") \
                if (d / "final.html").is_file() else ""
            body = _body_plain_text(html)
            for sent in vcv.sentinels_for(name):
                if sent in vcv._URL_SENTINEL_SET or sent not in smp["block"]:
                    continue
                if sent in body:
                    continue
                n += 1
    return n


def test_obs167_cli_fake_offanchor_no_crash_and_detail(tmp_path):
    """fake_offanchor:returncode==0 + 明细段存在 + 行数 == 现场计算。"""
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", "-B", str(CLI), "--renderer", str(FAKE_OFFANCHOR),
         "--out-dir", str(tmp_path / "out")],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=300)
    assert proc.returncode == 0, f"CLI 崩溃: rc={proc.returncode} {proc.stderr[-500:]}"
    assert "--- 缺失哨兵明细" in proc.stdout, "stdout 缺明细段"
    detail_lines = [l for l in proc.stdout.splitlines()
                    if " | " in l and "render_ok=" not in l
                    and not l.startswith("---") and not l.startswith("[")]
    expected = _expected_missing_count(FAKE_OFFANCHOR, tmp_path)
    assert len(detail_lines) == expected, \
        f"明细行数 {len(detail_lines)} != 现场计算 {expected}"


def test_obs167_cli_real_renderer_zero_detail(tmp_path):
    """真渲染器:明细段为 0 行(锚闭环后无缺失)。"""
    from tests.test_obs119_visibility import _resolved_renderer
    renderer, log = _resolved_renderer()
    if renderer is None:
        pytest.skip("渲染器不可得: " + "|".join(log))
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", "-B", str(CLI), "--renderer", str(renderer),
         "--out-dir", str(tmp_path / "out")],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=300)
    assert proc.returncode == 0, proc.stderr[-500:]
    detail_lines = [l for l in proc.stdout.splitlines()
                    if " | " in l and "render_ok=" not in l
                    and not l.startswith("---") and not l.startswith("[")]
    assert len(detail_lines) == 0, f"真渲染器明细应为 0 行: {detail_lines}"
