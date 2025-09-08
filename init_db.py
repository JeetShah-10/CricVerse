#!/usr/bin/env python3
"""
Database Initialization Script for CricVerse
Creates the PostgreSQL database and tables if they don't exist
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

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

def create_database_if_not_exists():
    """Create PostgreSQL database if it doesn't exist"""
    
    # Get database configuration
    pg_user = os.getenv('POSTGRES_USER', 'postgres')
    pg_password = os.getenv('POSTGRES_PASSWORD', 'admin')
    pg_host = os.getenv('POSTGRES_HOST', 'localhost')
    pg_port = os.getenv('POSTGRES_PORT', '5432')
    pg_database = os.getenv('POSTGRES_DB', 'stadium_db')
    
    print(f"🔌 Connecting to PostgreSQL server at {pg_host}:{pg_port}")
    
    try:
        # Connect to PostgreSQL server (not specific database)
        conn = psycopg2.connect(
            host=pg_host,
            port=pg_port,
            user=pg_user,
            password=pg_password,
            database='postgres'  # Connect to default postgres database first
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (pg_database,))
        exists = cursor.fetchone()
        
        if not exists:
            print(f"🏗️ Creating database '{pg_database}'...")
            cursor.execute(f'CREATE DATABASE "{pg_database}"')
            print(f"✅ Database '{pg_database}' created successfully!")
        else:
            print(f"✅ Database '{pg_database}' already exists")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print(f"Please ensure PostgreSQL is running and credentials are correct")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_app_database_connection():
    """Test the application's database connection"""
    try:
        # Import app after database creation
        from app import app, db
        
        with app.app_context():
            print("🧪 Testing application database connection...")
            
            # Test database connection
            with db.engine.connect() as connection:
                connection.execute(db.text("SELECT 1"))
            print("✅ Application database connection successful!")
            
            return True
            
    except Exception as e:
        print(f"❌ Application database connection failed: {e}")
        return False

def create_tables():
    """Create database tables using Flask-SQLAlchemy"""
    try:
        from app import app, db
        
        with app.app_context():
            print("📋 Creating database tables...")
            
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Check if tables exist  
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📊 Created tables: {', '.join(tables)}")
            
            return True
            
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False

def seed_database():
    """Seed the database with initial data"""
    try:
        print("🌱 Checking if database needs seeding...")
        
        from app import app, db, Customer
        
        with app.app_context():
            # Check if there are any users (indicating database is already seeded)
            user_count = Customer.query.count()
            
            if user_count == 0:
                print("🌱 Database appears empty, running seed script...")
                
                # Run the seed script
                import subprocess
                result = subprocess.run([sys.executable, 'seed.py'], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("✅ Database seeded successfully!")
                    print(result.stdout)
                else:
                    print("⚠️ Seeding completed with warnings:")
                    print(result.stdout)
                    if result.stderr:
                        print("Errors:", result.stderr)
            else:
                print(f"✅ Database already contains {user_count} users, skipping seeding")
                
            return True
            
    except Exception as e:
        print(f"❌ Failed to seed database: {e}")
        return False

def main():
    """Main initialization function"""
    print("🏏 CricVerse Database Initialization")
    print("=" * 50)
    
    # Load environment
    load_environment()
    
    # Step 1: Create database if needed
    if not create_database_if_not_exists():
        print("❌ Database creation failed. Exiting.")
        sys.exit(1)
    
    # Step 2: Test application database connection
    if not test_app_database_connection():
        print("❌ Application database connection failed. Exiting.")
        sys.exit(1)
    
    # Step 3: Create tables
    if not create_tables():
        print("❌ Table creation failed. Exiting.")
        sys.exit(1)
    
    # Step 4: Seed database if needed
    if not seed_database():
        print("⚠️ Database seeding failed, but continuing...")
    
    print("\n" + "=" * 50)
    print("🎉 Database initialization complete!")
    print("🚀 You can now start the CricVerse application")
    print("   Run: python app.py")

if __name__ == "__main__":
    main()
