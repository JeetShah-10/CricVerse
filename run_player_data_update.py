"""
BBL Player Data Update Execution Script
Main script to clear existing player data and populate with comprehensive information
"""

import sys
import os
import logging
from datetime import datetime

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from comprehensive_player_manager import ComprehensivePlayerManager
from enhanced_player_scraper import PlayerDataEnricher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('player_data_update.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Execute the complete player data update process"""
    
    print("=" * 60)
    print("🏏 BBL COMPREHENSIVE PLAYER DATA UPDATE SYSTEM")
    print("=" * 60)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Initialize the comprehensive player manager
        logger.info("🚀 Initializing Comprehensive Player Manager...")
        manager = ComprehensivePlayerManager()
        
        # Execute the complete update process
        logger.info("📊 Starting player data update process...")
        success = manager.run_complete_player_update()
        
        if success:
            print()
            print("✅ SUCCESS!")
            print("🎉 All BBL player data has been successfully updated!")
            print()
            print("📈 Summary:")
            print("   • Cleared all existing player records")
            print("   • Added 88 players across 8 BBL teams")
            print("   • Enhanced with comprehensive cricket statistics")
            print("   • Included realistic player roles and market values")
            print()
            
            # Display team breakdown
            print("🏏 Team Breakdown:")
            for team_name, team_data in manager.teams_data.items():
                player_count = len(team_data["players"])
                print(f"   • {team_name}: {player_count} players")
            
            print()
            print("🔍 Enhanced Features Added:")
            print("   • Batting and bowling styles")
            print("   • Player roles (Batsman, Bowler, All-rounder, Wicket-keeper)")
            print("   • Captain and wicket-keeper identification")
            print("   • Jersey numbers")
            print("   • Market valuations")
            print("   • Nationality information")
            print("   • Age data")
            
            return True
            
        else:
            print()
            print("❌ FAILED!")
            print("🚨 Player data update encountered errors.")
            print("📝 Check the logs for detailed error information.")
            return False
            
    except Exception as e:
        logger.error(f"💥 Critical error during player data update: {e}")
        print()
        print("❌ CRITICAL ERROR!")
        print(f"🚨 {e}")
        return False
    
    finally:
        print()
        print("=" * 60)
        print(f"📅 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

def verify_database_connection():
    """Verify that we can connect to the database"""
    try:
        from app import app, db
        from models import Team, Player
        
        with app.app_context():
            # Test database connection
            team_count = Team.query.count()
            player_count = Player.query.count()
            
            print(f"📊 Database Status:")
            print(f"   • Teams in database: {team_count}")
            print(f"   • Players in database: {player_count}")
            print()
            
            if team_count == 0:
                print("⚠️ WARNING: No teams found in database!")
                print("   Please ensure teams are properly seeded before running player update.")
                return False
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        print(f"🚨 Database connection error: {e}")
        return False

def show_team_preview():
    """Show a preview of what will be added"""
    manager = ComprehensivePlayerManager()
    
    print("🔍 PREVIEW: Players to be added")
    print("-" * 40)
    
    total_players = 0
    for team_name, team_data in manager.teams_data.items():
        player_count = len(team_data["players"])
        total_players += player_count
        print(f"📋 {team_name}: {player_count} players")
        
        # Show first few players as example
        for i, player in enumerate(team_data["players"][:3]):
            print(f"   {i+1}. {player}")
        if player_count > 3:
            print(f"   ... and {player_count-3} more")
        print()
    
    print(f"🎯 Total players to process: {total_players}")
    print()

if __name__ == "__main__":
    print("🏏 BBL Player Data Update System")
    print("================================")
    print()
    
    # Verify database connection first
    if not verify_database_connection():
        print("❌ Cannot proceed without database connection. Exiting.")
        sys.exit(1)
    
    # Show preview
    show_team_preview()
    
    # Ask for confirmation
    response = input("🤔 Do you want to proceed with the player data update? (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        print()
        success = main()
        sys.exit(0 if success else 1)
    else:
        print("❌ Operation cancelled by user.")
        sys.exit(0)