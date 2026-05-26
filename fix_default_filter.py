"""
fix_default_filter.py
=====================
Run from nutriscan/ root:
    python fix_default_filter.py

Replaces |default:"—" with |default_if_none:"—" in all templates.
"""
import pathlib

TEMPLATES = [
    'core/templates/core/dashboard.html',
    'core/templates/core/analyze.html',
    'core/templates/core/result.html',
    'core/templates/core/history.html',
    'core/templates/core/profile_setup.html',
    'core/templates/core/landing.html',
]

print('\nFix |default filter in templates')
print('=' * 40)

for filepath in TEMPLATES:
    path = pathlib.Path(filepath)
    if not path.exists():
        print(f'  SKIP: {filepath}')
        continue
    content = path.read_text(encoding='utf-8')
    original = content
    content = content.replace('|default:"—"', '|default_if_none:"—"')
    content = content.replace("|default:'—'", "|default_if_none:'—'")
    if content != original:
        path.write_text(content, encoding='utf-8')
        print(f'  FIXED: {filepath}')
    else:
        print(f'  OK: {filepath}')

print('=' * 40)
print('Done! Restart server.')