"""
NutriScan — core/ml/usda_api.py
================================
USDA FoodData Central API integration.

Responsibilities:
    1. Search the USDA database for a food by name
    2. Fetch the full nutrient detail for the best match
    3. Parse the JSON into a FoodCache model instance
    4. Handle rate limits, timeouts, and missing fields gracefully

API docs: https://fdc.nal.usda.gov/api-guide.html
Get a free key at: https://fdc.nal.usda.gov/api-key-signup.html
DEMO_KEY = 50 requests/hour, 1000/day (fine for development)

Usage:
    from core.ml.usda_api import fetch_and_cache
    food_cache = fetch_and_cache('pizza', 'Pizza')
"""

import logging
import requests
from django.conf import settings
from core.models import FoodCache

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────
USDA_BASE        = getattr(settings, 'USDA_API_BASE', 'https://api.nal.usda.gov/fdc/v1')
USDA_API_KEY     = getattr(settings, 'USDA_API_KEY', 'DEMO_KEY')
TIMEOUT          = 10   # seconds per request
MAX_SEARCH_HITS  = 5    # how many candidates to evaluate before giving up

# ── USDA nutrient ID → our field name mapping ─────────────────────
# Full list: https://fdc.nal.usda.gov/fdc-app.html#/food-details/...
NUTRIENT_MAP = {
    1008 : 'calories_kcal',     # Energy (kcal)
    1003 : 'protein_g',         # Protein
    1004 : 'fat_total_g',       # Total lipid (fat)
    1258 : 'fat_saturated_g',   # Fatty acids, total saturated
    1005 : 'carbs_g',           # Carbohydrate, by difference
    2000 : 'sugar_g',           # Total Sugars
    1079 : 'fiber_g',           # Fiber, total dietary
    1093 : 'sodium_mg',         # Sodium, Na
    1253 : 'cholesterol_mg',    # Cholesterol
    1106 : 'vitamin_a_mcg',     # Vitamin A, RAE
    1162 : 'vitamin_c_mg',      # Vitamin C
    1114 : 'vitamin_d_mcg',     # Vitamin D (D2 + D3)
    1178 : 'vitamin_b12_mcg',   # Vitamin B-12
    1087 : 'calcium_mg',        # Calcium, Ca
    1089 : 'iron_mg',           # Iron, Fe
    1092 : 'potassium_mg',      # Potassium, K
    1090 : 'magnesium_mg',      # Magnesium, Mg
    1095 : 'zinc_mg',           # Zinc, Zn
}

# ── Food category keywords → FoodCache.food_category ─────────────
CATEGORY_HINTS = {
    'Dairy'         : ['milk', 'cheese', 'yogurt', 'butter', 'cream', 'ice_cream'],
    'Meat'          : ['beef', 'pork', 'lamb', 'steak', 'burger', 'hot_dog',
                       'baby_back_ribs', 'filet_mignon', 'pork_chop'],
    'Poultry'       : ['chicken', 'turkey', 'duck'],
    'Seafood'       : ['fish', 'salmon', 'tuna', 'sushi', 'sashimi', 'shrimp',
                       'lobster', 'crab', 'scallops', 'oysters', 'clam_chowder'],
    'Grain'         : ['bread', 'pasta', 'rice', 'pizza', 'noodle', 'ramen',
                       'spaghetti', 'pho', 'pad_thai', 'macaroni'],
    'Vegetable'     : ['salad', 'broccoli', 'spinach', 'carrot', 'beet',
                       'caprese', 'edamame', 'hummus', 'falafel', 'spring_rolls'],
    'Fruit'         : ['apple', 'banana', 'strawberry', 'mango', 'berry',
                       'fruit_salad', 'smoothie'],
    'Dessert'       : ['cake', 'ice_cream', 'chocolate', 'cookie', 'donut',
                       'tiramisu', 'cheesecake', 'macarons', 'baklava',
                       'cannoli', 'creme_brulee', 'churros', 'waffles',
                       'pancakes', 'french_toast'],
    'Fast Food'     : ['burger', 'hot_dog', 'french_fries', 'pizza', 'nachos'],
    'Asian'         : ['sushi', 'ramen', 'pho', 'pad_thai', 'bibimbap',
                       'gyoza', 'dumplings', 'peking_duck', 'takoyaki',
                       'spring_rolls', 'fried_rice'],
    'Breakfast'     : ['eggs', 'omelette', 'waffles', 'pancakes', 'french_toast',
                       'breakfast_burrito', 'granola', 'oatmeal'],
    'Snack / Other' : [],
}


# ══════════════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════

