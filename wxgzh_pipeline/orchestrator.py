"""Orchestrator: fixed sequential 6-stage pipeline over installed sub-skills.

- doctor(): fail-closed environment check (skills locked, entrypoints, wechat cfg,
  writable project).
- run(): create run dir, execute stages in fixed order (no skip), gate the WeChat
  draft on all prior receipts, persist state atomically, emit evidence.
- resume(): continue the newest incomplete run without rerunning completed stages
  or recreating a draft.
- progress() / release_audit().
"""
from __future__ import annotations

import json
from pathlib import Path

from . import STAGES, __version__
from . import paths as P
from . import skill_discovery as SD
from .state import PipelineState, save_state, load_state, sha256_file
from .receipts import receipt_valid, load_receipt
from .evidence import write_delivery
from .stages import StageContext, StageError, execute_stage
from .stages import aihot, super_writer, zh_human_writing, media_enrichment, gzh_design, wechat_draft

SKILL_ROOT = Path(__file__).resolve().parents[1]
STAGE_MODULES = {
    "aihot": aihot, "super_writer": super_writer, "zh_human_writing": zh_human_writing,
    "media_enrichment": media_enrichment, "gzh_design": gzh_design, "wechat_draft": wechat_draft,
}
DEFAULT_FIXTURE = SKILL_ROOT / "fixtures" / "offline_pipeline_fixture"


