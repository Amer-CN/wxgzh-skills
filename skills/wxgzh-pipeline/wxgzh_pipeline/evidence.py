"""Final lightweight evidence package: final_delivery.json + root MANIFEST.json
(every run file with sha256). Desensitized; no secrets, no machine-absolute
paths inside the manifest entries (paths are relative to the run dir).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from . import STAGES
from .state import atomic_write_json, load_state, sha256_file
from .receipts import load_receipt


def build_manifest(run_dir: Path) -> dict:
    run_dir = Path(run_dir)
    files = []
    for p in sorted(run_dir.rglob("*")):
        if p.is_file() and p.name != "MANIFEST.json":
            b = p.read_bytes()
            files.append({"path": p.relative_to(run_dir).as_posix(),
                          "size": len(b), "sha256": hashlib.sha256(b).hexdigest()})
    return {"artifact": "wxgzh-pipeline-run-evidence", "run_dir_name": run_dir.name,
            "file_count": len(files), "files": files}


def build_delivery(run_dir: Path) -> dict:
    run_dir = Path(run_dir)
    st = load_state(run_dir)
    stages = []
    timing = {}
    for s in STAGES:
        r = load_receipt(run_dir, s)
        stages.append({"stage": s, "has_receipt": r is not None,
                       "validator_exit_code": (r or {}).get("validator_exit_code"),
                       "elapsed_seconds": (r or {}).get("elapsed_seconds")})
        if r:
            timing[s] = r.get("elapsed_seconds")
    manifest = build_manifest(run_dir)
    manifest_sha = hashlib.sha256(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    return {
        "run_id": st.run_id, "topic": st.topic, "profile": st.profile,
        "stages": stages, "stage_timing": timing,
        "uploaded_image_count": st.uploaded_image_count,
        "image_shortfall": st.image_shortfall,
        "draft_created": st.draft_created,
        "formally_published": False,
        "final_article_sha256": st.final_article_sha256,
        "manifest_sha256": manifest_sha,
    }


def write_delivery(run_dir: Path) -> tuple[Path, Path]:
    run_dir = Path(run_dir)
    manifest = build_manifest(run_dir)
    atomic_write_json(run_dir / "MANIFEST.json", manifest)
    delivery = build_delivery(run_dir)
    atomic_write_json(run_dir / "final_delivery.json", delivery)
    return run_dir / "final_delivery.json", run_dir / "MANIFEST.json"
