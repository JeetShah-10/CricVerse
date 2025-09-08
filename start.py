#!/usr/bin/env python3
"""
CricVerse Startup Script
Handles database setup and starts the application
"""

import os
import sys
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

def setup_database():
    """Set up the database and tables"""
    try:
        print("🏏 Setting up CricVerse database...")
        
        # Import app to trigger database connection
        from app import app, db
        
        with app.app_context():
            print("📋 Creating database tables...")
            
            # Create all tables
            db.create_all()
            
            # Check if tables exist
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if tables:
                print(f"✅ Database tables ready: {len(tables)} tables")
                print(f"   Tables: {', '.join(tables[:5])}{', ...' if len(tables) > 5 else ''}")
            else:
                print("⚠️ No tables found, but database connection successful")
            
            # Check if we need to seed the database
            from app import Customer
            user_count = Customer.query.count()
            
            if user_count == 0:
                print("🌱 Database appears empty, running seed script...")
                try:
                    import subprocess
                    result = subprocess.run([sys.executable, 'seed.py'], 
                                          capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        print("✅ Database seeded successfully!")
                        # Show a brief excerpt of the output
                        lines = result.stdout.strip().split('\n')
                        for line in lines[-5:]:  # Show last 5 lines
                            if line.strip():
                                print(f"   {line}")
                    else:
                        print("⚠️ Seeding had issues, but continuing...")
                        print(f"   Error: {result.stderr[:200]}...")
                        
                except Exception as e:
                    print(f"⚠️ Could not run seed script: {e}")
            else:
                print(f"✅ Database already contains {user_count} users")
                
            return True
            
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        print("   The application will still start but may not work properly")
        return False

def start_application():
    """Start the Flask application"""
    try:
        print("\n🚀 Starting CricVerse application...")
        
        # Import and run the app
        from app import app
        
        print("📡 Server configuration:")
        print("   - Host: 0.0.0.0")
        print("   - Port: 5000")
        print("   - Debug: True")
        print("   - URL: http://127.0.0.1:5000")
        
        print("\n" + "=" * 50)
        print("🎾 CricVerse is now running!")
        print("   Open your browser and go to: http://127.0.0.1:5000")
        print("   Press Ctrl+C to stop the server")
        print("=" * 50)
        
        # Start the Flask development server
        app.run(host='0.0.0.0', port=5000, debug=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        sys.exit(1)

def main():
    """Main startup function"""
    print("🏏 CricVerse Startup")
    print("=" * 30)
    
    # Load environment
    load_environment()
    
    # Setup database
    setup_database()
    
    # Start application
    start_application()

if __name__ == "__main__":
    main()
