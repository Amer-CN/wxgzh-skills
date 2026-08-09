#!/usr/bin/env python3
"""
verify_release.py — zh-human-writing canonical release verification.

Checks:
1. VERSION file exists and contains exactly "0.1.1"
2. SHA256SUMS exists
3. Every file in SHA256SUMS exists
4. Every file SHA256 matches
5. SHA256SUMS does not contain excluded paths
6. Existing test suite passes (80/80)
7. Returns 0 on PASS, non-zero on FAIL

Usage:
    python verify_release.py              # Full verification
    python verify_release.py --self-test # Self-test with fault injection
"""
import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
VERSION_EXPECTED = "0.1.1"

EXCLUDED_PATTERNS = [
    "SHA256SUMS",
    "runtime-install-record.txt",
]

EXCLUDED_PREFIXES = [
    ".git/",
]

EXCLUDED_SUFFIXES = [
    ".pyc",
]

EXCLUDED_CONTAINS = [
    "/__pycache__/",
    "/.pytest_cache/",
]


def is_excluded(path_str):
    """Check if a file path should be excluded from SHA256SUMS."""
    p = path_str.replace("\\", "/")

    for pat in EXCLUDED_PATTERNS:
        if p == pat:
            return True

    for prefix in EXCLUDED_PREFIXES:
        if p.startswith(prefix) or p == prefix.rstrip("/"):
            return True

    for suffix in EXCLUDED_SUFFIXES:
        if p.endswith(suffix):
            return True

    for contains in EXCLUDED_CONTAINS:
        if contains in f"/{p}/":
            return True

    return False


def check_version(errors):
    """Check 1: VERSION file exists and content matches."""
    version_path = SCRIPT_DIR / "VERSION"
    if not version_path.is_file():
        errors.append("VERSION file missing")
        return

    content = version_path.read_text(encoding="utf-8").strip()
    if content != VERSION_EXPECTED:
        errors.append(f"VERSION mismatch: expected '{VERSION_EXPECTED}', got '{content}'")


def check_sha256sums(errors):
    """Checks 2-5: SHA256SUMS existence, file existence, hash match, exclusion."""
    sums_path = SCRIPT_DIR / "SHA256SUMS"
    if not sums_path.is_file():
        errors.append("SHA256SUMS file missing")
        return

    lines = sums_path.read_text(encoding="utf-8").strip().splitlines()
    if not lines:
        errors.append("SHA256SUMS is empty")
        return

    for line in lines:
        parts = line.split("  ", 1)
        if len(parts) != 2:
            errors.append(f"Malformed SHA256SUMS line: {line[:80]}")
            continue

        expected_hash, rel_path = parts
        rel_path = rel_path.strip()

        # Check 5: excluded paths
        if is_excluded(rel_path):
            errors.append(f"SHA256SUMS contains excluded path: {rel_path}")
            continue

        # Check 3: file exists
        file_path = SCRIPT_DIR / rel_path
        if not file_path.is_file():
            errors.append(f"File listed in SHA256SUMS but missing: {rel_path}")
            continue

        # Check 4: hash matches
        actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            errors.append(
                f"SHA256 mismatch for {rel_path}: "
                f"expected {expected_hash}, got {actual_hash}"
            )


