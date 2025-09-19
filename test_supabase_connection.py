#!/usr/bin/env python3
"""
Test Supabase Connection for CricVerse
This script will test the connection to your Supabase PostgreSQL database.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

def test_supabase_connection():
    """Test connection to Supabase PostgreSQL database"""
    print("🧪 Testing Supabase connection...")
    
    # Load environment if available (won't override explicit env vars)
    try:
        if os.path.exists('cricverse.env'):
            load_dotenv('cricverse.env')
        else:
            load_dotenv()
    except Exception:
        pass

    # Prefer existing env; otherwise set known project defaults (safe for test)
    os.environ.setdefault('SUPABASE_URL', 'https://tiyokcstdmlhpswurelh.supabase.co')
    os.environ.setdefault('SUPABASE_KEY', 'anon-key-placeholder')
    # If DATABASE_URL is not set, fallback to pooler URL present in .env
    os.environ.setdefault('DATABASE_URL', 'postgresql://postgres.tiyokcstdmlhpswurelh:Jeetshah910@aws-1-ap-south-1.pooler.supabase.com:5432/postgres')
    
    try:
        # Import SQLAlchemy and test connection
        from sqlalchemy import create_engine, text
        
        # Create engine
        # Normalize URL to use pg8000 driver if generic scheme is used
        db_url = os.environ['DATABASE_URL']
        if db_url.startswith('postgresql://'):
            db_url = db_url.replace('postgresql://', 'postgresql+pg8000://', 1)
        engine = create_engine(db_url)
        
        # Test connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print("✅ Supabase connection successful!")
            print(f"   PostgreSQL Version: {version}")
            return True
            
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

def get_supabase_config_instructions():
    """Provide instructions for configuring Supabase"""
    print("\n📋 Supabase Configuration Instructions:")
    print("1. Go to https://supabase.com/dashboard/projects")
    print("2. Select your project (tiyokcstdmlhpswurelh)")
    print("3. Go to Settings > Database")
    print("4. Find your database password in the 'Connection Info' section")
    print("5. Update the DATABASE_URL in your .env file with your actual password:")
    print("   DATABASE_URL=postgresql://postgres:YOUR_ACTUAL_PASSWORD@db.tiyokcstdmlhpswurelh.supabase.co:5432/postgres")
    print("\n📝 Note: Replace 'YOUR_ACTUAL_PASSWORD' with your real database password")

if __name__ == "__main__":
    print("🚀 CricVerse Supabase Connection Test")
    print("=" * 40)
    
    # Test connection
    success = test_supabase_connection()
    
    if not success:
        get_supabase_config_instructions()
    
    print("\n💡 Tip: Once configured, you can run this test again to verify your connection.")