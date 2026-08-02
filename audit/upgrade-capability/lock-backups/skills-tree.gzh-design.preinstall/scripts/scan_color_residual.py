#!/usr/bin/env python3
"""色值残留扫描：检查锤子文件不含摸鱼绿色值，摸鱼绿文件不含锤子色值。"""

moyu_tokens = ['#059669', '#10b981', '#047857', '#34d399', '#6ee7b7',
               '#a7f3d0', '#bbf7d0', '#ecfdf5', '#f0fdf4']
hammer_tokens = ['#b3593b', '#c86442', '#8a4530', '#dab1a1', '#e3c6b9', '#ead6cc']

files = {
    'target-hammer.html': 'tests/hammer-upgrade/target-hammer.html',
    'reference-moyu-green.html': 'tests/hammer-upgrade/reference-moyu-green.html',
    'theme-hammer.md': 'references/theme-hammer.md',
    'theme-moyu-green.md': 'references/theme-moyu-green.md',
}

import os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

all_pass = True
for name, path in files.items():
    with open(path, encoding='utf-8') as f:
        content = f.read().lower()

    if 'hammer' in name.lower() or 'target' in name.lower():
        found = [t for t in moyu_tokens if t in content]
        status = 'PASS' if not found else 'FAIL'
        if found:
            all_pass = False
        print(f'{name}: {status} (moyu tokens found: {found})')
    else:
        found = [t for t in hammer_tokens if t in content]
        status = 'PASS' if not found else 'FAIL'
        if found:
            all_pass = False
        print(f'{name}: {status} (hammer tokens found: {found})')

print(f"\nOverall: {'ALL PASS' if all_pass else 'HAS FAILURES'}")
