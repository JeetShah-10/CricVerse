#!/usr/bin/env python3
"""
Realistic Cricket Stadium Seating Generator
===========================================

This script generates realistic seating data for cricket stadiums with:
- Multiple tiers (Lower, Club, Upper, Premium)
- Proper block naming (North, South, East, West with subdivisions)
- Realistic pricing based on location and tier
- Proper row and seat numbering
- Shade considerations based on orientation
"""

import os
import sys
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv

# Load environment variables
if os.path.exists('cricverse.env'):
    load_dotenv('cricverse.env')
else:
    load_dotenv()

def get_db_connection():
    """Get PostgreSQL database connection using DATABASE_URL"""
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not found in environment variables!")
            return None
        
        # psycopg2.connect can directly use the DATABASE_URL
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

class StadiumSeatingGenerator:
    def __init__(self):
        self.seating_data = []
        
        # Define seating structure based on real cricket stadiums
        self.seating_structure = {
            # LOWER TIER - Close to field, premium view
            'Lower': {
                'blocks': {
                    'North Lower': {'rows': 20, 'seats_per_row': 25, 'base_price': 85, 'has_shade': False},
                    'South Lower': {'rows': 20, 'seats_per_row': 25, 'base_price': 95, 'has_shade': True},  # Premium end
                    'East Lower': {'rows': 18, 'seats_per_row': 22, 'base_price': 75, 'has_shade': False},
                    'West Lower': {'rows': 18, 'seats_per_row': 22, 'base_price': 75, 'has_shade': True},
                },
                'seat_type': 'Premium'
            },
            
            # CLUB TIER - Corporate and member seating
            'Club': {
                'blocks': {
                    'North Club': {'rows': 12, 'seats_per_row': 20, 'base_price': 120, 'has_shade': True},
                    'South Club': {'rows': 12, 'seats_per_row': 20, 'base_price': 140, 'has_shade': True},
                    'East Club': {'rows': 10, 'seats_per_row': 18, 'base_price': 110, 'has_shade': True},
                    'West Club': {'rows': 10, 'seats_per_row': 18, 'base_price': 110, 'has_shade': True},
                },
                'seat_type': 'Corporate'
            },
            
            # UPPER TIER - General admission, good views
            'Upper': {
                'blocks': {
                    'North Upper A': {'rows': 25, 'seats_per_row': 28, 'base_price': 45, 'has_shade': False},
                    'North Upper B': {'rows': 25, 'seats_per_row': 28, 'base_price': 45, 'has_shade': False},
                    'South Upper A': {'rows': 25, 'seats_per_row': 28, 'base_price': 55, 'has_shade': True},
                    'South Upper B': {'rows': 25, 'seats_per_row': 28, 'base_price': 55, 'has_shade': True},
                    'East Upper A': {'rows': 30, 'seats_per_row': 32, 'base_price': 40, 'has_shade': False},
                    'East Upper B': {'rows': 30, 'seats_per_row': 32, 'base_price': 40, 'has_shade': False},
                    'East Upper C': {'rows': 30, 'seats_per_row': 32, 'base_price': 40, 'has_shade': False},
                    'West Upper A': {'rows': 30, 'seats_per_row': 32, 'base_price': 40, 'has_shade': True},
                    'West Upper B': {'rows': 30, 'seats_per_row': 32, 'base_price': 40, 'has_shade': True},
                    'West Upper C': {'rows': 30, 'seats_per_row': 32, 'base_price': 40, 'has_shade': True},
                },
                'seat_type': 'Standard'
            },
            
            # GENERAL ADMISSION - Economy seating
            'General': {
                'blocks': {
                    'North General': {'rows': 35, 'seats_per_row': 35, 'base_price': 25, 'has_shade': False},
                    'East General A': {'rows': 40, 'seats_per_row': 38, 'base_price': 20, 'has_shade': False},
                    'East General B': {'rows': 40, 'seats_per_row': 38, 'base_price': 20, 'has_shade': False},
                    'West General A': {'rows': 40, 'seats_per_row': 38, 'base_price': 20, 'has_shade': True},
                    'West General B': {'rows': 40, 'seats_per_row': 38, 'base_price': 20, 'has_shade': True},
                },
                'seat_type': 'Economy'
            },
            
            # PREMIUM BOXES - VIP and hospitality
            'Premium': {
                'blocks': {
                    'VIP Box A': {'rows': 3, 'seats_per_row': 8, 'base_price': 250, 'has_shade': True},
                    'VIP Box B': {'rows': 3, 'seats_per_row': 8, 'base_price': 250, 'has_shade': True},
                    'VIP Box C': {'rows': 3, 'seats_per_row': 8, 'base_price': 250, 'has_shade': True},
                    'President Box': {'rows': 2, 'seats_per_row': 12, 'base_price': 350, 'has_shade': True},
                    'Media Box': {'rows': 4, 'seats_per_row': 15, 'base_price': 200, 'has_shade': True},
                },
                'seat_type': 'VIP'
            }
        }
    
    def generate_seats_for_stadium(self, stadium_id, max_seats_per_stadium):
        """Generate all seats for a specific stadium, up to a maximum limit"""
        print(f"Generating seats for stadium ID: {stadium_id} (max {max_seats_per_stadium} seats)")
        
        current_stadium_seats_count = 0
        for tier_name, tier_data in self.seating_structure.items():
            for block_name, block_info in tier_data['blocks'].items():
                if current_stadium_seats_count >= max_seats_per_stadium:
                    break
                
                seats_generated_in_block = self.generate_block_seats(
                    stadium_id=stadium_id,
                    section=block_name,
                    seat_type=tier_data['seat_type'],
                    rows=block_info['rows'],
                    seats_per_row=block_info['seats_per_row'],
                    base_price=block_info['base_price'],
                    has_shade=block_info['has_shade'],
                    max_seats_per_stadium=max_seats_per_stadium,
                    current_stadium_seats_count=current_stadium_seats_count
                )
                current_stadium_seats_count += seats_generated_in_block
            if current_stadium_seats_count >= max_seats_per_stadium:
                break
        
        print(f"Generated {current_stadium_seats_count} seats for stadium {stadium_id}")
        return current_stadium_seats_count
    
    def generate_block_seats(self, stadium_id, section, seat_type, rows, seats_per_row, base_price, has_shade, max_seats_per_stadium, current_stadium_seats_count):
        """Generate seats for a specific block/section, respecting stadium seat limit"""
        seats_generated_in_block = 0
        for row in range(1, rows + 1):
            if current_stadium_seats_count + seats_generated_in_block >= max_seats_per_stadium:
                break

            # Use alphabetical row naming for premium tiers, numerical for general
            if seat_type in ['VIP', 'Corporate']:
                row_name = chr(64 + row)  # A, B, C, etc.
            else:
                row_name = str(row).zfill(2)  # 01, 02, 03, etc.
            
            for seat in range(1, seats_per_row + 1):
                if current_stadium_seats_count + seats_generated_in_block >= max_seats_per_stadium:
                    break

                seat_number = str(seat).zfill(2)
                
                # Apply pricing variations based on position
                price = self.calculate_seat_price(base_price, row, seat, seats_per_row, seat_type)
                
                seat_data = {
                    'stadium_id': stadium_id,
                    'section': section,
                    'row_number': row_name,
                    'seat_number': seat_number,
                    'seat_type': seat_type,
                    'price': price,
                    'has_shade': has_shade
                }
                
                self.seating_data.append(seat_data)
                seats_generated_in_block += 1
        return seats_generated_in_block
    
    def calculate_seat_price(self, base_price, row, seat, seats_per_row, seat_type):
        """Calculate dynamic pricing based on seat position"""
        price = base_price
        
        # Row-based pricing (closer rows are more expensive)
        if seat_type in ['Premium', 'Corporate', 'VIP']:
            # Premium seating: front rows cost more
            if row <= 5:
                price *= 1.2
            elif row <= 10:
                price *= 1.1
        else:
            # Standard seating: middle rows are optimal
            if 5 <= row <= 15:
                price *= 1.05
            elif row > 25:
                price *= 0.9
        
        # Position-based pricing (center seats cost more)
        center_position = seats_per_row // 2
        distance_from_center = abs(seat - center_position)
        
        if distance_from_center <= seats_per_row * 0.2:  # Center 40%
            price *= 1.1
        elif distance_from_center >= seats_per_row * 0.4:  # Outer 20% each side
            price *= 0.95
        
        return round(price, 2)
    
    def insert_seats_to_database(self):
        """Insert generated seats into the database"""
        conn = get_db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            insert_query = """
                INSERT INTO seat (stadium_id, section, row_number, seat_number, seat_type, price, has_shade)
                VALUES (%(stadium_id)s, %(section)s, %(row_number)s, %(seat_number)s, %(seat_type)s, %(price)s, %(has_shade)s)
            """
            
            print("Inserting seats into database...")
            execute_batch(cursor, insert_query, self.seating_data, page_size=1000)
            
            conn.commit()
            print(f"Successfully inserted {len(self.seating_data)} seats")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error inserting seats: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return False
    
    def generate_summary_report(self):
        """Generate a summary report of the seating structure"""
        print("\n" + "="*60)
        print("SEATING STRUCTURE SUMMARY")
        print("="*60)
        
        total_seats = 0
        total_revenue_potential = 0
        
        for tier_name, tier_data in self.seating_structure.items():
            tier_seats = 0
            tier_revenue = 0
            
            print(f"\n{tier_name.upper()} TIER ({tier_data['seat_type']} seats):")
            print("-" * 40)
            
            for block_name, block_info in tier_data['blocks'].items():
                block_seats = block_info['rows'] * block_info['seats_per_row']
                block_revenue = block_seats * block_info['base_price']
                tier_seats += block_seats
                tier_revenue += block_revenue
                
                print(f"  {block_name:<20} | {block_seats:>4} seats | ₹{block_info['base_price']:>3} | Shade: {'Yes' if block_info['has_shade'] else 'No'}")
            
            print(f"  {'':<20} | {'':<4}      | {'':<4}     | ")
            print(f"  {'TIER TOTAL':<20} | {tier_seats:>4} seats | ₹{tier_revenue:>7,.0f} potential")
            
            total_seats += tier_seats
            total_revenue_potential += tier_revenue
        
        print("\n" + "="*60)
        print(f"TOTAL STADIUM CAPACITY: {total_seats:,} seats")
        print(f"TOTAL REVENUE POTENTIAL: ₹{total_revenue_potential:,.0f}")
        print(f"AVERAGE TICKET PRICE: ₹{total_revenue_potential/total_seats:.2f}")
        print("="*60)

