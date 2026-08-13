"""dev2-hotfix1 P0 tests:

- P0#3  resume MUST call verify_receipt: tamper media_manifest => media+后续失效，
        绝不 ALREADY_COMPLETE；tamper upstream final_article.md => media/gzh/wechat 全失效
- P0#1d CLI compatibility: the pipeline builds argv with the REAL sub-skill CLI
        flags, and the fake_live shims mirror those flags exactly
- P0#6  AI HOT existence is really checked (NOT_INSTALLED => live FAIL_CLOSED)
- P0#9  reinstall from the PR trees => live doctor skill verification PASS
"""
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from conftest import SKILL_ROOT
from wxgzh_pipeline import execmodel as EM
from wxgzh_pipeline import producers as PR
from wxgzh_pipeline import skill_discovery as SD
from wxgzh_pipeline.skill_discovery import InstallReceiptError
from wxgzh_pipeline.zipping import (
    PIPELINE_RELEASE_EXCLUDES, PIPELINE_RELEASE_INCLUDES, _skip)


# ---------- P0#3: tamper + resume ----------

def test_resume_tamper_media_manifest_invalidates_media_and_later(orch):
    out = orch.run("t")
    assert out["status"] == "COMPLETE"
    rd = Path(out["run_dir"])
    man = rd / "media_enrichment" / "media_manifest.json"
    man.write_bytes(man.read_bytes() + b" ")  # tamper
    res = orch.resume(out["run_id"])
    assert res["status"] != "ALREADY_COMPLETE"
    rv = res["receipt_verification"]
    assert rv["media_enrichment"]["ok"] is False
    assert res["invalidated_from"] == "media_enrichment"
    # earlier stages stay valid; the run re-executes from media onward
    assert rv["aihot"]["ok"] and rv["super_writer"]["ok"] and rv["zh_human_writing"]["ok"]
    assert res["status"] == "COMPLETE"


def test_resume_tamper_upstream_article_invalidates_media_gzh_wechat(orch):
    out = orch.run("t")
    assert out["status"] == "COMPLETE"
    rd = Path(out["run_dir"])
    wechat_receipt = rd / "wechat_draft" / "stage_receipt.json"
    mtime_before = wechat_receipt.stat().st_mtime_ns
    fa = rd / "zh_human_writing" / "final_article.md"
    fa.write_text(fa.read_text(encoding="utf-8") + "\n篡改。\n", encoding="utf-8")
    res = orch.resume(out["run_id"])
    assert res["status"] != "ALREADY_COMPLETE"
    rv = res["receipt_verification"]
    # the tampered article is zh's OUTPUT and media/gzh's bound INPUT — all FAIL:
    for s in ("zh_human_writing", "media_enrichment", "gzh_design"):
        assert rv[s]["ok"] is False, s
    # cascade: everything from zh onward (incl. wechat_draft) is invalidated and
    # RE-EXECUTED — the wechat receipt file is freshly rewritten (outputs are
    # deterministic, so compare rewrite time, not bytes).
    assert res["invalidated_from"] == "zh_human_writing"
    assert res["status"] == "COMPLETE"
    assert wechat_receipt.stat().st_mtime_ns > mtime_before


# ---------- P0#1d: real-CLI compatibility ----------

REAL_CLI = {
    "media_entry": ("run_media_enrichment.py", ["--request", "--output-dir"]),
    "media_validator": ("validate_media_manifest.py", ["--manifest", "--request", "--bindings"]),
    "gzh_entry": ("render_article.py", ["--article", "--bindings", "--output-dir", "--theme"]),
    "wechat_entry": ("publish_wechat_draft.py", ["--html", "--title", "--audit-dir", "--dry-run"]),
}


class _Ctx:
    def __init__(self, run_dir, skills_home, network_mode="fake_live"):
        self.run_dir = run_dir
        self.skills_home = skills_home
        self.network_mode = network_mode


