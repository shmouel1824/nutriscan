"""
add_data_i18n.py
=================
Run from nutriscan/ root:
    python add_data_i18n.py

Adds data-i18n attributes to all translatable text elements
in all templates, and updates base.html to load translations.js
"""

import re
import pathlib

BASE = pathlib.Path('.')

# ══════════════════════════════════════════════════════════════
#  REPLACEMENTS PER TEMPLATE
#  Format: (old_html, new_html)
# ══════════════════════════════════════════════════════════════

DASHBOARD_FIXES = [
    # Stat labels
    ('<div class="stat-label">TOTAL ANALYSES</div>',
     '<div class="stat-label" data-i18n="TOTAL ANALYSES">TOTAL ANALYSES</div>'),
    ('<div class="stat-label">AVERAGE SCORE</div>',
     '<div class="stat-label" data-i18n="AVERAGE SCORE">AVERAGE SCORE</div>'),
    ('<div class="stat-label">TODAY\'S KCAL</div>',
     '<div class="stat-label" data-i18n="TODAY\'S KCAL">TODAY\'S KCAL</div>'),
    ('<div class="stat-label">BMI</div>',
     '<div class="stat-label" data-i18n="BMI">BMI</div>'),
    ('<div class="stat-sub">all time</div>',
     '<div class="stat-sub" data-i18n="all time">all time</div>'),
    ('<div class="stat-sub">out of 10</div>',
     '<div class="stat-sub" data-i18n="out of 10">out of 10</div>'),
    ('<div class="calorie-label">TODAY\'S CALORIE BUDGET</div>',
     '<div class="calorie-label" data-i18n="TODAY\'S CALORIE BUDGET">TODAY\'S CALORIE BUDGET</div>'),
    ('<div class="chart-title">7-day calorie trend</div>',
     '<div class="chart-title" data-i18n="7-day calorie trend">7-day calorie trend</div>'),
    ('<div class="chart-title">Score distribution</div>',
     '<div class="chart-title" data-i18n="Score distribution">Score distribution</div>'),
    ('<div class="section-title">Recent analyses</div>',
     '<div class="section-title" data-i18n="Recent analyses">Recent analyses</div>'),
    ('>View all →<',
     ' data-i18n="View all →">View all →<'),
    ('<div class="profile-mini-title">Most analysed</div>',
     '<div class="profile-mini-title" data-i18n="Most analysed">Most analysed</div>'),
    ('<div class="profile-mini-title">Your profile</div>',
     '<div class="profile-mini-title" data-i18n="Your profile">Your profile</div>'),
    ('<div class="profile-data-label">Goal</div>',
     '<div class="profile-data-label" data-i18n="Goal">Goal</div>'),
    ('<div class="profile-data-label">Activity</div>',
     '<div class="profile-data-label" data-i18n="Activity">Activity</div>'),
    ('<div class="profile-data-label">Daily target</div>',
     '<div class="profile-data-label" data-i18n="Daily target">Daily target</div>'),
    ('<div class="profile-data-label">TDEE</div>',
     '<div class="profile-data-label" data-i18n="TDEE">TDEE</div>'),
    ('<div class="empty-text">No food analysed yet.<br/>Start by scanning your first meal!</div>',
     '<div class="empty-text"><span data-i18n="No food analysed yet.">No food analysed yet.</span><br/><span data-i18n="Start by scanning your first meal!">Start by scanning your first meal!</span></div>'),
]