def fetch_and_cache(food_key: str, food_name: str) -> FoodCache:
    """
    Main entry point.
    1. Search USDA for food_name
    2. Fetch detail for best match
    3. Parse nutrients
    4. Save to FoodCache (upsert)
    Returns the FoodCache instance (may have null nutrients if API fails).
    """
    logger.info("USDA fetch started: key=%s name=%s", food_key, food_name)

    # Clean the search query
    query = food_name.replace('_', ' ').strip()

    fdc_id, raw_food = _search_best_match(query)

    if fdc_id is None:
        logger.warning("No USDA match for '%s'. Saving empty cache.", query)
        cache, _ = FoodCache.objects.get_or_create(
            food_key=food_key,
            defaults={'food_name': food_name}
        )
        return cache

    # Fetch detail if needed
    if raw_food is None:
        raw_food = _fetch_food_detail(fdc_id)

    if raw_food is None:
        cache, _ = FoodCache.objects.get_or_create(
            food_key=food_key,
            defaults={'food_name': food_name}
        )
        return cache

    # Parse and save
    return _parse_and_save(food_key, food_name, fdc_id, raw_food)


# ══════════════════════════════════════════════════════════════════════════════
#  PRIVATE HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _search_best_match(query: str):
    """
    Search USDA /foods/search for the query.
    Returns (fdc_id, food_dict) for the best match, or (None, None) on failure.
    Strategy: prefer 'Foundation' foods, then 'SR Legacy', then first result.
    """
    url    = f"{USDA_BASE}/foods/search"
    params = {
        'query'      : query,
        'api_key'    : USDA_API_KEY,
        'pageSize'   : MAX_SEARCH_HITS,
        'dataType'   : 'Foundation,SR Legacy,Survey (FNDDS)',
    }

    try:
        resp = requests.get(url, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.error("USDA search request failed: %s", exc)
        return None, None

    foods = data.get('foods', [])
    if not foods:
        logger.warning("USDA search returned 0 results for '%s'", query)
        return None, None

    # Prefer Foundation > SR Legacy > anything else
    priority = {'Foundation': 0, 'SR Legacy': 1, 'Survey (FNDDS)': 2}
    foods.sort(key=lambda f: priority.get(f.get('dataType', ''), 9))

    best = foods[0]
    logger.info("USDA best match: fdcId=%s desc=%s type=%s",
                best.get('fdcId'), best.get('description'), best.get('dataType'))
    return best['fdcId'], best


def _fetch_food_detail(fdc_id: int) -> dict | None:
    """
    Fetch full nutrient detail from USDA /food/{fdcId}.
    Returns raw dict or None on failure.
    """
    url    = f"{USDA_BASE}/food/{fdc_id}"
    params = {'api_key': USDA_API_KEY}

    try:
        resp = requests.get(url, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        logger.error("USDA detail fetch failed for fdcId=%s: %s", fdc_id, exc)
        return None


def _parse_and_save(food_key: str, food_name: str,
                    fdc_id: int, raw: dict) -> FoodCache:
    """
    Parse USDA nutrient data and upsert into FoodCache.
    Handles both /foods/search and /food/{id} response shapes.
    All values are per 100 g.
    """
    # Extract nutrients list (differs between search and detail endpoints)
    nutrients_list = raw.get('foodNutrients', [])

    # Build nutrient lookup: {nutrient_id: amount}
    nutrient_values: dict[int, float] = {}
    for item in nutrients_list:
        # Search endpoint shape: {nutrientId, value}
        nid    = item.get('nutrientId') or item.get('nutrient', {}).get('id')
        amount = item.get('value') or item.get('amount')
        if nid and amount is not None:
            try:
                nutrient_values[int(nid)] = float(amount)
            except (ValueError, TypeError):
                pass

    # Map to model fields
    field_values = {}
    for nid, field in NUTRIENT_MAP.items():
        if nid in nutrient_values:
            field_values[field] = round(nutrient_values[nid], 3)

    # Determine food category
    category = _classify_category(food_key)

    # Upsert
    cache, created = FoodCache.objects.update_or_create(
        food_key = food_key,
        defaults = {
            'food_name'      : food_name,
            'usda_fdc_id'    : str(fdc_id),
            'food_category'  : category,
            'raw_usda_json'  : raw,
            **field_values,
        }
    )

    action = 'created' if created else 'updated'
    logger.info("FoodCache %s: %s (fdcId=%s, fields=%d)",
                action, food_key, fdc_id, len(field_values))
    return cache


def _classify_category(food_key: str) -> str:
    """
    Heuristic category detection from the food_key string.
    Returns one of the CATEGORY_HINTS keys.
    """
    key_lower = food_key.lower()
    for category, keywords in CATEGORY_HINTS.items():
        if any(kw in key_lower for kw in keywords):
            return category
    # Fallback: try the key itself as a partial match
    for category, keywords in CATEGORY_HINTS.items():
        if any(key_lower in kw for kw in keywords):
            return category
    return 'Snack / Other'


# ══════════════════════════════════════════════════════════════════════════════
#  UTILITY — manual refresh
# ══════════════════════════════════════════════════════════════════════════════

def refresh_cache_entry(food_key: str) -> FoodCache | None:
    """
    Force-refresh one FoodCache entry from the USDA API.
    Useful for a management command or admin action.
    """
    try:
        old = FoodCache.objects.get(food_key=food_key)
        return fetch_and_cache(food_key, old.food_name)
    except FoodCache.DoesNotExist:
        logger.warning("Cannot refresh '%s': not in cache.", food_key)
        return None