def test_pipeline_builds_real_media_cli(tmp_path):
    ctx = _Ctx(tmp_path, tmp_path)
    sd = tmp_path / "media_enrichment"; sd.mkdir()
    args = PR._entry_args(ctx, "media_enrichment", sd, None, sd / "media_request.json")
    assert args[:2] == ["--phase", "discover"]
    assert "--request" in args and "--output-dir" in args
    v = PR._validator_args("media_enrichment", sd, sd / "media_request.json")
    assert v[0] == "--manifest" and v[2] == "--request" and v[4] == "--bindings"


def test_pipeline_builds_real_gzh_cli(tmp_path):
    ctx = _Ctx(tmp_path, tmp_path)
    sd = tmp_path / "gzh_design"; sd.mkdir()
    args = PR._entry_args(ctx, "gzh_design", sd, None, None)
    assert args[0] == "--article" and "--bindings" in args and "--output-dir" in args
    # 72E-1:handoff 无 cover 字段时行为与现状一致(--theme smartisan 收尾)
    # cover 参数追加在 --theme smartisan 之后,末尾两参数是 kicker
    assert "--theme" in args and args[args.index("--theme") + 1] == "smartisan"
    assert "--kicker" not in args
    # gzh official validator takes a POSITIONAL html path (no --html flag)
    v = PR._validator_args("gzh_design", sd, None)
    assert len(v) == 1 and v[0].endswith("final.html")


def test_pipeline_gzh_cover_handoff_wiring(tmp_path):
    """72E-1/OBS-251:handoff formatter.cover 存在时,gzh 调用携带封面四参数;
    --date 永远不传。"""
    sw = tmp_path / "super_writer"; sw.mkdir()
    (sw / "handoff.yaml").write_text("""handoff:
  schema_version: "2.1"
  formatter:
    cover:
      kicker: "实测观察"
      strike: "写作只能靠天赋？"
      tags: ["深度", "观察"]
""", encoding="utf-8")
    ctx = _Ctx(tmp_path, tmp_path)
    sd = tmp_path / "gzh_design"; sd.mkdir()
    args = PR._entry_args(ctx, "gzh_design", sd, None, None)
    # cover 参数追加在 --theme smartisan 之后,末尾两参数是 kicker
    assert "--theme" in args and args[args.index("--theme") + 1] == "smartisan"
    assert "--kicker" in args and args[args.index("--kicker") + 1] == "实测观察"
    assert "--strike" in args and args[args.index("--strike") + 1] == "写作只能靠天赋？"
    # cover 定义 {kicker, strike, tags};brand 缺省不传,走渲染默认
    assert "--brand" not in args
    assert "--tags" in args and args[args.index("--tags") + 1] == "深度,观察"
    assert "--date" not in args


def test_shims_mirror_real_cli_flags():
    home = EM.FAKE_LIVE_HOME
    shim_of = {
        "media_entry": home / "media-enrichment" / "run_media_enrichment.py",
        "media_validator": home / "media-enrichment" / "validate_media_manifest.py",
        "gzh_entry": home / "gzh-design" / "render_article.py",
        "wechat_entry": home / "gzh-design" / "publish_wechat_draft.py",
    }
    for key, (name, flags) in REAL_CLI.items():
        src = shim_of[key].read_text(encoding="utf-8")
        for flag in flags:
            assert f'"{flag}"' in src, f"shim {name} must accept {flag}"


