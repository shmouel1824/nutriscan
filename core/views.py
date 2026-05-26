"""
NutriScan — views.py
=====================
All views for the NutriScan food recognition & nutrition app.

Views:
    landing_view        GET/POST  /            Login + Register tabs
    logout_view         POST      /logout/
    profile_setup_view  GET/POST  /profile/setup/   First-time profile wizard
    profile_edit_view   GET/POST  /profile/edit/    Update profile anytime
    analyze_view        GET/POST  /analyze/          Main food analysis page
    result_view         GET       /result/<id>/      Detailed analysis result
    dashboard_view      GET       /dashboard/        User food history + stats
    history_view        GET       /history/          Full paginated history
    delete_entry_view   POST      /entry/<id>/delete/
    api_top_foods_view  GET       /api/top-foods/    JSON — for dashboard chart
"""

import json
import logging
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Avg, Count, Sum
from django.core.paginator import Paginator
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import UserProfile, FoodCache, FoodEntry, NutritionScore, ScoreLevel
from .forms import RegisterForm, UserProfileForm, FoodInputForm

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _get_or_create_profile(user):
    """Return UserProfile, creating one if it doesn't exist yet."""
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def _needs_profile_setup(user):
    """True if the user hasn't filled in their body data yet."""
    try:
        return not user.profile.profile_complete
    except UserProfile.DoesNotExist:
        return True


# ══════════════════════════════════════════════════════════════════════════════
#  LANDING  —  login / register
# ══════════════════════════════════════════════════════════════════════════════

def landing_view(request):
    """
    Public landing page.
    - GET  : show login form (register form available via tab)
    - POST : handle login OR register depending on 'action' hidden field
    Authenticated users are redirected to dashboard.
    """
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    login_errors    = {}
    register_form   = RegisterForm()
    active_tab      = 'login'          # which tab to show after a failed submit

    # ── LOGIN ─────────────────────────────────────────────────────
    if request.method == 'POST' and request.POST.get('action') == 'login':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', '')
            if next_url:
                return redirect(next_url)
            if _needs_profile_setup(user):
                return redirect('core:profile_setup')
            return redirect('core:dashboard')
        else:
            login_errors['error'] = 'Invalid username or password.'
            active_tab = 'login'

    # ── REGISTER ──────────────────────────────────────────────────
    elif request.method == 'POST' and request.POST.get('action') == 'register':
        register_form = RegisterForm(request.POST)
        active_tab    = 'register'

        if register_form.is_valid():
            user = register_form.save()
            login(request, user)
            messages.success(request, f"Welcome to NutriScan, {user.first_name or user.username}! "
                                       f"Let's set up your profile.")
            return redirect('core:profile_setup')

    context = {
        'register_form' : register_form,
        'login_errors'  : login_errors,
        'active_tab'    : active_tab,
    }
    return render(request, 'core/landing.html', context)


# ══════════════════════════════════════════════════════════════════════════════
#  LOGOUT
# ══════════════════════════════════════════════════════════════════════════════

@require_POST
def logout_view(request):
    logout(request)
    return redirect('core:landing')


# ══════════════════════════════════════════════════════════════════════════════
#  PROFILE SETUP  (first-time wizard)
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def profile_setup_view(request):
    """
    First-time profile setup shown right after registration.
    Saves body metrics, activity level, goal, and medical flags.
    After saving → redirect to analyze page.
    """
    profile = _get_or_create_profile(request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile saved! Now let's analyse some food 🥗")
            return redirect('core:analyze')
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'core/profile_setup.html', {
        'form'        : form,
        'setup_mode'  : True,
        'page_title'  : 'Set Up Your Profile',
    })


# ══════════════════════════════════════════════════════════════════════════════
#  PROFILE EDIT
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def profile_edit_view(request):
    """Update profile at any time from the dashboard."""
    profile = _get_or_create_profile(request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('core:dashboard')
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'core/profile_setup.html', {
        'form'       : form,
        'setup_mode' : False,
        'page_title' : 'Edit Profile',
        'profile'    : profile,
    })


