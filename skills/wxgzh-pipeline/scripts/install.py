#!/usr/bin/env python3
"""Transactional installer for wxgzh-pipeline and every locked file skill.

The installer is fail-closed and side-effect-free until every source, commit,
tree, repository, runtime hash, manifest member and staged receipt verifies.
It never runs an article, uploads an image, or touches WeChat drafts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve()


def _locate_skill_root() -> Path:
    for candidate in (
        _HERE.parents[1],
        _HERE.parents[1] / "wxgzh-pipeline",
        _HERE.parents[1].parent / "wxgzh-pipeline",
    ):
        if (candidate / "wxgzh_pipeline" / "__init__.py").is_file():
            return candidate
    return _HERE.parents[1]


SKILL_ROOT = _locate_skill_root()
sys.path.insert(0, str(SKILL_ROOT))
from wxgzh_pipeline import __version__  # noqa: E402
from wxgzh_pipeline import paths as P  # noqa: E402
from wxgzh_pipeline import skill_discovery as SD  # noqa: E402
from wxgzh_pipeline.skill_discovery import InstallReceiptError  # noqa: E402
from wxgzh_pipeline.zipping import PIPELINE_RELEASE_INCLUDES, copy_tree  # noqa: E402


def verify_pipeline_release_include(source_pipeline: Path, installed_pipeline: Path) -> dict:
    rel = Path(PIPELINE_RELEASE_INCLUDES[0])
    source = Path(source_pipeline) / rel
    installed = Path(installed_pipeline) / rel
    if not source.is_file() or not installed.is_file():
        raise InstallReceiptError("wxgzh-pipeline: release workflow missing")
    source_bytes = source.read_bytes()
    installed_bytes = installed.read_bytes()
    if installed_bytes != source_bytes:
        raise InstallReceiptError("wxgzh-pipeline: release workflow hash mismatch")
    return {"path": rel.as_posix(), "size": len(installed_bytes),
            "sha256": hashlib.sha256(installed_bytes).hexdigest()}


def _find_source() -> tuple[Path, Path | None, Path | None]:
    for bundle in {SKILL_ROOT.parent, _HERE.parents[1].parent, _HERE.parents[1]}:
        if (bundle / "locked-skills").is_dir() and (bundle / "wxgzh-pipeline").is_dir():
            return bundle / "wxgzh-pipeline", bundle / "locked-skills", bundle
    return SKILL_ROOT, None, None


# 77Z/OBS-374:装机同步完成标记——装机侧 pipeline skill root 落 .installed-from,
# 内容口径(内容最新性)供 scripts/version_check.py 优先读取(日期口径降级为
# detail 展示)。路径与 install() 既有 installed 目标推导同源(target/wxgzh-pipeline)。
INSTALLED_FROM_FILENAME = ".installed-from"


# 77AE/OBS-382:installer 同步时保留的装机侧生产数据文件(相对 wxgzh-pipeline skill 根)。
# - audit/quality/title-hits.md:只追加、RUN_ID 键(档 77AA 纪律)。
# - audit/quality/ai-tone-calibration.jsonl:append-only(整行精确并集，无原地改语义)。
PRESERVED_PRODUCTION_DATA = (
    "audit/quality/title-hits.md",
    "audit/quality/ai-tone-calibration.jsonl",
)


def _production_run_id(row_line: str) -> str:
    """title-hits 数据行按第二个 `|` 单元格(RUN_ID)取键。"""
    cells = [cell.strip() for cell in row_line.strip().strip("|").split("|")]
    return cells[1] if len(cells) >= 2 else ""


def _split_ledger_table(text: str):
    """拆分台账 ledger 表为(前缀行, 表头行, 分隔行, 数据行, 后缀行)；找不到返回 None。"""
    lines = text.splitlines()
    header_idx = None
    for idx, line in enumerate(lines):
        if line.strip().startswith("|") and "RUN_ID" in line:
            header_idx = idx
            break
    if header_idx is None or header_idx + 1 >= len(lines):
        return None
    sep_line = lines[header_idx + 1]
    if "---" not in sep_line:
        return None
    data_start = header_idx + 2
    data_end = data_start
    while data_end < len(lines) and lines[data_end].strip().startswith("|"):
        data_end += 1
    return (
        lines[:header_idx],
        lines[header_idx],
        sep_line,
        lines[data_start:data_end],
        lines[data_end:],
    )


def _merge_title_hits_text(new_text: str, backup_text: str) -> str:
    """title-hits 合并：new 顺序为底，new 赢同 RUN_ID，backup 独有行按 backup 顺序追加。"""
    new_parts = _split_ledger_table(new_text)
    backup_parts = _split_ledger_table(backup_text)
    if new_parts is None or backup_parts is None:
        # 非台账形态回退：整行精确并集(new 顺序 + backup 独有行)，双向不丢。
        new_lines = new_text.splitlines()
        backup_lines = backup_text.splitlines()
        seen = set(new_lines)
        merged = list(new_lines)
        for line in backup_lines:
            if line not in seen:
                seen.add(line)
                merged.append(line)
        result = "\n".join(merged)
        if new_text.endswith("\n") or backup_text.endswith("\n"):
            result += "\n" if merged else ""
        return result
    prefix, header, sep, new_rows, suffix = new_parts
    _, _, _, backup_rows, _ = backup_parts
    new_by_key: dict[str, str] = {}
    new_order: list[str] = []
    for row in new_rows:
        key = _production_run_id(row)
        if key and key not in new_by_key:
            new_order.append(key)
        if key:
            new_by_key[key] = row
        elif row not in new_by_key.values():
            # 无键行(如空行变体)按原文保留，避免丢行。
            new_order.append(row)
            new_by_key[row] = row
    merged_rows = [new_by_key[key] for key in new_order]
    for row in backup_rows:
        key = _production_run_id(row)
        if key:
            if key not in new_by_key:
                merged_rows.append(row)
        elif row not in set(merged_rows):
            merged_rows.append(row)
    result_lines = [*prefix, header, sep, *merged_rows, *suffix]
    result = "\n".join(result_lines)
    if new_text.endswith("\n"):
        result += "\n"
    return result


def _merge_jsonl_text(new_text: str, backup_text: str) -> str:
    """jsonl 合并：整行精确并集(backup 顺序 + new 独有行追加)。"""
    backup_lines = [line for line in backup_text.splitlines() if line != ""]
    new_lines = [line for line in new_text.splitlines() if line != ""]
    seen: set[str] = set()
    merged: list[str] = []
    for line in backup_lines:
        if line not in seen:
            seen.add(line)
            merged.append(line)
    for line in new_lines:
        if line not in seen:
            seen.add(line)
            merged.append(line)
    if not merged:
        return ""
    return "\n".join(merged) + "\n"


def _merge_production_file(backup_path, new_path) -> str:
    """合并单个生产数据文件(backup=装机旧版，new=仓侧新版)，结果落盘到 new_path。

    返回动作词：merged/kept-new/restored-backup/identical。
    """
    backup_path = Path(backup_path)
    new_path = Path(new_path)
    backup_exists = backup_path.is_file()
    new_exists = new_path.is_file()
    if not backup_exists and not new_exists:
        return "kept-new"
    if not backup_exists:
        return "kept-new"
    if not new_exists:
        new_path.parent.mkdir(parents=True, exist_ok=True)
        new_path.write_bytes(backup_path.read_bytes())
        return "restored-backup"
    backup_bytes = backup_path.read_bytes()
    new_bytes = new_path.read_bytes()
    if backup_bytes == new_bytes:
        return "identical"
    suffix = new_path.suffix.lower() or backup_path.suffix.lower()
    if suffix == ".jsonl":
        merged_text = _merge_jsonl_text(
            new_bytes.decode("utf-8"), backup_bytes.decode("utf-8"))
    else:
        merged_text = _merge_title_hits_text(
            new_bytes.decode("utf-8"), backup_bytes.decode("utf-8"))
    merged_bytes = merged_text.encode("utf-8")
    if merged_bytes == new_bytes:
        return "identical"
    new_path.write_bytes(merged_bytes)
    return "merged"


def _resolve_source_head(src: Path) -> tuple[str, str | None]:
    """源仓 HEAD sha + HEAD 可达的最新 v 前缀 tag(无则 None)。_git 已有可复用。"""
    git_root = Path(src)
    cur = Path(src).resolve()
    while not (cur / ".git").exists():
        if cur.parent == cur:
            break
        cur = cur.parent
    if (cur / ".git").exists():
        git_root = cur
    head = _git(git_root, "rev-parse", "HEAD")
    tag = None
    try:
        # HEAD 可达的最新 v-tag;git describe 无 tag 时返回非零,tag=None 即可。
        described = _git(git_root, "describe", "--tags", "--match", "v*",
                         "--abbrev=0", "HEAD")
        if described:
            tag = described
    except InstallReceiptError:
        tag = None
    return head or "", tag


def _write_installed_from(target: Path, src_pipeline: Path) -> Path | None:
    """77Z/OBS-374:写 .installed-from 到装机侧 pipeline skill root(单行 JSON)。

    装机同步完成后调用;源仓无 .git(纯 bundle 装机)时 head 为空——标记仍写
    (source_commit="" 表示来源不可考,version_check 侧视为标记缺失回退日期口径)。
    """
    try:
        head, tag = _resolve_source_head(src_pipeline)
        marker = {"source_commit": head,
                  "resolved_tag": tag,
                  "recorded_at": datetime.now(timezone.utc)
                  .replace(microsecond=0).isoformat().replace("+00:00", "Z")}
        path = Path(target) / "wxgzh-pipeline" / INSTALLED_FROM_FILENAME
        path.write_text(json.dumps(marker, ensure_ascii=False, separators=(",", ":")),
                        encoding="utf-8")
        return path
    except (InstallReceiptError, OSError, ValueError):
        return None


def _git(src: Path, *args: str) -> str | None:
    if not (Path(src) / ".git").exists():
        return None
    result = subprocess.run(
        ["git", "-C", str(src), *args], capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise InstallReceiptError(
            f"git {' '.join(args)} failed for {src}: "
            f"{(result.stderr or result.stdout).strip()}")
    value = result.stdout.strip()
    if not value:
        raise InstallReceiptError(
            f"git {' '.join(args)} returned no value for {src}")
    return value


def _norm_repo_url(url: str | None) -> str | None:
    if not url:
        return url
    normalized = url.strip()
    if normalized.endswith(".git"):
        normalized = normalized[:-4]
    if normalized.startswith("git@github.com:"):
        normalized = "https://github.com/" + normalized[len("git@github.com:"):]
    return normalized.rstrip("/")


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest_index(bundle: Path) -> dict[str, str]:
    manifest_path = bundle / "MANIFEST.json"
    if not manifest_path.is_file():
        raise InstallReceiptError("bundle MANIFEST.json missing")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return {item["path"]: item["sha256"] for item in manifest["files"]}
    except (ValueError, KeyError, TypeError) as exc:
        raise InstallReceiptError(f"invalid bundle MANIFEST.json: {exc}") from exc


def _validate_bundle_set(bundle: Path, expected_skills: set[str]) -> None:
    locked_dir = bundle / "locked-skills"
    actual_skills = {
        path.name for path in locked_dir.iterdir() if path.is_dir()
    } if locked_dir.is_dir() else set()
    if actual_skills != expected_skills:
        raise InstallReceiptError(
            f"bundle locked skill set mismatch: expected={sorted(expected_skills)} "
            f"actual={sorted(actual_skills)}")

    manifest_index = _manifest_index(bundle)
    proof_path = bundle / "source-proofs.json"
    recorded_proof_sha = manifest_index.get("source-proofs.json")
    if (not proof_path.is_file() or not recorded_proof_sha
            or _file_sha256(proof_path) != recorded_proof_sha):
        raise InstallReceiptError(
            "source-proofs.json missing or not hash-bound by bundle MANIFEST")
    try:
        proofs = json.loads(proof_path.read_text(encoding="utf-8"))
        proof_skills = set(proofs["skills"])
    except (ValueError, KeyError, TypeError) as exc:
        raise InstallReceiptError(f"invalid source-proofs.json: {exc}") from exc
    if proof_skills != expected_skills:
        raise InstallReceiptError(
            f"source proof skill set mismatch: expected={sorted(expected_skills)} "
            f"actual={sorted(proof_skills)}")

    for skill_name in sorted(expected_skills):
        prefix = f"locked-skills/{skill_name}/"
        listed = {path for path in manifest_index if path.startswith(prefix)}
        on_disk = {
            f"{prefix}{path.relative_to(locked_dir / skill_name).as_posix()}"
            for path in (locked_dir / skill_name).rglob("*") if path.is_file()
        }
        if not listed or listed != on_disk:
            raise InstallReceiptError(
                f"{skill_name}: MANIFEST file set mismatch; "
                f"missing={sorted(on_disk - listed)[:5]} extra={sorted(listed - on_disk)[:5]}")
        for relative_path in sorted(listed):
            path = bundle / relative_path
            if _file_sha256(path) != manifest_index[relative_path]:
                raise InstallReceiptError(
                    f"{skill_name}: {relative_path} does not match MANIFEST sha256")


def _bundle_source_proof(bundle: Path, skill_name: str, src: Path) -> dict:
    expected = {
        path.name for path in (bundle / "locked-skills").iterdir() if path.is_dir()
    }
    _validate_bundle_set(bundle, expected)
    proofs = json.loads((bundle / "source-proofs.json").read_text(encoding="utf-8"))
    proof = proofs["skills"].get(skill_name)
    if not isinstance(proof, dict):
        raise InstallReceiptError(f"{skill_name}: source proof missing")
    return proof


def _resolve_source_proof(
    bundle: Path | None, skill_name: str, src: Path, locked: dict,
) -> tuple[str, str, str]:
    git_root = Path(src)
    if (Path(src) / ".git").exists():
        git_root = Path(src)
    else:
        # 76K/合集仓:src 是合集仓内的子目录(skills/<name>),向上找 .git 根;
        # 树 sha = 根仓库对子目录的树(git rev-parse HEAD:<path>),commit 取根 HEAD。
        cur = Path(src).resolve()
        while not (cur / ".git").exists():
            if cur.parent == cur:
                break
            cur = cur.parent
        if (cur / ".git").exists():
            git_root = cur
    if git_root != Path(src) or (Path(src) / ".git").exists():
        actual = _git(git_root, "rev-parse", "HEAD")
        sub = ""
        if git_root != Path(src).resolve():
            sub = str(Path(src).resolve().relative_to(git_root)).replace("\\", "/")
        tree = (_git(git_root, "rev-parse", f"HEAD:{sub}") if sub
                else _git(git_root, "rev-parse", "HEAD^{tree}"))
        remote = _norm_repo_url(_git(git_root, "config", "--get", "remote.origin.url"))
        if not remote:
            raise InstallReceiptError(
                f"{skill_name}: git remote.origin.url missing — FAIL_CLOSED")
        return remote, actual or "", tree or ""
    if bundle is not None:
        proof = _bundle_source_proof(bundle, skill_name, src)
        return (
            _norm_repo_url(proof.get("repository_url")) or "",
            proof.get("full_commit_sha") or "",
            proof.get("source_tree_sha") or "",
        )
    raise InstallReceiptError(
        f"{skill_name}: no verifiable source (git checkout or manifest-bound bundle)")


def _resolve_sources(
    src_pipeline: Path,
    locked_dir: Path | None,
    bundle: Path | None,
    lock_skills: dict[str, dict],
    skills_src: Path | None,
) -> list[tuple[str, Path, dict | None]]:
    expected_skills = set(lock_skills)
    if bundle is not None:
        _validate_bundle_set(bundle, expected_skills)
    sources: list[tuple[str, Path, dict | None]] = [
        ("wxgzh-pipeline", src_pipeline, None),
    ]
    if skills_src is not None:
        for name in sorted(expected_skills):
            meta = lock_skills[name]
            repo_name = (_norm_repo_url(meta.get("repository_url")) or "").rsplit("/", 1)[-1]
            # 76K/合集仓:lock entry 的 path(如 skills/super-writer)优先;
            # 兼容旧 skills_src/name 与 skills_src/repo_name 布局。
            candidates = [
                Path(skills_src) / meta["path"] if meta.get("path") else None,
                Path(skills_src) / name,
                Path(skills_src) / repo_name,
                (Path(skills_src) / repo_name / meta["path"])
                if meta.get("path") else None,
            ]
            candidates = [c for c in candidates if c is not None]
            source = next((path for path in candidates if path.is_dir()), None)
            if source is None:
                raise InstallReceiptError(f"{name}: source not found under {skills_src}")
            sources.append((name, source, meta))
    elif locked_dir is not None:
        actual = {path.name for path in locked_dir.iterdir() if path.is_dir()}
        if actual != expected_skills:
            raise InstallReceiptError(
                f"bundle locked skill set mismatch: expected={sorted(expected_skills)} "
                f"actual={sorted(actual)}")
        sources.extend((name, locked_dir / name, lock_skills[name])
                       for name in sorted(expected_skills))
    else:
        raise InstallReceiptError("locked skill sources unavailable")
    if {name for name, _, meta in sources if meta is not None} != expected_skills:
        raise InstallReceiptError("resolved source set does not equal skills.lock")
    return sources


def _rollback_switch(
    target: Path,
    switched: list[str],
    backups: dict[str, Path],
    receipts_backup: Path | None,
) -> None:
    # Restore both successfully switched destinations and the current destination
    # whose OLD directory was backed up but whose NEW move may have failed before
    # it could be appended to ``switched``.
    restore_names = list(dict.fromkeys([*reversed(switched), *reversed(backups)]))
    for name in restore_names:
        destination = target / name
        if destination.exists():
            shutil.rmtree(destination)
        backup = backups.get(name)
        if backup and backup.exists():
            shutil.move(str(backup), str(destination))
    receipt_dir = target / SD.INSTALL_RECEIPTS_DIRNAME
    if receipt_dir.exists():
        shutil.rmtree(receipt_dir)
    if receipts_backup and receipts_backup.exists():
        shutil.move(str(receipts_backup), str(receipt_dir))


def install(
    target_skills_home: Path,
    dry_run: bool = True,
    skills_src: Path | None = None,
) -> dict:
    src_pipeline, locked_dir, bundle = _find_source()
    target = Path(target_skills_home)
    lock = SD.load_lock(src_pipeline)
    lock_skills = {
        name: meta for name, meta in lock.get("skills", {}).items()
        if meta.get("kind") != "agent_invoked_skill"
    }
    expected_skills = set(lock_skills)
    plan: list[dict] = []
    try:
        sources = _resolve_sources(
            src_pipeline, locked_dir, bundle, lock_skills,
            Path(skills_src) if skills_src is not None else None,
        )
        source_proofs: dict[str, tuple[str, str, str]] = {}
        pipeline_source = next(source for name, source, _ in sources if name == "wxgzh-pipeline")
        for name, source, meta in sources:
            action = {
                "skill": name, "src": str(source), "dst": str(target / name),
                "installed": False, "source_present": source.is_dir(),
                "commit_match": None, "source_tree_match": None,
                "repository_match": None, "runtime_root_match": None,
                "runtime_manifest_match": None, "receipt_written": False,
                "verify_all_ok": False, "install_receipt": None,
            }
            plan.append(action)
            if not source.is_dir():
                raise InstallReceiptError(f"{name}: source directory missing")
            if meta is not None:
                repository, commit, tree = _resolve_source_proof(bundle, name, source, meta)
                source_proofs[name] = (repository, commit, tree)
                action.update({
                    "commit_match": commit == meta.get("full_commit_sha"),
                    "source_tree_match": tree == meta.get("source_tree_sha"),
                    "repository_match": repository == _norm_repo_url(meta.get("repository_url")),
                })
                if not all((action["commit_match"], action["source_tree_match"],
                            action["repository_match"])):
                    raise InstallReceiptError(f"{name}: source proof does not match skills.lock")
        if dry_run:
            return {
                "ok": True, "dry_run": True, "target_skills_home": str(target),
                "env_untouched": True, "plan": plan,
                "hash_verification": "run without --dry-run to verify",
                "note": "installer never runs an article / uploads images / creates a draft",
            }

        transaction = target.parent / (
            f".{target.name}.hotfix5-install-{os.getpid()}-"
            f"{datetime.now().strftime('%Y%m%dT%H%M%S%f')}")
        staging_home = transaction / "staging"
        backups_dir = transaction / "backups"
        staging_home.mkdir(parents=True)
        backups_dir.mkdir(parents=True)
        try:
            for name, source, _ in sources:
                includes = PIPELINE_RELEASE_INCLUDES if name == "wxgzh-pipeline" else ()
                copy_tree(source, staging_home / name, include_paths=includes)
            pipeline_workflow = Path(PIPELINE_RELEASE_INCLUDES[0])
            staged_workflow = staging_home / "wxgzh-pipeline" / pipeline_workflow
            source_workflow = pipeline_source / pipeline_workflow
            verify_pipeline_release_include(pipeline_source, staging_home / "wxgzh-pipeline")

            for action in plan:
                name = action["skill"]
                meta = lock_skills.get(name)
                if meta is None:
                    action["installed"] = True
                    continue
                repository, commit, tree = source_proofs[name]
                SD.write_install_receipt(
                    staging_home, name,
                    repository_url=repository,
                    actual_commit=commit,
                    expected_commit=meta.get("full_commit_sha"),
                    expected_repository_url=_norm_repo_url(meta.get("repository_url")),
                    expected_root_sha256=meta.get("skill_root_sha256"),
                    expected_manifest_sha256=meta.get("runtime_manifest_sha256"),
                    source_tree_sha=tree,
                    expected_source_tree_sha=meta.get("source_tree_sha"),
                    installer_version=f"wxgzh-pipeline-installer/{__version__}",
                )
                action["runtime_root_match"] = True
                action["runtime_manifest_match"] = True
                action["receipt_written"] = True
                action["install_receipt"] = str(
                    SD.install_receipt_path(target, name))

            runtime_lock = {"lock_version": lock.get("lock_version"), "skills": lock_skills}
            verify_ok, verify = SD.verify_all(staging_home, runtime_lock)
            if set(verify) != expected_skills or not verify_ok or not all(
                verify[name].get("ok") for name in expected_skills
            ):
                raise InstallReceiptError(
                    f"staging verify_all failed for complete lock set: {verify}")

            target.mkdir(parents=True, exist_ok=True)
            switched: list[str] = []
            backups: dict[str, Path] = {}
            receipt_dir = target / SD.INSTALL_RECEIPTS_DIRNAME
            receipts_backup = None
            try:
                if receipt_dir.exists():
                    receipts_backup = backups_dir / SD.INSTALL_RECEIPTS_DIRNAME
                    shutil.move(str(receipt_dir), str(receipts_backup))
                for name, _, _ in sources:
                    destination = target / name
                    if destination.exists():
                        backup = backups_dir / name
                        shutil.move(str(destination), str(backup))
                        backups[name] = backup
                    shutil.move(str(staging_home / name), str(destination))
                    switched.append(name)
                shutil.move(
                    str(staging_home / SD.INSTALL_RECEIPTS_DIRNAME),
                    str(receipt_dir),
                )
            except Exception:
                _rollback_switch(target, switched, backups, receipts_backup)
                raise

            final_lock = {"lock_version": lock.get("lock_version"), "skills": lock_skills}
            final_ok, final_verify = SD.verify_all(target, final_lock)
            pipeline_release_include = verify_pipeline_release_include(
                pipeline_source, target / "wxgzh-pipeline")
            if not final_ok or set(final_verify) != expected_skills:
                _rollback_switch(target, switched, backups, receipts_backup)
                raise InstallReceiptError("post-switch verify_all failed; rolled back")
            required_action_gates = (
                "source_present", "commit_match", "source_tree_match",
                "repository_match", "runtime_root_match",
                "runtime_manifest_match", "receipt_written", "verify_all_ok",
            )
            for action in plan:
                if action["skill"] in expected_skills:
                    action["verify_all_ok"] = bool(
                        final_verify[action["skill"]].get("ok"))
                    action["installed"] = all(
                        action.get(field) is True for field in required_action_gates)
            complete_lock_ok = all(
                action.get("installed") is True
                for action in plan if action["skill"] in expected_skills
            )
            if not complete_lock_ok:
                _rollback_switch(target, switched, backups, receipts_backup)
                raise InstallReceiptError(
                    "post-switch complete lock action gates failed; rolled back")
            # 77AE/OBS-382:final verify 已在合并前跑过(干净树才能过)；此处合并装机侧
            # 生产数据(backup)与仓侧新版(target)，双向不丢；doctor 面天然排除 audit。
            production_data_preserved: dict[str, str] = {}
            if backups.get("wxgzh-pipeline") is not None:
                backup_root = backups["wxgzh-pipeline"]
                for rel in PRESERVED_PRODUCTION_DATA:
                    action_word = _merge_production_file(
                        backup_root / rel, target / "wxgzh-pipeline" / rel)
                    production_data_preserved[rel] = action_word
            # 77Z/OBS-374:装机同步完成处落 installed-from 标记(内容口径)。
            _write_installed_from(target, pipeline_source)
            return {
                "ok": True, "dry_run": False, "target_skills_home": str(target),
                "env_untouched": True, "plan": plan,
                "hash_verification": {
                    name: final_verify[name].get("ok") for name in sorted(expected_skills)
                },
                "pipeline_release_include": pipeline_release_include,
                "production_data_preserved": production_data_preserved,
                "note": "installer never runs an article / uploads images / creates a draft",
            }
        finally:
            if transaction.exists():
                shutil.rmtree(transaction)
    except (InstallReceiptError, OSError, ValueError, KeyError, TypeError) as exc:
        if not plan:
            plan = [{
                "skill": name, "installed": False, "receipt_written": False,
                "error": str(exc),
            } for name in sorted(expected_skills)]
        for action in plan:
            if not action.get("installed"):
                action.setdefault("error", str(exc))
        return {
            "ok": False, "dry_run": dry_run, "target_skills_home": str(target),
            "env_untouched": True, "plan": plan, "error": str(exc),
            "hash_verification": {},
            "note": "installer never runs an article / uploads images / creates a draft",
        }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", default=None)
    parser.add_argument("--project-root", default=None)
    parser.add_argument("--skills-src", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if args.target:
        target = Path(args.target)
    else:
        project_root = P.resolve_project_root(args.project_root)
        target = P.skills_home(project_root)
    report = install(
        target, dry_run=args.dry_run,
        skills_src=Path(args.skills_src) if args.skills_src else None,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