def test_real_skills_accept_same_flags_when_available():
    """When the real sub-skills are installed locally, their sources must accept
    the exact flags the pipeline passes (skipped hermetically in CI)."""
    homes = [Path(os.environ.get("WXGZH_REAL_SKILLS_HOME", "")),
             SKILL_ROOT.parent]
    real = {
        "media_entry": "media-enrichment/scripts/run_media_enrichment.py",
        "media_validator": "media-enrichment/scripts/validate_media_manifest.py",
        "gzh_entry": "gzh-design/scripts/render_article.py",
        "wechat_entry": "gzh-design/scripts/publish_wechat_draft.py",
    }
    checked = 0
    for key, rel in real.items():
        for home in homes:
            p = home / rel if str(home) else None
            if p and p.is_file():
                src = p.read_text(encoding="utf-8", errors="replace")
                for flag in REAL_CLI[key][1]:
                    assert f'"{flag}"' in src or f"'{flag}'" in src, f"{rel} missing {flag}"
                checked += 1
                break
    if checked == 0:
        pytest.skip("no real sub-skills available in this environment")


# ---------- P0#6/#8: AI HOT real CAPABILITY check ----------

def test_aihot_bare_skill_md_is_unverified_and_fails_live(tmp_path):
    """hotfix2: a bare SKILL.md is NOT a verified capability."""
    from wxgzh_pipeline.orchestrator import Orchestrator
    reg = tmp_path / "aihot"; reg.mkdir()
    (reg / "SKILL.md").write_text("---\nname: aihot\n---\n", encoding="utf-8")  # SKILL.md only
    o = Orchestrator(project_root=tmp_path, network_mode="live", skills_home=tmp_path,
                     env={"WXGZH_AIHOT_SKILL_DIR": str(reg),
                          "WECHAT_APP_ID": "wx123456", "WECHAT_APP_SECRET": "abcdef123456"})
    ok, rep = o.doctor()
    assert rep["EXTERNAL_DEPENDENCY_AIHOT"] == "UNVERIFIED"
    assert rep["LIVE_PIPELINE_ALLOWED"] is False
    assert ok is False and rep["FAIL_CLOSED"] is True


def test_aihot_not_installed_fails_closed_in_live(tmp_path):
    from wxgzh_pipeline.orchestrator import Orchestrator
    empty = tmp_path / "no-aihot-here"; empty.mkdir()
    o = Orchestrator(project_root=tmp_path, network_mode="live", skills_home=tmp_path,
                     env={"WXGZH_AIHOT_SKILL_DIR": str(empty),
                          "WECHAT_APP_ID": "wx123456", "WECHAT_APP_SECRET": "abcdef123456"})
    ok, rep = o.doctor()
    assert rep["EXTERNAL_DEPENDENCY_AIHOT"] == "UNVERIFIED"
    assert ok is False and rep["FAIL_CLOSED"] is True


def test_aihot_valid_registration_detected(tmp_path):
    """A real registration manifest (name + output_contract + discoverable) verifies."""
    from wxgzh_pipeline.skill_discovery import check_aihot
    manifest = tmp_path / "aihot_reg.json"
    manifest.write_text(json.dumps({"name": "aihot", "identifier": "aihot",
                                    "discoverable": True,
                                    "output_contract": {"items": "array"}}), encoding="utf-8")
    res = check_aihot(tmp_path, env={"WXGZH_AIHOT_REGISTRATION": str(manifest)})
    assert res["exists"] is True and res["status"] == "INSTALLED"
    assert res["live_pipeline_allowed"] is True
    # missing output_contract => UNVERIFIED
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"name": "aihot", "discoverable": True}), encoding="utf-8")
    res2 = check_aihot(tmp_path, env={"WXGZH_AIHOT_REGISTRATION": str(bad)})
    assert res2["exists"] is False and res2["status"] == "UNVERIFIED"


# ---------- P0#9: reinstall from PR trees => doctor skill verification PASS ----------

