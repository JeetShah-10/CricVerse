#!/usr/bin/env python3
"""
Final Supabase Setup for CricVerse
This script will help you complete the Supabase setup and test the connection.
"""

import os
import sys
from pathlib import Path

# Add project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

def get_database_password():
    """Get database password from user"""
    print("🔐 Supabase Database Password Required")
    print("=" * 40)
    print("To complete the Supabase setup, you need your database password.")
    print("\nHow to get your database password:")
    print("1. Go to https://supabase.com/dashboard/projects")
    print("2. Select your project (tiyokcstdmlhpswurelh)")
    print("3. Go to Settings > Database")
    print("4. Find your database password in the 'Connection Info' section")
    print("")
    
    password = input("Enter your Supabase database password: ").strip()
    return password

def update_env_with_password(password):
    """Update .env file with the actual password"""
    env_file = Path('c:\\Users\\shahj\\OneDrive\\Desktop\\Stadium System\\.env')
    
    if not env_file.exists():
        print("❌ .env file not found!")
        return False
    
    # Read current content
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Replace placeholder with actual password
    content = content.replace('YOUR_ACTUAL_PASSWORD', password)
    
    # Write updated content
    with open(env_file, 'w') as f:
        f.write(content)
    
    print("✅ .env file updated with your database password!")
    return True

def test_supabase_connection():
    """Test connection to Supabase PostgreSQL database"""
    print("\n🧪 Testing Supabase connection...")
    
    try:
        # Import SQLAlchemy and test connection
        from sqlalchemy import create_engine, text
        import logging
        logging.basicConfig(level=logging.INFO)
        
        # Get database URL from environment
        database_url = os.environ.get('DATABASE_URL')
        if not database_url or 'YOUR_ACTUAL_PASSWORD' in database_url:
            print("❌ Database URL not properly configured!")
            print("   Please update your .env file with the correct password.")
            return False
        
        # Create engine
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version(), current_database(), current_user"))
            row = result.fetchone()
            
            print("✅ Supabase connection successful!")
            print(f"   Database: {row[1]}")
            print(f"   User: {row[2]}")
            print(f"   PostgreSQL Version: {row[0].split(',')[0]}")
            return True
            
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

def create_database_tables():
    """Create database tables in Supabase"""
    print("\n🏗️  Creating database tables...")
    
    try:
        from app import create_app
        from app import db
        
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
    """Main setup function"""
    print("🚀 CricVerse Supabase Final Setup")
    print("=" * 40)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check if password needs to be updated
    database_url = os.environ.get('DATABASE_URL', '')
    if 'YOUR_ACTUAL_PASSWORD' in database_url:
        print("⚠️  Database password not configured yet!")
        password = get_database_password()
        
        if password:
            if update_env_with_password(password):
                # Reload environment
                load_dotenv()
            else:
                print("❌ Failed to update .env file!")
                return
        else:
            print("❌ No password provided!")
            return
    
    # Test connection
    if not test_supabase_connection():
        print("\n❌ Supabase setup failed!")
        return
    
    # Create database tables
    if not create_database_tables():
        print("\n❌ Failed to create database tables!")
        return
    
    print("\n🎉 Supabase setup completed successfully!")
    print("✅ Your CricVerse application is now configured to use Supabase!")

if __name__ == "__main__":
    main()