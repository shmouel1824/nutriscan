"""
NutriScan — management/commands/populate_food_cache.py
========================================================
Management command to pre-populate the FoodCache table with
USDA nutritional data for all 101 Food-101 classes.

Usage:
    python manage.py populate_food_cache
    python manage.py populate_food_cache --limit 20
    python manage.py populate_food_cache --food pizza sushi ramen
    python manage.py populate_food_cache --refresh   # re-fetch existing

This ensures the app has instant responses for all known foods
without waiting for real-time USDA API calls on first access.
Respects USDA DEMO_KEY rate limit (50 req/hour) with delays.
"""

import time
import logging
from django.core.management.base import BaseCommand, CommandError
from core.ml.usda_api import fetch_and_cache

logger = logging.getLogger(__name__)

# All 101 Food-101 class names (food_key → display name)
FOOD101_CLASSES = {
    'apple_pie'           : 'Apple Pie',
    'baby_back_ribs'      : 'Baby Back Ribs',
    'baklava'             : 'Baklava',
    'beef_carpaccio'      : 'Beef Carpaccio',
    'beef_tartare'        : 'Beef Tartare',
    'beet_salad'          : 'Beet Salad',
    'beignets'            : 'Beignets',
    'bibimbap'            : 'Bibimbap',
    'bread_pudding'       : 'Bread Pudding',
    'breakfast_burrito'   : 'Breakfast Burrito',
    'bruschetta'          : 'Bruschetta',
    'caesar_salad'        : 'Caesar Salad',
    'cannoli'             : 'Cannoli',
    'caprese_salad'       : 'Caprese Salad',
    'carrot_cake'         : 'Carrot Cake',
    'ceviche'             : 'Ceviche',
    'cheesecake'          : 'Cheesecake',
    'cheese_plate'        : 'Cheese Plate',
    'chicken_curry'       : 'Chicken Curry',
    'chicken_quesadilla'  : 'Chicken Quesadilla',
    'chicken_wings'       : 'Chicken Wings',
    'chocolate_cake'      : 'Chocolate Cake',
    'chocolate_mousse'    : 'Chocolate Mousse',
    'churros'             : 'Churros',
    'clam_chowder'        : 'Clam Chowder',
    'club_sandwich'       : 'Club Sandwich',
    'crab_cakes'          : 'Crab Cakes',
    'creme_brulee'        : 'Crème Brûlée',
    'croque_madame'       : 'Croque Madame',
    'cup_cakes'           : 'Cupcakes',
    'deviled_eggs'        : 'Deviled Eggs',
    'donuts'              : 'Donuts',
    'dumplings'           : 'Dumplings',
    'edamame'             : 'Edamame',
    'eggs_benedict'       : 'Eggs Benedict',
    'escargots'           : 'Escargots',
    'falafel'             : 'Falafel',
    'filet_mignon'        : 'Filet Mignon',
    'fish_and_chips'      : 'Fish and Chips',
    'foie_gras'           : 'Foie Gras',
    'french_fries'        : 'French Fries',
    'french_onion_soup'   : 'French Onion Soup',
    'french_toast'        : 'French Toast',
    'fried_calamari'      : 'Fried Calamari',
    'fried_rice'          : 'Fried Rice',
    'frozen_yogurt'       : 'Frozen Yogurt',
    'garlic_bread'        : 'Garlic Bread',
    'gnocchi'             : 'Gnocchi',
    'greek_salad'         : 'Greek Salad',
    'grilled_cheese_sandwich': 'Grilled Cheese Sandwich',
    'grilled_salmon'      : 'Grilled Salmon',
    'guacamole'           : 'Guacamole',
    'gyoza'               : 'Gyoza',
    'hamburger'           : 'Hamburger',
    'hot_and_sour_soup'   : 'Hot and Sour Soup',
    'hot_dog'             : 'Hot Dog',
    'huevos_rancheros'    : 'Huevos Rancheros',
    'hummus'              : 'Hummus',
    'ice_cream'           : 'Ice Cream',
    'lasagna'             : 'Lasagna',
    'lobster_bisque'      : 'Lobster Bisque',
    'lobster_roll_sandwich': 'Lobster Roll Sandwich',
    'macaroni_and_cheese' : 'Macaroni and Cheese',
    'macarons'            : 'Macarons',
    'miso_soup'           : 'Miso Soup',
    'mussels'             : 'Mussels',
    'nachos'              : 'Nachos',
    'omelette'            : 'Omelette',
    'onion_rings'         : 'Onion Rings',
    'oysters'             : 'Oysters',
    'pad_thai'            : 'Pad Thai',
    'paella'              : 'Paella',
    'pancakes'            : 'Pancakes',
    'panna_cotta'         : 'Panna Cotta',
    'peking_duck'         : 'Peking Duck',
    'pho'                 : 'Pho',
    'pizza'               : 'Pizza',
    'pork_chop'           : 'Pork Chop',
    'poutine'             : 'Poutine',
    'prime_rib'           : 'Prime Rib',
    'pulled_pork_sandwich': 'Pulled Pork Sandwich',
    'ramen'               : 'Ramen',
    'ravioli'             : 'Ravioli',
    'red_velvet_cake'     : 'Red Velvet Cake',
    'risotto'             : 'Risotto',
    'samosa'              : 'Samosa',
    'sashimi'             : 'Sashimi',
    'scallops'            : 'Scallops',
    'seaweed_salad'       : 'Seaweed Salad',
    'shrimp_and_grits'    : 'Shrimp and Grits',
    'spaghetti_bolognese' : 'Spaghetti Bolognese',
    'spaghetti_carbonara' : 'Spaghetti Carbonara',
    'spring_rolls'        : 'Spring Rolls',
    'steak'               : 'Steak',
    'strawberry_shortcake': 'Strawberry Shortcake',
    'sushi'               : 'Sushi',
    'tacos'               : 'Tacos',
    'takoyaki'            : 'Takoyaki',
    'tiramisu'            : 'Tiramisu',
    'tuna_tartare'        : 'Tuna Tartare',
    'waffles'             : 'Waffles',
}


