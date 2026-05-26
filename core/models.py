"""
NutriScan — models.py
=====================
Database schema for the NutriScan food recognition & nutrition app.

Models:
    UserProfile     — extends Django User with body data, goals, medical flags
    FoodCache       — cached USDA API results (avoid redundant API calls)
    FoodEntry       — one food analysis event per user (history log)
    NutritionScore  — detailed score breakdown linked to a FoodEntry
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import json


# ══════════════════════════════════════════════════════════════════════════════
#  CHOICES
# ══════════════════════════════════════════════════════════════════════════════

class ActivityLevel(models.TextChoices):
    SEDENTARY  = 'sedentary',  'Sedentary (desk job, little exercise)'
    LIGHT      = 'light',      'Lightly Active (1–3 days/week)'
    MODERATE   = 'moderate',   'Moderately Active (3–5 days/week)'
    ACTIVE     = 'active',     'Very Active (6–7 days/week)'
    ATHLETE    = 'athlete',    'Athlete / Intense daily training'


class HealthGoal(models.TextChoices):
    LOSE_WEIGHT   = 'lose_weight',   'Lose Weight'
    MAINTAIN      = 'maintain',      'Maintain Weight'
    GAIN_MUSCLE   = 'gain_muscle',   'Gain Muscle / Bulk'
    IMPROVE_HEALTH= 'improve_health','Improve General Health'


class BiologicalSex(models.TextChoices):
    MALE    = 'male',   'Male'
    FEMALE  = 'female', 'Female'
    OTHER   = 'other',  'Prefer not to say'


class InputMethod(models.TextChoices):
    IMAGE_UPLOAD = 'image_upload', 'Image Upload'
    IMAGE_URL    = 'image_url',    'Image URL'
    TEXT_NAME    = 'text_name',    'Food Name (text)'


class ScoreLevel(models.TextChoices):
    EXCELLENT = 'excellent', 'Excellent'
    GOOD      = 'good',      'Good'
    MODERATE  = 'moderate',  'Moderate'
    POOR      = 'poor',      'Poor'
    AVOID     = 'avoid',     'Avoid'


# ══════════════════════════════════════════════════════════════════════════════
#  USER PROFILE
# ══════════════════════════════════════════════════════════════════════════════

class UserProfile(models.Model):
    """
    Extends Django's built-in User model with body metrics,
    lifestyle data, health goals, and medical flags.
    One-to-one with User — created automatically on registration.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    # ── Body metrics ──────────────────────────────────────────────
    age = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(10), MaxValueValidator(120)],
        null=True, blank=True,
        help_text='Age in years'
    )
    biological_sex = models.CharField(
        max_length=10,
        choices=BiologicalSex.choices,
        default=BiologicalSex.OTHER
    )
    height_cm = models.DecimalField(
        max_digits=5, decimal_places=1,
        validators=[MinValueValidator(50), MaxValueValidator(300)],
        null=True, blank=True,
        help_text='Height in centimetres'
    )
    weight_kg = models.DecimalField(
        max_digits=5, decimal_places=1,
        validators=[MinValueValidator(10), MaxValueValidator(500)],
        null=True, blank=True,
        help_text='Weight in kilograms'
    )

    # ── Lifestyle ─────────────────────────────────────────────────
    activity_level = models.CharField(
        max_length=20,
        choices=ActivityLevel.choices,
        default=ActivityLevel.MODERATE
    )
    health_goal = models.CharField(
        max_length=20,
        choices=HealthGoal.choices,
        default=HealthGoal.MAINTAIN
    )

    # ── Medical flags (boolean checkboxes) ───────────────────────
    has_diabetes      = models.BooleanField(default=False, verbose_name='Diabetes')
    has_hypertension  = models.BooleanField(default=False, verbose_name='Hypertension')
    is_vegetarian     = models.BooleanField(default=False, verbose_name='Vegetarian')
    is_vegan          = models.BooleanField(default=False, verbose_name='Vegan')
    is_gluten_free    = models.BooleanField(default=False, verbose_name='Gluten Intolerant')
    is_lactose_free   = models.BooleanField(default=False, verbose_name='Lactose Intolerant')
    has_nut_allergy   = models.BooleanField(default=False, verbose_name='Nut Allergy')

    # ── Computed / cached fields ──────────────────────────────────
    daily_calorie_target = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Auto-computed from Mifflin-St Jeor + activity factor'
    )

    # ── Timestamps ────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ── Properties ───────────────────────────────────────────────
    @property
    def bmi(self):
        """Body Mass Index — returns None if data incomplete."""
        if self.height_cm and self.weight_kg:
            h_m = float(self.height_cm) / 100
            return round(float(self.weight_kg) / (h_m ** 2), 1)
        return None

    @property
    def bmi_category(self):
        """WHO BMI classification string."""
        bmi = self.bmi
        if bmi is None:
            return 'Unknown'
        if bmi < 18.5:
            return 'Underweight'
        if bmi < 25.0:
            return 'Normal weight'
        if bmi < 30.0:
            return 'Overweight'
        return 'Obese'

    @property
    def tdee(self):
        """
        Total Daily Energy Expenditure (kcal/day).
        Uses Mifflin-St Jeor BMR × activity multiplier.
        Returns None if body data is incomplete.
        """
        if not all([self.age, self.height_cm, self.weight_kg]):
            return None

        w = float(self.weight_kg)
        h = float(self.height_cm)
        a = self.age

        # Mifflin-St Jeor BMR
        if self.biological_sex == BiologicalSex.MALE:
            bmr = 10 * w + 6.25 * h - 5 * a + 5
        else:
            bmr = 10 * w + 6.25 * h - 5 * a - 161

        activity_multipliers = {
            ActivityLevel.SEDENTARY : 1.2,
            ActivityLevel.LIGHT     : 1.375,
            ActivityLevel.MODERATE  : 1.55,
            ActivityLevel.ACTIVE    : 1.725,
            ActivityLevel.ATHLETE   : 1.9,
        }
        multiplier = activity_multipliers.get(self.activity_level, 1.55)
        return round(bmr * multiplier)

    @property
    def profile_complete(self):
        """True if all required fields are filled (enables scoring)."""
        return all([self.age, self.height_cm, self.weight_kg])

    def __str__(self):
        return f"Profile({self.user.username})"

    class Meta:
        verbose_name        = 'User Profile'
        verbose_name_plural = 'User Profiles'


