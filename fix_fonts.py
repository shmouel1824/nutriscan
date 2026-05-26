"""
fix_fonts.py
============
Run from nutriscan/ root:
    python fix_fonts.py

Replaces var(--font-display) with var(--font-body) for all
numeric display elements across all templates.
"""

import os
import re

TEMPLATES = [
    'templates/base.html',
    'core/templates/core/dashboard.html',
    'core/templates/core/result.html',
    'core/templates/core/profile_setup.html',
    'core/templates/core/history.html',
    'core/templates/core/analyze.html',
    'core/templates/core/landing.html',
]

# CSS classes that display numbers — switch to body font
NUMERIC_CLASSES = [
    'stat-value',
    'calorie-current',
    'calorie-vals',
    'rec-portion-val',
    'entry-score',
    'spi-val',
    'portion-value',
    'bmi-num',
    'sub-score-val',
    'score-ring-text',
    'history-card-score',
    'stat-pill',
    'hero-footer',
]


def fix_file(filepath):
    if not os.path.exists(filepath):
        print(f"  SKIP (not found): {filepath}")
        return

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    changes = 0

    for cls in NUMERIC_CLASSES:
        # Match the CSS rule block for this class and replace font-display
        pattern = rf'(\.{cls}\s*{{[^}}]*?)var\(--font-display\)'
        while re.search(pattern, content, re.DOTALL):
            content = re.sub(
                pattern,
                r'\1var(--font-body)',
                content,
                flags=re.DOTALL
            )
            changes += 1

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  FIXED ({changes} replacements): {filepath}")
    else:
        print(f"  OK (no changes): {filepath}")


def main():
    print("\n NutriScan — Font fixer (numbers → DM Sans)")
    print("=" * 45)
    for f in TEMPLATES:
        fix_file(f)
    print("=" * 45)
    print("Done! Refresh your browser (Ctrl+Shift+R)\n")


if __name__ == '__main__':
    main()