class Orchestrator:
    def __init__(self, project_root=None, network_mode="offline_fixture",
                 fixture_dir=None, env=None, skills_home=None):
        self.env = dict(env) if env is not None else None
        _env = self.env if self.env is not None else None
        self.project_root = P.resolve_project_root(project_root, env=_env)
        self.skills_home = Path(skills_home) if skills_home else P.skills_home(self.project_root, env=_env)
        self.network_mode = network_mode
        self.fixture_dir = Path(fixture_dir) if fixture_dir else DEFAULT_FIXTURE
        self.lock = SD.load_lock(SKILL_ROOT)

    # ---------- doctor ----------
    def doctor(self, require_wechat: bool | None = None) -> tuple[bool, dict]:
        if require_wechat is None:
            require_wechat = (self.network_mode == "live")
        ok_skills, disc = SD.verify_all(self.skills_home, self.lock)
        env = self.env if self.env is not None else _os_environ()
        wechat_ok = bool(env.get("WECHAT_APP_ID")) and bool(env.get("WECHAT_APP_SECRET"))
        if not wechat_ok and (self.project_root / ".env").is_file():
            txt = (self.project_root / ".env").read_text(encoding="utf-8", errors="ignore")
            wechat_ok = ("WECHAT_APP_ID" in txt and "WECHAT_APP_SECRET" in txt)
        writable = _is_writable(self.project_root)
        report = {
            "wxgzh_pipeline_version": __version__, "project_root": str(self.project_root),
            "skills_home": str(self.skills_home), "network_mode": self.network_mode,
            "skills_locked_ok": ok_skills, "skills": disc,
            "wechat_config_present": wechat_ok, "wechat_required": require_wechat,
            "project_writable": writable,
        }
        ok = ok_skills and writable and (wechat_ok or not require_wechat)
        report["FAIL_CLOSED"] = not ok
        report["doctor"] = "PASS" if ok else "FAIL"
        return ok, report

    def _context(self, run_dir: Path, disc: dict, create_draft: bool) -> StageContext:
        return StageContext(run_dir=run_dir, skills_home=self.skills_home, discovery=disc,
                            network_mode=self.network_mode, fixture_dir=self.fixture_dir,
                            env=self.env or {}, create_wechat_draft=create_draft)

    # ---------- run ----------
    def run(self, topic: str, profile: str = "fast_publish", create_wechat_draft: bool = True) -> dict:
        ok, dreport = self.doctor()
        if not ok:
            return {"status": "FAIL_CLOSED", "reason": "doctor failed", "doctor": dreport}
        disc = dreport["skills"]
        run_dir = P.new_run_dir(self.project_root, topic)
        st = PipelineState(run_id=run_dir.name, topic=topic, profile=profile)
        save_state(run_dir, st)
        return self._drive(run_dir, st, disc, create_wechat_draft)

    def resume(self, run_id: str | None = None) -> dict:
        run_dir = self._find_resume_run(run_id)
        if run_dir is None:
            return {"status": "NO_RESUMABLE_RUN"}
        st = load_state(run_dir)
        if st.draft_created or st.is_complete():
            return {"status": "ALREADY_COMPLETE", "run_id": st.run_id,
                    "draft_created": st.draft_created, "note": "not recreating draft"}
        ok, dreport = self.doctor()
        if not ok:
            return {"status": "FAIL_CLOSED", "reason": "doctor failed", "doctor": dreport}
        # recompute completed-stage receipts still valid; drop invalid tail
        st.completed_stages = [s for s in STAGES
                               if s in st.completed_stages and receipt_valid(run_dir, s)]
        save_state(run_dir, st)
        return self._drive(run_dir, st, dreport["skills"], create_wechat_draft=True, resumed=True)

    def _drive(self, run_dir, st, disc, create_wechat_draft, resumed=False) -> dict:
        ctx = self._context(run_dir, disc, create_wechat_draft)
        for stage in STAGES:
            if stage in st.completed_stages:
                continue  # resume: never rerun a completed, receipt-valid stage
            # enforce strict order (no skipping)
            expected = st.next_stage()
            if stage != expected:
                st.mark_failed(stage); save_state(run_dir, st)
                return {"status": "FAIL_CLOSED", "reason": f"stage order violation: {stage} != {expected}"}
            # WeChat draft gate: all prior 5 receipts must be valid
            if stage == "wechat_draft":
                bad = [s for s in STAGES[:5] if not receipt_valid(run_dir, s)]
                if bad or not create_wechat_draft:
                    st.mark_failed(stage); save_state(run_dir, st)
                    return {"status": "FAIL_CLOSED",
                            "reason": f"draft blocked; invalid prior receipts={bad} create={create_wechat_draft}"}
            st.current_stage = stage
            save_state(run_dir, st)
            try:
                execute_stage(ctx, STAGE_MODULES[stage], st)
            except (StageError, NotImplementedError) as e:
                st.mark_failed(stage); save_state(run_dir, st)
                return {"status": "STAGE_FAILED", "run_id": st.run_id, "failed_stage": stage,
                        "error": str(e), "fail_closed": True}
            st.mark_complete(stage)
            st.current_stage = None
            save_state(run_dir, st)
        write_delivery(run_dir)
        return {"status": "COMPLETE", "run_id": st.run_id, "topic": st.topic,
                "completed_stages": st.completed_stages, "draft_created": st.draft_created,
                "formally_published": False, "resumed": resumed,
                "uploaded_image_count": st.uploaded_image_count, "run_dir": str(run_dir)}

    # ---------- progress ----------
    def progress(self, run_id: str | None = None) -> dict:
        run_dir = self._find_resume_run(run_id, include_complete=True)
        if run_dir is None:
            return {"status": "NO_RUN"}
        st = load_state(run_dir)
        timing = {s: (load_receipt(run_dir, s) or {}).get("elapsed_seconds")
                  for s in STAGES if load_receipt(run_dir, s)}
        return {"run_id": st.run_id, "topic": st.topic, "profile": st.profile,
                "current_stage": st.current_stage, "completed_stages": st.completed_stages,
                "failed_stage": st.failed_stage, "uploaded_image_count": st.uploaded_image_count,
                "draft_created": st.draft_created, "formally_published": False,
                "stage_timing": timing}

    # ---------- release audit ----------
    def release_audit(self) -> dict:
        ok_skills, disc = SD.verify_all(self.skills_home, self.lock)
        # audit: no formal-publish capability anywhere in the package
        pub = _scan_forbidden_endpoints(SKILL_ROOT / "wxgzh_pipeline")
        report = {"profile": "release_audit", "side_effects": "none",
                  "skills_locked_ok": ok_skills, "skills": disc,
                  "no_formal_publish_capability": not pub, "forbidden_endpoint_hits": pub,
                  "creates_wechat_draft": False, "uploads_images": False}
        report["RELEASE_AUDIT"] = "PASS" if (ok_skills and not pub) else "FAIL"
        return report

    # ---------- helpers ----------
    def _find_resume_run(self, run_id, include_complete=False):
        runs = P.list_runs(self.project_root)
        if run_id:
            for r in runs:
                if r.name == run_id:
                    return r
            return None
        candidates = []
        for r in reversed(runs):  # newest first
            sp = r / "pipeline_state.json"
            if not sp.is_file():
                continue
            st = load_state(r)
            if include_complete or (not st.is_complete() and not st.draft_created):
                candidates.append(r)
        return candidates[0] if candidates else None

    def list_incomplete(self):
        out = []
        for r in P.list_runs(self.project_root):
            sp = r / "pipeline_state.json"
            if sp.is_file():
                st = load_state(r)
                if not st.is_complete() and not st.draft_created:
                    out.append(r.name)
        return out


def _os_environ():
    import os
    return os.environ


def _is_writable(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        t = path / ".wxgzh_write_test"
        t.write_text("x", encoding="utf-8")
        t.unlink()
        return True
    except Exception:
        return False


def _scan_forbidden_endpoints(pkg_dir: Path) -> list:
    """Prove no formal-publish/mass-send/scheduled/delete WeChat ENDPOINTS exist.

    Needles are assembled from fragments so this scanner file itself never
    contains a contiguous forbidden-endpoint literal (avoids self-matching).
    """
    _fp = "free" + "publish"
    _mass = "mass"
    needles = ["cgi-bin/" + _fp, _fp + "/submit", "cgi-bin/message/" + _mass,
               _mass + "/sendall", "cgi-bin/draft/" + "delete", "cgi-bin/message/" + _mass + "/send"]
    hits = []
    for p in Path(pkg_dir).rglob("*.py"):
        txt = p.read_text(encoding="utf-8", errors="ignore")
        for n in needles:
            if n in txt:
                hits.append({"file": str(p), "endpoint": n})
    return hits
