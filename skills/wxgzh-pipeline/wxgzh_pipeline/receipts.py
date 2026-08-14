"""Stage execution receipts. A stage with no valid receipt is treated as NOT
executed (spec section 9). Receipts are the durable proof — not chat claims.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .state import atomic_write_json, read_json, sha256_file

REQUIRED_FIELDS = [
    "stage", "skill_name", "skill_dir", "skill_version", "skill_root_sha256",
    "invoked_entrypoint", "entrypoint_path", "entrypoint_sha256",
    "input_files", "input_hashes", "output_files",
    "output_hashes", "validator_path", "validator_sha256", "validator_exit_code",
    "official_validator", "official_validators", "network_mode",
    "started_at", "ended_at", "elapsed_seconds", "side_effects",
]

# fields every official-validator record must carry (P0#1)
OFFICIAL_VALIDATOR_FIELDS = ["path", "sha256", "command", "exit_code",
                             "stdout_sha256", "stderr_sha256"]


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def hash_files(paths: list[Path]) -> dict:
    out = {}
    for p in paths:
        p = Path(p)
        if p.is_file():
            out[p.name] = sha256_file(p)
    return out


def hash_files_by_path(paths: list[Path]) -> dict:
    """Key by FULL path string — upstream inputs live in different stage dirs,
    and a missing input must be representable (value None => recorded missing)."""
    out = {}
    for p in paths:
        p = Path(p)
        out[str(p)] = sha256_file(p) if p.is_file() else None
    return out


def build_receipt(*, skill_name, skill_dir, skill_version, skill_root_sha256,
                  invoked_entrypoint, input_files, output_files,
                  validator_path, validator_sha256, validator_exit_code,
                  started_at, ended_at, side_effects=None,
                  entrypoint_path=None, entrypoint_sha256=None,
                  official_validator=None, official_validators=None,
                  network_mode=None, stage=None, wall_seconds=None) -> dict:
    inp = [str(p) for p in input_files]
    out = [str(p) for p in output_files]
    try:
        elapsed = (datetime.strptime(ended_at, "%Y-%m-%dT%H:%M:%SZ")
                   - datetime.strptime(started_at, "%Y-%m-%dT%H:%M:%SZ")).total_seconds()
    except Exception:
        elapsed = 0.0
    return {
        "stage": stage,
        "skill_name": skill_name, "skill_dir": str(skill_dir),
        "skill_version": skill_version, "skill_root_sha256": skill_root_sha256,
        "invoked_entrypoint": invoked_entrypoint,
        "entrypoint_path": entrypoint_path, "entrypoint_sha256": entrypoint_sha256,
        "input_files": inp, "input_hashes": hash_files_by_path(input_files),
        "output_files": out, "output_hashes": hash_files(output_files),
        "validator_path": validator_path, "validator_sha256": validator_sha256,
        "validator_exit_code": int(validator_exit_code),
        "official_validator": official_validator,
        "official_validators": official_validators or [],
        "network_mode": network_mode,
        "started_at": started_at, "ended_at": ended_at,
        "elapsed_seconds": round(elapsed, 3),
        "validation_seconds": round(elapsed, 3),
        "wall_seconds": round(wall_seconds, 3) if wall_seconds is not None else None,
        "side_effects": side_effects or [],
    }


def receipt_path(run_dir: Path, stage: str) -> Path:
    return Path(run_dir) / stage / "stage_receipt.json"


def write_receipt(run_dir: Path, stage: str, receipt: dict) -> Path:
    p = receipt_path(run_dir, stage)
    atomic_write_json(p, receipt)
    return p


def validate_receipt(receipt: dict) -> list[str]:
    """Structural validation (P0#1). Empty objects, deleted fields, and
    inconsistent hash coverage are all failures."""
    if not isinstance(receipt, dict) or not receipt:
        return ["receipt is empty or not an object"]
    errs = [f"missing field: {f}" for f in REQUIRED_FIELDS if f not in receipt]
    if errs:
        return errs
    if receipt.get("validator_exit_code", 1) != 0:
        errs.append(f"validator_exit_code != 0 ({receipt.get('validator_exit_code')})")
    # input_files set must EXACTLY equal input_hashes key set
    in_files = set(receipt.get("input_files") or [])
    in_keys = set((receipt.get("input_hashes") or {}).keys())
    if in_files != in_keys:
        errs.append(f"input_files/input_hashes mismatch: only_files={sorted(in_files - in_keys)[:3]} "
                    f"only_hashes={sorted(in_keys - in_files)[:3]}")
    # output_files (by name) must EXACTLY equal output_hashes key set
    out_names = {Path(p).name for p in (receipt.get("output_files") or [])}
    out_keys = set((receipt.get("output_hashes") or {}).keys())
    if out_names != out_keys:
        errs.append(f"output_files/output_hashes mismatch: only_files={sorted(out_names - out_keys)[:3]} "
                    f"only_hashes={sorted(out_keys - out_names)[:3]}")
    # every official validator record must be complete + exit 0
    officials = list(receipt.get("official_validators") or [])
    if receipt.get("official_validator"):
        officials.append(receipt["official_validator"])
    # 档72B-2 OBS-225:退出码可接受性走 execmodel 单一真源(R106),
    # 不在此处再写一份判断;exit-1 警告的 receipt 是有效 receipt。
    from .execmodel import validator_exit_acceptable  # 函数内 import,防循环
    for ov in officials:
        missing = [f for f in OFFICIAL_VALIDATOR_FIELDS if not ov.get(f) and ov.get(f) != 0]
        if missing:
            errs.append(f"official validator record incomplete: missing {missing}")
        name = Path(ov.get("path") or "").name
        if not validator_exit_acceptable(name, ov.get("exit_code")):
            errs.append(f"official validator exit_code != 0 ({ov.get('exit_code')})")
    return errs


def load_receipt(run_dir: Path, stage: str) -> dict | None:
    p = receipt_path(run_dir, stage)
    if not p.is_file():
        return None
    return read_json(p)


def receipt_valid(run_dir: Path, stage: str) -> bool:
    r = load_receipt(run_dir, stage)
    return r is not None and not validate_receipt(r)


def _history_path() -> Path:
    """Upgrade ledger written by scripts/relock.py (P0-1, 档27)."""
    return Path(__file__).resolve().parents[1] / "skills.lock.history.json"


def _find_upgrade_chain(skill_name: str, receipt_root: str,
                        current_root: str,
                        history_path: Path | None = None) -> list[dict] | None:
    """Trace a FULL chain of relock ledger records from receipt_root to
    current_root for the given skill (multi-hop allowed, 档28 P0-2).

    Strict (any problem => None => TAMPERED):
      - ledger missing / not a JSON array / empty / malformed -> None
      - every hop must be a dict whose old_root_sha256 equals the previous
        new_root_sha256, whose new_root_sha256 advances the chain, and whose
        skill matches the receipt's skill_name
      - cycles are rejected; the chain must end EXACTLY at current_root
    Returns the ordered records (oldest -> newest) or None."""
    ledger = history_path if history_path is not None else _history_path()
    try:
        data = read_json(ledger)
    except (OSError, ValueError):
        return None
    if not isinstance(data, list) or not data:
        return None
    by_old: dict[str, list[dict]] = {}
    for rec in data:
        if not isinstance(rec, dict):
            return None
        # 76S/OBS-292:残缺的「非目标 skill」记录(如历史上 media-enrichment 早期
        # relock 未回填哈希)不得阻断其他 skill 的链验证——先按 skill 过滤,
        # 只对目标 skill 的记录严格要求 old/new/entry_id 字段完整。
        if rec.get("skill") != skill_name:
            continue
        old = rec.get("old_root_sha256")
        new = rec.get("new_root_sha256")
        if not isinstance(old, str) or not isinstance(new, str) or not old or not new:
            return None
        if not isinstance(rec.get("entry_id"), str) or not rec.get("entry_id"):
            return None
        by_old.setdefault(old, []).append(rec)

    def dfs(cur: str, path: list[dict], seen: set[str]):
        if cur == current_root:
            return path
        if cur in seen:
            return None  # cycle
        seen.add(cur)
        for rec in by_old.get(cur, []):
            nxt = rec["new_root_sha256"]
            if nxt == cur:
                continue
            found = dfs(nxt, path + [rec], seen)
            if found is not None:
                return found
        return None

    return dfs(receipt_root, [], set())


def verify_receipt(run_dir: Path, stage: str, skills_home: Path | None = None,
                   network_mode: str | None = None,
                   history_path: Path | None = None) -> tuple[bool, list, dict]:
    """Tamper detection (P0#1/#2/#3). Starts with FULL structural validation
    (validate_receipt), then verifies identity + per-mode expectations, then
    recomputes EVERY recorded hash from disk. Empty receipts, deleted fields,
    deleted hash entries, and missing files are all FAIL — never a skip."""
    r = load_receipt(run_dir, stage)
    if not r:
        return False, ["receipt missing or empty"], {"skill_root_state": "OK",
                                                    "upgrade_entry_ids": []}
    mism = list(validate_receipt(r))  # structural first (P0#1)
    sd = Path(run_dir) / stage

    # identity: receipt must belong to THIS stage/skill and (if given) this mode
    from .execmodel import (STAGE_EXEC, STAGE_SKILL, EXPECTED_OUTPUTS,
                            AGENT_VALIDATORS, SUBPROC, WECHAT)
    if r.get("stage") != stage:
        mism.append(f"stage mismatch: receipt.stage={r.get('stage')} != {stage}")
    if r.get("skill_name") != STAGE_SKILL.get(stage):
        mism.append(f"skill mismatch: receipt.skill_name={r.get('skill_name')} != {STAGE_SKILL.get(stage)}")
    rmode = r.get("network_mode")
    if network_mode is not None and rmode != network_mode:
        mism.append(f"network_mode mismatch: receipt={rmode} != current={network_mode}")

    real_exec = rmode in ("fake_live", "live")
    # executable stages MUST record their entrypoint (real execution modes)
    if real_exec and STAGE_EXEC.get(stage) in (SUBPROC, WECHAT):
        if not r.get("entrypoint_path") or not r.get("entrypoint_sha256"):
            mism.append("executable stage missing entrypoint_path/entrypoint_sha256")
    # stages that declare official validators MUST carry complete records
    if real_exec:
        if stage in ("media_enrichment", "gzh_design") and not r.get("official_validator"):
            mism.append(f"{stage}: official_validator missing")
        if AGENT_VALIDATORS.get(stage) and len(r.get("official_validators") or []) < len(AGENT_VALIDATORS[stage]):
            mism.append(f"{stage}: official_validators incomplete "
                        f"({len(r.get('official_validators') or [])}/{len(AGENT_VALIDATORS[stage])})")

    # expected contract outputs must all be covered by output_hashes
    missing_expected = [o for o in EXPECTED_OUTPUTS.get(stage, [])
                        if o not in (r.get("output_hashes") or {})]
    if missing_expected:
        mism.append(f"expected outputs not covered by output_hashes: {missing_expected}")

    # inputs — full-path keyed; recorded None means it was missing at run time
    for path_str, want in (r.get("input_hashes") or {}).items():
        p = Path(path_str)
        cur = sha256_file(p) if p.is_file() else None
        if want is None:
            mism.append(f"input was missing at run time: {path_str}")
        elif cur is None:
            mism.append(f"input missing now: {path_str}")
        elif cur != want:
            mism.append(f"input hash mismatch: {path_str}")

    # outputs — must exist and match
    for name, h in (r.get("output_hashes") or {}).items():
        p = sd / name
        if not p.is_file():
            mism.append(f"output missing: {name}")
        elif sha256_file(p) != h:
            mism.append(f"output hash mismatch: {name}")

    # entrypoint / pipeline validator — recorded path+sha must both exist AND match
    for label, path_key, sha_key in [("validator", "validator_path", "validator_sha256"),
                                     ("entrypoint", "entrypoint_path", "entrypoint_sha256")]:
        p, want = r.get(path_key), r.get(sha_key)
        if p and want:
            if not Path(p).is_file():
                mism.append(f"{label} script missing: {p}")
            elif sha256_file(Path(p)) != want:
                mism.append(f"{label} hash mismatch")

    # official sub-skill validator(s) — same strictness
    officials = list(r.get("official_validators") or [])
    if r.get("official_validator"):
        officials.append(r["official_validator"])
    for ov in officials:
        p, want = ov.get("path"), ov.get("sha256")
        if p and want:
            if not Path(p).is_file():
                mism.append(f"official_validator script missing: {p}")
            elif sha256_file(Path(p)) != want:
                mism.append("official_validator hash mismatch")

    # sub-skill root sha (live only) — THREE-STATE (档28 P0-2):
    #   OK            receipt root == installed root (normal resume)
    #   SKILL_UPGRADED  mismatch, but a FULL relock chain (receipt -> current)
    #                   exists in skills.lock.history.json; NOT a tamper, but the
    #                   stage MUST be re-run; matched entry_ids are returned
    #   TAMPERED      mismatch with no traceable chain -> strict FAIL (as before)
    skill_root_state = "OK"
    upgrade_entry_ids: list[str] = []
    if skills_home and r.get("network_mode") == "live" and r.get("skill_root_sha256"):
        from .skill_discovery import compute_root_sha
        skill_dir = Path(r.get("skill_dir") or (Path(skills_home) / r.get("skill_name", "")))
        cur, _ = compute_root_sha(skill_dir)
        if cur != r["skill_root_sha256"]:
            chain = _find_upgrade_chain(str(r.get("skill_name", "")),
                                        str(r["skill_root_sha256"]), str(cur),
                                        history_path=history_path)
            if chain:
                skill_root_state = "SKILL_UPGRADED"
                upgrade_entry_ids = [rec["entry_id"] for rec in chain]
            else:
                skill_root_state = "TAMPERED"
                mism.append(
                    "skill_root_sha256 mismatch (installed sub-skill changed; "
                    "no full upgrade chain in skills.lock.history.json)")

    extra = {"skill_root_state": skill_root_state,
             "upgrade_entry_ids": upgrade_entry_ids}
    return (not mism), mism, extra
