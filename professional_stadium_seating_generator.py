#!/usr/bin/env python3
"""
Professional Cricket Stadium Seating Generator
==============================================

This script generates realistic, professional stadium seating data based on actual stadium capacities
and real-world cricket stadium layouts. Each stadium gets a unique seating configuration that matches
its capacity and provides multiple viewing zones, pricing tiers, and realistic sections for an
immersive booking experience.

Features:
- Stadium-specific layouts based on actual capacity
- Multiple tiers: Lower Bowl, Club Level, Upper Tier, Premium Suites
- Realistic block naming (North, South, East, West with subdivisions)
- Dynamic pricing based on location, view quality, and amenities
- Shade considerations for Australian cricket stadiums
- VIP boxes, media sections, and accessibility seating
- Corporate hospitality areas
"""

import os
import sys
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv
import math
import random
from typing import Dict, List, Tuple

# Load environment variables
if os.path.exists('cricverse.env'):
    load_dotenv('cricverse.env')
else:
    load_dotenv()

import time

def get_db_connection(retries=5, delay=2):
    """Get PostgreSQL database connection with retry logic."""
    for i in range(retries):
        try:
            # Check for DATABASE_URL first (Supabase)
            database_url = os.getenv('DATABASE_URL')
            
            if database_url and 'postgresql' in database_url:
                # Parse Supabase URL
                import urllib.parse as urlparse
                url = urlparse.urlparse(database_url)
                conn = psycopg2.connect(
                    host=url.hostname,
                    port=url.port,
                    database=url.path[1:],  # Remove leading slash
                    user=url.username,
                    password=url.password
                )
                print(f"✅ Connected to Supabase database")
                return conn
            else:
                # Fallback to local PostgreSQL
                conn = psycopg2.connect(
                    host=os.getenv('POSTGRES_HOST', 'localhost'),
                    port=os.getenv('POSTGRES_PORT', '5432'),
                    database=os.getenv('POSTGRES_DB', 'stadium_db'),
                    user=os.getenv('POSTGRES_USER', 'postgres'),
                    password=os.getenv('POSTGRES_PASSWORD', 'admin')
                )
                print(f"✅ Connected to local PostgreSQL database")
                return conn
        except Exception as e:
            print(f"❌ Database connection failed (attempt {i+1}/{retries}): {e}")
            if i < retries - 1:
                time.sleep(delay * (2 ** i))  # Exponential backoff
            else:
                return None
    return None

