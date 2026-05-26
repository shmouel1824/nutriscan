"""
fix_urls.py
===========
Run this script from the nutriscan/ root folder:
    python fix_urls.py

It fixes all missing 'core:' namespace prefixes in:
- core/views.py          (redirect() calls)
- all HTML templates     ({% url %} tags)
"""

import os
import re

# ── Files to fix ──────────────────────────────────────────
VIEW_FILES = [
    'core/views.py',
]

TEMPLATE_FILES = [
    'templates/base.html',
    'core/templates/core/landing.html',
    'core/templates/core/analyze.html',
    'core/templates/core/result.html',
    'core/templates/core/dashboard.html',
    'core/templates/core/profile_setup.html',
    'core/templates/core/history.html',
]

# ── URL names that belong to the 'core' namespace ─────────
CORE_NAMES = [
    'landing',
    'logout',
    'profile_setup',
    'profile_edit',
    'analyze',
    'result',
    'dashboard',
    'history',
    'delete_entry',
    'api_top_foods',
]


def fix_views(filepath):
    """Fix redirect('name') → redirect('core:name') in views.py"""
    if not os.path.exists(filepath):
        print(f"  SKIP (not found): {filepath}")
        return

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    for name in CORE_NAMES:
        # redirect('name') but NOT redirect('core:name')
        content = re.sub(
            rf"redirect\('{name}'\)",
            f"redirect('core:{name}')",
            content
        )
        # redirect('name', ...) with extra args
        content = re.sub(
            rf"redirect\('{name}',",
            f"redirect('core:{name}',",
            content
        )

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  FIXED: {filepath}")
    else:
        print(f"  OK (no changes): {filepath}")


def fix_template(filepath):
    """Fix {% url 'name' %} → {% url 'core:name' %} in templates"""
    if not os.path.exists(filepath):
        print(f"  SKIP (not found): {filepath}")
        return

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    for name in CORE_NAMES:
        # {% url 'name' %} and {% url 'name' arg %}
        content = re.sub(
            rf"{{% url '{name}'",
            f"{{% url 'core:{name}'",
            content
        )

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  FIXED: {filepath}")
    else:
        print(f"  OK (no changes): {filepath}")


def main():
    print("\n NutriScan — URL namespace fixer")
    print("=" * 40)

    print("\n[1] Fixing views.py redirect() calls...")
    for f in VIEW_FILES:
        fix_views(f)

    print("\n[2] Fixing template {% url %} tags...")
    for f in TEMPLATE_FILES:
        fix_template(f)

    print("\n" + "=" * 40)
    print("Done! Restart the server:")
    print("  Ctrl+C  then  python manage.py runserver\n")


if __name__ == '__main__':
    main()