# ══════════════════════════════════════════════════════════════════════════════
#  FOOD CACHE  (USDA API results)
# ══════════════════════════════════════════════════════════════════════════════

class FoodCache(models.Model):
    """
    Stores USDA FoodData Central API results to avoid redundant calls.
    Key: food_key (the Food-101 class name, e.g. 'pizza', 'sushi').
    If a key is in this table → serve from DB, skip the API call.
    Nutrition values per 100g.
    """
    # ── Identification ────────────────────────────────────────────
    food_key       = models.CharField(max_length=100, unique=True, db_index=True,
                                       help_text='Food-101 class name (snake_case)')
    food_name      = models.CharField(max_length=200,
                                       help_text='Human-readable name')
    usda_fdc_id    = models.CharField(max_length=50, blank=True,
                                       help_text='USDA FoodData Central ID')

    # ── Macronutrients (per 100g) ─────────────────────────────────
    calories_kcal  = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    protein_g      = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    fat_total_g    = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    fat_saturated_g= models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    carbs_g        = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    sugar_g        = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    fiber_g        = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    sodium_mg      = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    cholesterol_mg = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)

    # ── Key Micronutrients (per 100g) ─────────────────────────────
    vitamin_a_mcg  = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True,
                                          verbose_name='Vitamin A (µg RAE)')
    vitamin_c_mg   = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True,
                                          verbose_name='Vitamin C (mg)')
    vitamin_d_mcg  = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True,
                                          verbose_name='Vitamin D (µg)')
    vitamin_b12_mcg= models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True,
                                          verbose_name='Vitamin B12 (µg)')
    calcium_mg     = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    iron_mg        = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    potassium_mg   = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    magnesium_mg   = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    zinc_mg        = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)

    # ── Extra classification ──────────────────────────────────────
    glycemic_index  = models.PositiveSmallIntegerField(null=True, blank=True,
                                                        help_text='Approximate GI (0–100)')
    food_category   = models.CharField(max_length=100, blank=True,
                                        help_text='e.g. "Dairy", "Meat", "Grain"')
    raw_usda_json   = models.JSONField(default=dict, blank=True,
                                        help_text='Full raw USDA API response')

    # ── Cache management ──────────────────────────────────────────
    cached_at       = models.DateTimeField(auto_now_add=True)
    last_refreshed  = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.food_name} ({self.food_key})"

    class Meta:
        verbose_name        = 'Food Cache Entry'
        verbose_name_plural = 'Food Cache'
        ordering            = ['food_name']


# ══════════════════════════════════════════════════════════════════════════════
#  FOOD ENTRY  (one analysis event per user)
# ══════════════════════════════════════════════════════════════════════════════

