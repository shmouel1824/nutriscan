"""
NutriScan — signals.py
======================
Django signals to automate UserProfile lifecycle.

- post_save on User  → create / update UserProfile automatically
- post_save on UserProfile → recompute daily_calorie_target (TDEE)

Register in apps.py: ready() calls signals import.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create an empty UserProfile whenever a new User is registered."""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Keep the profile in sync when User is saved."""
    if hasattr(instance, 'profile'):
        instance.profile.save()


@receiver(post_save, sender=UserProfile)
def update_calorie_target(sender, instance, **kwargs):
    """
    Recompute and cache daily_calorie_target whenever profile is saved.
    Adjusts for health goal:
        lose_weight   → TDEE - 500 kcal
        maintain      → TDEE
        gain_muscle   → TDEE + 300 kcal
        improve_health→ TDEE
    Uses update_fields to avoid infinite save loop.
    """
    tdee = instance.tdee
    if tdee is None:
        return  # body data not yet complete

    goal_adjustment = {
        'lose_weight'   : -500,
        'maintain'      :    0,
        'gain_muscle'   :  300,
        'improve_health':    0,
    }
    adjustment = goal_adjustment.get(instance.health_goal, 0)
    target     = max(1200, tdee + adjustment)   # never go below 1200 kcal

    # Only write if changed — prevents recursion
    if instance.daily_calorie_target != target:
        UserProfile.objects.filter(pk=instance.pk).update(
            daily_calorie_target=target
        )
