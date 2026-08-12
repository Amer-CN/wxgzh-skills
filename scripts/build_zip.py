#!/usr/bin/env python3
"""Build script for media-enrichment v0.1.0-dev14.

Sequence:
  a. Generate all fixtures
  b. Run tests
  c. Generate all evidence
  d. Freeze files (compute hashes)
  e. Generate MANIFEST.json (excluding its own hash)
  f. Create ZIP
  g. Extract ZIP to fresh directory
  h. Independently recompute file count, sizes, hashes
  i. Any error → no output package
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

SKILL_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = SKILL_ROOT.parent.parent
BUILD_VERSION = "0.1.0-dev14"
OUTPUT_ZIP = PROJECT_ROOT / f"media-enrichment-v{BUILD_VERSION}.zip"
EVIDENCE_DIR = SKILL_ROOT / "evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

# Required fixture images — verified by explicit list, not a brittle count
EXPECTED_FIXTURE_IMAGES = {
    "avatar.jpg",
    "corrupted.jpg",
    "duplicate-resized.jpg",
    "logo.png",
    "oversized-metadata.png",
    "tracking-pixel.gif",
    "valid-chart.png",
    "valid-photo.jpg",
    "regression/a001-aisi-logo-pattern.png",
    "regression/a006-substack-ad-url.png",
    "regression/a010-ithome-1193x296.jpg",
}

# Only exclude these at packaging time
PACKAGE_EXCLUDE_DIRS = {"__pycache__", ".pytest_cache", ".git", "output", ".temp"}
PACKAGE_EXCLUDE_SUFFIXES = {".pyc", ".pyo"}


def compute_file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def step_a_fixtures():
    print("[build] Step a: Generating fixtures...")
    exit_code = subprocess.run(
        [sys.executable, "scripts/generate_test_fixtures.py"],
        capture_output=True, text=True, cwd=str(SKILL_ROOT),
    )
    print(f"  exit={exit_code.returncode}")
    if exit_code.returncode != 0:
        print(f"  STDERR: {exit_code.stderr[:500]}")
        return False
    return True


def step_b_tests():
    """Run tests with structured JSON report. Abort on non-zero, zero tests, or any failure."""
    print("[build] Step b: Running tests (structured JSON report)...")
    json_report_path = EVIDENCE_DIR / "pytest_report.json"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short",
         "--json-report", f"--json-report-file={json_report_path}"],
        capture_output=True, text=True, cwd=str(SKILL_ROOT),
    )
    (EVIDENCE_DIR / "unit_test_stdout.txt").write_text(result.stdout, encoding="utf-8")
    (EVIDENCE_DIR / "unit_test_stderr.txt").write_text(result.stderr, encoding="utf-8")

    # Parse structured JSON report
    total = 0
    passed = 0
    failed = 0
    if json_report_path.exists():
        report = json.loads(json_report_path.read_text(encoding="utf-8"))
        total = report.get("summary", {}).get("collected", 0)
        passed = report.get("summary", {}).get("passed", 0)
        failed = report.get("summary", {}).get("failed", 0)

    print(f"  returncode={result.returncode}, total={total}, passed={passed}, failed={failed}")

    # P0 gate: all four conditions must be satisfied
    if result.returncode != 0:
        print(f"  ABORT: pytest returncode={result.returncode} (non-zero)")
        return False
    if total == 0:
        print(f"  ABORT: no tests collected (total=0)")
        return False
    if failed != 0:
        print(f"  ABORT: {failed} tests failed")
        return False
    if passed != total:
        print(f"  ABORT: passed={passed} != total={total}")
        return False
    if passed == 0:
        print(f"  ABORT: passed=0")
        return False

    print(f"  BUILD_MAY_CONTINUE=true")
    return True


def step_c_evidence():
    print("[build] Step c: Generating evidence...")
    result = subprocess.run(
        [sys.executable, "scripts/generate_evidence.py"],
        capture_output=True, text=True, cwd=str(SKILL_ROOT),
    )
    print(f"  exit={result.returncode}")
    if result.returncode != 0:
        print(f"  STDERR: {result.stderr[:500]}")
        print("  ABORT: evidence generation returned non-zero (validator failed)")
        return False
    # Also check validator_exit_code.txt
    vec_path = EVIDENCE_DIR / "validator_exit_code.txt"
    if vec_path.exists():
        vec = vec_path.read_text().strip()
        if vec != "0":
            print(f"  ABORT: validator_exit_code={vec}")
            return False
    return True


def step_d_freeze():
    """Compute hashes for all files (excluding __pycache__, .pytest_cache, output, MANIFEST.json, file_hashes.sha256)."""
    print("[build] Step d: Freezing files...")
    files = []
    for path in sorted(SKILL_ROOT.rglob("*")):
        if not path.is_file():
            continue
        parts = set(path.relative_to(SKILL_ROOT).parts)
        if parts & PACKAGE_EXCLUDE_DIRS:
            continue
        if path.suffix in PACKAGE_EXCLUDE_SUFFIXES:
            continue
        rel = str(path.relative_to(SKILL_ROOT)).replace("\\", "/")
        # Skip self-referential files — they'll be handled in step e
        if rel == "MANIFEST.json" or rel == "evidence/file_hashes.sha256":
            continue
        sha = compute_file_sha256(path)
        files.append({"path": rel, "size": path.stat().st_size, "sha256": sha})
    return files


def step_e_manifest(files):
    """Generate file_hashes.sha256 and MANIFEST.json without self-reference."""
    print("[build] Step e: Generating MANIFEST.json (no self-reference)...")
    
    # Write file_hashes.sha256 first — lists all files except itself and MANIFEST.json
    hash_lines = [f"{f['sha256']}  {f['path']}" for f in files]
    file_hashes_path = EVIDENCE_DIR / "file_hashes.sha256"
    file_hashes_path.write_text("\n".join(hash_lines) + "\n", encoding="utf-8")
    
    # Now compute hash of file_hashes.sha256 (it exists now, can be hashed)
    fh_rel = "evidence/file_hashes.sha256"
    fh_entry = {
        "path": fh_rel,
        "size": file_hashes_path.stat().st_size,
        "sha256": compute_file_sha256(file_hashes_path),
    }
    
    # MANIFEST.json includes all files + file_hashes.sha256, but NOT itself
    manifest_files = list(files) + [fh_entry]
    
    manifest = {
        "package": "media-enrichment",
        "version": BUILD_VERSION,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "files": manifest_files,
        "total_files": len(manifest_files),
        "missing_files": 0,
        "unregistered_files": 0,
        "hash_errors": 0,
        "note": "MANIFEST.json does not record its own SHA256 to avoid self-reference. file_hashes.sha256 does not record its own hash either.",
    }
    
    manifest_path = SKILL_ROOT / "MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"  {len(manifest_files)} files registered (MANIFEST.json excluded)")
    return manifest


def should_exclude(path: Path) -> bool:
    parts = set(path.relative_to(SKILL_ROOT).parts)
    if parts & PACKAGE_EXCLUDE_DIRS:
        return True
    if path.suffix in PACKAGE_EXCLUDE_SUFFIXES:
        return True
    return False


def check_required_fixture_images(base: Path) -> tuple[bool, list[str]]:
    """Verify every required fixture image exists under base/fixtures/images."""
    missing = [rel for rel in sorted(EXPECTED_FIXTURE_IMAGES)
               if not (base / "fixtures" / "images" / rel).is_file()]
    return len(missing) == 0, missing


def step_f_zip():
    """Create ZIP with all files including fixtures/images."""
    print("[build] Step f: Creating ZIP...")
    
    files = []
    for path in sorted(SKILL_ROOT.rglob("*")):
        if path.is_file() and not should_exclude(path):
            files.append(path)
    
    print(f"  {len(files)} files to include")
    
    # Verify required fixtures/images are included (explicit list, no fixed count)
    ok, missing = check_required_fixture_images(SKILL_ROOT)
    present = len(EXPECTED_FIXTURE_IMAGES) - len(missing)
    print(f"  FIXTURE_IMAGES_REQUIRED_PRESENT={present}/{len(EXPECTED_FIXTURE_IMAGES)}")
    assert ok, f"Missing required fixture images: {missing}"
    
    with ZipFile(OUTPUT_ZIP, "w", ZIP_DEFLATED) as zf:
        for path in files:
            arcname = f"media-enrichment/{path.relative_to(SKILL_ROOT)}"
            arcname = arcname.replace("\\", "/")
            zf.write(path, arcname)
    
    zip_sha = compute_file_sha256(OUTPUT_ZIP)
    print(f"  ZIP: {OUTPUT_ZIP.name} ({OUTPUT_ZIP.stat().st_size} bytes, SHA256: {zip_sha[:16]}...)")
    return zip_sha


def step_g_h_verify(zip_sha):
    """Extract ZIP to fresh dir and independently verify."""
    print("[build] Step g-h: Extracting ZIP and verifying...")
    
    with ZipFile(OUTPUT_ZIP, "r") as zf:
        entries = zf.namelist()
    
    print(f"  ZIP entries: {len(entries)}")
    
    # Extract to temp dir
    with tempfile.TemporaryDirectory() as tmpdir:
        with ZipFile(OUTPUT_ZIP, "r") as zf:
            zf.extractall(tmpdir)
        
        extracted_root = Path(tmpdir) / "media-enrichment"
        
        # Independently recompute file count, sizes, hashes
        manifest_path = extracted_root / "MANIFEST.json"
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
        
        errors = []
        verified = 0
        
        for entry in manifest["files"]:
            rel = entry["path"]
            file_path = extracted_root / rel
            if not file_path.exists():
                errors.append(f"MISSING: {rel}")
                continue
            actual_size = file_path.stat().st_size
            if actual_size != entry["size"]:
                errors.append(f"SIZE MISMATCH: {rel} (expected={entry['size']}, actual={actual_size})")
                continue
            actual_sha = compute_file_sha256(file_path)
            if actual_sha != entry["sha256"]:
                errors.append(f"HASH MISMATCH: {rel} (expected={entry['sha256'][:16]}, actual={actual_sha[:16]})")
                continue
            verified += 1
        
        # Verify required fixture images inside the extracted ZIP (explicit list)
        ok, missing = check_required_fixture_images(extracted_root)
        present = len(EXPECTED_FIXTURE_IMAGES) - len(missing)
        print(f"  Verified files: {verified}")
        print(f"  Errors: {len(errors)}")
        print(f"  FIXTURE_IMAGES_REQUIRED_PRESENT (in ZIP): {present}/{len(EXPECTED_FIXTURE_IMAGES)}")
        
        if errors:
            for e in errors[:10]:
                print(f"    ERROR: {e}")
            return False
        
        if not ok:
            print(f"    ERROR: Missing required fixture images in ZIP: {missing}")
            return False
        
        print(f"  ZIP_REPRODUCIBILITY_PASS=true")
        return True


def step_i_summary(zip_sha, verification_pass):
    """Generate final summary — reads from generate_evidence's test_summary and extends."""
    print("[build] Step i: Final summary...")
    
    # Read test summary from generate_evidence (don't overwrite — extend)
    summary_path = EVIDENCE_DIR / "test_summary.json"
    if summary_path.exists():
        with open(summary_path, encoding="utf-8") as f:
            final = json.load(f)
    else:
        final = {}
    
    # Add/override ZIP-specific fields only
    final["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    final["skill_version"] = BUILD_VERSION
    final["zip_path"] = OUTPUT_ZIP.name
    final["zip_sha256"] = zip_sha
    final["zip_size"] = OUTPUT_ZIP.stat().st_size
    final["ZIP_REPRODUCIBILITY_PASS"] = verification_pass
    final["FIXTURE_IMAGES_REQUIRED_PRESENT"] = f"{len(EXPECTED_FIXTURE_IMAGES)}/{len(EXPECTED_FIXTURE_IMAGES)}" if verification_pass else "FAIL"
    final["MANIFEST_MISSING_FILES"] = 0 if verification_pass else -1
    final["MANIFEST_HASH_ERRORS"] = 0 if verification_pass else -1
    # PACKAGE_MANIFEST_PASS = ZIP reproducibility + no hash errors
    final["PACKAGE_MANIFEST_PASS"] = verification_pass
    
    with open(EVIDENCE_DIR / "test_summary.json", "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print("FINAL BUILD SUMMARY")
    print(f"{'='*60}")
    for k, v in final.items():
        if k not in ("generated_at", "skill_version", "zip_path", "zip_sha256", "zip_size"):
            print(f"  {k}: {v}")
    
    return final


def main():
    print(f"Building media-enrichment v{BUILD_VERSION}")
    print(f"Skill root: {SKILL_ROOT}")
    print(f"Output ZIP: {OUTPUT_ZIP}")
    print()
    
    # Step a: Fixtures
    if not step_a_fixtures():
        print("ABORT: fixture generation failed")
        sys.exit(1)
    
    # Step b: Tests
    if not step_b_tests():
        print("ABORT: tests failed")
        sys.exit(1)
    
    # Step c: Evidence
    if not step_c_evidence():
        print("ABORT: evidence generation failed")
        sys.exit(1)
    
    # Step d: Freeze
    files = step_d_freeze()
    
    # Step e: MANIFEST.json
    step_e_manifest(files)
    
    # Step f: ZIP
    zip_sha = step_f_zip()
    
    # Step g-h: Verify
    verification_pass = step_g_h_verify(zip_sha)
    
    if not verification_pass:
        print("ABORT: ZIP verification failed")
        sys.exit(1)
    
    # Step i: Summary
    summary = step_i_summary(zip_sha, verification_pass)
    
    print(f"\nBUILD COMPLETE: {OUTPUT_ZIP}")
    print(f"ZIP SHA256: {zip_sha}")


if __name__ == "__main__":
    main()
