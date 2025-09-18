"""
Concession Data Update Execution Script
Main script to clear existing concession data and populate with comprehensive Australian vegetarian options
"""

import sys
import os
import logging
from datetime import datetime

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from comprehensive_aussie_concessions_generator import ComprehensiveAussieConcessionGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('concession_data_update.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Execute the complete concession data update process"""
    
    print("=" * 70)
    print("🍽️ COMPREHENSIVE AUSTRALIAN VEGETARIAN CONCESSIONS UPDATE")
    print("=" * 70)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Initialize the comprehensive concession generator
        logger.info("🚀 Initializing Comprehensive Aussie Concession Generator...")
        generator = ComprehensiveAussieConcessionGenerator()
        
        # Execute the complete update process
        logger.info("📊 Starting concession data update process...")
        success = generator.run_complete_concession_update()
        
        if success:
            print()
            print("✅ SUCCESS!")
            print("🎉 All Australian vegetarian concession data has been successfully updated!")
            print()
            print("📈 Summary:")
            print("   • Cleared all existing concession and menu item records")
            print("   • Added 8-10 diverse cuisine concession stalls per stadium")
            print("   • Each concession has 10-15 carefully curated vegetarian menu items")
            print("   • Covers 8 BBL stadiums with comprehensive dining options")
            print()
            
            # Display cuisine variety
            print("🌏 Cuisine Variety Added:")
            cuisines = [
                "🇦🇺 Australian BBQ", "🇬🇷 Mediterranean", "🇯🇵 Asian Fusion", "🇮🇹 Italian",
                "🇲🇽 Mexican", "🇮🇳 Indian", "🥗 Health Food", "🇺🇸 American",
                "🇱🇧 Lebanese", "🇩🇪 German"
            ]
            for cuisine in cuisines:
                print(f"   • {cuisine}")
            
            print()
            print("🔍 Enhanced Features:")
            print("   • 100% vegetarian menu items across all concessions")
            print("   • Diverse price points from budget to premium")
            print("   • Strategic stadium zone placement")
            print("   • Realistic operating hours for match days")
            print("   • Detailed item descriptions and categories")
            print("   • Fresh, local Australian ingredients emphasized")
            
            return True
            
        else:
            print()
            print("❌ FAILED!")
            print("🚨 Concession data update encountered errors.")
            print("📝 Check the logs for detailed error information.")
            return False
            
    except Exception as e:
        logger.error(f"💥 Critical error during concession data update: {e}")
        print()
        print("❌ CRITICAL ERROR!")
        print(f"🚨 {e}")
        return False
    
    finally:
        print()
        print("=" * 70)
        print(f"📅 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

def verify_database_connection():
    """Verify that we can connect to the database"""
    try:
        from app import app, db
        from models import Stadium, Concession, MenuItem
        
        with app.app_context():
            # Test database connection
            stadium_count = Stadium.query.count()
            concession_count = Concession.query.count()
            menu_item_count = MenuItem.query.count()
            
            print(f"📊 Database Status:")
            print(f"   • Stadiums in database: {stadium_count}")
            print(f"   • Current concessions: {concession_count}")
            print(f"   • Current menu items: {menu_item_count}")
            print()
            
            if stadium_count == 0:
                print("⚠️ WARNING: No stadiums found in database!")
                print("   Please ensure stadiums are properly seeded before running concession update.")
                return False
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        print(f"🚨 Database connection error: {e}")
        return False

def show_concession_preview():
    """Show a preview of what will be added"""
    generator = ComprehensiveAussieConcessionGenerator()
    
    print("🔍 PREVIEW: Concession types to be added")
    print("-" * 50)
    
    for i, concept in enumerate(generator.concession_concepts[:5], 1):  # Show first 5 as preview
        print(f"📋 {i}. {concept['name']} ({concept['category']})")
        print(f"   {concept['description']}")
        print(f"   Sample items: {len(concept['menu_items'])} vegetarian options")
        print()
    
    print(f"🎯 Total cuisine types: {len(generator.concession_concepts)}")
    print(f"🏟️ Each stadium will get 8-10 randomly selected concession types")
    print(f"🍽️ Each concession will have 10-15 carefully curated menu items")
    print()

if __name__ == "__main__":
    print("🍽️ Australian Vegetarian Concessions Update System")
    print("==================================================")
    print()
    
    # Verify database connection first
    if not verify_database_connection():
        print("❌ Cannot proceed without database connection. Exiting.")
        sys.exit(1)
    
    # Show preview
    show_concession_preview()
    
    # Ask for confirmation
    response = input("🤔 Do you want to proceed with the concession data update? (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        print()
        success = main()
        sys.exit(0 if success else 1)
    else:
        print("❌ Operation cancelled by user.")
        sys.exit(0)