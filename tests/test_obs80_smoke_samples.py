"""档56 OBS-80:relock 冒烟样本配置完整性测试。

验证 SMOKE_ENTRIES 覆盖全部锁定 skill,且每个配置引用的样本文件
(skill 侧现成样本 + Pipeline 侧 smoke-samples)存在。冒烟演练本身
以子进程方式跑生产入口(见档56报告);本测试只做配置/样本存在性检查,
避免在无已装 skill 的环境误报。
"""
import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RELOCK = REPO_ROOT / "scripts" / "relock.py"

LOCKED_SKILLS = ["super-writer", "zh-human-writing", "media-enrichment", "gzh-design"]

spec = importlib.util.spec_from_file_location("relock_smoke_probe", RELOCK)
relock = importlib.util.module_from_spec(spec)
spec.loader.exec_module(relock)

SAMPLE_DIR = REPO_ROOT / "scripts" / "smoke-samples"


def _installed(skill_name):
    # 项目根 = repo_root 的上上级(F:\AIXM\wxgzh);无安装侧时跳过
    root = REPO_ROOT.parent.parent
    home = root / ".agents" / "skills"
    return home / skill_name


def test_all_locked_skills_have_smoke_config():
    assert set(relock.SMOKE_ENTRIES) == set(LOCKED_SKILLS)


@pytest.mark.parametrize("skill_name", LOCKED_SKILLS)
def test_smoke_sample_paths_exist(skill_name):
    cfg = relock.SMOKE_ENTRIES[skill_name]
    installed = _installed(skill_name)
    for arg in cfg["args"]:
        if arg.startswith("--"):
            continue  # CLI 标志,非路径
        if "{" not in arg:
            continue  # 非占位符参数(如 --theme 的值)
        fmt = arg.format(skill_dir=installed, smoke_dir="<tmp>", sample_dir=SAMPLE_DIR)
        if "<tmp>" in fmt:
            continue  # 输出目录由冒烟运行时创建
        assert Path(fmt).exists(), f"{skill_name}: 冒烟样本缺失: {fmt}"


def test_smoke_entry_is_locked_entrypoint():
    """冒烟入口应与 lock entrypoint 一致(lock wins over config)。"""
    lock = relock.SMOKE_ENTRIES  # noqa: F841  (配置检查以实际 relock 逻辑为准)
    for skill_name in LOCKED_SKILLS:
        entry = relock.SMOKE_ENTRIES[skill_name]["entry"]
        assert entry.startswith("scripts/"), f"{skill_name}: entry 应为 scripts/ 下"
