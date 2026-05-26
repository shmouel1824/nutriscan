"""
NutriScan — apps.py
===================
AppConfig that wires up signals on startup.
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name    = 'core'
    label   = 'core'
    verbose_name = 'NutriScan Core'

    def ready(self):
        import core.signals  # noqa: F401 — registers all signal handlers
