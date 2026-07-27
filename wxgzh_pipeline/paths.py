"""Cross-platform path resolution + run-dir helpers. No hardcoded machine paths.

Project-root resolution order (spec section 6):
  1. explicit config (arg)
  2. WXGZH_PROJECT_ROOT
  3. AGENT_SKILLS_HOME (its parent is the project root)
  4. current project's .agents/skills (walk up from cwd)
  5. standard skill location under the user home
All via pathlib; works on Windows / macOS / Linux.
"""
from __future__ import annotations

import os
import re
import secrets as _secrets
import string
from datetime import datetime
from pathlib import Path


def _has_skills(p: Path) -> bool:
    return (p / ".agents" / "skills").is_dir()


def resolve_project_root(explicit: str | os.PathLike | None = None,
                         env: dict | None = None,
                         start: Path | None = None) -> Path:
    env = os.environ if env is None else env
    # 1. explicit
    if explicit:
        return Path(explicit).expanduser().resolve()
    # 2. WXGZH_PROJECT_ROOT
    if env.get("WXGZH_PROJECT_ROOT"):
        return Path(env["WXGZH_PROJECT_ROOT"]).expanduser().resolve()
    # 3. AGENT_SKILLS_HOME -> parent-of-parent is the project root (.../.agents/skills)
    if env.get("AGENT_SKILLS_HOME"):
        sh = Path(env["AGENT_SKILLS_HOME"]).expanduser().resolve()
        # .../<root>/.agents/skills -> root
        if sh.name == "skills" and sh.parent.name == ".agents":
            return sh.parent.parent
        return sh
    # 4. walk up from start/cwd for a dir containing .agents/skills
    cur = (start or Path.cwd()).resolve()
    for cand in [cur, *cur.parents]:
        if _has_skills(cand):
            return cand
    # 5. user home standard location
    home = Path.home()
    if _has_skills(home):
        return home
    return cur


def skills_home(project_root: Path, env: dict | None = None) -> Path:
    env = os.environ if env is None else env
    if env.get("AGENT_SKILLS_HOME"):
        return Path(env["AGENT_SKILLS_HOME"]).expanduser().resolve()
    return (project_root / ".agents" / "skills").resolve()


def run_root(project_root: Path) -> Path:
    return (project_root / ".temp" / "wxgzh-pipeline").resolve()


def slugify(topic: str, maxlen: int = 24) -> str:
    """ASCII-safe slug; non-ascii collapses to 'topic' so RUN_ID stays portable."""
    s = topic.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    if not s:
        s = "topic"
    return s[:maxlen].strip("-") or "topic"


def make_run_id(topic: str, now: datetime | None = None) -> str:
    now = now or datetime.now()
    rand = "".join(_secrets.choice(string.ascii_lowercase + string.digits) for _ in range(6))
    return f"{now.strftime('%Y%m%dT%H%M%S')}-{slugify(topic)}-{rand}"


def new_run_dir(project_root: Path, topic: str) -> Path:
    d = run_root(project_root) / make_run_id(topic)
    d.mkdir(parents=True, exist_ok=True)
    return d


def list_runs(project_root: Path) -> list[Path]:
    rr = run_root(project_root)
    if not rr.is_dir():
        return []
    return sorted([p for p in rr.iterdir() if p.is_dir()], key=lambda p: p.name)