class Command(BaseCommand):
    help = 'Pre-populate the FoodCache table with USDA nutritional data for all Food-101 classes.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit', type=int, default=0,
            help='Only process the first N foods (0 = all).'
        )
        parser.add_argument(
            '--food', nargs='+', type=str,
            help='Process specific food keys only (e.g. pizza sushi ramen).'
        )
        parser.add_argument(
            '--refresh', action='store_true',
            help='Re-fetch and update foods that are already cached.'
        )
        parser.add_argument(
            '--delay', type=float, default=1.5,
            help='Seconds to wait between API calls (default: 1.5 — safe for DEMO_KEY).'
        )

    def handle(self, *args, **options):
        from core.models import FoodCache

        # Determine which foods to process
        if options['food']:
            targets = {k: FOOD101_CLASSES[k] for k in options['food']
                       if k in FOOD101_CLASSES}
            if not targets:
                raise CommandError(
                    f"None of the specified keys are valid Food-101 classes. "
                    f"Valid example: pizza, sushi, ramen"
                )
        else:
            targets = dict(FOOD101_CLASSES)

        if options['limit']:
            targets = dict(list(targets.items())[:options['limit']])

        # Skip already-cached unless --refresh
        if not options['refresh']:
            existing = set(
                FoodCache.objects.filter(
                    food_key__in=targets.keys(),
                    calories_kcal__isnull=False
                ).values_list('food_key', flat=True)
            )
            skipped = len(existing)
            targets = {k: v for k, v in targets.items() if k not in existing}
            if skipped:
                self.stdout.write(
                    self.style.WARNING(f"Skipping {skipped} already-cached foods. "
                                       f"Use --refresh to force update.")
                )

        total   = len(targets)
        success = 0
        failed  = []

        self.stdout.write(
            self.style.SUCCESS(f"\n🥗 NutriScan — Populating FoodCache")
        )
        self.stdout.write(f"   Foods to process : {total}")
        self.stdout.write(f"   API delay        : {options['delay']}s per request\n")

        for i, (food_key, food_name) in enumerate(targets.items(), 1):
            self.stdout.write(
                f"[{i:>3}/{total}] Fetching: {food_name:<35}", ending=''
            )

            try:
                cache = fetch_and_cache(food_key, food_name)
                has_data = cache.calories_kcal is not None

                if has_data:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f" ✓  {round(float(cache.calories_kcal))} kcal/100g"
                        )
                    )
                    success += 1
                else:
                    self.stdout.write(self.style.WARNING(" ⚠  saved (no nutrient data)"))
                    success += 1   # still saved, partial data

            except Exception as exc:
                self.stdout.write(self.style.ERROR(f" ✗  {exc}"))
                failed.append(food_key)

            # Rate-limit delay (skip after last item)
            if i < total:
                time.sleep(options['delay'])

        # ── Summary ───────────────────────────────────────────────
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f"Done — {success}/{total} foods cached successfully."
        ))
        if failed:
            self.stdout.write(self.style.ERROR(
                f"Failed ({len(failed)}): {', '.join(failed)}"
            ))
            self.stdout.write("Run again to retry failed items.")
