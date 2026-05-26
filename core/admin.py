"""
NutriScan — admin.py
====================
Django admin configuration.
Designed for Jazzmin (pip install django-jazzmin) but works with default admin too.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.db.models import Count, Avg
from .models import UserProfile, FoodCache, FoodEntry, NutritionScore


# ══════════════════════════════════════════════════════════════════════════════
#  INLINE: UserProfile inside User admin
# ══════════════════════════════════════════════════════════════════════════════

class UserProfileInline(admin.StackedInline):
    model   = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile & Health Data'
    fieldsets = (
        ('Body Metrics', {
            'fields': (
                ('age', 'biological_sex'),
                ('height_cm', 'weight_kg'),
            )
        }),
        ('Lifestyle', {
            'fields': (
                ('activity_level', 'health_goal'),
                'daily_calorie_target',
            )
        }),
        ('Medical Flags', {
            'fields': (
                ('has_diabetes', 'has_hypertension'),
                ('is_vegetarian', 'is_vegan'),
                ('is_gluten_free', 'is_lactose_free', 'has_nut_allergy'),
            )
        }),
    )


# ══════════════════════════════════════════════════════════════════════════════
#  EXTENDED USER ADMIN
# ══════════════════════════════════════════════════════════════════════════════

class UserAdmin(BaseUserAdmin):
    inlines   = [UserProfileInline]
    list_display = ['username', 'email', 'first_name', 'last_name',
                    'get_bmi', 'get_goal', 'get_entries_count', 'is_staff']

    def get_bmi(self, obj):
        try:
            bmi = obj.profile.bmi
            if bmi is None:
                return '—'
            color = '#3fb950' if 18.5 <= bmi < 25 else '#e3b341' if bmi < 30 else '#ff7b72'
            return format_html(
                '<span style="color:{}; font-weight:600">{} ({})</span>',
                color, bmi, obj.profile.bmi_category
            )
        except UserProfile.DoesNotExist:
            return '—'
    get_bmi.short_description = 'BMI'

    def get_goal(self, obj):
        try:
            return obj.profile.get_health_goal_display()
        except UserProfile.DoesNotExist:
            return '—'
    get_goal.short_description = 'Goal'

    def get_entries_count(self, obj):
        return obj.food_entries.count()
    get_entries_count.short_description = 'Analyses'


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# ══════════════════════════════════════════════════════════════════════════════
#  FOOD CACHE ADMIN
# ══════════════════════════════════════════════════════════════════════════════

@admin.register(FoodCache)
class FoodCacheAdmin(admin.ModelAdmin):
    list_display  = ['food_name', 'food_key', 'calories_kcal', 'protein_g',
                     'fat_total_g', 'sugar_g', 'sodium_mg', 'food_category', 'cached_at']
    list_filter   = ['food_category']
    search_fields = ['food_name', 'food_key', 'usda_fdc_id']
    readonly_fields = ['cached_at', 'last_refreshed', 'raw_usda_json']
    ordering      = ['food_name']

    fieldsets = (
        ('Identification', {
            'fields': ('food_key', 'food_name', 'usda_fdc_id', 'food_category', 'glycemic_index')
        }),
        ('Macronutrients (per 100g)', {
            'fields': (
                ('calories_kcal',),
                ('protein_g', 'fat_total_g', 'fat_saturated_g'),
                ('carbs_g', 'sugar_g', 'fiber_g'),
                ('sodium_mg', 'cholesterol_mg'),
            )
        }),
        ('Micronutrients (per 100g)', {
            'classes': ('collapse',),
            'fields': (
                ('vitamin_a_mcg', 'vitamin_c_mg'),
                ('vitamin_d_mcg', 'vitamin_b12_mcg'),
                ('calcium_mg', 'iron_mg'),
                ('potassium_mg', 'magnesium_mg', 'zinc_mg'),
            )
        }),
        ('Cache Info', {
            'classes': ('collapse',),
            'fields': ('cached_at', 'last_refreshed', 'raw_usda_json')
        }),
    )


# ══════════════════════════════════════════════════════════════════════════════
#  NUTRITION SCORE INLINE
# ══════════════════════════════════════════════════════════════════════════════

class NutritionScoreInline(admin.StackedInline):
    model   = NutritionScore
    can_delete = False
    readonly_fields = ['computed_at']
    fieldsets = (
        ('Sub-Scores (0–10)', {
            'fields': (
                ('score_calories', 'score_protein', 'score_fat'),
                ('score_sugar', 'score_sodium', 'score_fiber'),
                ('score_vitamins', 'score_medical'),
            )
        }),
        ('Feedback', {
            'fields': ('warnings', 'positives', 'computed_at')
        }),
    )


# ══════════════════════════════════════════════════════════════════════════════
#  FOOD ENTRY ADMIN
# ══════════════════════════════════════════════════════════════════════════════

@admin.register(FoodEntry)
class FoodEntryAdmin(admin.ModelAdmin):
    list_display  = ['get_user', 'predicted_name', 'get_confidence_badge',
                     'portion_g', 'get_score_badge', 'input_method', 'created_at']
    list_filter   = ['score_level', 'input_method', 'created_at']
    search_fields = ['user__username', 'predicted_food', 'predicted_name']
    readonly_fields = ['created_at', 'top3_predictions', 'calories_for_portion']
    inlines       = [NutritionScoreInline]
    date_hierarchy = 'created_at'

    fieldsets = (
        ('User & Input', {
            'fields': ('user', 'input_method', 'image', 'image_url', 'text_input')
        }),
        ('ML Prediction', {
            'fields': (
                ('predicted_food', 'predicted_name'),
                ('confidence', 'top3_predictions'),
                'food_cache',
            )
        }),
        ('Portion & Score', {
            'fields': (
                ('portion_g', 'calories_for_portion'),
                ('score_value', 'score_level'),
                'recommended_portion_g',
                'score_summary',
            )
        }),
        ('Timestamps', {
            'classes': ('collapse',),
            'fields': ('created_at',)
        }),
    )

    def get_user(self, obj):
        return obj.user.username
    get_user.short_description = 'User'
    get_user.admin_order_field = 'user__username'

    def get_confidence_badge(self, obj):
        pct = float(obj.confidence)
        color = '#3fb950' if pct >= 70 else '#e3b341' if pct >= 40 else '#ff7b72'
        return format_html(
            '<span style="color:{}; font-weight:600">{}%</span>',
            color, obj.confidence
        )
    get_confidence_badge.short_description = 'Confidence'

    def get_score_badge(self, obj):
        if not obj.score_value:
            return '—'
        colors = {
            'excellent': '#3fb950',
            'good':      '#58a6ff',
            'moderate':  '#e3b341',
            'poor':      '#f0883e',
            'avoid':     '#ff7b72',
        }
        color = colors.get(obj.score_level, '#8b949e')
        return format_html(
            '<span style="color:{}; font-weight:700">{}/10 {}</span>',
            color, obj.score_value, obj.score_emoji
        )
    get_score_badge.short_description = 'Score'

    def calories_for_portion(self, obj):
        cal = obj.calories_for_portion
        return f"{cal} kcal" if cal else "—"
    calories_for_portion.short_description = 'Calories (portion)'


# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN SITE CUSTOMISATION
# ══════════════════════════════════════════════════════════════════════════════

admin.site.site_header  = '🥗 NutriScan Admin'
admin.site.site_title   = 'NutriScan'
admin.site.index_title  = 'NutriScan Control Panel'