class FoodEntry(models.Model):
    """
    One food analysis event: a user submitted food (image/url/text),
    the model identified it, and we computed a nutrition + personal score.
    This forms the user's food history / journal.
    """
    # ── Relations ─────────────────────────────────────────────────
    user       = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='food_entries'
    )
    food_cache = models.ForeignKey(
        FoodCache,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='entries',
        help_text='Linked cache entry (nutrition data source)'
    )

    # ── Input data ────────────────────────────────────────────────
    input_method  = models.CharField(max_length=20, choices=InputMethod.choices)
    image         = models.ImageField(
        upload_to='food_images/%Y/%m/',
        null=True, blank=True,
        help_text='Uploaded image file'
    )
    image_url     = models.URLField(blank=True, help_text='External image URL')
    text_input    = models.CharField(max_length=255, blank=True,
                                      help_text='Food name typed by user')

    # ── ML model predictions ──────────────────────────────────────
    predicted_food    = models.CharField(max_length=100,
                                          help_text='Top-1 prediction (food_key)')
    predicted_name    = models.CharField(max_length=200,
                                          help_text='Human-readable predicted food name')
    confidence        = models.DecimalField(max_digits=5, decimal_places=2,
                                             help_text='Model confidence % (0–100)')
    top3_predictions  = models.JSONField(default=list, blank=True,
                                          help_text='[{food, food_key, confidence}, ...]')

    # ── User-specified portion ────────────────────────────────────
    portion_g = models.PositiveSmallIntegerField(
        default=100,
        validators=[MinValueValidator(1), MaxValueValidator(2000)],
        help_text='Portion size in grams'
    )

    # ── Personalised score ────────────────────────────────────────
    score_value = models.DecimalField(
        max_digits=4, decimal_places=1,
        null=True, blank=True,
        help_text='Composite personalised score (0–10)'
    )
    score_level = models.CharField(
        max_length=10,
        choices=ScoreLevel.choices,
        blank=True
    )
    recommended_portion_g = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text='AI-recommended portion for this user (grams)'
    )
    score_summary = models.TextField(
        blank=True,
        help_text='Short explanation of the score for the user'
    )

    # ── Timestamps ────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)

    # ── Helpers ───────────────────────────────────────────────────
    @property
    def calories_for_portion(self):
        """Calories adjusted for the user-specified portion."""
        if self.food_cache and self.food_cache.calories_kcal:
            return round(float(self.food_cache.calories_kcal) * self.portion_g / 100, 1)
        return None

    @property
    def score_emoji(self):
        emoji_map = {
            ScoreLevel.EXCELLENT: '🟢',
            ScoreLevel.GOOD:      '🔵',
            ScoreLevel.MODERATE:  '🟡',
            ScoreLevel.POOR:      '🟠',
            ScoreLevel.AVOID:     '🔴',
        }
        return emoji_map.get(self.score_level, '⚪')

    def __str__(self):
        return f"{self.user.username} → {self.predicted_name} ({self.created_at:%Y-%m-%d})"

    class Meta:
        verbose_name        = 'Food Entry'
        verbose_name_plural = 'Food Entries'
        ordering            = ['-created_at']
        indexes             = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['predicted_food']),
        ]


# ══════════════════════════════════════════════════════════════════════════════
#  NUTRITION SCORE BREAKDOWN  (detailed per-nutrient scoring)
# ══════════════════════════════════════════════════════════════════════════════

class NutritionScore(models.Model):
    """
    Detailed breakdown of the personalised nutrition score for one FoodEntry.
    Stores per-category sub-scores so the frontend can render a rich report card.
    """
    entry = models.OneToOneField(
        FoodEntry,
        on_delete=models.CASCADE,
        related_name='nutrition_score'
    )

    # ── Sub-scores (0–10 each) ────────────────────────────────────
    score_calories    = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True,
                                             help_text='How well calories fit daily target')
    score_protein     = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True,
                                             help_text='Protein adequacy for goal')
    score_fat         = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True,
                                             help_text='Fat quality (penalises sat fat)')
    score_sugar       = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True,
                                             help_text='Sugar penalty')
    score_sodium      = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True,
                                             help_text='Sodium — penalised for hypertension')
    score_fiber       = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True,
                                             help_text='Fiber bonus')
    score_vitamins    = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True,
                                             help_text='Micronutrient richness')
    score_medical     = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True,
                                             help_text='Medical compatibility (diabetes, allergy…)')

    # ── Flags / warnings ─────────────────────────────────────────
    warnings          = models.JSONField(default=list, blank=True,
                                          help_text='["High sodium — watch hypertension", ...]')
    positives         = models.JSONField(default=list, blank=True,
                                          help_text='["Good protein source", ...]')
    computed_at       = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Score({self.entry}) = {self.entry.score_value}/10"

    class Meta:
        verbose_name        = 'Nutrition Score'
        verbose_name_plural = 'Nutrition Scores'