# ══════════════════════════════════════════════════════════════════════════════
#  ANALYZE  —  main food input page
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def analyze_view(request):
    """
    GET  : show the food input form (upload / URL / text)
    POST : run ML prediction → fetch nutrition → compute score → save entry
           → redirect to result page
    """
    profile = _get_or_create_profile(request.user)

    # Nudge user to complete profile if needed
    if not profile.profile_complete:
        messages.warning(request,
            'Complete your profile to get personalised nutrition scores!')

    if request.method == 'POST':
        form = FoodInputForm(request.POST, request.FILES)

        if form.is_valid():
            method   = form.cleaned_data['input_method']
            portion  = form.cleaned_data['portion_g']

            try:
                # ── Step 1: Run ML prediction ──────────────────────
                predictions = _run_prediction(form.cleaned_data, request.FILES)

                if not predictions:
                    messages.error(request, 'Could not identify the food. Please try again.')
                    return render(request, 'core/analyze.html',
                                  {'form': form, 'profile': profile})

                top_pred    = predictions[0]
                food_key    = top_pred['food_key']
                food_name   = top_pred['food']
                confidence  = top_pred['confidence']

                # ── Step 2: Get nutrition (cache or USDA API) ──────
                food_cache = _get_or_fetch_nutrition(food_key, food_name)

                # ── Step 3: Compute personalised score ─────────────
                score_data = _compute_nutrition_score(food_cache, profile, portion)

                # ── Step 4: Save FoodEntry ─────────────────────────
                entry = FoodEntry(
                    user             = request.user,
                    food_cache       = food_cache,
                    input_method     = method,
                    predicted_food   = food_key,
                    predicted_name   = food_name,
                    confidence       = Decimal(str(confidence)),
                    top3_predictions = predictions,
                    portion_g        = portion,
                    score_value      = score_data['score'],
                    score_level      = score_data['level'],
                    recommended_portion_g = score_data['recommended_portion'],
                    score_summary    = score_data['summary'],
                )

                # Attach image / URL / text depending on method
                if method == 'image_upload' and 'image' in request.FILES:
                    entry.image = request.FILES['image']
                elif method == 'image_url':
                    entry.image_url  = form.cleaned_data['image_url']
                elif method == 'text_name':
                    entry.text_input = form.cleaned_data['text_input']

                entry.save()

                # ── Step 5: Save NutritionScore breakdown ──────────
                NutritionScore.objects.create(
                    entry           = entry,
                    score_calories  = score_data['sub_scores'].get('calories'),
                    score_protein   = score_data['sub_scores'].get('protein'),
                    score_fat       = score_data['sub_scores'].get('fat'),
                    score_sugar     = score_data['sub_scores'].get('sugar'),
                    score_sodium    = score_data['sub_scores'].get('sodium'),
                    score_fiber     = score_data['sub_scores'].get('fiber'),
                    score_vitamins  = score_data['sub_scores'].get('vitamins'),
                    score_medical   = score_data['sub_scores'].get('medical'),
                    warnings        = score_data['warnings'],
                    positives       = score_data['positives'],
                )

                return redirect('core:result', entry_id=entry.pk)

            except Exception as exc:
                logger.exception("Error during food analysis: %s", exc)
                messages.error(request,
                    'Something went wrong during analysis. Please try again.')

    else:
        form = FoodInputForm()

    return render(request, 'core/analyze.html', {
        'form'    : form,
        'profile' : profile,
    })


# ── Internal helpers for analyze_view ─────────────────────────────

def _run_prediction(cleaned_data, files):
    """
    Route to the correct predictor function based on input method.
    Returns list of prediction dicts or empty list on failure.
    """
    method = cleaned_data['input_method']

    try:
        from core.ml.predictor import (
            predict_from_upload,
            predict_from_url,
            predict_from_pil,
        )
        from PIL import Image

        if method == 'image_upload':
            return predict_from_upload(files['image'])

        elif method == 'image_url':
            return predict_from_url(cleaned_data['image_url'])

        elif method == 'text_name':
            # Text input: no image → use food name as top prediction directly,
            # confidence = 100 (user explicitly named it)
            food_key  = cleaned_data['text_input'].lower().replace(' ', '_')
            food_name = cleaned_data['text_input'].title()
            return [{'food': food_name, 'food_key': food_key, 'confidence': 100.0}]

    except Exception as exc:
        logger.exception("Prediction failed: %s", exc)
        return []


def _get_or_fetch_nutrition(food_key, food_name):
    """
    Return FoodCache entry for this food_key.
    If not in DB → call USDA API and cache the result.
    Returns None if everything fails.
    """
    # Check cache first
    try:
        return FoodCache.objects.get(food_key=food_key)
    except FoodCache.DoesNotExist:
        pass

    # Fetch from USDA
    try:
        from core.ml.usda_api import fetch_and_cache
        return fetch_and_cache(food_key, food_name)
    except Exception as exc:
        logger.warning("USDA fetch failed for %s: %s", food_key, exc)
        # Return a minimal cache entry so the rest of the flow works
        cache, _ = FoodCache.objects.get_or_create(
            food_key  = food_key,
            defaults  = {'food_name': food_name},
        )
        return cache


