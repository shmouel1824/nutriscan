"""
NutriScan — core/ml/nutrition_score.py
=======================================
Personalised nutrition scoring engine.

Given:
    - A FoodCache entry (nutrient data per 100 g)
    - A UserProfile   (age, weight, height, sex, activity, goal, flags)
    - A portion size  (grams)

Returns a score dict with:
    score            : Decimal  0–10  overall composite score
    level            : str      'excellent' | 'good' | 'moderate' | 'poor' | 'avoid'
    recommended_portion: int    grams — how much this user should eat
    summary          : str      one-paragraph human-readable verdict
    sub_scores       : dict     per-category scores (0–10)
    warnings         : list     specific concern messages
    positives        : list     specific benefit messages

Scoring philosophy
------------------
Each sub-score is 0–10 (10 = perfect for this user).
The composite score is a WEIGHTED average tuned by health goal.
Medical flags can HARD-CAP the score (e.g. high sodium → max 4/10 for
hypertension users regardless of other nutrients).
"""

import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
#  DAILY REFERENCE VALUES  (DRVs)
#  Base values for a 2000 kcal reference adult — adjusted per user below.
# ══════════════════════════════════════════════════════════════════════════════

DRV_BASE = {
    'calories_kcal'   : 2000,
    'protein_g'       : 50,
    'fat_total_g'     : 65,
    'fat_saturated_g' : 20,
    'carbs_g'         : 275,
    'sugar_g'         : 50,
    'fiber_g'         : 28,
    'sodium_mg'       : 2300,
    'cholesterol_mg'  : 300,
    'vitamin_c_mg'    : 90,
    'vitamin_d_mcg'   : 20,
    'calcium_mg'      : 1300,
    'iron_mg'         : 18,
    'potassium_mg'    : 4700,
}

# ── Goal-based calorie adjustments (applied on top of user TDEE) ──
GOAL_CALORIE_FACTOR = {
    'lose_weight'   : 0.80,   # 20% deficit
    'maintain'      : 1.00,
    'gain_muscle'   : 1.15,   # 15% surplus
    'improve_health': 1.00,
}

# ── Activity-based protein multiplier (g per kg body weight) ──────
PROTEIN_PER_KG = {
    'sedentary' : 0.8,
    'light'     : 1.0,
    'moderate'  : 1.2,
    'active'    : 1.6,
    'athlete'   : 2.0,
}

# ── Composite weight schemes per health goal ──────────────────────
# Keys must match sub_scores keys. Sum = 1.0
GOAL_WEIGHTS = {
    'lose_weight': {
        'calories' : 0.30,
        'protein'  : 0.20,
        'fat'      : 0.15,
        'sugar'    : 0.15,
        'sodium'   : 0.05,
        'fiber'    : 0.10,
        'vitamins' : 0.05,
        'medical'  : 0.00,   # applied as hard cap, not weight
    },
    'maintain': {
        'calories' : 0.20,
        'protein'  : 0.15,
        'fat'      : 0.15,
        'sugar'    : 0.10,
        'sodium'   : 0.10,
        'fiber'    : 0.10,
        'vitamins' : 0.20,
        'medical'  : 0.00,
    },
    'gain_muscle': {
        'calories' : 0.15,
        'protein'  : 0.35,
        'fat'      : 0.15,
        'sugar'    : 0.10,
        'sodium'   : 0.05,
        'fiber'    : 0.05,
        'vitamins' : 0.15,
        'medical'  : 0.00,
    },
    'improve_health': {
        'calories' : 0.10,
        'protein'  : 0.15,
        'fat'      : 0.15,
        'sugar'    : 0.15,
        'sodium'   : 0.10,
        'fiber'    : 0.15,
        'vitamins' : 0.20,
        'medical'  : 0.00,
    },
}


# ══════════════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════