ANALYZE_FIXES = [
    ('<div class="page-kicker">food analysis</div>',
     '<div class="page-kicker" data-i18n="food analysis">food analysis</div>'),
    ('<h1 style="font-size:2rem; letter-spacing:-1px">What did you eat?</h1>',
     '<h1 style="font-size:2rem; letter-spacing:-1px" data-i18n="What did you eat?">What did you eat?</h1>'),
    ('<p style="margin-top:8px">Upload a photo, paste a link, or type the name. Our AI does the rest.</p>',
     '<p style="margin-top:8px" data-i18n="Upload a photo, paste a link, or type the name. Our AI does the rest.">Upload a photo, paste a link, or type the name. Our AI does the rest.</p>'),
    ('<div class="method-title">Upload photo</div>',
     '<div class="method-title" data-i18n="Upload photo">Upload photo</div>'),
    ('<div class="method-title">Image URL</div>',
     '<div class="method-title" data-i18n="Image URL">Image URL</div>'),
    ('<div class="method-title">Type name</div>',
     '<div class="method-title" data-i18n="Type name">Type name</div>'),
    ('<div class="drop-title">Drop your food photo here</div>',
     '<div class="drop-title" data-i18n="Drop your food photo here">Drop your food photo here</div>'),
    ('<div class="drop-sub">or click to browse — JPG, PNG, WEBP up to 10 MB</div>',
     '<div class="drop-sub" data-i18n="or click to browse — JPG, PNG, WEBP up to 10 MB">or click to browse — JPG, PNG, WEBP up to 10 MB</div>'),
    ('<span>Analyse this food</span> <span>→</span>',
     '<span data-i18n="Analyse this food →">Analyse this food →</span>'),
    ('<span style="font-size:14px">Analysing…</span>',
     '<span style="font-size:14px" data-i18n="Analysing…">Analysing…</span>'),
]

RESULT_FIXES = [
    ('<div class="food-label">Identified food</div>',
     '<div class="food-label" data-i18n="Identified food">Identified food</div>'),
    ('<div class="food-label" style="margin-bottom:10px">Alternative predictions</div>',
     '<div class="food-label" style="margin-bottom:10px" data-i18n="Alternative predictions">Alternative predictions</div>'),
    ('<h3 style="font-size:1rem;color:var(--text-2);font-weight:600;margin-bottom:16px;font-family:var(--font-mono);text-transform:uppercase;letter-spacing:0.5px">Score breakdown</h3>',
     '<h3 style="font-size:1rem;color:var(--text-2);font-weight:600;margin-bottom:16px;font-family:var(--font-mono);text-transform:uppercase;letter-spacing:0.5px" data-i18n="Score breakdown">Score breakdown</h3>'),
    ('<div class="nutrients-title">Full nutrition breakdown</div>',
     '<div class="nutrients-title" data-i18n="Full nutrition breakdown">Full nutrition breakdown</div>'),
    ('<div class="rec-portion-label">Recommended for you</div>',
     '<div class="rec-portion-label" data-i18n="Recommended for you">Recommended for you</div>'),
    ('<div class="feedback-title green">✓ Strengths</div>',
     '<div class="feedback-title green" data-i18n="✓ Strengths">✓ Strengths</div>'),
    ('<div class="feedback-title amber">⚠ Watch out for</div>',
     '<div class="feedback-title amber" data-i18n="⚠ Watch out for">⚠ Watch out for</div>'),
    ('>Analyse another food →<',
     ' data-i18n="Analyse another food →">Analyse another food →<'),
    ('>Delete entry<',
     ' data-i18n="Delete entry">Delete entry<'),
    ('<div class="feedback-item" style="color:var(--text-3)">No notable strengths found.</div>',
     '<div class="feedback-item" style="color:var(--text-3)" data-i18n="No notable strengths found.">No notable strengths found.</div>'),
    ('<div class="feedback-item" style="color:var(--text-3)">No concerns for your profile.</div>',
     '<div class="feedback-item" style="color:var(--text-3)" data-i18n="No concerns for your profile.">No concerns for your profile.</div>'),
]

