#!/usr/bin/env python3
"""
Vegetarian Concessions Management Utility
==========================================

A tool to view and manage the vegetarian concessions (food stalls) system
with authentic Indian menu items priced in INR.
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

class ConcessionsManager:
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
    
    def show_all_concessions_overview(self):
        """Show overview of all concessions across stadiums"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                s.name as stadium,
                COUNT(c.id) as concession_count,
                COUNT(mi.id) as menu_items,
                AVG(mi.price)::NUMERIC(10,0) as avg_price_inr
            FROM stadium s 
            LEFT JOIN concession c ON s.id = c.stadium_id 
            LEFT JOIN menu_item mi ON c.id = mi.concession_id
            GROUP BY s.id, s.name
            ORDER BY s.name;
        """)
        
        results = cursor.fetchall()
        cursor.close()
        
        headers = ["Stadium", "Concessions", "Menu Items", "Avg Price (₹)"]
        print(f"\n{'🇦🇺  AUSTRALIAN VEGETARIAN CONCESSIONS OVERVIEW (₹)'}")
        print("=" * 80)
        print(tabulate(results, headers=headers, tablefmt="grid"))
    
    def show_stadium_concessions(self, stadium_id):
        """Show all concessions for a specific stadium"""
        cursor = self.conn.cursor()
        
        # Get stadium name
        cursor.execute("SELECT name FROM stadium WHERE id = %s", (stadium_id,))
        result = cursor.fetchone()
        if not result:
            print("❌ Stadium not found")
            cursor.close()
            return
        stadium_name = result[0]
        
        # Get concessions for the stadium
        cursor.execute("""
            SELECT 
                c.name,
                c.category,
                c.location_zone,
                c.opening_hours,
                COUNT(mi.id) as menu_items,
                AVG(mi.price)::NUMERIC(10,0) as avg_price_inr
            FROM concession c
            LEFT JOIN menu_item mi ON c.id = mi.concession_id
            WHERE c.stadium_id = %s
            GROUP BY c.id, c.name, c.category, c.location_zone, c.opening_hours
            ORDER BY c.name;
        """, (stadium_id,))
        
        results = cursor.fetchall()
        cursor.close()
        
        if not results:
            print(f"❌ No concessions found for {stadium_name}")
            return
        
        print(f"\n🏟️  CONCESSIONS AT: {stadium_name}")
        print("=" * 100)
        
        headers = ["Stall Name", "Category", "Location", "Hours", "Items", "Avg Price (₹)"]
        print(tabulate(results, headers=headers, tablefmt="grid"))
    
    def show_concession_menu(self, concession_name):
        """Show menu for a specific concession"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                c.name as concession,
                c.category,
                c.description,
                s.name as stadium
            FROM concession c
            JOIN stadium s ON c.stadium_id = s.id
            WHERE c.name = %s
            LIMIT 1;
        """, (concession_name,))
        
        concession_info = cursor.fetchone()
        if not concession_info:
            print(f"❌ Concession '{concession_name}' not found")
            cursor.close()
            return
        
        # Get menu items
        cursor.execute("""
            SELECT 
                mi.name,
                mi.description,
                mi.price,
                CASE WHEN mi.is_available THEN '✅' ELSE '❌' END as available,
                CASE WHEN mi.is_vegetarian THEN '🌱' ELSE '🥩' END as vegetarian
            FROM menu_item mi
            JOIN concession c ON mi.concession_id = c.id
            WHERE c.name = %s
            ORDER BY mi.price;
        """, (concession_name,))
        
        menu_items = cursor.fetchall()
        cursor.close()
        
        name, category, desc, stadium = concession_info
        
        print(f"\n🍽️  MENU: {name}")
        print(f"📍 Location: {stadium}")
        print(f"🏷️  Category: {category}")
        print(f"📝 Description: {desc}")
        print("=" * 80)
        
        headers = ["Item", "Description", "Price (₹)", "Available", "Vegetarian"]
        print(tabulate(menu_items, headers=headers, tablefmt="grid"))
    
    def show_category_analysis(self):
        """Show analysis by food category"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                c.category,
                COUNT(DISTINCT c.id) as concessions,
                COUNT(mi.id) as total_items,
                MIN(mi.price) as min_price,
                MAX(mi.price) as max_price,
                AVG(mi.price)::NUMERIC(10,0) as avg_price
            FROM concession c
            LEFT JOIN menu_item mi ON c.id = mi.concession_id
            GROUP BY c.category
            ORDER BY avg_price DESC;
        """)
        
        results = cursor.fetchall()
        cursor.close()
        
        print(f"\n📊 FOOD CATEGORY ANALYSIS")
        print("=" * 90)
        
        headers = ["Category", "Stalls", "Items", "Min ₹", "Max ₹", "Avg ₹"]
        print(tabulate(results, headers=headers, tablefmt="grid"))
    
    def find_affordable_options(self, max_price=100):
        """Find affordable menu options under specified price"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                c.name as stall,
                mi.name as item,
                mi.description,
                mi.price,
                s.name as stadium
            FROM menu_item mi
            JOIN concession c ON mi.concession_id = c.id
            JOIN stadium s ON c.stadium_id = s.id
            WHERE mi.price <= %s AND mi.is_available = true
            ORDER BY mi.price, c.name;
        """, (max_price,))
        
        results = cursor.fetchall()
        cursor.close()
        
        if not results:
            print(f"❌ No items found under ₹{max_price}")
            return
        
        print(f"\n💰 AFFORDABLE OPTIONS (Under ₹{max_price})")
        print("=" * 100)
        
        headers = ["Stall", "Item", "Description", "Price (₹)", "Stadium"]
        print(tabulate(results, headers=headers, tablefmt="grid"))
    
    def interactive_menu(self):
        """Interactive menu for concessions management"""
        stadiums = self.get_stadiums()
        
        while True:
            print(f"\n{'🌱 VEGETARIAN CONCESSIONS MANAGER'}")
            print("=" * 50)
            print("1. All Concessions Overview")
            print("2. Stadium-wise Concessions")
            print("3. View Specific Menu")
            print("4. Category Analysis")
            print("5. Find Affordable Options")
            print("6. List All Stadiums")
            print("0. Exit")
            
            choice = input("\nSelect an option (0-6): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                self.show_all_concessions_overview()
            elif choice == "2":
                self._stadium_selection_menu(stadiums, self.show_stadium_concessions)
            elif choice == "3":
                stall_name = input("\nEnter concession name: ").strip()
                if stall_name:
                    self.show_concession_menu(stall_name)
                else:
                    print("❌ Please enter a valid concession name")
            elif choice == "4":
                self.show_category_analysis()
            elif choice == "5":
                try:
                    budget = int(input("Enter maximum price (₹): ").strip())
                    self.find_affordable_options(budget)
                except ValueError:
                    print("❌ Please enter a valid number")
            elif choice == "6":
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
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

def main():
    print("🇦🇺 AUSTRALIAN VEGETARIAN CONCESSIONS MANAGER (₹)")
    print("=================================")
    
    manager = ConcessionsManager()
    
    try:
        if len(sys.argv) > 1:
            # Command line mode
            command = sys.argv[1].lower()
            if command == "overview":
                manager.show_all_concessions_overview()
            elif command == "stadium" and len(sys.argv) > 2:
                stadium_id = int(sys.argv[2])
                manager.show_stadium_concessions(stadium_id)
            elif command == "menu" and len(sys.argv) > 2:
                concession_name = " ".join(sys.argv[2:])
                manager.show_concession_menu(concession_name)
            elif command == "categories":
                manager.show_category_analysis()
            elif command == "affordable" and len(sys.argv) > 2:
                max_price = int(sys.argv[2])
                manager.find_affordable_options(max_price)
            else:
                print("Usage: python concessions_manager.py [overview|stadium|menu|categories|affordable] [args...]")
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
