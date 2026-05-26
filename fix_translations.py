"""
fix_translations.py
====================
Run from nutriscan/ root:
    python fix_translations.py

Adds {% trans "..." %} tags to all template text strings
that are not yet translated.
"""

import re
import pathlib

TEMPLATES = {
    'core/templates/core/dashboard.html': [
        ('Total analyses',          '{% trans "Total analyses" %}'),
        ('Average score',           '{% trans "Average score" %}'),
        ("Today's kcal",            '{% trans "Today\'s kcal" %}'),
        ('all time',                '{% trans "all time" %}'),
        ('out of 10',               '{% trans "out of 10" %}'),
        ('7-day calorie trend',     '{% trans "7-day calorie trend" %}'),
        ('Score distribution',      '{% trans "Score distribution" %}'),
        ('Recent analyses',         '{% trans "Recent analyses" %}'),
        ('View all',                '{% trans "View all" %}'),
        ('Most analysed',           '{% trans "Most analysed" %}'),
        ('Your profile',            '{% trans "Your profile" %}'),
        ("Today's calorie budget",  '{% trans "Today\'s calorie budget" %}'),
        ('No food analysed yet.',   '{% trans "No food analysed yet." %}'),
        ('Start by scanning your first meal!', '{% trans "Start by scanning your first meal!" %}'),
        ('+ Analyse food',          '{% trans "+ Analyse food" %}'),
        ('Good day,',               '{% trans "Good day," %}'),
        ('Edit profile',            '{% trans "Edit profile" %}'),
    ],
    'core/templates/core/analyze.html': [
        ('What did you eat?',       '{% trans "What did you eat?" %}'),
        ('Upload photo',            '{% trans "Upload photo" %}'),
        ('Image URL',               '{% trans "Image URL" %}'),
        ('Type name',               '{% trans "Type name" %}'),
        ('Drop your food photo here','{% trans "Drop your food photo here" %}'),
        ('or click to browse',      '{% trans "or click to browse" %}'),
        ('Portion size (grams)',     '{% trans "Portion size (grams)" %}'),
        ('Analyse this food',       '{% trans "Analyse this food" %}'),
        ('Analysing',               '{% trans "Analysing" %}'),
    ],
    'core/templates/core/result.html': [
        ('Identified food',         '{% trans "Identified food" %}'),
        ('Alternative predictions', '{% trans "Alternative predictions" %}'),
        ('Score breakdown',         '{% trans "Score breakdown" %}'),
        ('Full nutrition breakdown','{% trans "Full nutrition breakdown" %}'),
        ('Recommended for you',     '{% trans "Recommended for you" %}'),
        ('Strengths',               '{% trans "Strengths" %}'),
        ('Watch out for',           '{% trans "Watch out for" %}'),
        ('Analyse another food',    '{% trans "Analyse another food" %}'),
        ('Delete entry',            '{% trans "Delete entry" %}'),
    ],
    'core/templates/core/history.html': [
        ('Food history',            '{% trans "Food history" %}'),
        ('All scores',              '{% trans "All scores" %}'),
        ('Filter',                  '{% trans "Filter" %}'),
        ('+ Analyse food',          '{% trans "+ Analyse food" %}'),
    ],
    'core/templates/core/profile_setup.html': [
        ('Body metrics',            '{% trans "Body metrics" %}'),
        ('Lifestyle',               '{% trans "Lifestyle" %}'),
        ('Medical',                 '{% trans "Medical" %}'),
        ('Next step',               '{% trans "Next step" %}'),
        ('Save profile',            '{% trans "Save profile" %}'),
        ('Back',                    '{% trans "Back" %}'),
        ('Diabetes',                '{% trans "Diabetes" %}'),
        ('Hypertension',            '{% trans "Hypertension" %}'),
        ('Vegetarian',              '{% trans "Vegetarian" %}'),
        ('Vegan',                   '{% trans "Vegan" %}'),
        ('Gluten intolerant',       '{% trans "Gluten intolerant" %}'),
        ('Lactose intolerant',      '{% trans "Lactose intolerant" %}'),
        ('Nut allergy',             '{% trans "Nut allergy" %}'),
    ],
}

print('\nNutriScan — Translation fixer')
print('=' * 45)

total_fixes = 0

for filepath, replacements in TEMPLATES.items():
    path = pathlib.Path(filepath)
    if not path.exists():
        print(f'  SKIP (not found): {filepath}')
        continue

    content = path.read_text(encoding='utf-8')
    original = content
    fixes = 0

    # Make sure {% load i18n %} and {% load custom_filters %} are present
    if '{% load i18n %}' not in content:
        # Add after the first line (extends tag)
        content = content.replace(
            "{% extends 'base.html' %}",
            "{% extends 'base.html' %}\n{% load i18n %}"
        )
        fixes += 1

    for old_text, new_text in replacements:
        # Only replace plain text inside HTML tags, not already translated ones
        # Skip if already wrapped in {% trans %}
        if f'{{% trans "{old_text}"' in content:
            continue
        if f'{{% trans \'{old_text}\'' in content:
            continue

        # Replace in common HTML patterns
        for pattern in [
            f'>{old_text}<',
            f'>{old_text} <',
        ]:
            replacement = pattern.replace(old_text, new_text)
            if pattern in content:
                content = content.replace(pattern, replacement)
                fixes += 1

    if content != original:
        path.write_text(content, encoding='utf-8')
        print(f'  FIXED ({fixes} changes): {filepath}')
        total_fixes += fixes
    else:
        print(f'  OK: {filepath}')

print('=' * 45)
print(f'Total fixes: {total_fixes}')
print('\nRefresh browser with Ctrl+Shift+R')