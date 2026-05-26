"""
fix_load_i18n.py
=================
Run from nutriscan/ root:
    python fix_load_i18n.py

Adds {% load i18n %} to every child template that uses {% trans %}
"""
import pathlib

TEMPLATES = [
    'core/templates/core/dashboard.html',
    'core/templates/core/analyze.html',
    'core/templates/core/result.html',
    'core/templates/core/history.html',
    'core/templates/core/profile_setup.html',
    'core/templates/core/landing.html',
    'templates/base.html',
]

print('\nNutriScan — Fix {% load i18n %}')
print('=' * 45)

for filepath in TEMPLATES:
    path = pathlib.Path(filepath)
    if not path.exists():
        print(f'  SKIP: {filepath}')
        continue

    content = path.read_text(encoding='utf-8')
    original = content

    # Fix base.html — remove duplicate {% load i18n %} from body
    if filepath == 'templates/base.html':
        # Remove the duplicate inside <body>
        content = content.replace(
            '  {% load i18n %}\n  {% get_current_language as CURRENT_LANG %}\n\n  {% if user.is_authenticated %}',
            '  {% if user.is_authenticated %}'
        )
        # Make sure top has both loads
        if not content.startswith('{% load i18n %}'):
            content = '{% load i18n %}\n{% get_current_language as CURRENT_LANG %}\n{% load static %}\n' + content

    else:
        # For child templates — add {% load i18n %} after extends tag
        if '{% load i18n %}' not in content:
            content = content.replace(
                "{% extends 'base.html' %}",
                "{% extends 'base.html' %}\n{% load i18n %}"
            )

    if content != original:
        path.write_text(content, encoding='utf-8')
        print(f'  FIXED: {filepath}')
    else:
        print(f'  OK: {filepath}')

print('\n' + '=' * 45)
print('Done! Restart server and Ctrl+Shift+R')