def main():
    print("🏟️  CRICKET STADIUM SEATING GENERATOR")
    print("=====================================")
    
    generator = StadiumSeatingGenerator()
    
    # Show seating structure summary
    generator.generate_summary_report()
    
    print("\nGenerating seating data for all stadiums...")
    
    # Get all stadium IDs
    conn = get_db_connection()
    if not conn:
        print("❌ Could not connect to database")
        sys.exit(1)
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM stadium ORDER BY id;")
        stadiums = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not stadiums:
            print("❌ No stadiums found in database")
            sys.exit(1)
        
        print(f"\nFound {len(stadiums)} stadiums:")
        for stadium_id, stadium_name in stadiums:
            print(f"  - {stadium_id}: {stadium_name}")
        
        # Generate seats for each stadium
        total_generated = 0
        TOTAL_DESIRED_SEATS = 30000
        max_seats_per_stadium = TOTAL_DESIRED_SEATS // len(stadiums) if stadiums else TOTAL_DESIRED_SEATS
        
        for stadium_id, stadium_name in stadiums:
            print(f"\n🏟️  Processing: {stadium_name}")
            generator.seating_data = []  # Reset for each stadium
            seats_count = generator.generate_seats_for_stadium(stadium_id, max_seats_per_stadium)
            
            if generator.insert_seats_to_database():
                print(f"✅ Successfully created {seats_count:,} seats for {stadium_name}")
                total_generated += seats_count
            else:
                print(f"❌ Failed to create seats for {stadium_name}")
        
        print(f"\n🎉 COMPLETED!")
        print(f"Generated {total_generated:,} seats across {len(stadiums)} stadiums")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