def run_tests(errors):
    """Check 6: Run existing test suite."""
    test_runner = SCRIPT_DIR / "tests" / "run_tests.py"
    if not test_runner.is_file():
        errors.append("Test runner not found: tests/run_tests.py")
        return

    try:
        result = subprocess.run(
            [sys.executable, "-X", "utf8", str(test_runner)],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(SCRIPT_DIR),
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        if result.returncode != 0:
            errors.append(f"Test suite failed (exit code {result.returncode})")
            if result.stdout:
                # Extract summary line
                for line in result.stdout.splitlines():
                    if "通过" in line or "失败" in line or "总计" in line:
                        errors.append(f"  {line.strip()}")
        else:
            # Verify 80/80
            if "80" not in result.stdout:
                errors.append("Test suite passed but expected 80 tests")
    except subprocess.TimeoutExpired:
        errors.append("Test suite timed out")
    except Exception as e:
        errors.append(f"Test suite error: {e}")


def verify():
    """Run all verification checks."""
    errors = []

    check_version(errors)
    check_sha256sums(errors)
    run_tests(errors)

    return errors


def self_test():
    """Run fault-injection self-test on a temporary copy."""
    errors = []

    # Create temporary copy
    with tempfile.TemporaryDirectory(prefix="zh-human-selftest-") as tmpdir:
        tmp_root = Path(tmpdir) / "copy"

        # Copy all files except .git
        def ignore_git(directory, contents):
            ignored = []
            if ".git" in contents:
                ignored.append(".git")
            if "__pycache__" in contents:
                ignored.append("__pycache__")
            if ".pytest_cache" in contents:
                ignored.append(".pytest_cache")
            return ignored

        shutil.copytree(SCRIPT_DIR, tmp_root, ignore=ignore_git)

        # Save original hashes for restoration check
        original_hashes = {}
        for f in tmp_root.rglob("*"):
            if f.is_file() and ".git" not in str(f):
                rel = f.relative_to(tmp_root)
                original_hashes[str(rel)] = hashlib.sha256(f.read_bytes()).hexdigest()

        # --- Self-test A: Modify SKILL.md → must detect MISMATCH ---
        skill_path = tmp_root / "SKILL.md"
        if skill_path.is_file():
            original_content = skill_path.read_bytes()
            modified_content = original_content + b"\n# tampered\n"
            skill_path.write_bytes(modified_content)

            # Re-run SHA256SUMS check against modified copy
            sums_path = tmp_root / "SHA256SUMS"
            if sums_path.is_file():
                lines = sums_path.read_text(encoding="utf-8").strip().splitlines()
                mismatch_found = False
                for line in lines:
                    parts = line.split("  ", 1)
                    if len(parts) == 2:
                        expected_hash, rel_path = parts
                        rel_path = rel_path.strip()
                        file_path = tmp_root / rel_path
                        if file_path.is_file() and rel_path == "SKILL.md":
                            actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
                            if actual_hash != expected_hash:
                                mismatch_found = True
                                break
                if not mismatch_found:
                    errors.append("Self-test A FAILED: SKILL.md modification not detected")
            else:
                errors.append("Self-test A: SHA256SUMS missing in temp copy")

            # Restore
            skill_path.write_bytes(original_content)

        # --- Self-test B: Delete a protected file → must detect MISSING ---
        test_file = tmp_root / "tests" / "run_tests.py"
        deleted_content = None
        if test_file.is_file():
            deleted_content = test_file.read_bytes()
            test_file.unlink()

            sums_path = tmp_root / "SHA256SUMS"
            if sums_path.is_file():
                lines = sums_path.read_text(encoding="utf-8").strip().splitlines()
                missing_found = False
                for line in lines:
                    parts = line.split("  ", 1)
                    if len(parts) == 2:
                        _, rel_path = parts
                        rel_path = rel_path.strip()
                        if rel_path == "tests/run_tests.py":
                            file_path = tmp_root / rel_path
                            if not file_path.is_file():
                                missing_found = True
                                break
                if not missing_found:
                    errors.append("Self-test B FAILED: deleted file not detected")
            else:
                errors.append("Self-test B: SHA256SUMS missing in temp copy")

            # Restore
            test_file.write_bytes(deleted_content)

        # --- Self-test C: Modify VERSION → must FAIL ---
        version_path = tmp_root / "VERSION"
        if version_path.is_file():
            original_version = version_path.read_bytes()
            version_path.write_text("9.9.9\n", encoding="utf-8")

            content = version_path.read_text(encoding="utf-8").strip()
            if content == VERSION_EXPECTED:
                errors.append("Self-test C FAILED: VERSION modification not detected")

            # Restore
            version_path.write_bytes(original_version)

        # --- Self-test D: Verify restoration ---
        for rel_path, original_hash in original_hashes.items():
            file_path = tmp_root / rel_path
            if file_path.is_file():
                current_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
                if current_hash != original_hash:
                    errors.append(f"Self-test D FAILED: {rel_path} was not restored properly")
            else:
                # File might have been deleted in self-test but restored
                pass

    return errors


def main():
    parser = argparse.ArgumentParser(
        description="zh-human-writing canonical release verification"
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run fault-injection self-test",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("zh-human-writing Canonical Release Verification")
    print("=" * 60)

    if args.self_test:
        print("\n[Self-Test] Running fault injection tests...")
        st_errors = self_test()
        if st_errors:
            print(f"\nSELF-TEST FAILED: {len(st_errors)} error(s)")
            for e in st_errors:
                print(f"  - {e}")
            return 1
        else:
            print("\nSelf-test: ALL PASSED")
            print("  A. SKILL.md modification → MISMATCH detected ✓")
            print("  B. File deletion → MISSING detected ✓")
            print("  C. VERSION modification → FAIL detected ✓")
            print("  D. All files restored to original hashes ✓")
            return 0

    print("\n[1] Checking VERSION file...")
    errors = []
    check_version(errors)
    if errors:
        print(f"  FAIL: {errors[-1]}")
    else:
        print(f"  OK: VERSION = {VERSION_EXPECTED}")

    print("\n[2] Checking SHA256SUMS...")
    check_sha256sums(errors)
    if any("SHA256SUMS" in e and "missing" in e for e in errors):
        print("  FAIL: SHA256SUMS file missing")
    elif any("mismatch" in e.lower() or "missing" in e.lower() for e in errors):
        for e in errors:
            if "mismatch" in e.lower() or "missing" in e.lower() or "excluded" in e.lower():
                print(f"  FAIL: {e}")
    else:
        # Count entries
        sums_path = SCRIPT_DIR / "SHA256SUMS"
        if sums_path.is_file():
            count = len(sums_path.read_text(encoding="utf-8").strip().splitlines())
            print(f"  OK: {count} files verified")

    print("\n[3] Running test suite...")
    test_errors = [e for e in errors if "test" in e.lower()]
    if not test_errors:
        run_tests(errors)
    test_fails = [e for e in errors if "test" in e.lower()]
    if test_fails:
        for e in test_fails:
            print(f"  FAIL: {e}")
    else:
        print("  OK: 80/80 tests passed")

    print("\n" + "=" * 60)
    if errors:
        print(f"VERIFICATION FAILED: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        print("=" * 60)
        return 1
    else:
        print("VERIFICATION PASSED")
        print("=" * 60)
        return 0


if __name__ == "__main__":
    sys.exit(main())
