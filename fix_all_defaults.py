"""
fix_all_defaults.py
====================
Run from nutriscan/ root:
    python fix_all_defaults.py

Fixes ALL problematic |default usages in dashboard.html
"""
import pathlib, re

path = pathlib.Path('core/templates/core/dashboard.html')
content = path.read_text(encoding='utf-8')
original = content

# Fix 1: |default:user.username (variable, not string)
content = content.replace(
    '{{ user.first_name|default:user.username }}',
    '{% if user.first_name %}{{ user.first_name }}{% else %}{{ user.username }}{% endif %}'
)

# Fix 2: any remaining |default:"value" -> |default_if_none:"value"
content = re.sub(r'\|default:"([^"]*)"', r'|default_if_none:"\1"', content)
content = re.sub(r"\|default:'([^']*)'", r"|default_if_none:'\1'", content)

# Fix 3: |default:calorie_target (variable)
content = content.replace(
    '|default:2000',
    '|default_if_none:2000'
)

# Save
if content != original:
    path.write_text(content, encoding='utf-8')
    print('FIXED: dashboard.html')
    # Show remaining |default
    lines = content.splitlines()
    remaining = [(i+1, l.strip()) for i, l in enumerate(lines) if '|default' in l]
    if remaining:
        print(f'\nRemaining |default occurrences ({len(remaining)}):')
        for num, line in remaining:
            print(f'  Line {num}: {line[:100]}')
    else:
        print('No more |default issues!')
else:
    print('No changes needed')