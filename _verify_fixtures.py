#!/usr/bin/env python3
"""Final fixture verification for hotfix.2."""
import sys
sys.path.insert(0, 'scripts')
from validate_semantic_map import validate_semantic_map
from pathlib import Path

ROOT = Path('.')
gzh_root = Path('f:/AIXM/wxgzh/gzh-design-skill/')
use_formatter = gzh_root.exists()
print(f"gzh-design-skill exists: {use_formatter}")
print()

fixtures = [
    ('fixture-a-simple', None),
    ('fixture-b-tutorial', None),
    ('fixture-c-analysis', 'evidence-map.md'),
]

total_errors = 0

for name, ev_name in fixtures:
    fdir = ROOT / 'tests' / 'fixtures' / 'semantic' / name
    article = fdir / 'article.md'
    sm = fdir / 'semantic-map.yaml'
    ev = fdir / ev_name if ev_name else None

    # Check fixture files exist
    missing = []
    if not article.exists():
        missing.append(str(article))
    if not sm.exists():
        missing.append(str(sm))
    if ev_name and not ev.exists():
        missing.append(str(ev))

    if missing:
        print(f"=== {name} ===")
        print(f"  ERROR: Missing fixture files: {', '.join(missing)}")
        print()
        total_errors += len(missing)
        continue

    kwargs = {}
    if use_formatter:
        kwargs['formatter_root'] = str(gzh_root)
    if ev:
        kwargs['evidence_map_path'] = str(ev)

    errors, warnings, info = validate_semantic_map(article, sm, **kwargs)
    print(f"=== {name} ===")
    print(f"  Errors: {len(errors)}")
    print(f"  Warnings: {len(warnings)}")
    print(f"  Passed: {info.get('passed')}")
    print(f"  formatter_root_used: {info.get('formatter_root_used')}")
    print(f"  evidence_map_used: {info.get('evidence_map_used')}")
    if errors:
        for e in errors:
            print(f"    ERROR: {e}")
    if warnings:
        for w in warnings:
            print(f"    WARN: {w}")
    print()
    total_errors += len(errors)

print(f"Total errors: {total_errors}")
sys.exit(1 if total_errors > 0 else 0)
