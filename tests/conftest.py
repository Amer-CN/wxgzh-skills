"""Shared test fixtures. Skill root is added to sys.path; skills_home is the
parent dir (wxgzh-pipeline lives inside the skills home). All tests run offline
(no WeChat side effects).
"""
import sys
from pathlib import Path

import pytest

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
    return Orchestrator(project_root=tmp_path, network_mode="fake_live",
                        skills_home=skills_home, fixture_dir=FAKE_FIXTURE)


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
