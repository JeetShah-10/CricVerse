#!/usr/bin/env python3
"""
Supabase Database Configuration and Setup for CricVerse
This script will configure the Supabase connection and create the necessary tables.
"""

import os
import sys
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

def configure_environment():
    """Configure environment variables for Supabase connection"""
    print("🔧 Configuring Supabase environment...")
    
    # Load environment from cricverse.env if it exists
    env_file = project_dir / 'cricverse.env'
    if env_file.exists():
        print("✅ Found cricverse.env file")
        # Load the environment variables
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    else:
        print("⚠️  No cricverse.env file found, using default configuration")
    
    # Set default values if not present
    if 'SECRET_KEY' not in os.environ:
        os.environ['SECRET_KEY'] = 'cricverse-secure-secret-key-for-production-change-this-value'
    
    if 'DATABASE_URL' not in os.environ:
        os.environ['DATABASE_URL'] = 'sqlite:///cricverse.db'
    
    print(f"📊 Database URL: {os.environ.get('DATABASE_URL', 'Not set')}")
    return True

def test_database_connection():
    """Test the database connection"""
    print("\n🧪 Testing database connection...")
    
    try:
        from app import create_app
        from app import db
        
        # Create app context
        app = create_app('development')
        
        with app.app_context():
            # Test connection by executing a simple query
            result = db.session.execute(db.text('SELECT 1'))
            row = result.fetchone()
            
            if row and row[0] == 1:
                print("✅ Database connection successful!")
                return True
            else:
                print("❌ Database connection failed!")
                return False
                
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

def create_database_tables():
    """Create database tables"""
    print("\n🏗️  Creating database tables...")
    
    try:
        from app import create_app
        from app import db
        from app.models import (
            Customer, Team, Stadium, Player, Event, Match, Seat, Booking, 
            Ticket, Concession, MenuItem, Parking, Order, Payment,
            CustomerProfile, PaymentTransaction, QRCode, Notification,
            MatchUpdate, ChatConversation, ChatMessage, BookingAnalytics,
            SystemLog, WebSocketConnection, TicketTransfer, ResaleMarketplace,
            SeasonTicket, SeasonTicketMatch, AccessibilityAccommodation,
            AccessibilityBooking, VerificationSubmission, StadiumAdmin,
            EventUmpire, ParkingBooking, Photo
        )
        
        # Create app context
        app = create_app('development')
        
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Failed to create database tables: {e}")
        return False

def main():
    """Main configuration function"""
    print("🚀 Starting CricVerse Supabase Configuration...")
    print("=" * 50)
    
    try:
        # Configure environment
        if not configure_environment():
            print("❌ Environment configuration failed!")
            sys.exit(1)
        
        # Test database connection
        if not test_database_connection():
            print("❌ Database connection test failed!")
            sys.exit(1)
        
        # Create database tables
        if not create_database_tables():
            print("❌ Database table creation failed!")
            sys.exit(1)
        
        print("\n🎉 Supabase configuration completed successfully!")
        print("You can now run your Flask application with:")
        print("   python app.py")
        
    except KeyboardInterrupt:
        print("\n\n❌ Configuration cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()