def compute_score(food_cache, profile, portion_g: int) -> dict:
    """
    Main entry point.
    Returns the full score dict consumed by views.py and NutritionScore model.
    """
    # ── Fallback if no nutrient data available ────────────────────
    if food_cache is None or not _has_nutrition_data(food_cache):
        return _empty_score("No nutritional data available for this food.")

    # ── Compute user's personal daily targets ─────────────────────
    targets = _build_personal_targets(profile)

    # ── Scale nutrients to the actual portion ─────────────────────
    portion = _scale_to_portion(food_cache, portion_g)

    # ── Compute individual sub-scores ─────────────────────────────
    sub = {}
    warnings  = []
    positives = []

    sub['calories'], cal_msg = _score_calories(portion, targets, profile)
    sub['protein'],  pro_msg = _score_protein(portion, targets, profile)
    sub['fat'],      fat_msg = _score_fat(portion, targets)
    sub['sugar'],    sug_msg = _score_sugar(portion, targets, profile)
    sub['sodium'],   sod_msg = _score_sodium(portion, targets, profile)
    sub['fiber'],    fib_msg = _score_fiber(portion, targets)
    sub['vitamins'], vit_msg = _score_vitamins(portion, targets)
    sub['medical'],  med_msg = _score_medical(food_cache, profile)

    # Collect messages
    for score_val, msg, is_warn in [
        (sub['calories'],  cal_msg, sub['calories'] < 5),
        (sub['protein'],   pro_msg, sub['protein']  < 5),
        (sub['fat'],       fat_msg, sub['fat']       < 5),
        (sub['sugar'],     sug_msg, sub['sugar']     < 5),
        (sub['sodium'],    sod_msg, sub['sodium']    < 5),
        (sub['fiber'],     fib_msg, sub['fiber']     < 7),
        (sub['vitamins'],  vit_msg, sub['vitamins']  > 6),
        (sub['medical'],   med_msg, sub['medical']   < 7),
    ]:
        if msg:
            (warnings if is_warn else positives).append(msg)

    # ── Weighted composite ────────────────────────────────────────
    goal    = getattr(profile, 'health_goal', 'maintain') or 'maintain'
    weights = GOAL_WEIGHTS.get(goal, GOAL_WEIGHTS['maintain'])
    raw_score = sum(sub[k] * weights[k] for k in weights)

    # ── Medical hard cap ──────────────────────────────────────────
    if sub['medical'] < 3:
        raw_score = min(raw_score, 3.0)
        warnings.insert(0, med_msg)
    elif sub['medical'] < 6:
        raw_score = min(raw_score, 6.5)

    raw_score = max(0.0, min(10.0, raw_score))
    score     = round(raw_score, 1)

    # ── Level ─────────────────────────────────────────────────────
    level = _score_to_level(score)

    # ── Recommended portion ───────────────────────────────────────
    rec_portion = _recommended_portion(food_cache, profile, targets, portion_g)

    # ── Summary text ─────────────────────────────────────────────
    summary = _build_summary(food_cache, profile, score, level,
                              rec_portion, portion_g, warnings, positives)

    return {
        'score'              : Decimal(str(score)),
        'level'              : level,
        'recommended_portion': rec_portion,
        'summary'            : summary,
        'sub_scores'         : {k: Decimal(str(round(v, 1))) for k, v in sub.items()},
        'warnings'           : warnings,
        'positives'          : positives,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  PERSONAL TARGETS
# ══════════════════════════════════════════════════════════════════════════════

def _build_personal_targets(profile) -> dict:
    """
    Compute personalised daily nutrient targets for this user.
    Falls back to DRV_BASE if profile is incomplete.
    """
    targets = dict(DRV_BASE)

    # ── Calorie target ────────────────────────────────────────────
    tdee = getattr(profile, 'tdee', None)
    if tdee:
        goal          = getattr(profile, 'health_goal', 'maintain') or 'maintain'
        factor        = GOAL_CALORIE_FACTOR.get(goal, 1.0)
        targets['calories_kcal'] = round(tdee * factor)

    # ── Protein target ────────────────────────────────────────────
    weight_kg = float(getattr(profile, 'weight_kg', None) or 70)
    activity  = getattr(profile, 'activity_level', 'moderate') or 'moderate'
    prot_per_kg = PROTEIN_PER_KG.get(activity, 1.2)
    targets['protein_g'] = round(weight_kg * prot_per_kg)

    # ── Sodium: tighter for hypertension ─────────────────────────
    if getattr(profile, 'has_hypertension', False):
        targets['sodium_mg'] = 1500   # AHA recommendation

    # ── Sugar: tighter for diabetes ──────────────────────────────
    if getattr(profile, 'has_diabetes', False):
        targets['sugar_g'] = 25

    # ── Fiber: higher for diabetes / weight loss ──────────────────
    if getattr(profile, 'has_diabetes', False) or \
       getattr(profile, 'health_goal', '') == 'lose_weight':
        targets['fiber_g'] = 38

    return targets


# ══════════════════════════════════════════════════════════════════════════════
#  NUTRIENT SCALING
# ══════════════════════════════════════════════════════════════════════════════

def _scale_to_portion(food_cache, portion_g: int) -> dict:
    """Return a dict of nutrient values scaled from per-100g to portion_g."""
    factor = portion_g / 100
    fields = [
        'calories_kcal', 'protein_g', 'fat_total_g', 'fat_saturated_g',
        'carbs_g', 'sugar_g', 'fiber_g', 'sodium_mg', 'cholesterol_mg',
        'vitamin_a_mcg', 'vitamin_c_mg', 'vitamin_d_mcg', 'vitamin_b12_mcg',
        'calcium_mg', 'iron_mg', 'potassium_mg', 'magnesium_mg', 'zinc_mg',
    ]
    result = {}
    for f in fields:
        val = getattr(food_cache, f, None)
        if val is not None:
            result[f] = float(val) * factor
    return result


# ══════════════════════════════════════════════════════════════════════════════
#  SUB-SCORE FUNCTIONS  (each returns float 0–10, str message)
# ══════════════════════════════════════════════════════════════════════════════

def _score_calories(portion: dict, targets: dict, profile) -> tuple[float, str]:
    """
    How well does this portion fit into the daily calorie budget?
    Assume one meal = ~30% of daily target, snack = ~15%.
    We compare against 30% meal share.
    """
    if 'calories_kcal' not in portion:
        return 5.0, ''

    meal_budget = targets['calories_kcal'] * 0.30
    ratio       = portion['calories_kcal'] / meal_budget

    if ratio <= 0.7:
        return 9.0, f"Low calorie ({round(portion['calories_kcal'])} kcal) — fits your daily target easily."
    if ratio <= 1.0:
        return 8.0, f"Reasonable calories ({round(portion['calories_kcal'])} kcal) for one meal."
    if ratio <= 1.3:
        return 6.0, f"Slightly high calories ({round(portion['calories_kcal'])} kcal) for one meal."
    if ratio <= 1.7:
        return 3.5, f"High calorie meal ({round(portion['calories_kcal'])} kcal) — watch your daily total."
    return 1.5, f"Very high calorie ({round(portion['calories_kcal'])} kcal) — consider a smaller portion."


def _score_protein(portion: dict, targets: dict, profile) -> tuple[float, str]:
    """Protein as % of daily target."""
    if 'protein_g' not in portion:
        return 5.0, ''

    # Protein per meal ≈ 25–35% of daily target
    meal_target = targets['protein_g'] * 0.30
    pct         = portion['protein_g'] / meal_target * 100

    if pct >= 90:
        return 10.0, f"Excellent protein source ({round(portion['protein_g'], 1)} g) — great for your goal."
    if pct >= 60:
        return 8.0, f"Good protein content ({round(portion['protein_g'], 1)} g)."
    if pct >= 30:
        return 5.5, f"Moderate protein ({round(portion['protein_g'], 1)} g)."
    return 3.0, f"Low protein content ({round(portion['protein_g'], 1)} g)."


def _score_fat(portion: dict, targets: dict) -> tuple[float, str]:
    """
    Score fat quality: total fat vs meal budget, with saturated fat penalty.
    """
    if 'fat_total_g' not in portion:
        return 5.0, ''

    meal_fat_budget = targets['fat_total_g'] * 0.30
    fat_ratio       = portion['fat_total_g'] / meal_fat_budget

    # Saturated fat penalty
    sat_pct = 0.0
    if 'fat_saturated_g' in portion and portion['fat_total_g'] > 0:
        sat_pct = portion['fat_saturated_g'] / portion['fat_total_g'] * 100

    base_score = max(1.0, 10.0 - fat_ratio * 4)

    if sat_pct > 50:
        penalty = 3.0
        msg = (f"High saturated fat ({round(portion.get('fat_saturated_g', 0), 1)} g, "
               f"{round(sat_pct)}% of fat) — limit for heart health.")
    elif sat_pct > 30:
        penalty = 1.5
        msg = f"Moderate saturated fat content ({round(sat_pct)}% of total fat)."
    else:
        penalty = 0.0
        msg = f"Healthy fat profile ({round(portion['fat_total_g'], 1)} g total fat)." if fat_ratio < 1 else ''

    return max(0.0, min(10.0, base_score - penalty)), msg


def _score_sugar(portion: dict, targets: dict, profile) -> tuple[float, str]:
    """Sugar per meal vs daily target. Harder penalty for diabetes."""
    if 'sugar_g' not in portion:
        return 7.0, ''   # unknown → neutral

    daily_sugar = targets['sugar_g']
    meal_pct    = portion['sugar_g'] / daily_sugar * 100
    is_diabetic = getattr(profile, 'has_diabetes', False)

    if meal_pct <= 10:
        return 10.0, f"Very low sugar ({round(portion['sugar_g'], 1)} g) ✓"
    if meal_pct <= 25:
        return 7.5, f"Moderate sugar content ({round(portion['sugar_g'], 1)} g)."
    if meal_pct <= 50:
        score = 4.0 if is_diabetic else 5.5
        return score, f"{'High' if is_diabetic else 'Notable'} sugar ({round(portion['sugar_g'], 1)} g) — mindful eating recommended."
    score = 1.0 if is_diabetic else 3.0
    return score, f"Very high sugar ({round(portion['sugar_g'], 1)} g) — {'avoid for diabetes management' if is_diabetic else 'limit intake'}."


def _score_sodium(portion: dict, targets: dict, profile) -> tuple[float, str]:
    """Sodium per meal vs daily target. Critical for hypertension."""
    if 'sodium_mg' not in portion:
        return 7.0, ''

    meal_limit   = targets['sodium_mg'] * 0.33   # 1/3 of daily per meal
    ratio        = portion['sodium_mg'] / meal_limit
    is_hyper     = getattr(profile, 'has_hypertension', False)

    if ratio <= 0.5:
        return 10.0, f"Low sodium ({round(portion['sodium_mg'])} mg) ✓"
    if ratio <= 1.0:
        return 8.0 if not is_hyper else 6.0, \
               f"Acceptable sodium ({round(portion['sodium_mg'])} mg)."
    if ratio <= 1.5:
        score = 3.0 if is_hyper else 5.0
        return score, (f"{'High sodium risk for hypertension' if is_hyper else 'Elevated sodium'} "
                       f"({round(portion['sodium_mg'])} mg).")
    score = 1.0 if is_hyper else 2.5
    return score, f"Very high sodium ({round(portion['sodium_mg'])} mg) — {'dangerous for hypertension' if is_hyper else 'reduce portion'}."


def _score_fiber(portion: dict, targets: dict) -> tuple[float, str]:
    """Fiber is beneficial — reward generously."""
    if 'fiber_g' not in portion:
        return 5.0, ''

    meal_target = targets['fiber_g'] * 0.33
    pct         = portion['fiber_g'] / meal_target * 100

    if pct >= 100:
        return 10.0, f"Excellent fiber content ({round(portion['fiber_g'], 1)} g) — great for digestion."
    if pct >= 60:
        return 8.0, f"Good fiber content ({round(portion['fiber_g'], 1)} g)."
    if pct >= 30:
        return 6.0, f"Some fiber ({round(portion['fiber_g'], 1)} g)."
    return 3.5, f"Low fiber ({round(portion['fiber_g'], 1)} g) — pair with vegetables."


def _score_vitamins(portion: dict, targets: dict) -> tuple[float, str]:
    """
    Micronutrient richness score.
    Counts how many key vitamins/minerals meet ≥10% DRV per meal.
    """
    vitamin_fields = {
        'vitamin_c_mg'  : ('Vitamin C',  targets.get('vitamin_c_mg', 90)  * 0.10),
        'vitamin_d_mcg' : ('Vitamin D',  targets.get('vitamin_d_mcg', 20) * 0.10),
        'calcium_mg'    : ('Calcium',    targets.get('calcium_mg', 1300)  * 0.10),
        'iron_mg'       : ('Iron',       targets.get('iron_mg', 18)       * 0.10),
        'potassium_mg'  : ('Potassium',  targets.get('potassium_mg', 4700)* 0.10),
    }

    hits    = []
    present = 0

    for field, (name, threshold) in vitamin_fields.items():
        if field in portion:
            present += 1
            if portion[field] >= threshold:
                hits.append(name)

    if present == 0:
        return 5.0, ''

    richness = len(hits) / present
    score    = min(10.0, richness * 10 + 2)   # base 2, up to 10

    if hits:
        return score, f"Good source of: {', '.join(hits)}."
    return score, ''


def _score_medical(food_cache, profile) -> tuple[float, str]:
    """
    Medical compatibility check.
    Returns 10 (fully compatible) down to 0 (incompatible/dangerous).
    Hard caps are applied in compute_score() based on this score.
    """
    issues = []
    score  = 10.0

    food_key  = (food_cache.food_key or '').lower()
    food_name = (food_cache.food_name or '').lower()
    combined  = food_key + ' ' + food_name

    # ── Diabetes ──────────────────────────────────────────────────
    if getattr(profile, 'has_diabetes', False):
        high_gi_keywords = [
            'candy', 'cake', 'donut', 'waffle', 'pancake', 'french_toast',
            'ice_cream', 'chocolate_cake', 'churros', 'baklava',
            'creme_brulee', 'bread_pudding',
        ]
        if any(kw in combined for kw in high_gi_keywords):
            score -= 4.0
            issues.append("High glycemic index food — monitor blood sugar carefully.")

        gi = food_cache.glycemic_index
        if gi and gi > 70:
            score -= 3.0
            issues.append(f"High GI ({gi}) — significant blood sugar spike risk.")

    # ── Hypertension ──────────────────────────────────────────────
    if getattr(profile, 'has_hypertension', False):
        high_sodium_keywords = [
            'hot_dog', 'pizza', 'nachos', 'ramen', 'pho', 'soy',
            'fried_rice', 'clam_chowder', 'lobster_bisque',
        ]
        if any(kw in combined for kw in high_sodium_keywords):
            score -= 2.5
            issues.append("This food is typically high in sodium — caution with hypertension.")

    # ── Nut allergy ────────────────────────────────────────────────
    if getattr(profile, 'has_nut_allergy', False):
        nut_keywords = [
            'pecan', 'walnut', 'almond', 'cashew', 'peanut',
            'pistachio', 'hazelnut', 'baklava', 'pad_thai',
            'satay', 'mole', 'praline',
        ]
        if any(kw in combined for kw in nut_keywords):
            score = 0.0
            issues.append("⚠️ ALLERGY ALERT: This food may contain nuts — avoid if allergic.")

    # ── Gluten intolerance ────────────────────────────────────────
    if getattr(profile, 'is_gluten_free', False):
        gluten_keywords = [
            'bread', 'pasta', 'pizza', 'ramen', 'dumpling', 'gyoza',
            'pho', 'noodle', 'waffle', 'pancake', 'french_toast',
            'fried_rice', 'spring_rolls', 'samosa', 'empanada',
        ]
        if any(kw in combined for kw in gluten_keywords):
            score -= 3.5
            issues.append("May contain gluten — check ingredients if gluten-intolerant.")

    # ── Lactose intolerance ───────────────────────────────────────
    if getattr(profile, 'is_lactose_free', False):
        dairy_keywords = [
            'cheese', 'milk', 'cream', 'butter', 'yogurt', 'ice_cream',
            'cheesecake', 'tiramisu', 'cannoli', 'creme_brulee',
            'lasagna', 'pizza', 'mac_and_cheese',
        ]
        if any(kw in combined for kw in dairy_keywords):
            score -= 2.5
            issues.append("May contain dairy — check ingredients if lactose-intolerant.")

    # ── Vegan / Vegetarian ────────────────────────────────────────
    if getattr(profile, 'is_vegan', False):
        non_vegan_keywords = [
            'beef', 'pork', 'chicken', 'lamb', 'steak', 'burger',
            'hot_dog', 'bacon', 'sushi', 'sashimi', 'fish', 'shrimp',
            'lobster', 'crab', 'scallops', 'oysters', 'clam',
            'cheese', 'milk', 'cream', 'butter', 'egg', 'omelette',
            'peking_duck', 'duck',
        ]
        if any(kw in combined for kw in non_vegan_keywords):
            score = 0.0
            issues.append("Not vegan — this food contains animal products.")

    elif getattr(profile, 'is_vegetarian', False):
        meat_keywords = [
            'beef', 'pork', 'chicken', 'lamb', 'steak', 'burger',
            'hot_dog', 'bacon', 'peking_duck', 'duck',
            'sushi', 'sashimi', 'fish', 'shrimp', 'lobster', 'crab',
            'scallops', 'oysters', 'clam',
        ]
        if any(kw in combined for kw in meat_keywords):
            score = 0.0
            issues.append("Not vegetarian — this food contains meat or fish.")

    score = max(0.0, min(10.0, score))
    msg   = issues[0] if issues else ''
    return score, msg


# ══════════════════════════════════════════════════════════════════════════════
#  RECOMMENDED PORTION
# ══════════════════════════════════════════════════════════════════════════════

def _recommended_portion(food_cache, profile, targets: dict, actual_portion: int) -> int:
    """
    Compute the portion (g) that best matches the user's calorie meal target.
    Clamps to [30, 600] g.
    """
    cal_per_100 = float(getattr(food_cache, 'calories_kcal', None) or 0)
    if cal_per_100 <= 0:
        return actual_portion   # can't compute without calorie data

    meal_kcal   = targets['calories_kcal'] * 0.30
    ideal_g     = (meal_kcal / cal_per_100) * 100
    return max(30, min(600, round(ideal_g / 10) * 10))   # round to nearest 10 g


# ══════════════════════════════════════════════════════════════════════════════
#  SCORE → LEVEL
# ══════════════════════════════════════════════════════════════════════════════

def _score_to_level(score: float) -> str:
    if score >= 8.0: return 'excellent'
    if score >= 6.5: return 'good'
    if score >= 4.5: return 'moderate'
    if score >= 2.5: return 'poor'
    return 'avoid'


# ══════════════════════════════════════════════════════════════════════════════
#  SUMMARY TEXT GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

def _build_summary(food_cache, profile, score: float, level: str,
                   rec_portion: int, actual_portion: int,
                   warnings: list, positives: list) -> str:
    """
    Build a personalised one-paragraph summary for the user.
    """
    food_name = food_cache.food_name if food_cache else 'This food'
    goal_label = {
        'lose_weight'   : 'weight loss',
        'maintain'      : 'weight maintenance',
        'gain_muscle'   : 'muscle gain',
        'improve_health': 'improving your health',
    }.get(getattr(profile, 'health_goal', 'maintain'), 'your goals')

    level_phrases = {
        'excellent': f"is an excellent choice for {goal_label}",
        'good'     : f"is a good choice for {goal_label}",
        'moderate' : f"is acceptable for {goal_label}, but eat mindfully",
        'poor'     : f"is not ideal for {goal_label}",
        'avoid'    : f"is not recommended for your profile",
    }

    verdict = level_phrases.get(level, 'has been analysed')
    parts   = [f"{food_name} {verdict} (score: {score}/10)."]

    if rec_portion != actual_portion:
        diff = rec_portion - actual_portion
        direction = "increase" if diff > 0 else "reduce"
        parts.append(
            f"We recommend {rec_portion} g per serving — "
            f"{direction} your portion by {abs(diff)} g for optimal results."
        )

    if positives:
        parts.append("Strengths: " + " ".join(positives[:2]))

    if warnings:
        parts.append("Watch out for: " + " ".join(warnings[:2]))

    return " ".join(parts)


# ══════════════════════════════════════════════════════════════════════════════
#  UTILITY
# ══════════════════════════════════════════════════════════════════════════════

def _has_nutrition_data(food_cache) -> bool:
    """Return True if at least calorie data is present."""
    return getattr(food_cache, 'calories_kcal', None) is not None


def _empty_score(reason: str) -> dict:
    return {
        'score'              : Decimal('5.0'),
        'level'              : 'moderate',
        'recommended_portion': 100,
        'summary'            : reason,
        'sub_scores'         : {
            k: Decimal('5.0')
            for k in ['calories', 'protein', 'fat', 'sugar',
                      'sodium', 'fiber', 'vitamins', 'medical']
        },
        'warnings'  : [],
        'positives' : [],
    }