HISTORY_FIXES = [
    ('<h2 style="font-size:1.8rem;letter-spacing:-0.5px">Food history</h2>',
     '<h2 style="font-size:1.8rem;letter-spacing:-0.5px" data-i18n="Food history">Food history</h2>'),
    ('>+ Analyse food<',
     ' data-i18n="+ Analyse food">+ Analyse food<'),
    ('<option value="">All scores</option>',
     '<option value="" data-i18n="All scores">All scores</option>'),
    ('>Filter<',
     ' data-i18n="Filter">Filter<'),
    ('>✕ Clear<',
     ' data-i18n="✕ Clear">✕ Clear<'),
    ('<p>No entries match your filters.</p>',
     '<p data-i18n="No entries match your filters.">No entries match your filters.</p>'),
    ('>Clear filters<',
     ' data-i18n="Clear filters">Clear filters<'),
]

PROFILE_FIXES = [
    ('<div class="step-label">Body metrics</div>',
     '<div class="step-label" data-i18n="Body metrics">Body metrics</div>'),
    ('<div class="step-label">Lifestyle</div>',
     '<div class="step-label" data-i18n="Lifestyle">Lifestyle</div>'),
    ('<div class="section-title">Body metrics</div>',
     '<div class="section-title" data-i18n="Body metrics">Body metrics</div>'),
    ('<div class="section-desc">Used to compute your BMI and daily calorie target (TDEE).</div>',
     '<div class="section-desc" data-i18n="Used to compute your BMI and daily calorie target (TDEE).">Used to compute your BMI and daily calorie target (TDEE).</div>'),
    ('<div class="section-title">Lifestyle</div>',
     '<div class="section-title" data-i18n="Lifestyle">Lifestyle</div>'),
    ('<div class="section-title">Medical &amp; dietary flags</div>',
     '<div class="section-title" data-i18n="Medical & dietary flags">Medical &amp; dietary flags</div>'),
    ('<div class="section-desc">These affect your personalised score — high-risk items are flagged automatically.</div>',
     '<div class="section-desc" data-i18n="These affect your personalised score — high-risk items are flagged automatically.">These affect your personalised score — high-risk items are flagged automatically.</div>'),
    ('<span class="ns-checkbox-label">🩺 Diabetes</span>',
     '<span class="ns-checkbox-label" data-i18n="🩺 Diabetes">🩺 Diabetes</span>'),
    ('<span class="ns-checkbox-label">❤️ Hypertension</span>',
     '<span class="ns-checkbox-label" data-i18n="❤️ Hypertension">❤️ Hypertension</span>'),
    ('<span class="ns-checkbox-label">🌿 Vegetarian</span>',
     '<span class="ns-checkbox-label" data-i18n="🌿 Vegetarian">🌿 Vegetarian</span>'),
    ('<span class="ns-checkbox-label">🌱 Vegan</span>',
     '<span class="ns-checkbox-label" data-i18n="🌱 Vegan">🌱 Vegan</span>'),
    ('<span class="ns-checkbox-label">🌾 Gluten intolerant</span>',
     '<span class="ns-checkbox-label" data-i18n="🌾 Gluten intolerant">🌾 Gluten intolerant</span>'),
    ('<span class="ns-checkbox-label">🥛 Lactose intolerant</span>',
     '<span class="ns-checkbox-label" data-i18n="🥛 Lactose intolerant">🥛 Lactose intolerant</span>'),
    ('<span class="ns-checkbox-label">🥜 Nut allergy</span>',
     '<span class="ns-checkbox-label" data-i18n="🥜 Nut allergy">🥜 Nut allergy</span>'),
    ('>Next step →<',
     ' data-i18n="Next step →">Next step →<'),
    ('>← Back<',
     ' data-i18n="← Back">← Back<'),
    ('>Save profile ✓<',
     ' data-i18n="Save profile ✓">Save profile ✓<'),
    ('<div class="steps-title">Setup steps</div>',
     '<div class="steps-title" data-i18n="Setup steps">Setup steps</div>'),
]

ALL_TEMPLATES = {
    'core/templates/core/dashboard.html'    : DASHBOARD_FIXES,
    'core/templates/core/analyze.html'      : ANALYZE_FIXES,
    'core/templates/core/result.html'       : RESULT_FIXES,
    'core/templates/core/history.html'      : HISTORY_FIXES,
    'core/templates/core/profile_setup.html': PROFILE_FIXES,
}

