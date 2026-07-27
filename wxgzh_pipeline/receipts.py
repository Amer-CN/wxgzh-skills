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


def build_receipt(*, skill_name, skill_dir, skill_version, skill_root_sha256,
                  invoked_entrypoint, input_files, output_files,
                  validator_path, validator_sha256, validator_exit_code,
                  started_at, ended_at, side_effects=None) -> dict:
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
        "input_files": inp, "input_hashes": hash_files(input_files),
        "output_files": out, "output_hashes": hash_files(output_files),
        "validator_path": validator_path, "validator_sha256": validator_sha256,
        "validator_exit_code": int(validator_exit_code),
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