def _compute_nutrition_score(food_cache, profile, portion_g):
    """
    Compute personalised nutrition score.
    Delegates to the nutrition_score module if profile is complete,
    otherwise returns a generic score.
    """
    try:
        from core.ml.nutrition_score import compute_score
        return compute_score(food_cache, profile, portion_g)
    except Exception as exc:
        logger.warning("Score computation failed: %s", exc)
        return {
            'score'              : Decimal('5.0'),
            'level'              : ScoreLevel.MODERATE,
            'recommended_portion': portion_g,
            'summary'            : 'Score unavailable — complete your profile for personalised results.',
            'sub_scores'         : {},
            'warnings'           : [],
            'positives'          : [],
        }


# ══════════════════════════════════════════════════════════════════════════════
#  RESULT
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def result_view(request, entry_id):
    """
    Detailed analysis result page for one FoodEntry.
    Shows: image, top-3 predictions, full nutrition breakdown,
    personalised score card, recommended portion, warnings/positives.
    """
    entry = get_object_or_404(FoodEntry, pk=entry_id, user=request.user)

    # Prefetch related data
    food        = entry.food_cache
    score_obj   = getattr(entry, 'nutrition_score', None)
    profile     = _get_or_create_profile(request.user)

    # Build nutrient rows for the detail table (scaled to portion)
    portion_factor = entry.portion_g / 100
    nutrient_rows  = []

    if food:
        def scaled(val):
            if val is None:
                return None
            return round(float(val) * portion_factor, 1)

        nutrient_rows = [
            # (label, value, unit, icon)
            ('Calories',      scaled(food.calories_kcal),   'kcal', '🔥'),
            ('Protein',       scaled(food.protein_g),       'g',    '💪'),
            ('Total Fat',     scaled(food.fat_total_g),     'g',    '🧈'),
            ('Saturated Fat', scaled(food.fat_saturated_g), 'g',    '⚠️'),
            ('Carbohydrates', scaled(food.carbs_g),         'g',    '🌾'),
            ('Sugar',         scaled(food.sugar_g),         'g',    '🍬'),
            ('Fiber',         scaled(food.fiber_g),         'g',    '🌿'),
            ('Sodium',        scaled(food.sodium_mg),       'mg',   '🧂'),
            ('Cholesterol',   scaled(food.cholesterol_mg),  'mg',   '❤️'),
            ('Vitamin C',     scaled(food.vitamin_c_mg),    'mg',   '🍊'),
            ('Vitamin D',     scaled(food.vitamin_d_mcg),   'µg',   '☀️'),
            ('Calcium',       scaled(food.calcium_mg),      'mg',   '🦴'),
            ('Iron',          scaled(food.iron_mg),         'mg',   '🔩'),
            ('Potassium',     scaled(food.potassium_mg),    'mg',   '🍌'),
        ]
        # Remove rows where value is None
        nutrient_rows = [(l, v, u, i) for l, v, u, i in nutrient_rows if v is not None]

    # Sub-score list for the radar / bar display
    sub_scores = []
    if score_obj:
        sub_scores = [
            ('Calories',  score_obj.score_calories),
            ('Protein',   score_obj.score_protein),
            ('Fat',       score_obj.score_fat),
            ('Sugar',     score_obj.score_sugar),
            ('Sodium',    score_obj.score_sodium),
            ('Fiber',     score_obj.score_fiber),
            ('Vitamins',  score_obj.score_vitamins),
            ('Medical',   score_obj.score_medical),
        ]
        sub_scores = [(l, float(v)) for l, v in sub_scores if v is not None]

    context = {
        'entry'         : entry,
        'food'          : food,
        'score_obj'     : score_obj,
        'profile'       : profile,
        'nutrient_rows' : nutrient_rows,
        'sub_scores'    : sub_scores,
        'sub_scores_json': json.dumps(sub_scores),
    }
    return render(request, 'core/result.html', context)


