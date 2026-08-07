"""档72B-1R OBS-223:fake_live validator shim 与 producers 传参的 CLI 契约守护。

72B-1 事故:producers 给 change_report.py 传 --length-retention,
fake_live shim 缺该参数 → argparse exit 2 → 17 个不相干测试以
'STAGE_FAILED' == 'COMPLETE' 集体变红,错误信号被淹没。

本测试直接 import producers._agent_validator_args 生成 argv(禁止手抄),
对每一条 (skill, rel, args) 用 sys.executable 真跑 fake_live shim,
断言 returncode != 2(argparse 错误退出码)。producers.py 一改参数,
测试自动跟进;shim 参数漂移在源头以可读消息暴露。

hermetic(R62):只碰 tmp_path 与仓内 fake_live/,不读 installed skills、
不读 .agents、不联网。shim 定位走 execmodel.resolve_agent_validator
的 fake_live 分支,不依赖开发机路径。
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from wxgzh_pipeline import execmodel as EM
from wxgzh_pipeline.producers import _agent_validator_args

REPO_ROOT = Path(__file__).resolve().parents[1]

STAGES = ("super_writer", "zh_human_writing")


def _hermetic_env() -> dict:
    """父环境副本,剔除 shim 行为注入口,防止外壳变量污染默认关闭语义。"""
    env = os.environ.copy()
    env.pop("WXGZH_FAKE_FIDELITY_EXIT", None)
    return env

# generation-profile.yaml 会被 _super_writer_policy 解析,占位文本必须是合法长度策略。
GENERATION_PROFILE = (
    "article_mode: full_mode\n"
    "target_visible_chars: 3000\n"
    "acceptable_min: 2000\n"
    "acceptable_max: 4000\n"
)


def _all_validator_entries(run_dir: Path) -> list[tuple[str, str, list]]:
    """收集两个 agent 阶段的全部 (skill, script_rel, args),argv 来自生产代码。"""
    entries: list[tuple[str, str, list]] = []
    for stage in STAGES:
        ctx = SimpleNamespace(run_dir=str(run_dir))
        sd = run_dir / stage
        if stage == "super_writer":
            # _agent_validator_args 会当场解析长度策略,必须先落合法文件。
            (sd).mkdir(parents=True, exist_ok=True)
            (sd / "generation-profile.yaml").write_text(
                GENERATION_PROFILE, encoding="utf-8")
        entries.extend(_agent_validator_args(stage, ctx, run_dir / stage))
    return entries


def _materialize_paths(argv: list, tmp_path: Path) -> None:
    """按 argv 实际值造出全部引用文件;generation-profile.yaml 用合法内容。"""
    for value in argv:
        path = Path(value)
        if not path.is_absolute():
            continue
        assert path.resolve().is_relative_to(tmp_path.resolve()), (
            f"argv 引用越出 tmp_path: {path} (argv={argv!r})"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.name == "generation-profile.yaml":
            path.write_text(GENERATION_PROFILE, encoding="utf-8")
        else:
            path.write_text("placeholder\n", encoding="utf-8")


def test_obs223_fake_live_shims_accept_producers_argv(tmp_path):
    run_dir = tmp_path / "runs" / "0c"
    checked = 0
    failures = []
    for skill, rel, args in _all_validator_entries(run_dir):
        _materialize_paths(args, tmp_path)
        shim = EM.resolve_agent_validator(skill, rel, "fake_live", REPO_ROOT)
        assert shim.is_file(), f"shim not found: {shim}"
        proc = subprocess.run(
            [sys.executable, str(shim), *args],
            capture_output=True,
            text=True,
            timeout=60,
            # Windows 上最小 env 会导致子进程 Python 初始化失败;复制父环境
            # 并剔除 shim 行为注入口,保证默认关闭语义不被外壳污染(R104)。
            env=_hermetic_env(),
        )
        checked += 1
        if proc.returncode == 2:
            failures.append(
                "shim : %s\nargv : %r\nstderr: %s"
                % (shim.relative_to(REPO_ROOT), args, (proc.stderr or "").strip())
            )
    assert checked >= 6, (
        f"覆盖范围异常:只检查了 {checked} 条 validator(argv 应来自 "
        f"{STAGES} 两个阶段共 6 条;若 producers 增删校验器请同步此下限)"
    )
    assert not failures, (
        "fake_live shim 拒绝 producers 传参(argparse exit 2),CLI 契约漂移:\n"
        + "\n---\n".join(failures)
    )