# ══════════════════════════════════════════════════════════════
#  PATCH base.html — add translations.js
# ══════════════════════════════════════════════════════════════
def patch_base_html():
    path = BASE / 'templates' / 'base.html'
    if not path.exists():
        print('  SKIP: templates/base.html not found')
        return

    content = path.read_text(encoding='utf-8')
    changed = False

    # Add {% load static %} if not present
    if '{% load static %}' not in content:
        content = content.replace(
            '{% load i18n %}',
            '{% load i18n %}\n{% load static %}'
        )
        changed = True
        print('  Added {% load static %}')

    # Add translations.js before </body>
    if 'translations.js' not in content:
        content = content.replace(
            '{% block extra_js %}{% endblock %}\n</body>',
            '{% block extra_js %}{% endblock %}\n'
            '<script src="{% static \'js/nutriscan_translations.js\' %}"></script>\n'
            '</body>'
        )
        # Also try alternate format
        if 'translations.js' not in content:
            content = content.replace(
                '</body>',
                '<script src="{% static \'js/nutriscan_translations.js\' %}"></script>\n</body>',
                1
            )
        changed = True
        print('  Added translations.js script tag')

    # Update lang switcher buttons to use NutriLang.set()
    if 'NutriLang.set' not in content:
        content = content.replace(
            "onclick=\"setLang('en')\"",
            "onclick=\"NutriLang.set('en')\""
        )
        content = content.replace(
            "onclick=\"setLang('he')\"",
            "onclick=\"NutriLang.set('he')\""
        )
        # Add data-lang attributes
        content = content.replace(
            "class=\"lang-btn {% if CURRENT_LANG == 'en' %}active{% endif %}\"\n                onclick=\"NutriLang.set('en')\">",
            "class=\"lang-btn {% if CURRENT_LANG == 'en' %}active{% endif %}\" data-lang=\"en\"\n                onclick=\"NutriLang.set('en')\">"
        )
        content = content.replace(
            "class=\"lang-btn {% if CURRENT_LANG == 'he' %}active{% endif %}\"\n                onclick=\"NutriLang.set('he')\">",
            "class=\"lang-btn {% if CURRENT_LANG == 'he' %}active{% endif %}\" data-lang=\"he\"\n                onclick=\"NutriLang.set('he')\">"
        )
        changed = True
        print('  Updated lang buttons to use NutriLang.set()')

    if changed:
        path.write_text(content, encoding='utf-8')
        print('  base.html saved')
    else:
        print('  base.html OK (no changes needed)')


# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════
print('\nNutriScan — data-i18n attribute fixer')
print('=' * 50)

# Create static/js/ folder
js_dir = BASE / 'static' / 'js'
js_dir.mkdir(parents=True, exist_ok=True)
print(f'\n[0] Created: {js_dir}')
print('    Place nutriscan_translations.js in this folder!')

print('\n[1] Patching base.html...')
patch_base_html()

print('\n[2] Adding data-i18n to templates...')
total = 0
for filepath, fixes in ALL_TEMPLATES.items():
    path = BASE / filepath
    if not path.exists():
        print(f'  SKIP (not found): {filepath}')
        continue

    content = path.read_text(encoding='utf-8')
    original = content
    count = 0

    for old, new in fixes:
        if old in content and new not in content:
            content = content.replace(old, new)
            count += 1

    if content != original:
        path.write_text(content, encoding='utf-8')
        print(f'  FIXED ({count} changes): {filepath}')
        total += count
    else:
        print(f'  OK: {filepath}')

print('\n' + '=' * 50)
print(f'Total changes: {total}')
print("""
Next steps:
1. Copy nutriscan_translations.js to static/js/
2. Run: python manage.py collectstatic --noinput
3. Restart: python manage.py runserver
4. Ctrl+Shift+R in browser
""")