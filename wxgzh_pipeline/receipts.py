"""Stage execution receipts. A stage with no valid receipt is treated as NOT
executed (spec section 9). Receipts are the durable proof — not chat claims.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .state import atomic_write_json, sha256_file

REQUIRED_FIELDS = [
    "skill_name", "skill_dir", "skill_version", "skill_root_sha256",
    "invoked_entrypoint", "input_files", "input_hashes", "output_files",
    "output_hashes", "validator_path", "validator_sha256", "validator_exit_code",
    "started_at", "ended_at", "elapsed_seconds", "side_effects",
]


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
                  network_mode=None) -> dict:
    inp = [str(p) for p in input_files]
    out = [str(p) for p in output_files]
    try:
        elapsed = (datetime.strptime(ended_at, "%Y-%m-%dT%H:%M:%SZ")
                   - datetime.strptime(started_at, "%Y-%m-%dT%H:%M:%SZ")).total_seconds()
    except Exception:
        elapsed = 0.0
    return {
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
        "side_effects": side_effects or [],
    }


def receipt_path(run_dir: Path, stage: str) -> Path:
    return Path(run_dir) / stage / "stage_receipt.json"


def write_receipt(run_dir: Path, stage: str, receipt: dict) -> Path:
    p = receipt_path(run_dir, stage)
    atomic_write_json(p, receipt)
    return p


def validate_receipt(receipt: dict) -> list[str]:
    errs = [f"missing field: {f}" for f in REQUIRED_FIELDS if f not in receipt]
    if not errs and receipt.get("validator_exit_code", 1) != 0:
        errs.append(f"validator_exit_code != 0 ({receipt.get('validator_exit_code')})")
    return errs


def load_receipt(run_dir: Path, stage: str) -> dict | None:
    p = receipt_path(run_dir, stage)
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def receipt_valid(run_dir: Path, stage: str) -> bool:
    r = load_receipt(run_dir, stage)
    return r is not None and not validate_receipt(r)


def verify_receipt(run_dir: Path, stage: str, skills_home: Path | None = None) -> tuple[bool, list]:
    """Tamper detection (P0#2/#3): recompute EVERY recorded hash from disk —
    inputs (full-path keyed), outputs, entrypoint, validators, official
    validator(s), and (live) the sub-skill root sha. A MISSING file is a FAIL,
    never a skip. Any drift => tampered."""
    r = load_receipt(run_dir, stage)
    if r is None:
        return False, ["receipt missing"]
    sd = Path(run_dir) / stage
    mism = []

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

    # sub-skill root sha (live only — installed skill must still match the receipt)
    if skills_home and r.get("network_mode") == "live" and r.get("skill_root_sha256"):
        from .skill_discovery import compute_root_sha
        skill_dir = Path(r.get("skill_dir") or (Path(skills_home) / r.get("skill_name", "")))
        cur, _ = compute_root_sha(skill_dir)
        if cur != r["skill_root_sha256"]:
            mism.append("skill_root_sha256 mismatch (installed sub-skill changed)")

    return (not mism), mism
