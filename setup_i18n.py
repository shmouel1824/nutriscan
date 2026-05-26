"""
setup_i18n.py
=============
Run from nutriscan/ root:
    python setup_i18n.py

This script:
1. Creates locale/en/LC_MESSAGES/ and locale/he/LC_MESSAGES/
2. Writes the .po translation files
3. Patches settings.py (LANGUAGES, LOCALE_PATHS, LocaleMiddleware)
4. Patches nutriscan_project/urls.py (adds i18n_patterns)
5. Tries to compile messages
"""

import os, re, subprocess, pathlib

BASE = pathlib.Path('.')

# ── Step 1: Create locale folders ─────────────────────────────
print('\n[1] Creating locale folders...')
for lang in ['en', 'he']:
    path = BASE / 'locale' / lang / 'LC_MESSAGES'
    path.mkdir(parents=True, exist_ok=True)
    print(f'    Created: {path}')

# ── Step 2: Write .po files ────────────────────────────────────
print('\n[2] Writing translation files...')

EN_PO = """# NutriScan English
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\\n"
"Language: en\\n"

msgid "Analyze"
msgstr "Analyze"
msgid "Dashboard"
msgstr "Dashboard"
msgid "History"
msgstr "History"
msgid "Profile"
msgstr "Profile"
msgid "Sign out"
msgstr "Sign out"
msgid "Admin"
msgstr "Admin"
msgid "Know exactly what you eat."
msgstr "Know exactly what you eat."
msgid "Sign in"
msgstr "Sign in"
msgid "Create account"
msgstr "Create account"
msgid "Welcome back"
msgstr "Welcome back"
msgid "Get started"
msgstr "Get started"
msgid "Username"
msgstr "Username"
msgid "Password"
msgstr "Password"
msgid "Confirm"
msgstr "Confirm"
msgid "First name"
msgstr "First name"
msgid "Email"
msgstr "Email"
msgid "Admin panel"
msgstr "Admin panel"
msgid "Set Up Your Profile"
msgstr "Set Up Your Profile"
msgid "Edit Profile"
msgstr "Edit Profile"
msgid "Body metrics"
msgstr "Body metrics"
msgid "Age"
msgstr "Age"
msgid "Biological sex"
msgstr "Biological sex"
msgid "Height (cm)"
msgstr "Height (cm)"
msgid "Weight (kg)"
msgstr "Weight (kg)"
msgid "Lifestyle"
msgstr "Lifestyle"
msgid "Activity level"
msgstr "Activity level"
msgid "Health goal"
msgstr "Health goal"
msgid "Medical & dietary flags"
msgstr "Medical & dietary flags"
msgid "Diabetes"
msgstr "Diabetes"
msgid "Hypertension"
msgstr "Hypertension"
msgid "Vegetarian"
msgstr "Vegetarian"
msgid "Vegan"
msgstr "Vegan"
msgid "Gluten intolerant"
msgstr "Gluten intolerant"
msgid "Lactose intolerant"
msgstr "Lactose intolerant"
msgid "Nut allergy"
msgstr "Nut allergy"
msgid "Next step"
msgstr "Next step"
msgid "Back"
msgstr "Back"
msgid "Save profile"
msgstr "Save profile"
msgid "What did you eat?"
msgstr "What did you eat?"
msgid "Upload photo"
msgstr "Upload photo"
msgid "Image URL"
msgstr "Image URL"
msgid "Type name"
msgstr "Type name"
msgid "Portion size (grams)"
msgstr "Portion size (grams)"
msgid "Analyse this food"
msgstr "Analyse this food"
msgid "Identified food"
msgstr "Identified food"
msgid "Score breakdown"
msgstr "Score breakdown"
msgid "Full nutrition breakdown"
msgstr "Full nutrition breakdown"
msgid "Recommended for you"
msgstr "Recommended for you"
msgid "Strengths"
msgstr "Strengths"
msgid "Watch out for"
msgstr "Watch out for"
msgid "Analyse another food"
msgstr "Analyse another food"
msgid "Delete entry"
msgstr "Delete entry"
msgid "Total analyses"
msgstr "Total analyses"
msgid "Average score"
msgstr "Average score"
msgid "Today's kcal"
msgstr "Today's kcal"
msgid "Recent analyses"
msgstr "Recent analyses"
msgid "View all"
msgstr "View all"
msgid "Your profile"
msgstr "Your profile"
msgid "No food analysed yet."
msgstr "No food analysed yet."
msgid "Analyse food"
msgstr "Analyse food"
msgid "Food history"
msgstr "Food history"
msgid "All scores"
msgstr "All scores"
msgid "Filter"
msgstr "Filter"
msgid "Clear"
msgstr "Clear"
msgid "Excellent"
msgstr "Excellent"
msgid "Good"
msgstr "Good"
msgid "Moderate"
msgstr "Moderate"
msgid "Poor"
msgstr "Poor"
msgid "Avoid"
msgstr "Avoid"
"""

