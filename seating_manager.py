#!/usr/bin/env python3
"""
Stadium Seating Management Utility
==================================

A management tool to view and analyze the realistic cricket stadium seating system.
Provides easy access to seating statistics, pricing information, and booking management.
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv
from tabulate import tabulate

# Load environment variables
if os.path.exists('cricverse.env'):
    load_dotenv('cricverse.env')
else:
    load_dotenv()

def get_db_connection():
    """Get PostgreSQL database connection"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            database=os.getenv('POSTGRES_DB', 'stadium_db'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', 'admin')
        )
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

class SeatingManager:
    def __init__(self):
        self.conn = get_db_connection()
        if not self.conn:
            print("❌ Could not connect to database")
            sys.exit(1)
    
    def get_stadiums(self):
        """Get list of all stadiums"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name FROM stadium ORDER BY id;")
        stadiums = cursor.fetchall()
        cursor.close()
        return stadiums
    
    def show_stadium_overview(self, stadium_id=None):
        """Show overview of all stadiums or a specific stadium"""
        cursor = self.conn.cursor()
        
        if stadium_id:
            cursor.execute("""
                SELECT s.name, COUNT(seat.id) as total_seats, 
                       AVG(seat.price)::NUMERIC(10,2) as avg_price,
                       MIN(seat.price) as min_price,
                       MAX(seat.price) as max_price
                FROM stadium s 
                JOIN seat ON s.id = seat.stadium_id 
                WHERE s.id = %s
                GROUP BY s.id, s.name;
            """, (stadium_id,))
        else:
            cursor.execute("""
                SELECT s.name, COUNT(seat.id) as total_seats, 
                       AVG(seat.price)::NUMERIC(10,2) as avg_price,
                       MIN(seat.price) as min_price,
                       MAX(seat.price) as max_price
                FROM stadium s 
                JOIN seat ON s.id = seat.stadium_id 
                GROUP BY s.id, s.name
                ORDER BY s.name;
            """)
        
        results = cursor.fetchall()
        cursor.close()
        
        headers = ["Stadium", "Total Seats", "Avg Price", "Min Price", "Max Price"]
        print(f"\n{'🏟️  STADIUM OVERVIEW'}")
        print("=" * 80)
        print(tabulate(results, headers=headers, tablefmt="grid", floatfmt=".2f"))
    
    def show_seating_breakdown(self, stadium_id):
        """Show detailed seating breakdown for a stadium"""
        cursor = self.conn.cursor()
        
        # Get stadium name
        cursor.execute("SELECT name FROM stadium WHERE id = %s", (stadium_id,))
        stadium_name = cursor.fetchone()[0]
        
        # Get seating breakdown by section and type
        cursor.execute("""
            SELECT section, seat_type, COUNT(*) as seat_count, 
                   MIN(price) as min_price, MAX(price) as max_price, 
                   AVG(price)::NUMERIC(10,2) as avg_price,
                   CASE WHEN has_shade THEN 'Yes' ELSE 'No' END as shade
            FROM seat 
            WHERE stadium_id = %s 
            GROUP BY section, seat_type, has_shade
            ORDER BY 
                CASE seat_type 
                    WHEN 'VIP' THEN 1 
                    WHEN 'Corporate' THEN 2 
                    WHEN 'Premium' THEN 3 
                    WHEN 'Standard' THEN 4 
                    WHEN 'Economy' THEN 5 
                END, section;
        """, (stadium_id,))
        
        results = cursor.fetchall()
        cursor.close()
        
        print(f"\n🏟️  SEATING BREAKDOWN: {stadium_name}")
        print("=" * 100)
        
        headers = ["Section", "Type", "Seats", "Min $", "Max $", "Avg $", "Shade"]
        print(tabulate(results, headers=headers, tablefmt="grid", floatfmt=".2f"))
        
        # Summary by tier
        tier_summary = {}
        for row in results:
            seat_type = row[1]
            seat_count = row[2]
            avg_price = float(row[5])
            
            if seat_type not in tier_summary:
                tier_summary[seat_type] = {'count': 0, 'revenue': 0}
            
            tier_summary[seat_type]['count'] += seat_count
            tier_summary[seat_type]['revenue'] += seat_count * avg_price
        
        print(f"\n📊 TIER SUMMARY:")
        print("-" * 50)
        total_seats = 0
        total_revenue = 0
        
        for seat_type, data in sorted(tier_summary.items()):
            count = data['count']
            revenue = data['revenue']
            avg_tier_price = revenue / count
            
            print(f"{seat_type:<12} | {count:>6,} seats | ${avg_tier_price:>6.2f} avg | ${revenue:>10,.0f} potential")
            total_seats += count
            total_revenue += revenue
        
        print("-" * 50)
        print(f"{'TOTAL':<12} | {total_seats:>6,} seats | ${total_revenue/total_seats:>6.2f} avg | ${total_revenue:>10,.0f} potential")
    
    def show_pricing_analysis(self, stadium_id):
        """Show pricing analysis for different sections"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT name FROM stadium WHERE id = %s", (stadium_id,))
        stadium_name = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN section LIKE '%VIP%' OR section LIKE '%President%' OR section LIKE '%Media%' THEN 'VIP/Premium Boxes'
                    WHEN section LIKE '%Club%' THEN 'Club/Corporate'
                    WHEN section LIKE '%Lower%' THEN 'Lower Tier'
                    WHEN section LIKE '%Upper%' THEN 'Upper Tier'
                    WHEN section LIKE '%General%' THEN 'General Admission'
                    ELSE 'Other'
                END as tier_group,
                COUNT(*) as total_seats,
                AVG(price)::NUMERIC(10,2) as avg_price,
                MIN(price) as min_price,
                MAX(price) as max_price,
                SUM(CASE WHEN has_shade THEN 1 ELSE 0 END) as shaded_seats
            FROM seat 
            WHERE stadium_id = %s
            GROUP BY tier_group
            ORDER BY avg_price DESC;
        """, (stadium_id,))
        
        results = cursor.fetchall()
        cursor.close()
        
        print(f"\n💰 PRICING ANALYSIS: {stadium_name}")
        print("=" * 90)
        
        headers = ["Tier Group", "Total Seats", "Avg Price", "Min Price", "Max Price", "Shaded Seats"]
        print(tabulate(results, headers=headers, tablefmt="grid", floatfmt=".2f"))
    
    def find_best_value_seats(self, stadium_id, budget_max=None, has_shade=None):
        """Find best value seats within budget and preferences"""
        cursor = self.conn.cursor()
        
        query = """
            SELECT section, row_number, seat_number, price, seat_type,
                   CASE WHEN has_shade THEN 'Yes' ELSE 'No' END as shade
            FROM seat 
            WHERE stadium_id = %s
        """
        params = [stadium_id]
        
        if budget_max:
            query += " AND price <= %s"
            params.append(budget_max)
        
        if has_shade is not None:
            query += " AND has_shade = %s"
            params.append(has_shade)
        
        query += " ORDER BY price, section, row_number, seat_number LIMIT 20;"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        
        if not results:
            print("❌ No seats found matching your criteria")
            return
        
        print(f"\n🎯 BEST VALUE SEATS (Top 20)")
        print("=" * 80)
        
        headers = ["Section", "Row", "Seat", "Price", "Type", "Shade"]
        print(tabulate(results, headers=headers, tablefmt="grid", floatfmt=".2f"))
    
    def interactive_menu(self):
        """Interactive menu for seating management"""
        stadiums = self.get_stadiums()
        
        while True:
            print(f"\n{'🏟️  CRICKET STADIUM SEATING MANAGER'}")
            print("=" * 50)
            print("1. Stadium Overview")
            print("2. Detailed Seating Breakdown")
            print("3. Pricing Analysis")
            print("4. Find Best Value Seats")
            print("5. List All Stadiums")
            print("0. Exit")
            
            choice = input("\nSelect an option (0-5): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                self.show_stadium_overview()
            elif choice == "2":
                self._stadium_selection_menu(stadiums, self.show_seating_breakdown)
            elif choice == "3":
                self._stadium_selection_menu(stadiums, self.show_pricing_analysis)
            elif choice == "4":
                self._best_value_menu(stadiums)
            elif choice == "5":
                print(f"\n📍 AVAILABLE STADIUMS:")
                for stadium_id, name in stadiums:
                    print(f"  {stadium_id}: {name}")
            else:
                print("❌ Invalid option. Please try again.")
    
    def _stadium_selection_menu(self, stadiums, callback_function):
        """Helper menu for stadium selection"""
        print(f"\n📍 SELECT STADIUM:")
        for i, (stadium_id, name) in enumerate(stadiums, 1):
            print(f"  {i}. {name}")
        
        try:
            selection = int(input(f"\nEnter stadium number (1-{len(stadiums)}): ")) - 1
            if 0 <= selection < len(stadiums):
                stadium_id = stadiums[selection][0]
                callback_function(stadium_id)
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Please enter a valid number")
    
    def _best_value_menu(self, stadiums):
        """Helper menu for best value seat search"""
        self._stadium_selection_menu(stadiums, self._best_value_search)
    
    def _best_value_search(self, stadium_id):
        """Interactive best value search"""
        print(f"\n🔍 SEAT SEARCH CRITERIA:")
        
        budget = input("Maximum budget (or press Enter for no limit): ").strip()
        budget_max = float(budget) if budget else None
        
        shade_pref = input("Prefer shaded seats? (y/n or press Enter for no preference): ").strip().lower()
        has_shade = True if shade_pref == 'y' else False if shade_pref == 'n' else None
        
        self.find_best_value_seats(stadium_id, budget_max, has_shade)
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

def main():
    print("🏟️  CRICKET STADIUM SEATING MANAGER")
    print("==================================")
    
    manager = SeatingManager()
    
    try:
        if len(sys.argv) > 1:
            # Command line mode
            command = sys.argv[1].lower()
            if command == "overview":
                manager.show_stadium_overview()
            elif command == "breakdown" and len(sys.argv) > 2:
                stadium_id = int(sys.argv[2])
                manager.show_seating_breakdown(stadium_id)
            elif command == "pricing" and len(sys.argv) > 2:
                stadium_id = int(sys.argv[2])
                manager.show_pricing_analysis(stadium_id)
            else:
                print("Usage: python seating_manager.py [overview|breakdown|pricing] [stadium_id]")
        else:
            # Interactive mode
            manager.interactive_menu()
    
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        manager.close()

if __name__ == "__main__":
    main()
