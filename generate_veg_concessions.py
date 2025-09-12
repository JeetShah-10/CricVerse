#!/usr/bin/env python3
"""
Vegetarian Concessions Generator
================================

Generates realistic, purely vegetarian food stalls (concessions) for each stadium
with authentic Indian menu items priced in INR. The selection is randomized per
stadium so that not all stadiums have the same stalls or menus.
"""

import os
import random
from typing import List, Dict
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv

# Load environment variables
if os.path.exists('cricverse.env'):
    load_dotenv('cricverse.env')
else:
    load_dotenv()

# Random seed for reproducibility across runs; comment this to make it different every run
random.seed()

STALL_CATALOG: List[Dict] = [
    {
        'name': 'Chaat Junction',
        'category': 'Indian Street Food',
        'menu': [
            ('Pani Puri', 'Crispy puris with spiced tangy water and potato stuffing', 80, 120),
            ('Sev Puri', 'Papdi topped with potatoes, chutneys and sev', 90, 140),
            ('Bhel Puri', 'Murmura bhel with chutneys and veggies', 80, 120),
            ('Dahi Puri', 'Crispy puris with curd and chutneys', 100, 150),
            ('Ragda Pattice', 'Potato patties with white pea curry', 120, 180),
        ]
    },
    {
        'name': 'South Tiffins',
        'category': 'South Indian',
        'menu': [
            ('Masala Dosa', 'Crispy dosa with spiced potato filling', 120, 180),
            ('Plain Dosa', 'Classic crispy dosa with chutney', 90, 140),
            ('Idli Sambar', 'Steamed idlis with sambar and chutneys', 80, 130),
            ('Vada Sambar', 'Medu vada with hot sambar', 90, 140),
            ('Mini Tiffin', 'Idli, vada, mini dosa combo', 150, 220),
        ]
    },
    {
        'name': 'Punjabi Zaika',
        'category': 'North Indian',
        'menu': [
            ('Chole Bhature', 'Spicy chickpeas with fluffy bhature', 150, 220),
            ('Paneer Tikka Roll', 'Grilled paneer roll with mint chutney', 140, 200),
            ('Aloo Paratha', 'Stuffed paratha with curd and pickle', 120, 180),
            ('Rajma Chawal Bowl', 'Kidney bean curry with rice', 140, 200),
            ('Paneer Butter Masala Bowl', 'Paneer curry with butter naan', 180, 260),
        ]
    },
    {
        'name': 'Bombay Sandwich Co.',
        'category': 'Sandwiches & Grills',
        'menu': [
            ('Veg Grilled Sandwich', 'Loaded with veggies and cheese', 120, 180),
            ('Paneer Tikka Sandwich', 'Paneer tikka filling, grilled', 140, 200),
            ('Cheese Chilli Toast', 'Cheesy toast with green chillies', 110, 160),
            ('Veg Club Sandwich', 'Triple decker classic', 150, 220),
            ('Corn & Cheese Sandwich', 'Buttery sweet corn & cheese', 120, 170),
        ]
    },
    {
        'name': 'Wrap n Roll',
        'category': 'Kathi & Wraps',
        'menu': [
            ('Veg Kathi Roll', 'Mixed veg roll with spices', 120, 170),
            ('Paneer Kathi Roll', 'Grilled paneer with onions', 140, 200),
            ('Mushroom Tikka Roll', 'Spiced mushroom wrap', 130, 190),
            ('Falafel Wrap', 'Crispy falafel with tahini', 150, 210),
        ]
    },
    {
        'name': 'Desi Chinese',
        'category': 'Indo-Chinese',
        'menu': [
            ('Veg Fried Rice', 'Wok tossed rice with veggies', 120, 170),
            ('Veg Hakka Noodles', 'Street style noodles', 130, 180),
            ('Veg Manchurian (Dry)', 'Crispy veg balls tossed in sauce', 150, 210),
            ('Paneer Chilli (Dry)', 'Paneer tossed in spicy sauce', 170, 230),
        ]
    },
    {
        'name': 'Tandoori Treats',
        'category': 'Tandoor',
        'menu': [
            ('Tandoori Paneer Tikka', 'Marinated paneer skewers', 180, 260),
            ('Veg Seekh Kebab', 'Spiced veg mince skewers', 160, 220),
            ('Tandoori Aloo', 'Baby potatoes in tandoori marinade', 140, 200),
            ('Butter Naan (2pc)', 'Soft naan with butter', 80, 120),
        ]
    },
    {
        'name': 'Healthy Bowls',
        'category': 'Salads & Bowls',
        'menu': [
            ('Quinoa Veg Bowl', 'Quinoa, veggies, tangy dressing', 180, 240),
            ('Sprout Chaat Bowl', 'High-protein sprout mix', 120, 170),
            ('Greek Salad', 'Feta, olives, cucumber', 180, 240),
            ('Fruit Bowl', 'Seasonal fresh fruits', 120, 160),
        ]
    },
    {
        'name': 'Sweet Tooth',
        'category': 'Desserts',
        'menu': [
            ('Gulab Jamun (2pc)', 'Warm syrupy dumplings', 80, 120),
            ('Rasmalai (2pc)', 'Saffron milk soaked', 120, 180),
            ('Kulfi Stick', 'Malai/pista/mango', 80, 120),
            ('Matka Kulfi', 'Traditional matka kulfi', 140, 200),
        ]
    },
    {
        'name': 'Thirst Quenchers',
        'category': 'Beverages',
        'menu': [
            ('Masala Chaas', 'Spiced buttermilk', 60, 90),
            ('Nimbu Pani', 'Fresh lemonade', 60, 100),
            ('Sugarcane Juice', 'Ganne ka ras (hygienic)', 80, 120),
            ('Cold Coffee', 'Classic with ice cream', 120, 180),
            ('Cutting Chai', 'Mumbai style tea', 20, 30),
        ]
    },
]

