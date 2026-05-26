"""
NutriScan — settings.py
========================
Production-ready Django settings.
Reads secrets from environment variables (Railway / .env file).

Usage:
    Local:   create a .env file (see .env.example below)
    Railway: set env vars in the Railway dashboard
"""

import os
from pathlib import Path
from decouple import config, Csv
import dj_database_url

# ── Base paths ────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ── Security ──────────────────────────────────────────────────────
SECRET_KEY = config('SECRET_KEY', default='change-me-in-production-please')
DEBUG      = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# ── Application definition ────────────────────────────────────────
INSTALLED_APPS = [
    # Jazzmin MUST be before django.contrib.admin
    'jazzmin',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'crispy_forms',
    'crispy_bootstrap5',

    # NutriScan apps
    'core.apps.CoreConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # serve static on Railway
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'nutriscan_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'nutriscan_project.wsgi.application'

# ── Database ──────────────────────────────────────────────────────
# Railway injects DATABASE_URL automatically.
# Local: set DATABASE_URL=sqlite:///db.sqlite3 in .env
DATABASE_URL = config('DATABASE_URL', default=f'sqlite:///{BASE_DIR}/db.sqlite3')
DATABASES = {
    'default': dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,
        ssl_require=not DEBUG,
    )
}

# ── Password validation ───────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── Internationalisation ──────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'Asia/Jerusalem'
USE_I18N      = True
USE_TZ        = True

# ── Static & Media files ──────────────────────────────────────────
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ── Auth redirects ────────────────────────────────────────────────
LOGIN_URL          = '/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL= '/'

# ── Crispy forms ──────────────────────────────────────────────────
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK          = 'bootstrap5'

# ── ML Model paths ────────────────────────────────────────────────
ML_MODEL_PATH       = BASE_DIR / 'core/ml/weights/efficientnet_nutriscan.pth'
ML_CLASS_NAMES_PATH = BASE_DIR / 'core/ml/weights/class_names.json'

# ── USDA FoodData Central API ─────────────────────────────────────
USDA_API_KEY = config('USDA_API_KEY', default='DEMO_KEY')
USDA_API_BASE= 'https://api.nal.usda.gov/fdc/v1'

# ── Jazzmin admin theme ───────────────────────────────────────────
JAZZMIN_SETTINGS = {
    'site_title'        : 'NutriScan',
    'site_header'       : '🥗 NutriScan Admin',
    'site_brand'        : 'NutriScan',
    'welcome_sign'      : 'Welcome to NutriScan Admin Panel',
    'copyright'         : 'NutriScan',
    'search_model'      : ['auth.user', 'core.foodentry'],
    'topmenu_links'     : [
        {'name': 'Home',      'url': 'admin:index'},
        {'name': 'Site',      'url': '/', 'new_window': True},
        {'name': 'Dashboard', 'url': '/dashboard/', 'new_window': True},
    ],
    'show_sidebar'      : True,
    'navigation_expanded': True,
    'icons': {
        'auth'              : 'fas fa-users-cog',
        'auth.user'         : 'fas fa-user',
        'auth.Group'        : 'fas fa-users',
        'core.foodcache'    : 'fas fa-database',
        'core.foodentry'    : 'fas fa-camera',
        'core.userprofile'  : 'fas fa-id-card',
        'core.nutritionscore': 'fas fa-chart-bar',
    },
    'default_icon_parents' : 'fas fa-folder',
    'default_icon_children': 'fas fa-circle-dot',
    'theme'             : 'darkly',
    'dark_mode_theme'   : 'darkly',
    
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ════════════════════════════════════════════════════════════
#  .env.example  (create this file locally, never commit it)
# ════════════════════════════════════════════════════════════
# SECRET_KEY=your-secret-key-here
# DEBUG=True
# ALLOWED_HOSTS=localhost,127.0.0.1
# DATABASE_URL=sqlite:///db.sqlite3
# USDA_API_KEY=your-usda-api-key-here
