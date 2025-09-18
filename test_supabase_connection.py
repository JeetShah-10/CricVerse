#!/usr/bin/env python3
"""
Test Supabase Connection for CricVerse
This script will test the connection to your Supabase PostgreSQL database.
"""

import os
import sys
from pathlib import Path

# Add project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

def test_supabase_connection():
    """Test connection to Supabase PostgreSQL database"""
    print("🧪 Testing Supabase connection...")
    
    # Set the Supabase configuration from your backup file
    os.environ['SUPABASE_URL'] = 'https://tiyokcstdmlhpswurelh.supabase.co'
    os.environ['SUPABASE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRpeW9rY3N0ZG1saHBzd3VyZWxoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc2OTkxOTMsImV4cCI6MjA3MzI3NTE5M30.60sud90R8o7elSLmt7AuYK7lYb_F8mIKp04UsCfa0Lo'
    
    # Try to connect using the Supabase connection string from your backup
    # Note: You'll need to replace the password with your actual database password
    os.environ['DATABASE_URL'] = 'postgresql://postgres:YOUR_ACTUAL_PASSWORD@db.tiyokcstdmlhpswurelh.supabase.co:5432/postgres'
    
    try:
        # Import SQLAlchemy and test connection
        from sqlalchemy import create_engine, text
        
        # Create engine
        engine = create_engine(os.environ['DATABASE_URL'])
        
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