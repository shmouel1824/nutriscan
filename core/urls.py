"""
NutriScan — urls.py  (core app)
================================
App-level URL patterns for the core app.
Include this in the project urls.py with:
    path('', include('core.urls')),
"""

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [

    # ── Auth ──────────────────────────────────────────────────────
    path('',
         views.landing_view,
         name='landing'),

    path('logout/',
         views.logout_view,
         name='logout'),

    # ── Profile ───────────────────────────────────────────────────
    path('profile/setup/',
         views.profile_setup_view,
         name='profile_setup'),

    path('profile/edit/',
         views.profile_edit_view,
         name='profile_edit'),

    # ── Core flow ─────────────────────────────────────────────────
    path('analyze/',
         views.analyze_view,
         name='analyze'),

    path('result/<int:entry_id>/',
         views.result_view,
         name='result'),

    # ── Dashboard & History ───────────────────────────────────────
    path('dashboard/',
         views.dashboard_view,
         name='dashboard'),

    path('history/',
         views.history_view,
         name='history'),

    path('entry/<int:entry_id>/delete/',
         views.delete_entry_view,
         name='delete_entry'),

    # ── Internal JSON API ─────────────────────────────────────────
    path('api/top-foods/',
         views.api_top_foods_view,
         name='api_top_foods'),
]