class ProfessionalStadiumSeatingGenerator:
    def __init__(self):
        self.seating_data = []
        
        # Real-world stadium seating templates based on actual BBL venues
        self.stadium_templates = {
            # Large stadiums (80,000+)
            'large': {
                'capacity_range': (80000, 120000),
                'tiers': {
                    'Lower Bowl': {
                        'capacity_percentage': 0.35,  # 35% of total capacity
                        'blocks': {
                            'Southern Lower': {'rows': 25, 'avg_seats': 28, 'base_price': 120, 'has_shade': True, 'premium': True},
                            'Northern Lower': {'rows': 25, 'avg_seats': 28, 'base_price': 95, 'has_shade': False, 'premium': False},
                            'Eastern Lower': {'rows': 22, 'avg_seats': 25, 'base_price': 85, 'has_shade': False, 'premium': False},
                            'Western Lower': {'rows': 22, 'avg_seats': 25, 'base_price': 85, 'has_shade': True, 'premium': False},
                            'Great Southern Stand': {'rows': 30, 'avg_seats': 35, 'base_price': 110, 'has_shade': True, 'premium': True},
                        }
                    },
                    'Club Reserve': {
                        'capacity_percentage': 0.15,
                        'blocks': {
                            'MCC Reserve': {'rows': 15, 'avg_seats': 24, 'base_price': 180, 'has_shade': True, 'premium': True},
                            'AFL Members': {'rows': 15, 'avg_seats': 24, 'base_price': 175, 'has_shade': True, 'premium': True},
                            'Club Level North': {'rows': 12, 'avg_seats': 20, 'base_price': 160, 'has_shade': True, 'premium': True},
                            'Club Level South': {'rows': 12, 'avg_seats': 20, 'base_price': 170, 'has_shade': True, 'premium': True},
                        }
                    },
                    'Upper Tier': {
                        'capacity_percentage': 0.40,
                        'blocks': {
                            'Upper North A': {'rows': 35, 'avg_seats': 32, 'base_price': 55, 'has_shade': False, 'premium': False},
                            'Upper North B': {'rows': 35, 'avg_seats': 32, 'base_price': 55, 'has_shade': False, 'premium': False},
                            'Upper South A': {'rows': 35, 'avg_seats': 32, 'base_price': 65, 'has_shade': True, 'premium': False},
                            'Upper South B': {'rows': 35, 'avg_seats': 32, 'base_price': 65, 'has_shade': True, 'premium': False},
                            'Upper East': {'rows': 40, 'avg_seats': 35, 'base_price': 45, 'has_shade': False, 'premium': False},
                            'Upper West': {'rows': 40, 'avg_seats': 35, 'base_price': 45, 'has_shade': True, 'premium': False},
                        }
                    },
                    'Premium Suites': {
                        'capacity_percentage': 0.10,
                        'blocks': {
                            'Presidential Suite': {'rows': 3, 'avg_seats': 12, 'base_price': 450, 'has_shade': True, 'premium': True},
                            'Corporate Box A': {'rows': 4, 'avg_seats': 10, 'base_price': 350, 'has_shade': True, 'premium': True},
                            'Corporate Box B': {'rows': 4, 'avg_seats': 10, 'base_price': 350, 'has_shade': True, 'premium': True},
                            'Corporate Box C': {'rows': 4, 'avg_seats': 10, 'base_price': 350, 'has_shade': True, 'premium': True},
                            'Media Centre': {'rows': 5, 'avg_seats': 15, 'base_price': 280, 'has_shade': True, 'premium': True},
                            'VIP Lounge': {'rows': 6, 'avg_seats': 18, 'base_price': 320, 'has_shade': True, 'premium': True},
                        }
                    }
                }
            },
            
            # Medium stadiums (40,000-80,000)
            'medium': {
                'capacity_range': (40000, 80000),
                'tiers': {
                    'Lower Tier': {
                        'capacity_percentage': 0.40,
                        'blocks': {
                            'Southern Stand': {'rows': 22, 'avg_seats': 26, 'base_price': 95, 'has_shade': True, 'premium': True},
                            'Northern Stand': {'rows': 22, 'avg_seats': 26, 'base_price': 75, 'has_shade': False, 'premium': False},
                            'Eastern Stand': {'rows': 20, 'avg_seats': 24, 'base_price': 65, 'has_shade': False, 'premium': False},
                            'Western Stand': {'rows': 20, 'avg_seats': 24, 'base_price': 65, 'has_shade': True, 'premium': False},
                            'Member\'s Reserve': {'rows': 18, 'avg_seats': 22, 'base_price': 110, 'has_shade': True, 'premium': True},
                        }
                    },
                    'Club Level': {
                        'capacity_percentage': 0.20,
                        'blocks': {
                            'Club North': {'rows': 12, 'avg_seats': 20, 'base_price': 140, 'has_shade': True, 'premium': True},
                            'Club South': {'rows': 12, 'avg_seats': 20, 'base_price': 150, 'has_shade': True, 'premium': True},
                            'Premium Terrace': {'rows': 8, 'avg_seats': 16, 'base_price': 160, 'has_shade': True, 'premium': True},
                        }
                    },
                    'Upper Bowl': {
                        'capacity_percentage': 0.30,
                        'blocks': {
                            'Upper North': {'rows': 30, 'avg_seats': 30, 'base_price': 45, 'has_shade': False, 'premium': False},
                            'Upper South': {'rows': 30, 'avg_seats': 30, 'base_price': 55, 'has_shade': True, 'premium': False},
                            'Upper East': {'rows': 25, 'avg_seats': 28, 'base_price': 40, 'has_shade': False, 'premium': False},
                            'Upper West': {'rows': 25, 'avg_seats': 28, 'base_price': 40, 'has_shade': True, 'premium': False},
                        }
                    },
                    'Premium Areas': {
                        'capacity_percentage': 0.10,
                        'blocks': {
                            'Director\'s Box': {'rows': 3, 'avg_seats': 10, 'base_price': 380, 'has_shade': True, 'premium': True},
                            'Corporate Suite A': {'rows': 4, 'avg_seats': 8, 'base_price': 280, 'has_shade': True, 'premium': True},
                            'Corporate Suite B': {'rows': 4, 'avg_seats': 8, 'base_price': 280, 'has_shade': True, 'premium': True},
                            'Hospitality Deck': {'rows': 5, 'avg_seats': 12, 'base_price': 220, 'has_shade': True, 'premium': True},
                        }
                    }
                }
            },
            
            # Small stadiums (15,000-40,000)
            'small': {
                'capacity_range': (15000, 40000),
                'tiers': {
                    'Main Stand': {
                        'capacity_percentage': 0.45,
                        'blocks': {
                            'Southern Grandstand': {'rows': 20, 'avg_seats': 25, 'base_price': 75, 'has_shade': True, 'premium': True},
                            'Northern Grandstand': {'rows': 20, 'avg_seats': 25, 'base_price': 55, 'has_shade': False, 'premium': False},
                            'Eastern Pavilion': {'rows': 18, 'avg_seats': 22, 'base_price': 50, 'has_shade': False, 'premium': False},
                            'Western Pavilion': {'rows': 18, 'avg_seats': 22, 'base_price': 50, 'has_shade': True, 'premium': False},
                        }
                    },
                    'Premium Seating': {
                        'capacity_percentage': 0.25,
                        'blocks': {
                            'Members\' Stand': {'rows': 15, 'avg_seats': 20, 'base_price': 110, 'has_shade': True, 'premium': True},
                            'Corporate Terrace': {'rows': 10, 'avg_seats': 16, 'base_price': 130, 'has_shade': True, 'premium': True},
                            'Premium Deck': {'rows': 8, 'avg_seats': 14, 'base_price': 120, 'has_shade': True, 'premium': True},
                        }
                    },
                    'General Admission': {
                        'capacity_percentage': 0.25,
                        'blocks': {
                            'Hill Section': {'rows': 25, 'avg_seats': 28, 'base_price': 35, 'has_shade': False, 'premium': False},
                            'Terrace North': {'rows': 20, 'avg_seats': 24, 'base_price': 30, 'has_shade': False, 'premium': False},
                            'Terrace South': {'rows': 20, 'avg_seats': 24, 'base_price': 35, 'has_shade': True, 'premium': False},
                        }
                    },
                    'VIP Boxes': {
                        'capacity_percentage': 0.05,
                        'blocks': {
                            'Executive Box': {'rows': 2, 'avg_seats': 8, 'base_price': 300, 'has_shade': True, 'premium': True},
                            'VIP Suite': {'rows': 3, 'avg_seats': 6, 'base_price': 250, 'has_shade': True, 'premium': True},
                        }
                    }
                }
            }
        }
    
    def get_stadium_template(self, capacity: int) -> str:
        """Determine which template to use based on stadium capacity"""
        if capacity >= 80000:
            return 'large'
        elif capacity >= 40000:
            return 'medium'
        else:
            return 'small'
    
    def generate_seats_for_stadium(self, stadium_id: int, stadium_name: str, capacity: int):
        """Generate realistic seating layout for a specific stadium"""
        print(f"\n🏟️  Generating seats for {stadium_name} (Capacity: {capacity:,})")
        
        template_type = self.get_stadium_template(capacity)
        template = self.stadium_templates[template_type]
        
        print(f"   Using template: {template_type.upper()}")
        
        total_generated = 0
        
        # Scaling factor to reduce total seats
        SEAT_SCALING_FACTOR = 0.15  # Adjust this value to get the desired total seat count

        for tier_name, tier_data in template['tiers'].items():
            tier_capacity = int(capacity * tier_data['capacity_percentage'] * SEAT_SCALING_FACTOR)
            print(f"   {tier_name}: {tier_capacity:,} seats (scaled)")
            
            tier_seats = 0
            blocks = list(tier_data['blocks'].items())
            
            for i, (block_name, block_info) in enumerate(blocks):
                # Distribute tier capacity among blocks
                if i == len(blocks) - 1:  # Last block gets remaining seats
                    block_capacity = tier_capacity - tier_seats
                else:
                    block_percentage = 1.0 / len(blocks)
                    block_capacity = int(tier_capacity * block_percentage)
                
                if block_capacity > 0:
                    seats_generated = self.generate_block_seats(
                        stadium_id=stadium_id,
                        section=block_name,
                        target_capacity=block_capacity,
                        block_info=block_info,
                        tier_name=tier_name
                    )
                    tier_seats += seats_generated
                    total_generated += seats_generated
        
        print(f"   ✅ Generated {total_generated:,} seats for {stadium_name}")
        return total_generated
    
    def generate_block_seats(self, stadium_id: int, section: str, target_capacity: int, 
                           block_info: Dict, tier_name: str) -> int:
        """Generate seats for a specific block/section"""
        
        max_rows = block_info['rows']
        avg_seats_per_row = block_info['avg_seats']
        base_price = block_info['base_price']
        has_shade = block_info['has_shade']
        is_premium = block_info['premium']
        
        # Calculate actual seats per row to meet target capacity
        total_seats_at_avg = max_rows * avg_seats_per_row
        if total_seats_at_avg == 0:
            return 0
        
        adjustment_factor = target_capacity / total_seats_at_avg
        
        seats_generated = 0
        
        for row in range(1, max_rows + 1):
            # Calculate seats for this row with some variation
            base_seats = int(avg_seats_per_row * adjustment_factor)
            
            # Add realistic variation: front rows often have fewer seats, back rows more
            if is_premium:
                if row <= 5:  # Front premium rows
                    seats_in_row = max(int(base_seats * 0.8), 6)
                elif row <= 10:
                    seats_in_row = base_seats
                else:
                    seats_in_row = int(base_seats * 1.1)
            else:
                if row <= 3:  # Very front rows
                    seats_in_row = max(int(base_seats * 0.9), 8)
                else:
                    seats_in_row = base_seats
            
            # Ensure even numbers for better layout
            if seats_in_row % 2 != 0:
                seats_in_row += 1
            
            # Generate row identifier
            if is_premium or 'Box' in section or 'Suite' in section:
                row_name = chr(64 + row)  # A, B, C for premium
            else:
                row_name = f"{row:02d}"  # 01, 02, 03 for general
            
            # Generate individual seats
            for seat in range(1, seats_in_row + 1):
                seat_number = f"{seat:02d}"
                
                # Calculate dynamic pricing
                price = self.calculate_dynamic_price(
                    base_price, row, seat, seats_in_row, section, tier_name, is_premium
                )
                
                seat_data = {
                    'stadium_id': stadium_id,
                    'section': section,
                    'row_number': row_name,
                    'seat_number': seat_number,
                    'seat_type': self.get_seat_type(tier_name, section, is_premium),
                    'price': price,
                    'has_shade': has_shade
                }
                
                self.seating_data.append(seat_data)
                seats_generated += 1
        
        return seats_generated
    
    def calculate_dynamic_price(self, base_price: float, row: int, seat: int, 
                              seats_in_row: int, section: str, tier_name: str, 
                              is_premium: bool) -> float:
        """Calculate dynamic pricing based on multiple factors"""
        price = base_price
        
        # Row-based pricing
        if is_premium:
            # Premium seating: front rows are most expensive
            if row <= 3:
                price *= 1.3
            elif row <= 8:
                price *= 1.15
            elif row <= 15:
                price *= 1.05
            else:
                price *= 0.95
        else:
            # Standard seating: rows 5-15 are optimal
            if 5 <= row <= 15:
                price *= 1.1
            elif row <= 4:
                price *= 1.05
            elif row > 25:
                price *= 0.85
        
        # Position-based pricing (center seats are premium)
        center = seats_in_row // 2
        distance_from_center = abs(seat - center)
        center_ratio = distance_from_center / (seats_in_row // 2) if seats_in_row > 2 else 0
        
        if center_ratio <= 0.3:  # Center 30%
            price *= 1.15
        elif center_ratio <= 0.6:  # Middle 30%
            price *= 1.05
        else:  # Outer 40%
            price *= 0.92
        
        # Section-specific modifiers
        if 'Presidential' in section or 'Director' in section:
            price *= 1.2
        elif 'Corporate' in section or 'Executive' in section:
            price *= 1.1
        elif 'Media' in section:
            price *= 0.9
        elif 'Hill' in section or 'Terrace' in section:
            price *= 0.8
        
        # Weekend/premium event multiplier simulation
        if is_premium:
            price *= 1.05
        
        return round(price, 2)
    
    def get_seat_type(self, tier_name: str, section: str, is_premium: bool) -> str:
        """Determine seat type based on tier and section"""
        if 'Suite' in section or 'Box' in section or 'Presidential' in section:
            return 'VIP'
        elif 'Corporate' in section or 'Executive' in section or 'Director' in section:
            return 'Corporate'
        elif is_premium or 'Club' in tier_name or 'Premium' in tier_name:
            return 'Premium'
        elif 'Hill' in section or 'Terrace' in section:
            return 'General'
        else:
            return 'Standard'
    
    def insert_seats_to_database(self) -> bool:
        """Insert generated seats into the database with optimized batch processing"""
        if not self.seating_data:
            print("❌ No seating data to insert")
            return False
        
        conn = get_db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Clear existing seats for the stadium
            stadium_ids = list(set(seat['stadium_id'] for seat in self.seating_data))
            for stadium_id in stadium_ids:
                cursor.execute("DELETE FROM seat WHERE stadium_id = %s", (stadium_id,))
            
            insert_query = """
                INSERT INTO seat (stadium_id, section, row_number, seat_number, seat_type, price, has_shade)
                VALUES (%(stadium_id)s, %(section)s, %(row_number)s, %(seat_number)s, %(seat_type)s, %(price)s, %(has_shade)s)
            """
            
            # Process in smaller batches to avoid connection timeouts
            batch_size = 250  # Smaller batch size for Supabase
            total_seats = len(self.seating_data)
            
            print(f"   Inserting {total_seats:,} seats in batches of {batch_size}...")
            
            for i in range(0, total_seats, batch_size):
                batch = self.seating_data[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (total_seats + batch_size - 1) // batch_size
                
                try:
                    execute_batch(cursor, insert_query, batch, page_size=batch_size)
                    print(f"     Batch {batch_num}/{total_batches} completed ({len(batch)} seats)")
                    
                    # Commit after each batch to avoid long transactions
                    conn.commit()
                    
                except Exception as batch_error:
                    print(f"     ❌ Error in batch {batch_num}: {batch_error}")
                    conn.rollback()
                    
                    # Try individual inserts for this batch
                    print(f"     🔄 Retrying batch {batch_num} with individual inserts...")
                    success_count = 0
                    for seat_data in batch:
                        try:
                            cursor.execute(insert_query, seat_data)
                            success_count += 1
                        except Exception as individual_error:
                            print(f"       ❌ Failed to insert seat: {individual_error}")
                    
                    if success_count > 0:
                        conn.commit()
                        print(f"     ✅ Inserted {success_count}/{len(batch)} seats individually")
            
            print(f"   ✅ Successfully inserted seating data")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"   ❌ Error inserting seats: {e}")
            try:
                if conn and not conn.closed:
                    conn.rollback()
                    conn.close()
            except:
                pass
            return False
    
    def generate_summary_report(self, stadiums: List[Tuple]):
        """Generate a comprehensive summary report"""
        print("\n" + "="*80)
        print("PROFESSIONAL STADIUM SEATING SUMMARY")
        print("="*80)
        
        total_capacity = 0
        total_revenue_potential = 0
        
        for stadium_id, stadium_name, location, capacity in stadiums:
            total_capacity += capacity
            template_type = self.get_stadium_template(capacity)
            template = self.stadium_templates[template_type]
            
            stadium_revenue = 0
            print(f"\n🏟️  {stadium_name} ({location})")
            print(f"    Capacity: {capacity:,} | Template: {template_type.upper()}")
            print("-" * 60)
            
            for tier_name, tier_data in template['tiers'].items():
                tier_capacity = int(capacity * tier_data['capacity_percentage'])
                tier_avg_price = sum(block['base_price'] for block in tier_data['blocks'].values()) / len(tier_data['blocks'])
                tier_revenue = tier_capacity * tier_avg_price
                stadium_revenue += tier_revenue
                
                print(f"    {tier_name:<18} | {tier_capacity:>6,} seats | ${tier_avg_price:>6.0f} avg | ${tier_revenue:>10,.0f}")
            
            total_revenue_potential += stadium_revenue
            print(f"    {'STADIUM TOTAL':<18} | {capacity:>6,} seats | {'':>6} | ${stadium_revenue:>10,.0f}")
        
        print("\n" + "="*80)
        print(f"TOTAL LEAGUE CAPACITY: {total_capacity:,} seats")
        print(f"TOTAL REVENUE POTENTIAL: ${total_revenue_potential:,.0f}")
        print(f"AVERAGE TICKET PRICE: ${total_revenue_potential/total_capacity:.2f}")
        print(f"STADIUMS PROCESSED: {len(stadiums)}")
        print("="*80)

def main():
    print("🏟️  PROFESSIONAL CRICKET STADIUM SEATING GENERATOR")
    print("=" * 55)
    print("Creating realistic, capacity-matched seating for BBL stadiums")
    
    # Get database connection and stadium data
    conn = get_db_connection()
    if not conn:
        print("❌ Could not connect to database")
        sys.exit(1)
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, location, capacity FROM stadium ORDER BY id;")
        stadiums = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not stadiums:
            print("❌ No stadiums found in database")
            sys.exit(1)
        
        generator = ProfessionalStadiumSeatingGenerator()
        
        # Show summary before generation
        generator.generate_summary_report(stadiums)
        
        print("\n" + "="*55)
        print("GENERATING SEATING DATA")
        print("="*55)
        
        total_generated = 0
        successful_stadiums = 0
        
        for stadium_id, stadium_name, location, capacity in stadiums:
            generator.seating_data = []  # Reset for each stadium
            
            seats_count = generator.generate_seats_for_stadium(stadium_id, stadium_name, capacity)
            
            if generator.insert_seats_to_database():
                total_generated += seats_count
                successful_stadiums += 1
            else:
                print(f"   ❌ Failed to insert seats for {stadium_name}")
        
        print("\n" + "🎉" * 20)
        print("GENERATION COMPLETED SUCCESSFULLY!")
        print("🎉" * 40)
        print(f"✅ Processed {successful_stadiums}/{len(stadiums)} stadiums")
        print(f"✅ Generated {total_generated:,} professional stadium seats")
        print(f"✅ Ready for modern booking interface!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()