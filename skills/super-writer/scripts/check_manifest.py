#!/usr/bin/env python3
"""Check MANIFEST.sha256 integrity."""
import hashlib
import os
import sys

def check_manifest(manifest_path):
    with open(manifest_path, 'r', encoding='utf-8') as f:
        lines = f.read().strip().split('\n')

    ok = 0
    fail = 0
    for line in lines:
        parts = line.split('  ', 1)
        if len(parts) != 2:
            continue
        sha, filepath = parts
        if not os.path.exists(filepath):
            print(f"FAIL: file not found: {filepath}")
            fail += 1
            continue
        actual = hashlib.sha256(open(filepath, 'rb').read()).hexdigest()
        if actual == sha:
            ok += 1
        else:
            print(f"FAIL: {filepath}")
            fail += 1

    print(f"OK: {ok}, FAIL: {fail}")
    return fail == 0

if __name__ == '__main__':
    manifest = sys.argv[1] if len(sys.argv) > 1 else 'MANIFEST.sha256'
    success = check_manifest(manifest)
    sys.exit(0 if success else 1)