# ══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def dashboard_view(request):
    """
    User's personal dashboard:
    - Recent 5 food entries
    - Aggregate stats (avg score, total analyses, avg calories)
    - Top 3 most analysed foods
    - Daily calorie summary (today)
    - Score distribution for chart
    """
    user    = request.user
    profile = _get_or_create_profile(user)
    entries = FoodEntry.objects.filter(user=user).select_related('food_cache')

    # ── Aggregate stats ───────────────────────────────────────────
    stats = entries.aggregate(
        total_analyses = Count('id'),
        avg_score      = Avg('score_value'),
    )
    total_analyses = stats['total_analyses'] or 0
    avg_score      = round(float(stats['avg_score'] or 0), 1)

    # ── Recent entries (last 5) ────────────────────────────────────
    recent_entries = entries[:5]

    # ── Today's calorie total ──────────────────────────────────────
    today = timezone.now().date()
    today_entries = entries.filter(created_at__date=today)
    today_calories = sum(
        (e.calories_for_portion or 0) for e in today_entries
    )

    # ── Top foods (most analysed) ─────────────────────────────────
    top_foods = (
        entries.values('predicted_name')
               .annotate(count=Count('id'), avg_score=Avg('score_value'))
               .order_by('-count')[:5]
    )

    # ── Score distribution (for doughnut chart) ───────────────────
    score_dist = {
        level: entries.filter(score_level=level).count()
        for level in ['excellent', 'good', 'moderate', 'poor', 'avoid']
    }

    # ── Calorie trend: last 7 days ────────────────────────────────
    from datetime import timedelta
    calorie_trend = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_entries = entries.filter(created_at__date=day)
        day_cals = sum((e.calories_for_portion or 0) for e in day_entries)
        calorie_trend.append({
            'date'    : day.strftime('%a'),
            'calories': round(day_cals),
        })

    context = {
        'profile'         : profile,
        'recent_entries'  : recent_entries,
        'total_analyses'  : total_analyses,
        'avg_score'       : avg_score,
        'today_calories'  : round(today_calories),
        'calorie_target'  : profile.daily_calorie_target,
        'top_foods'       : top_foods,
        'score_dist'      : score_dist,
        'score_dist_json' : json.dumps(score_dist),
        'calorie_trend_json': json.dumps(calorie_trend),
        'needs_profile'   : not profile.profile_complete,
    }
    return render(request, 'core/dashboard.html', context)


# ══════════════════════════════════════════════════════════════════════════════
#  HISTORY  (paginated)
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def history_view(request):
    """
    Full paginated food history for the current user.
    Supports filtering by score_level and search by food name.
    """
    entries_qs = FoodEntry.objects.filter(
        user=request.user
    ).select_related('food_cache').order_by('-created_at')

    # ── Filters ───────────────────────────────────────────────────
    score_filter = request.GET.get('score', '')
    search       = request.GET.get('q', '').strip()

    if score_filter:
        entries_qs = entries_qs.filter(score_level=score_filter)
    if search:
        entries_qs = entries_qs.filter(predicted_name__icontains=search)

    # ── Pagination ────────────────────────────────────────────────
    paginator   = Paginator(entries_qs, 12)
    page_number = request.GET.get('page', 1)
    page_obj    = paginator.get_page(page_number)

    context = {
        'page_obj'     : page_obj,
        'score_filter' : score_filter,
        'search'       : search,
        'score_choices': ScoreLevel.choices,
        'total_count'  : entries_qs.count(),
    }
    return render(request, 'core/history.html', context)


# ══════════════════════════════════════════════════════════════════════════════
#  DELETE ENTRY
# ══════════════════════════════════════════════════════════════════════════════

@login_required
@require_POST
def delete_entry_view(request, entry_id):
    """Delete one food entry (POST only, owned by current user)."""
    entry = get_object_or_404(FoodEntry, pk=entry_id, user=request.user)
    entry.delete()
    messages.success(request, 'Entry deleted.')

    # Return to previous page or history
    next_url = request.POST.get('next', 'history')
    return redirect(next_url)


# ══════════════════════════════════════════════════════════════════════════════
#  JSON API  —  for chart.js on dashboard
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def api_top_foods_view(request):
    """
    GET /api/top-foods/
    Returns JSON: top 10 most analysed foods for this user.
    Used by the dashboard Chart.js bar chart.
    """
    data = (
        FoodEntry.objects
        .filter(user=request.user)
        .values('predicted_name')
        .annotate(count=Count('id'), avg_score=Avg('score_value'))
        .order_by('-count')[:10]
    )
    return JsonResponse({
        'foods'  : [d['predicted_name'] for d in data],
        'counts' : [d['count'] for d in data],
        'scores' : [round(float(d['avg_score'] or 0), 1) for d in data],
    })
