#!/usr/bin/env python3
"""Generate a source bundle markdown file listing all project files."""
import os, sys, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.dirname(ROOT)
BUNDLE_NAME = "super-writer-v0.4.12-rc1-source-bundle.md"
BUNDLE_PATH = os.path.join(OUTPUT_DIR, BUNDLE_NAME)

EXCLUDE_DIRS = {'__pycache__', '.git', '.pytest_cache'}
EXCLUDE_FILES = {'MANIFEST.sha256', 'gen_source_bundle.py', 'prepackage_check.py'}
EXCLUDE_EXTENSIONS = {'.pyc', '.pyo', '.tmp'}
EXCLUDE_PATTERNS = [
    'v0.3.0-rc1-test-integration-report.md',
    'super-writer-v0.3.0-rc1-hotfix.1-test-report.md',
    'super-writer-v0.3.0-rc1-hotfix.2-test-report.md',
    'super-writer-v0.3.1-rc1-test-report.md',
    'super-writer-v0.3.0-rc1-hotfix.1-source-bundle.md',
]


def should_exclude(rel_path):
    parts = rel_path.replace('\\', '/').split('/')
    for d in EXCLUDE_DIRS:
        if d in parts:
            return True
    name = os.path.basename(rel_path)
    if name in EXCLUDE_FILES:
        return True
    if os.path.splitext(rel_path)[1] in EXCLUDE_EXTENSIONS:
        return True
    n = rel_path.replace(os.sep, '/')
    for p in EXCLUDE_PATTERNS:
        if n == p or n.endswith('/' + p):
            return True
    return False


def collect():
    files = []
    for dp, dns, fns in os.walk(ROOT):
        dns[:] = [d for d in dns if d not in EXCLUDE_DIRS]
        for fn in fns:
            fp = os.path.join(dp, fn)
            rp = os.path.relpath(fp, ROOT)
            if should_exclude(rp):
                continue
            files.append((fp, rp))
    files.sort(key=lambda x: x[1].replace('\\', '/'))
    return files


def main():
    files = collect()
    lines = [f"# Super Writer v0.3.1-rc1 Source Bundle\n", f"Total files: {len(files)}\n\n"]
    lines.append("| # | File | Lines |\n|---|------|-------|\n")
    for i, (fp, rp) in enumerate(files, 1):
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                lc = len(f.read().split('\n'))
        except Exception:
            lc = 0
        lines.append(f"| {i} | {rp.replace(os.sep, '/')} | {lc} |\n")
    lines.append("\n---\n\n")
    for fp, rp in files:
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            content = "(binary or unreadable)"
        lines.append(f"\n## File: {rp.replace(os.sep, '/')}\n\n```\n{content}\n```\n")

    out = '\n'.join(lines)
    with open(BUNDLE_PATH, 'w', encoding='utf-8', newline='\n') as f:
        f.write(out)
    sha = hashlib.sha256(out.encode('utf-8')).hexdigest()
    print(f"=== Source Bundle Generated ===")
    print(f"File: {BUNDLE_PATH}")
    print(f"SHA-256: {sha}")
    print(f"Files: {len(files)}")


if __name__ == '__main__':
    main()