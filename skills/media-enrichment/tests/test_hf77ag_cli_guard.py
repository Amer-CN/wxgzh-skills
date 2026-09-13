"""77AG/OBS-384:自测工具参数护栏 + 未知参数零副作用。

覆盖 generate_evidence.py / build_zip.py（同病并入）：
bogus flag → exit 2 且 skill 树零新增文件；--help → exit 0 且零副作用
（含 import 时不建 evidence/）；裸调语义由既有套件覆盖（本文件只加护栏断言）。

子进程 stdout/stderr 甩 DEVNULL（不用管道——沙箱曾报 WinError 5）；
快照排除 pytest 自身 volatile 目录（__pycache__/.pytest_cache）。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
GENERATE = SKILL_ROOT / "scripts" / "generate_evidence.py"
BUILD_ZIP = SKILL_ROOT / "scripts" / "build_zip.py"
VOLATILE = {"__pycache__", ".pytest_cache"}


def _snapshot() -> set[str]:
    out = set()
    for p in SKILL_ROOT.rglob("*"):
        rel = p.relative_to(SKILL_ROOT)
        if any(part in VOLATILE for part in rel.parts):
            continue
        if p.is_file():
            out.add(rel.as_posix())
    return out


def _run_nopipe(script: Path, *args: str) -> int:
    with open("NUL" if sys.platform == "win32" else "/dev/null", "w") as devnull:
        proc = subprocess.run(
            [sys.executable, "-X", "utf8", str(script), *args],
            stdout=devnull, stderr=devnull, cwd=str(SKILL_ROOT))
    return proc.returncode


def _assert_zero_side_effect(script: Path, *args: str) -> int:
    assert not (SKILL_ROOT / "evidence").exists()
    before = _snapshot()
    code = _run_nopipe(script, *args)
    after = _snapshot()
    assert after - before == set(), f"新增文件: {sorted(after - before)}"
    assert not (SKILL_ROOT / "evidence").exists()
    return code


def test_77ag_generate_evidence_bogus_flag_exit2_zero_files():
    """①bogus flag → exit 2 + skill 树零新增。"""
    code = _assert_zero_side_effect(GENERATE, "--bogus-flag-77ag")
    assert code == 2, f"未知参数应 exit 2，实得 {code}"


def test_77ag_generate_evidence_help_zero_side_effect():
    """②--help → exit 0 + 零副作用（含 import 时不建 evidence/）。"""
    code = _assert_zero_side_effect(GENERATE, "--help")
    assert code == 0, f"--help 应 exit 0，实得 {code}"


def test_77ag_build_zip_bogus_flag_exit2_zero_files():
    """③build_zip 同病：bogus flag → exit 2 + 零新增。"""
    code = _assert_zero_side_effect(BUILD_ZIP, "--bogus-flag-77ag")
    assert code == 2, f"未知参数应 exit 2，实得 {code}"


def test_77ag_build_zip_help_zero_side_effect():
    """④build_zip --help → exit 0 + 零副作用。"""
    code = _assert_zero_side_effect(BUILD_ZIP, "--help")
    assert code == 0, f"--help 应 exit 0，实得 {code}"