LOCATION_ZONES = [
    'North Stand - Concourse L1', 'North Stand - Concourse L2',
    'South Stand - Concourse L1', 'South Stand - Concourse L2',
    'East Stand - Concourse L1',  'East Stand - Concourse L2',
    'West Stand - Concourse L1',  'West Stand - Concourse L2',
    'Members Pavilion', 'Family Zone', 'Premium Concourse'
]

OPENING_HOURS = [
    '10:00 - 22:00', '11:00 - 21:30', '12:00 - 22:30', 'Match Hours Only'
]

def price_in_range(lo: int, hi: int) -> int:
    """Return a randomized price in INR between lo and hi inclusive, rounded to nearest 5."""
    p = random.randint(lo, hi)
    return int(round(p / 5) * 5)


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        database=os.getenv('POSTGRES_DB', 'stadium_db'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'admin')
    )


def generate_concessions_for_stadium(stadium_id: int, rng: random.Random):
    """Randomly choose a set of vegetarian stalls for a stadium and build menu items."""
    # Choose 5 to 9 unique stalls per stadium
    stall_count = rng.randint(5, 9)
    stalls = rng.sample(STALL_CATALOG, stall_count)

    concessions = []
    menu_items = []

    for stall in stalls:
        location = rng.choice(LOCATION_ZONES)
        hours = rng.choice(OPENING_HOURS)

        concession = {
            'stadium_id': stadium_id,
            'name': stall['name'],
            'category': stall['category'],
            'location_zone': location,
            'opening_hours': hours,
            'description': f"Pure Veg | {stall['category']}"
        }
        concessions.append(concession)

        # For menu items, pick 4 to 6 per stall
        item_count = rng.randint(4, min(6, len(stall['menu'])))
        items = rng.sample(stall['menu'], item_count)

        for name, desc, lo, hi in items:
            price = price_in_range(lo, hi)
            menu_items.append({
                'stall_name': stall['name'],  # temporary key to map after insert
                'name': name,
                'description': desc,
                'price': price,
                'category': stall['category'],
                'is_available': True
            })

    return concessions, menu_items


def main():
    print('🌱 Generating Vegetarian Concessions (INR) ...')
    conn = get_db_connection()
    cur = conn.cursor()

    # Get stadiums
    cur.execute('SELECT id, name FROM stadium ORDER BY id;')
    stadiums = cur.fetchall()
    print(f'Found {len(stadiums)} stadiums')

    # Clear existing concessions and menu items (already done by caller, but safe here)
    cur.execute('DELETE FROM menu_item;')
    cur.execute('DELETE FROM concession;')
    conn.commit()

    # Insert concessions per stadium
    concession_insert = (
        "INSERT INTO concession (stadium_id, name, category, location_zone, opening_hours, description)"
        " VALUES (%(stadium_id)s, %(name)s, %(category)s, %(location_zone)s, %(opening_hours)s, %(description)s)"
        " RETURNING id, name"
    )

    menu_insert = (
        "INSERT INTO menu_item (concession_id, name, description, price, category, is_available)"
        " VALUES (%(concession_id)s, %(name)s, %(description)s, %(price)s, %(category)s, %(is_available)s)"
    )

    total_concessions = 0
    total_items = 0

    for stadium_id, stadium_name in stadiums:
        print(f"\n🏟️  Stadium: {stadium_name}")
        rng = random.Random(stadium_id * 7919 + len(stadium_name))  # per-stadium seed for stability
        concessions, items = generate_concessions_for_stadium(stadium_id, rng)

        # Insert concessions and collect created IDs
        inserted_ids = {}
        for c in concessions:
            cur.execute(concession_insert, c)
            new_id, name = cur.fetchone()
            inserted_ids[name] = new_id
            total_concessions += 1

        # Map items to concession IDs and insert
        batch = []
        for mi in items:
            cid = inserted_ids.get(mi['stall_name'])
            if cid:
                batch.append({
                    'concession_id': cid,
                    'name': mi['name'],
                    'description': mi['description'],
                    'price': mi['price'],
                    'category': mi['category'],
                    'is_available': mi['is_available'],
                })
        if batch:
            execute_batch(cur, menu_insert, batch, page_size=200)
            total_items += len(batch)

        conn.commit()
        print(f"  → Added {len(concessions)} concessions and {len(batch)} menu items")

    cur.close()
    conn.close()

    print(f"\n✅ Completed: {total_concessions} concessions, {total_items} menu items across {len(stadiums)} stadiums (All Veg, INR)")


if __name__ == '__main__':
    main()