HE_PO = """# NutriScan Hebrew
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\\n"
"Language: he\\n"

msgid "Analyze"
msgstr "ניתוח מזון"
msgid "Dashboard"
msgstr "לוח בקרה"
msgid "History"
msgstr "היסטוריה"
msgid "Profile"
msgstr "פרופיל"
msgid "Sign out"
msgstr "התנתק"
msgid "Admin"
msgstr "ניהול"
msgid "Know exactly what you eat."
msgstr "דע בדיוק מה אתה אוכל."
msgid "Sign in"
msgstr "כניסה"
msgid "Create account"
msgstr "הרשמה"
msgid "Welcome back"
msgstr "ברוך שובך"
msgid "Get started"
msgstr "בוא נתחיל"
msgid "Username"
msgstr "שם משתמש"
msgid "Password"
msgstr "סיסמה"
msgid "Confirm"
msgstr "אימות סיסמה"
msgid "First name"
msgstr "שם פרטי"
msgid "Email"
msgstr "אימייל"
msgid "Admin panel"
msgstr "פאנל ניהול"
msgid "Set Up Your Profile"
msgstr "הגדרת פרופיל"
msgid "Edit Profile"
msgstr "עריכת פרופיל"
msgid "Body metrics"
msgstr "נתוני גוף"
msgid "Age"
msgstr "גיל"
msgid "Biological sex"
msgstr "מין ביולוגי"
msgid "Height (cm)"
msgstr "גובה (סמ)"
msgid "Weight (kg)"
msgstr "משקל (קג)"
msgid "Lifestyle"
msgstr "אורח חיים"
msgid "Activity level"
msgstr "רמת פעילות גופנית"
msgid "Health goal"
msgstr "יעד בריאותי"
msgid "Medical & dietary flags"
msgstr "נתונים רפואיים ותזונתיים"
msgid "Diabetes"
msgstr "סוכרת"
msgid "Hypertension"
msgstr "לחץ דם גבוה"
msgid "Vegetarian"
msgstr "צמחוני"
msgid "Vegan"
msgstr "טבעוני"
msgid "Gluten intolerant"
msgstr "אי סבילות לגלוטן"
msgid "Lactose intolerant"
msgstr "אי סבילות ללקטוז"
msgid "Nut allergy"
msgstr "אלרגיה לאגוזים"
msgid "Next step"
msgstr "השלב הבא"
msgid "Back"
msgstr "חזרה"
msgid "Save profile"
msgstr "שמור פרופיל"
msgid "What did you eat?"
msgstr "מה אכלת?"
msgid "Upload photo"
msgstr "העלאת תמונה"
msgid "Image URL"
msgstr "קישור לתמונה"
msgid "Type name"
msgstr "הקלד שם"
msgid "Portion size (grams)"
msgstr "גודל מנה (גרם)"
msgid "Analyse this food"
msgstr "נתח מזון זה"
msgid "Identified food"
msgstr "מזון שזוהה"
msgid "Score breakdown"
msgstr "פירוט הציון"
msgid "Full nutrition breakdown"
msgstr "פירוט תזונתי מלא"
msgid "Recommended for you"
msgstr "מומלץ עבורך"
msgid "Strengths"
msgstr "יתרונות"
msgid "Watch out for"
msgstr "שים לב ל"
msgid "Analyse another food"
msgstr "נתח מזון נוסף"
msgid "Delete entry"
msgstr "מחק רשומה"
msgid "Total analyses"
msgstr "סהכ ניתוחים"
msgid "Average score"
msgstr "ציון ממוצע"
msgid "Today's kcal"
msgstr "קלוריות היום"
msgid "Recent analyses"
msgstr "ניתוחים אחרונים"
msgid "View all"
msgstr "הצג הכל"
msgid "Your profile"
msgstr "הפרופיל שלך"
msgid "No food analysed yet."
msgstr "טרם נותח מזון."
msgid "Analyse food"
msgstr "נתח מזון"
msgid "Food history"
msgstr "היסטוריית מזון"
msgid "All scores"
msgstr "כל הציונים"
msgid "Filter"
msgstr "סינון"
msgid "Clear"
msgstr "נקה"
msgid "Excellent"
msgstr "מעולה"
msgid "Good"
msgstr "טוב"
msgid "Moderate"
msgstr "בינוני"
msgid "Poor"
msgstr "חלש"
msgid "Avoid"
msgstr "הימנע"
"""

