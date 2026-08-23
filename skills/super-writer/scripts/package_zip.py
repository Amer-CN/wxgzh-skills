#!/usr/bin/env python3
"""Package super-writer-v0.4.9-rc1.zip with MANIFEST.sha256."""
import os, hashlib, zipfile, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIP_NAME = "super-writer-v0.4.9-rc1.zip"
OUTPUT_DIR = os.path.dirname(ROOT)  # parent of super-writer/
ZIP_PATH = os.path.join(OUTPUT_DIR, ZIP_NAME)

# Files/dirs to exclude
EXCLUDE_DIRS = {'__pycache__', '.git', '.pytest_cache'}
EXCLUDE_FILES = {'prepackage_check.py', 'MANIFEST.sha256'}
EXCLUDE_EXTENSIONS = {'.pyc', '.pyo', '.tmp'}
# Exclude test reports (generated artifacts, not source files)
EXCLUDE_PATTERNS = [
    'v0.3.0-rc1-test-integration-report.md',
    'super-writer-v0.3.0-rc1-hotfix.1-test-report.md',
    'super-writer-v0.3.0-rc1-hotfix.2-test-report.md',
    'super-writer-v0.3.1-rc1-test-report.md',
    'super-writer-v0.3.0-rc1-hotfix.1-source-bundle.md',
]


def should_exclude(rel_path):
    parts = rel_path.replace('\\', '/').split('/')
    for exc_dir in EXCLUDE_DIRS:
        exc_parts = exc_dir.split('/')
        for i in range(len(parts) - len(exc_parts) + 1):
            if parts[i:i+len(exc_parts)] == exc_parts:
                return True
    basename = os.path.basename(rel_path)
    if basename in EXCLUDE_FILES:
        return True
    if os.path.splitext(rel_path)[1] in EXCLUDE_EXTENSIONS:
        return True
    # Check patterns
    normalized = rel_path.replace(os.sep, '/')
    for pattern in EXCLUDE_PATTERNS:
        if normalized == pattern or normalized.endswith('/' + pattern):
            return True
    return False

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

# Collect files
files_to_pack = []
excluded = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    # Remove excluded dirs in-place
    rel_dir = os.path.relpath(dirpath, ROOT)
    dirnames[:] = [d for d in dirnames if d not in {'__pycache__', '.git', '.pytest_cache'}]
    for filename in filenames:
        filepath = os.path.join(dirpath, filename)
        rel_path = os.path.relpath(filepath, ROOT)
        if should_exclude(rel_path):
            excluded.append(rel_path)
            continue
        files_to_pack.append((filepath, rel_path))

files_to_pack.sort(key=lambda x: x[1])

# Generate MANIFEST.sha256
manifest_lines = []
for filepath, rel_path in files_to_pack:
    sha = compute_sha256(filepath)
    manifest_lines.append(f"{sha}  {rel_path.replace(os.sep, '/')}")

manifest_content = "\n".join(manifest_lines) + "\n"
manifest_path = os.path.join(ROOT, "MANIFEST.sha256")
with open(manifest_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(manifest_content)

# Add MANIFEST to file list
files_to_pack.append((manifest_path, "MANIFEST.sha256"))

# Create ZIP
if os.path.exists(ZIP_PATH):
    os.remove(ZIP_PATH)

with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as zf:
    for filepath, rel_path in files_to_pack:
        arcname = os.path.join("super-writer", rel_path)
        zf.write(filepath, arcname)

# Compute ZIP SHA-256
zip_sha = compute_sha256(ZIP_PATH)

# Output summary
print(f"=== Packaging Complete ===")
print(f"ZIP: {ZIP_PATH}")
print(f"SHA-256: {zip_sha}")
print(f"Files in ZIP: {len(files_to_pack)}")
print(f"Excluded files: {len(excluded)}")
print(f"\nExcluded file list:")
for f in excluded:
    print(f"  - {f}")
print(f"\nMANIFEST.sha256 written with {len(manifest_lines)} entries")

# Verify ZIP integrity
print(f"\n=== ZIP Integrity Check ===")
with zipfile.ZipFile(ZIP_PATH, 'r') as zf:
    bad = zf.testzip()
    if bad:
        print(f"  CORRUPT: {bad}")
        sys.exit(1)
    else:
        names = zf.namelist()
        print(f"  Verified {len(names)} entries: PASSED")
        # Check no .tmp files in ZIP
        tmp_files = [n for n in names if n.endswith('.tmp')]
        if tmp_files:
            print(f"  ERROR: .tmp files found in ZIP: {tmp_files}")
            sys.exit(1)
        print(f"  No .tmp files in ZIP: PASSED")
        # Check no old test reports
        old_reports = [n for n in names if 'test-integration-report' in n]
        if old_reports:
            print(f"  ERROR: Old test reports found in ZIP: {old_reports}")
            sys.exit(1)
        print(f"  No old test reports in ZIP: PASSED")
        # Check no HTML/PNG
        html_png = [n for n in names if n.endswith('.html') or n.endswith('.png')]
        if html_png:
            print(f"  ERROR: HTML/PNG files found in ZIP: {html_png}")
            sys.exit(1)
        print(f"  No HTML/PNG in ZIP: PASSED")
