"""Shared test fixtures. Skill root is added to sys.path; skills_home is the
parent dir (wxgzh-pipeline lives inside the skills home). All tests run offline
(no WeChat side effects).
"""
import os
import sys
from pathlib import Path

import pytest

# 77X/OBS-360:测试套件豁免版本新鲜度检查——编排器第 0 步经此零联网
# (不发起 version_check.py 子进程;豁免门行为本身由 test_hf77x_misc.py 断言)。
os.environ.setdefault("WXGZH_SKIP_VERSION_CHECK", "1")

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT))
SKILLS_HOME = SKILL_ROOT.parent
FIXTURE = SKILL_ROOT / "fixtures" / "offline_pipeline_fixture"
FAKE_FIXTURE = SKILL_ROOT / "fixtures" / "fake_live_fixture"


@pytest.fixture
def skill_root():
    return SKILL_ROOT


@pytest.fixture
def skills_home():
    return SKILLS_HOME


@pytest.fixture
def fixture_dir():
    return FAKE_FIXTURE


@pytest.fixture
def orch(tmp_path, skills_home):
    """Behavioral fixture runs the REAL dev2 machinery in fake_live mode (agent
    handshake + real subprocess + real validators + receipt hashes), with fake
    sub-skills and a fake WeChat client — no real side effects, fully hermetic."""
    from wxgzh_pipeline.orchestrator import Orchestrator
    media_root = SKILL_ROOT.parent / "media-enrichment"
    env = {"WXGZH_FIXED_MEDIA_ROOT": str(media_root)} if media_root.is_dir() else {}
    return Orchestrator(project_root=tmp_path, network_mode="fake_live",
                        skills_home=skills_home, fixture_dir=FAKE_FIXTURE, env=env)


@pytest.fixture
def offline_orch(tmp_path, skills_home):
    from wxgzh_pipeline.orchestrator import Orchestrator
    return Orchestrator(project_root=tmp_path, network_mode="offline_fixture",
                        skills_home=skills_home, fixture_dir=FIXTURE)


def load_validator(name):
    import importlib.util
    p = SKILL_ROOT / "validators" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m
