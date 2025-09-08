#!/usr/bin/env python3
"""
Database Status Check for CricVerse
Quick diagnostic tool to check database connection and status
"""

import os
from dotenv import load_dotenv

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

def check_database_status():
    """Check database connection and status"""
    print("🏏 CricVerse Database Status Check")
    print("=" * 40)
    
    try:
        # Import app to get database configuration
        from app import app, db
        
        print(f"📊 Database URL: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        with app.app_context():
            # Test database connection
            print("🔌 Testing database connection...")
            
            try:
                with db.engine.connect() as connection:
                    result = connection.execute(db.text("SELECT 1"))
                    print("✅ Database connection successful!")
                
                # Check tables
                from sqlalchemy import inspect
                inspector = inspect(db.engine)
                tables = inspector.get_table_names()
                
                print(f"📋 Tables found: {len(tables)}")
                if tables:
                    for table in tables:
                        print(f"   - {table}")
                else:
                    print("   No tables found")
                
                # Check user data
                from app import Customer, Stadium, Team, Event
                
                print("\n📊 Data Summary:")
                print(f"   - Users: {Customer.query.count()}")
                print(f"   - Stadiums: {Stadium.query.count()}")
                print(f"   - Teams: {Team.query.count()}")
                print(f"   - Events: {Event.query.count()}")
                
                # Check for admin users
                admin_count = Customer.query.filter_by(role='admin').count()
                print(f"   - Admin Users: {admin_count}")
                
                if admin_count > 0:
                    admins = Customer.query.filter_by(role='admin').all()
                    print("   Admin accounts:")
                    for admin in admins:
                        print(f"     • {admin.name} ({admin.email})")
                
                return True
                
            except Exception as e:
                print(f"❌ Database connection failed: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Failed to check database: {e}")
        return False

def main():
    """Main check function"""
    load_environment()
    success = check_database_status()
    
    if success:
        print("\n✅ Database status check complete!")
        print("🚀 Ready to run CricVerse!")
    else:
        print("\n❌ Database issues detected!")
        print("💡 Try running: python start.py")

if __name__ == "__main__":
    main()
