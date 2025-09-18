#!/usr/bin/env python3
"""
Final Verification Script for CricVerse Supabase Configuration
This script verifies that all components of the Supabase configuration are working correctly
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

def load_environment():
    """Load environment variables"""
    if os.path.exists('cricverse.env'):
        load_dotenv('cricverse.env')
        print("✅ Loaded cricverse.env")
        return True
    elif os.path.exists('.env'):
        load_dotenv('.env')
        print("✅ Loaded .env")
        return True
    else:
        print("❌ No environment file found")
        return False

def verify_database_connection():
    """Verify database connection to Supabase"""
    print("🔍 Verifying Supabase database connection...")
    
    try:
        # Get database URL from environment
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not found in environment variables!")
            return False
        
        # Create engine
        engine = create_engine(database_url, echo=False)
        
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

def verify_required_tables():
    """Verify that all required tables exist"""
    print("🔍 Verifying required database tables...")
    
    try:
        # Get database URL from environment
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not found in environment variables!")
            return False
        
        # Create engine
        engine = create_engine(database_url, echo=False)
        
        # Get list of tables
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            
        # Check for required tables
        required_tables = [
            'customer', 'stadium', 'team', 'player', 'event', 
            'seat', 'booking', 'ticket', 'concession', 'menu_item', 'match'
        ]
        
        print(f"📊 Found {len(tables)} tables in database")
        
        all_present = True
        for table in required_tables:
            if table in tables:
                print(f"   ✅ {table}")
            else:
                print(f"   ❌ {table} (MISSING)")
                all_present = False
                
        if all_present:
            print("✅ All required tables are present!")
            return True
        else:
            print("❌ Some required tables are missing!")
            return False
            
    except Exception as e:
        print(f"❌ Failed to verify tables: {e}")
        return False

def verify_application_running():
    """Verify that the application is running"""
    print("🔍 Verifying application status...")
    
    try:
        import requests
        response = requests.get('http://localhost:5000', timeout=5)
        if response.status_code == 200:
            print("✅ Application is running and accessible!")
            return True
        else:
            print(f"❌ Application returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Application is not accessible at http://localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Failed to check application status: {e}")
        return False

def main():
    """Main verification function"""
    print("🏏 CricVerse Supabase Final Verification")
    print("=" * 50)
    
    # Load environment
    if not load_environment():
        sys.exit(1)
    
    # Verify components
    checks = [
        ("Database Connection", verify_database_connection),
        ("Required Tables", verify_required_tables),
        ("Application Status", verify_application_running)
    ]
    
    results = []
    for check_name, check_function in checks:
        print(f"\n{check_name}:")
        result = check_function()
        results.append((check_name, result))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {check_name}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL VERIFICATIONS PASSED!")
        print("✅ CricVerse Supabase configuration is complete and working!")
        print("\n🚀 You can access the application at: http://localhost:5000")
        print("📝 Note: This is a minimal version. For full functionality,")
        print("   fix the chatbot_service_fixed.py file and restart the full application.")
    else:
        print("❌ SOME VERIFICATIONS FAILED!")
        print("⚠️ Please check the errors above and resolve them.")
    
    print("=" * 50)

if __name__ == "__main__":
    main()