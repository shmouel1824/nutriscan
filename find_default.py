"""
find_default.py
===============
Run from nutriscan/ root:
    python find_default.py

Finds ALL occurrences of |default in all templates and shows them.
"""
import pathlib, re

TEMPLATES = [
    'core/templates/core/dashboard.html',
    'core/templates/core/analyze.html',
    'core/templates/core/result.html',
    'core/templates/core/history.html',
    'core/templates/core/profile_setup.html',
    'core/templates/core/landing.html',
]

print('\nSearching for |default in all templates...')
print('=' * 55)

for filepath in TEMPLATES:
    path = pathlib.Path(filepath)
    if not path.exists():
        continue
    lines = path.read_text(encoding='utf-8').splitlines()
    found = False
    for i, line in enumerate(lines, 1):
        if '|default' in line:
            if not found:
                print(f'\n{filepath}:')
                found = True
            print(f'  Line {i:>4}: {line.strip()[:100]}')

print('\n' + '=' * 55)
print('Fix: replace |default with |default_if_none in lines above')