#!/usr/bin/env python3
"""
Verify Supabase Tables Script for CricVerse
Checks if all required tables were created successfully
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

def load_environment():
    """Load environment variables"""
    if os.path.exists('cricverse.env'):
        load_dotenv('cricverse.env')
        print("✅ Loaded cricverse.env")
    elif os.path.exists('.env'):
        load_dotenv('.env')
        print("✅ Loaded .env")
    else:
        print("⚠️ No environment file found, using defaults")

def verify_tables():
    """Verify that all required tables were created"""
    print("🔍 Verifying database tables...")
    
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
            
        print(f"📊 Found {len(tables)} tables in database:")
        for table in tables:
            print(f"   • {table}")
            
        # Check for required tables
        required_tables = [
            'customer', 'stadium', 'team', 'player', 'event', 
            'seat', 'booking', 'ticket', 'concession', 'menu_item', 'match'
        ]
        
        missing_tables = []
        for table in required_tables:
            if table not in tables:
                missing_tables.append(table)
            else:
                print(f"✅ {table}")
                
        if missing_tables:
            print(f"❌ Missing tables: {', '.join(missing_tables)}")
            return False
        else:
            print("✅ All required tables are present!")
            return True
            
    except Exception as e:
        print(f"❌ Failed to verify tables: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main verification function"""
    print("🏏 CricVerse Supabase Table Verification")
    print("=" * 50)
    
    # Load environment
    load_environment()
    
    # Verify tables
    if verify_tables():
        print("\n" + "=" * 50)
        print("🎉 Supabase table verification complete!")
        print("✅ All required tables are present in the database")
        print("🚀 You can now start the CricVerse application")
        print("   Run: python app.py")
    else:
        print("\n" + "=" * 50)
        print("❌ Supabase table verification failed!")
        print("⚠️ Some required tables are missing")

if __name__ == "__main__":
    main()