en_path = BASE / 'locale' / 'en' / 'LC_MESSAGES' / 'django.po'
he_path = BASE / 'locale' / 'he' / 'LC_MESSAGES' / 'django.po'
en_path.write_text(EN_PO, encoding='utf-8')
he_path.write_text(HE_PO, encoding='utf-8')
print(f'    Written: {en_path}')
print(f'    Written: {he_path}')

# ── Step 3: Patch settings.py ──────────────────────────────────
print('\n[3] Patching settings.py...')
settings_path = BASE / 'nutriscan_project' / 'settings.py'
settings = settings_path.read_text(encoding='utf-8')
changed = False

if 'LANGUAGES' not in settings:
    old = "LANGUAGE_CODE = 'en-us'"
    if old not in settings:
        old = "LANGUAGE_CODE = 'en'"
    new = """LANGUAGE_CODE = 'en'

from django.utils.translation import gettext_lazy as _
LANGUAGES = [
    ('en', _('English')),
    ('he', _('Hebrew')),
]
LOCALE_PATHS = [BASE_DIR / 'locale']"""
    settings = settings.replace(old, new)
    changed = True
    print('    Added LANGUAGES + LOCALE_PATHS')
else:
    print('    LANGUAGES already present')

if 'LocaleMiddleware' not in settings:
    old = "    'django.contrib.sessions.middleware.SessionMiddleware',"
    new = """    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',"""
    settings = settings.replace(old, new)
    changed = True
    print('    Added LocaleMiddleware')
else:
    print('    LocaleMiddleware already present')

if changed:
    settings_path.write_text(settings, encoding='utf-8')
    print('    settings.py saved')

# ── Step 4: Patch urls.py ──────────────────────────────────────
print('\n[4] Patching nutriscan_project/urls.py...')
urls_path = BASE / 'nutriscan_project' / 'urls.py'
urls = urls_path.read_text(encoding='utf-8')

if 'i18n_patterns' not in urls:
    urls_path.write_text(
        "from django.contrib import admin\n"
        "from django.urls import path, include\n"
        "from django.conf.urls.i18n import i18n_patterns\n"
        "from django.conf import settings\n"
        "from django.conf.urls.static import static\n\n"
        "urlpatterns = [\n"
        "    path('admin/', admin.site.urls),\n"
        "    path('i18n/', include('django.conf.urls.i18n')),\n"
        "]\n\n"
        "urlpatterns += i18n_patterns(\n"
        "    path('', include('core.urls', namespace='core')),\n"
        "    prefix_default_language=False,\n"
        ")\n\n"
        "if settings.DEBUG:\n"
        "    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)\n"
        "    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)\n",
        encoding='utf-8'
    )
    print('    Added i18n_patterns + /i18n/ route')
else:
    print('    Already patched')

# ── Step 5: Compile messages ───────────────────────────────────
print('\n[5] Compiling messages...')
result = subprocess.run(
    ['python', 'manage.py', 'compilemessages'],
    capture_output=True, text=True
)
if result.returncode == 0:
    print('    Compiled successfully!')
else:
    print('    Could not compile automatically.')
    print('    Install gettext from:')
    print('    https://mlocati.github.io/articles/gettext-iconv-windows.html')
    print('    Then run: python manage.py compilemessages')

print('\n' + '='*50)
print('  i18n setup complete!')
print('='*50)
print("""
Next steps:
1. Replace templates/base.html with the new one (included in zip)
2. Install gettext if compilemessages failed
3. python manage.py compilemessages
4. python manage.py runserver
""")
