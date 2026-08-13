#!/usr/bin/env python3
from pathlib import Path
import re, sys, yaml

root = Path(__file__).resolve().parents[1]
required = [
    'SKILL.md', 'README.md',
    'references/workflow.md', 'references/research-evidence.md',
    'references/core-finding.md', 'references/structure-design.md',
    'references/drafting.md', 'references/editorial-review.md',
    'references/edit-learning.md', 'references/handoff.md',
    'templates/writing-brief.md', 'templates/evidence-map.md',
    'templates/core-card.md', 'templates/outline.md',
    'templates/editor-report.md'
]
errors = []
for rel in required:
    if not (root / rel).exists():
        errors.append(f'missing: {rel}')

skill = (root / 'SKILL.md').read_text(encoding='utf-8')
m = re.match(r'^---\n(.*?)\n---\n', skill, re.S)
if not m:
    errors.append('SKILL.md frontmatter missing')
else:
    try:
        meta = yaml.safe_load(m.group(1))
        for key in ('name', 'description'):
            if not meta.get(key): errors.append(f'frontmatter missing {key}')
    except Exception as exc:
        errors.append(f'invalid YAML frontmatter: {exc}')

for link in re.findall(r'`((?:references|templates|profiles)/[^`]+)`', skill):
    if not (root / link).exists():
        errors.append(f'broken reference in SKILL.md: {link}')

if errors:
    print('\n'.join('ERROR ' + e for e in errors))
    sys.exit(1)
print(f'OK: {len(required)} required files; all SKILL.md references resolve')
