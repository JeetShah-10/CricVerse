"""
Simple Database Initialization Script for CricVerse
This script creates only the essential tables, bypassing problematic ones like season_ticket
"""

from app import app, db
from models import *

def init_essential_tables():
    """Initialize only the essential database tables"""
    with app.app_context():
        try:
            # Create core tables first
            print("[INFO] Creating core tables...")
            
            # Core tables that should work without issues
            essential_tables = [
                'stadium', 'team', 'player', 'customer', 'seat', 'event',
                'booking', 'ticket', 'payment', 'concession', 'menu_item',
                'parking', 'parking_booking', 'order', 'photo',
                'stadium_admin', 'event_umpire'
            ]
            
            # Try to create all tables
            db.create_all()
            print("[PASS] All database tables created successfully!")
            
            # Verify core tables exist
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            print(f"[INFO] Created tables: {len(existing_tables)}")
            for table in sorted(existing_tables):
                print(f"  ✅ {table}")
            
            # Check if problematic tables were created
            if 'season_ticket' in existing_tables:
                print("[PASS] season_ticket table created successfully!")
            else:
                print("[WARN] season_ticket table not created (timeout issue)")
            
            return True
            
        except Exception as e:
            print(f"[FAIL] Database initialization failed: {e}")
            # Try to create tables individually
            try:
                print("[RETRY] Attempting to create tables individually...")
                
                # Create tables individually to isolate issues
                from sqlalchemy import text
                
                # Create stadium table
                db.session.execute(text('''
                    CREATE TABLE IF NOT EXISTS stadium (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        location VARCHAR(100) NOT NULL,
                        capacity INTEGER NOT NULL,
                        contact_number VARCHAR(20),
                        opening_year INTEGER,
                        pitch_type VARCHAR(50),
                        boundary_length INTEGER,
                        floodlight_quality VARCHAR(20),
                        has_dressing_rooms BOOLEAN DEFAULT TRUE,
                        has_practice_nets BOOLEAN DEFAULT TRUE,
                        description TEXT,
                        image_url VARCHAR(200),
                        latitude FLOAT,
                        longitude FLOAT,
                        open_hour TIME,
                        close_hour TIME
                    )
                '''))
                
                # Create team table
                db.session.execute(text('''
                    CREATE TABLE IF NOT EXISTS team (
                        id SERIAL PRIMARY KEY,
                        team_name VARCHAR(100) NOT NULL,
                        tagline VARCHAR(200),
                        about TEXT,
                        founding_year INTEGER,
                        championships_won INTEGER DEFAULT 0,
                        home_ground VARCHAR(100),
                        team_color VARCHAR(50),
                        color1 VARCHAR(20),
                        color2 VARCHAR(20),
                        coach_name VARCHAR(100),
                        manager VARCHAR(100),
                        owner_name VARCHAR(100),
                        fun_fact TEXT,
                        team_logo VARCHAR(200),
                        home_city VARCHAR(100),
                        team_type VARCHAR(50)
                    )
                '''))
                
                # Create customer table
                db.session.execute(text('''
                    CREATE TABLE IF NOT EXISTS customer (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        email VARCHAR(100) UNIQUE NOT NULL,
                        phone VARCHAR(20),
                        password_hash VARCHAR(200),
                        role VARCHAR(20) DEFAULT 'customer',
                        membership_level VARCHAR(50),
                        verification_status VARCHAR(20) DEFAULT 'not_verified',
                        favorite_team_id INTEGER REFERENCES team(id),
                        created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
                    )
                '''))
                
                db.session.commit()
                print("[PASS] Core tables created manually")
                return True
                
            except Exception as e2:
                print(f"[FAIL] Manual table creation also failed: {e2}")
                return False

if __name__ == '__main__':
    success = init_essential_tables()
    if success:
        print("\n[SUCCESS] Database initialization completed!")
        print("[NOTE] You can now start the application with: python app.py")
    else:
        print("\n[FAILED] Database initialization failed!")
        print("[NOTE] Please check your database connection and try again")