"""Reproducible (bit-for-bit) zipping + filtered tree copy helpers.

Deterministic zips: entries sorted, fixed timestamp (1980-01-01), fixed
external attrs, fixed compression — so two builds from identical inputs produce
byte-identical archives (verified by scripts/verify_reproducible_zip.py).
"""
from __future__ import annotations

import hashlib
import shutil
import zipfile
from pathlib import Path

EXCLUDE_DIRS = {"__pycache__", ".git", ".pytest_cache", ".github", ".temp", ".pytest"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}
# never bundle these (secrets / machine-specific / heavy artifacts)
FORBIDDEN_NAMES = {".env"}
FORBIDDEN_SUFFIXES = {".zip"}
FIXED_DATE = (1980, 1, 1, 0, 0, 0)
PIPELINE_RELEASE_INCLUDES = (".github/workflows/ci.yml",)
PIPELINE_RELEASE_EXCLUDES = (".gitattributes",)


def _skip(p: Path, include_paths=(), exclude_paths=()) -> bool:
    p = Path(p)
    posix = p.as_posix()
    excluded = {Path(item).as_posix() for item in exclude_paths}
    if posix in excluded:
        return True
    included = {Path(item).as_posix() for item in include_paths}
    if posix in included:
        return False
    if any(part in EXCLUDE_DIRS for part in p.parts):
        return True
    if p.suffix.lower() in EXCLUDE_SUFFIXES or p.suffix.lower() in FORBIDDEN_SUFFIXES:
        return True
    if p.name in FORBIDDEN_NAMES or p.name.startswith(".env"):
        return True
    return False


def copy_tree(src: Path, dst: Path, include_paths=(), exclude_paths=()) -> int:
    src, dst = Path(src), Path(dst)
    n = 0
    for p in sorted(src.rglob("*")):
        if p.is_file() and not _skip(p.relative_to(src), include_paths, exclude_paths):
            target = dst / p.relative_to(src)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, target)
            n += 1
    return n


def deterministic_zip(src_dir: Path, out_zip: Path, arc_prefix: str = "", include_paths=(), exclude_paths=()) -> str:
    """Create a reproducible zip of src_dir; return its sha256."""
    src_dir = Path(src_dir)
    out_zip = Path(out_zip)
    if out_zip.exists():
        out_zip.unlink()
    files = sorted(p for p in src_dir.rglob("*")
                   if p.is_file() and not _skip(
                       p.relative_to(src_dir), include_paths, exclude_paths))
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            arcname = (Path(arc_prefix) / p.relative_to(src_dir)).as_posix() if arc_prefix \
                else p.relative_to(src_dir).as_posix()
            zi = zipfile.ZipInfo(arcname, date_time=FIXED_DATE)
            zi.external_attr = (0o644 & 0xFFFF) << 16
            zi.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(zi, p.read_bytes())
    return hashlib.sha256(out_zip.read_bytes()).hexdigest()
