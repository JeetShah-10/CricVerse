#!/usr/bin/env python3
"""
Australian Vegetarian Concessions Generator
============================================

Generates realistic Australian vegetarian food stalls for Big Bash League stadiums
with authentic Aussie menu items priced in AUD. The selection is randomized per
stadium to create variety across different venues.
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

# Random seed for reproducibility
random.seed()

AUSSIE_STALL_CATALOG: List[Dict] = [
    {
        'name': 'The Pie Shop',
        'category': 'Australian Pies',
        'menu': [
            ('Veggie Pie', 'Classic Australian meat pie with mixed vegetables', 8.50, 12.00),
            ('Mushroom & Herb Pie', 'Creamy mushroom pie with fresh herbs', 9.00, 13.50),
            ('Spinach & Ricotta Pie', 'Flaky pastry with spinach and ricotta filling', 8.50, 12.50),
            ('Potato & Leek Pie', 'Hearty potato and leek in golden pastry', 8.00, 11.50),
            ('Cheese & Onion Pie', 'Traditional cheese and onion combination', 7.50, 11.00),
        ]
    },
    {
        'name': 'Fair Dinkum Sandwiches',
        'category': 'Sandwiches & Rolls',
        'menu': [
            ('Veggie Sanger', 'Classic Australian sandwich with salad', 9.50, 14.00),
            ('Cheese & Tomato Roll', 'Fresh roll with cheese, tomato and lettuce', 8.50, 12.50),
            ('Avocado & Feta Wrap', 'Whole grain wrap with avocado and feta', 11.00, 16.00),
            ('Mushroom & Swiss Roll', 'Grilled mushrooms with Swiss cheese', 10.50, 15.00),
            ('Garden Salad Roll', 'Fresh mixed salad in crusty roll', 9.00, 13.50),
        ]
    },
    {
        'name': 'Barbie Grill Station',
        'category': 'BBQ & Grills',
        'menu': [
            ('Grilled Halloumi', 'BBQ halloumi cheese with herbs', 12.00, 18.00),
            ('Veggie Burger', 'House-made vegetarian patty with salad', 14.00, 20.00),
            ('Grilled Corn Cob', 'BBQ corn with butter and herbs', 6.00, 9.00),
            ('Mushroom Skewer', 'Marinated mushrooms grilled to perfection', 10.00, 15.00),
            ('Veggie Sausage Roll', 'Aussie-style vegetarian sausage roll', 7.50, 11.00),
        ]
    },
    {
        'name': 'Aussie Fish & Chips',
        'category': 'Fish & Chips',
        'menu': [
            ('Beer Battered Chips', 'Thick cut chips in beer batter', 8.00, 12.00),
            ('Wedges with Sour Cream', 'Crispy potato wedges with toppings', 9.50, 14.00),
            ('Onion Rings', 'Golden beer battered onion rings', 7.50, 11.50),
            ('Garden Salad', 'Fresh mixed salad with dressing', 10.00, 15.00),
        ]
    },
    {
        'name': 'Melbourne Coffee Co.',
        'category': 'Coffee & Beverages',
        'menu': [
            ('Flat White', 'Melbourne-style flat white coffee', 4.50, 6.50),
            ('Long Black', 'Strong black coffee, Australian style', 4.00, 5.50),
            ('Cappuccino', 'Classic Italian coffee with foam art', 4.50, 6.50),
            ('Iced Coffee', 'Cold coffee with ice cream and cream', 6.50, 9.00),
            ('Fresh Orange Juice', 'Squeezed Australian oranges', 5.50, 8.00),
            ('Lemon Lime & Bitters', 'Classic Aussie refresher', 4.00, 6.00),
        ]
    },
    {
        'name': 'The Lamington Hut',
        'category': 'Australian Sweets',
        'menu': [
            ('Lamington', 'Classic sponge cake in coconut', 4.50, 6.50),
            ('Anzac Biscuit', 'Traditional oat and coconut biscuit', 3.50, 5.00),
            ('Pavlova Slice', 'Meringue base with cream and berries', 6.50, 9.50),
            ('Tim Tam Slice', 'Chocolate biscuit slice', 5.00, 7.50),
            ('Caramel Slice', 'Golden syrup caramel slice', 5.50, 8.00),
        ]
    },
    {
        'name': 'Healthy Aussie Bowl',
        'category': 'Healthy Bowls',
        'menu': [
            ('Quinoa Power Bowl', 'Australian quinoa with roasted vegetables', 14.00, 19.00),
            ('Greek Bowl', 'Feta, olives, cucumber with grain base', 12.50, 17.50),
            ('Avocado Toast Bowl', 'Smashed avo on sourdough with extras', 13.00, 18.00),
            ('Seasonal Fruit Bowl', 'Fresh Australian seasonal fruits', 8.50, 12.50),
        ]
    },
    {
        'name': 'Outback Wraps',
        'category': 'Wraps & Rolls',
        'menu': [
            ('Veggie Wrap', 'Mixed vegetables in wholemeal wrap', 10.50, 15.00),
            ('Mediterranean Wrap', 'Feta, olives, cucumber wrap', 11.50, 16.50),
            ('Hummus & Salad Wrap', 'House-made hummus with fresh salad', 10.00, 14.50),
            ('Cheese & Spinach Roll', 'Warm roll with melted cheese', 9.00, 13.00),
        ]
    },
    {
        'name': 'Fizzy & Fresh',
        'category': 'Drinks & Refreshers',
        'menu': [
            ('Bundaberg Ginger Beer', 'Australian craft ginger beer', 4.50, 6.50),
            ('Sparkling Water', 'Australian spring sparkling water', 3.50, 5.00),
            ('Iced Tea', 'Refreshing iced tea with lemon', 4.00, 6.00),
            ('Fresh Lemonade', 'House-made Australian lemonade', 5.00, 7.50),
            ('Smoothie', 'Fresh fruit smoothie with yogurt', 7.50, 11.00),
        ]
    },
    {
        'name': 'Bush Tucker Bites',
        'category': 'Australian Fusion',
        'menu': [
            ('Wattle Seed Damper', 'Traditional bread with native seeds', 6.50, 9.50),
            ('Macadamia Crusted Vegetables', 'Australian nuts with seasonal veg', 12.00, 17.00),
            ('Bush Tomato Salad', 'Native tomatoes with mixed greens', 11.00, 15.50),
            ('Finger Lime Tartlet', 'Native citrus in pastry shell', 7.00, 10.50),
        ]
    },
]

LOCATION_ZONES = [
    'Great Southern Stand', 'Ponsford Stand', 'Olympic Stand',
    'Members Reserve', 'MCC Members Area', 'Premium Club',
    'Northern Concourse', 'Southern Concourse', 'Eastern Concourse', 'Western Concourse',
    'Family Zone', 'General Admission', 'Club Level'
]

OPENING_HOURS = [
    'Gates Open - Close', '11:00 AM - 11:00 PM', '10:30 AM - 10:30 PM', 'Match Days Only'
]

def price_in_range(lo: float, hi: float) -> float:
    """Return a randomized price in AUD between lo and hi, rounded to nearest $0.50."""
    p = random.uniform(lo, hi)
    return round(p * 2) / 2  # Round to nearest 50 cents


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        database=os.getenv('POSTGRES_DB', 'stadium_db'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'admin')
    )


def generate_concessions_for_stadium(stadium_id: int, rng: random.Random):
    """Randomly choose Australian vegetarian stalls for a stadium."""
    # Choose 6 to 10 unique stalls per stadium
    stall_count = rng.randint(6, 10)
    stalls = rng.sample(AUSSIE_STALL_CATALOG, stall_count)

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
            'description': f"Vegetarian Australian | {stall['category']}"
        }
        concessions.append(concession)

        # For menu items, pick 3 to 5 per stall
        item_count = rng.randint(3, min(5, len(stall['menu'])))
        items = rng.sample(stall['menu'], item_count)

        for name, desc, lo, hi in items:
            price = price_in_range(lo, hi)
            menu_items.append({
                'stall_name': stall['name'],
                'name': name,
                'description': desc,
                'price': price,
                'category': stall['category'],
                'is_available': True,
                'is_vegetarian': True  # All Australian items are vegetarian
            })

    return concessions, menu_items


def main():
    print('🇦🇺 Generating Australian Vegetarian Concessions (AUD) ...')
    conn = get_db_connection()
    cur = conn.cursor()

    # Get stadiums
    cur.execute('SELECT id, name FROM stadium ORDER BY id;')
    stadiums = cur.fetchall()
    print(f'Found {len(stadiums)} BBL stadiums')

    # Clear existing concessions
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
        "INSERT INTO menu_item (concession_id, name, description, price, category, is_available, is_vegetarian)"
        " VALUES (%(concession_id)s, %(name)s, %(description)s, %(price)s, %(category)s, %(is_available)s, %(is_vegetarian)s)"
    )

    total_concessions = 0
    total_items = 0

    for stadium_id, stadium_name in stadiums:
        print(f"\n🏟️  Stadium: {stadium_name}")
        rng = random.Random(stadium_id * 1337 + len(stadium_name))
        concessions, items = generate_concessions_for_stadium(stadium_id, rng)

        # Insert concessions
        inserted_ids = {}
        for c in concessions:
            cur.execute(concession_insert, c)
            new_id, name = cur.fetchone()
            inserted_ids[name] = new_id
            total_concessions += 1

        # Insert menu items
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
                    'is_vegetarian': mi['is_vegetarian'],
                })
        if batch:
            execute_batch(cur, menu_insert, batch, page_size=100)
            total_items += len(batch)

        conn.commit()
        print(f"  → Added {len(concessions)} Aussie stalls and {len(batch)} menu items")

    cur.close()
    conn.close()

    print(f"\n✅ G'day mate! Created {total_concessions} Australian veggie stalls, {total_items} menu items across {len(stadiums)} BBL stadiums")
    print(f"🥧 Fair dinkum vegetarian tucker with true blue Aussie prices!")


if __name__ == '__main__':
    main()