def test_reinstall_from_pr_trees_doctor_pass(tmp_path):
    clones_dir = os.environ.get("WXGZH_SUBSKILL_CLONES", "")
    if not clones_dir or not Path(clones_dir).is_dir():
        pytest.skip("WXGZH_SUBSKILL_CLONES not set (PR trees unavailable here)")
    clones = Path(clones_dir)
    mapping = {"super-writer": "super-writer", "zh-human-writing": "zh-human-writing",
               "media-enrichment": "media-enrichment", "gzh-design-skill": "gzh-design"}
    staging = tmp_path / "skills"; staging.mkdir()
    for src_name, dst_name in mapping.items():
        shutil.copytree(clones / src_name, staging / dst_name,
                        ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
    lock = SD.load_lock(SKILL_ROOT)
    aihot_dir = staging / "aihot"; aihot_dir.mkdir()
    (aihot_dir / "SKILL.md").write_text("---\nname: aihot\n---\n", encoding="utf-8")
    (aihot_dir / "registration.json").write_text(json.dumps(
        {"name": "aihot", "identifier": "aihot", "discoverable": True,
         "output_contract": {"items": "array"}}), encoding="utf-8")
    ok, disc = SD.verify_all(staging, lock, env={"WXGZH_AIHOT_SKILL_DIR": str(aihot_dir)})
    problems = {k: v for k, v in disc.items() if not v["ok"]}
    assert ok, f"reinstalled PR trees must verify against the lock: {problems}"


# ---------- OBS-26: real Portable Installer preserves Pipeline release include ----------

WORKFLOW_REL = Path(".github/workflows/ci.yml")
WORKFLOW_SIZE = 6173
WORKFLOW_SHA256 = "751294ac42db62b6a045a5aaa298c1eca1ad527ef30ffff6bef2fceb9401375d"
LOCKED_HEADS = {
    "super-writer": "1e58d01e38346018886ab1ad6a183228263eae49",
    "zh-human-writing": "0c8962f354e9acc73f29bc57a8b328fc98695a10",
    "media-enrichment": "cedf92ca45b0cdb7e010d489e9da67dd28ef6e59",
    "gzh-design-skill": "0007d7e6a4493aab59070d9c31dcde83830302fd",
}
LOCKED_REPOS = {
    "super-writer": "https://github.com/Amer-CN/super-writer.git",
    "zh-human-writing": "https://github.com/Amer-CN/zh-human-writing.git",
    "media-enrichment": "https://github.com/Amer-CN/media-enrichment.git",
    "gzh-design-skill": "https://github.com/Amer-CN/gzh-design-skill.git",
}


def _portable_skill_sources(tmp_path: Path) -> Path:
    clones = tmp_path / "locked-clones"
    clones.mkdir()
    explicit = Path(os.environ["WXGZH_SUBSKILL_CLONES"]) if os.environ.get(
        "WXGZH_SUBSKILL_CLONES") else None
    preexisting = {
        "super-writer": os.environ.get("WXGZH_REAL_SUPER_WRITER_ROOT"),
        "media-enrichment": os.environ.get("WXGZH_FIXED_MEDIA_ROOT"),
    }
    for source_name, commit in LOCKED_HEADS.items():
        install_name = "gzh-design" if source_name == "gzh-design-skill" else source_name
        dst = clones / install_name
        src = ((explicit / source_name) if explicit else None) or preexisting.get(source_name)
        if src and Path(src).is_dir():
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            subprocess.run(["git", "clone", "--quiet", LOCKED_REPOS[source_name], str(dst)], check=True)
        subprocess.run(["git", "-C", str(dst), "checkout", "--quiet", commit], check=True)
    return clones


def _count_release_tree(root: Path) -> tuple[int, int]:
    files = [p for p in root.rglob("*")
             if p.is_file() and "__pycache__" not in p.parts and p.suffix.lower() != ".pyc"]
    dirs = [p for p in root.rglob("*") if p.is_dir() and "__pycache__" not in p.parts]
    return len(files), len(dirs)


def _load_installer_module():
    path = SKILL_ROOT / "scripts" / "install.py"
    spec = importlib.util.spec_from_file_location("hotfix7r4_installer", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_portable_installer_preserves_pipeline_release_include(tmp_path):
    clones = _portable_skill_sources(tmp_path)
    for lock_name, meta in SD.load_lock(SKILL_ROOT)["skills"].items():
        if meta.get("kind") == "agent_invoked_skill":
            continue
        source = clones / lock_name
        actual = subprocess.run(["git", "-C", str(source), "rev-parse", "HEAD"],
                                capture_output=True, text=True, check=True).stdout.strip()
        assert actual == meta["full_commit_sha"]

    clean_source = tmp_path / "clean-pipeline-source"
    tracked = subprocess.run(["git", "-C", str(SKILL_ROOT), "ls-files", "-z"],
                             capture_output=True, check=True).stdout.split(b"\0")
    for raw in tracked:
        if not raw:
            continue
        rel = Path(os.fsdecode(raw))
        source = SKILL_ROOT / rel
        if source.is_file() and not _skip(
                rel, PIPELINE_RELEASE_INCLUDES, PIPELINE_RELEASE_EXCLUDES):
            destination = clean_source / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
    out_dir = tmp_path / "out"
    staging = tmp_path / "build-staging"
    build = subprocess.run([
        sys.executable, str(clean_source / "scripts/build_portable_bundle.py"),
        "--out", str(out_dir), "--skills-home", str(clones), "--staging", str(staging),
    ], capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert build.returncode == 0, build.stdout + build.stderr
    extract = tmp_path / "bundle-extract"
    with zipfile.ZipFile(Path(json.loads(build.stdout)["bundle_zip"])) as archive:
        archive.extractall(extract)
    bundle = extract / "portable-bundle"
    target = tmp_path / "installed-skills"
    install = subprocess.run([
        sys.executable, str(bundle / "installer/install.py"), "--target", str(target),
    ], capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert install.stdout.strip(), (
        f"installer emitted no JSON (exit={install.returncode})\nstdout={install.stdout}\nstderr={install.stderr}")
    result = json.loads(install.stdout)
    assert install.returncode == 0, install.stdout + install.stderr
    assert result["ok"] is True

    installed_pipeline = target / "wxgzh-pipeline"
    workflow = installed_pipeline / WORKFLOW_REL
    data = workflow.read_bytes()
    assert data == (bundle / "wxgzh-pipeline" / WORKFLOW_REL).read_bytes()
    assert data == (clean_source / WORKFLOW_REL).read_bytes()
    assert data == (SKILL_ROOT / WORKFLOW_REL).read_bytes()
    assert len(data) == WORKFLOW_SIZE
    assert hashlib.sha256(data).hexdigest() == WORKFLOW_SHA256
    assert _count_release_tree(installed_pipeline)[0] == 130
    assert _count_release_tree(target) == (662, 101)
    assert len(list((target / ".install-receipts").glob("*.json"))) == 4
    for name in ("super-writer", "zh-human-writing", "media-enrichment", "gzh-design"):
        assert not (target / name / ".github").exists()

    shipped_test = subprocess.run([
        sys.executable, "-m", "pytest",
        "tests/test_hotfix7_live_handshake.py::test_integration_workflow_fails_closed_after_tee",
        "-q", "-o", "addopts=",
    ], cwd=installed_pipeline, capture_output=True, text=True,
       encoding="utf-8", errors="replace")
    assert shipped_test.returncode == 0, shipped_test.stdout + shipped_test.stderr

    installer = _load_installer_module()
    missing = tmp_path / "negative-missing"
    shutil.copytree(installed_pipeline, missing,
                    ignore=shutil.ignore_patterns(".github", "__pycache__", "*.pyc"))
    with pytest.raises(InstallReceiptError, match="release workflow missing"):
        installer.verify_pipeline_release_include(installed_pipeline, missing)
    tampered = tmp_path / "negative-tampered"
    shutil.copytree(installed_pipeline, tampered,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (tampered / WORKFLOW_REL).write_bytes(data + b"\n# tampered\n")
    with pytest.raises(InstallReceiptError, match="release workflow hash mismatch"):
        installer.verify_pipeline_release_include(installed_pipeline, tampered)
