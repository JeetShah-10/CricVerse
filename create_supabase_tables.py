#!/usr/bin/env python3
"""
Direct Supabase Table Creation Script for CricVerse
Creates database tables directly in Supabase without using the full application
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

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

def test_supabase_connection():
    """Test connection to Supabase PostgreSQL database"""
    print("🧪 Testing Supabase connection...")
    
    try:
        # Get database URL from environment
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not found in environment variables!")
            return False
        
        print(f"🔌 Connecting to: {database_url.split('@')[0]}@****")
        
        # Normalize for pg8000 driver if generic scheme is used
        if database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+pg8000://', 1)
        # Normalize for pg8000 driver if generic scheme is used
        if database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+pg8000://', 1)
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

def create_tables_directly():
    """Create database tables directly using SQLAlchemy"""
    print("🏗️ Creating database tables...")
    
    try:
        # Get database URL from environment
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not found in environment variables!")
            return False
        
        # Create engine
        engine = create_engine(database_url, echo=False)
        
        # Create tables using raw SQL (simplified version)
        table_creation_sql = """
        -- Create tables in the correct order to handle foreign key dependencies
        
        -- Customer table
        CREATE TABLE IF NOT EXISTS customer (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            phone VARCHAR(20),
            password_hash VARCHAR(200),
            role VARCHAR(20) DEFAULT 'customer',
            membership_level VARCHAR(50),
            verification_status VARCHAR(20) DEFAULT 'not_verified',
            favorite_team_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_customer_favorite_team_id ON customer (favorite_team_id);
        CREATE INDEX IF NOT EXISTS idx_customer_created_at ON customer (created_at);
        CREATE INDEX IF NOT EXISTS idx_customer_updated_at ON customer (updated_at);
        
        -- Stadium table
        CREATE TABLE IF NOT EXISTS stadium (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
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
        );
        CREATE INDEX IF NOT EXISTS idx_stadium_location ON stadium (location);
        CREATE INDEX IF NOT EXISTS idx_stadium_latitude_longitude ON stadium (latitude, longitude);
        
        -- Team table
        CREATE TABLE IF NOT EXISTS team (
            id SERIAL PRIMARY KEY,
            team_name VARCHAR(100) UNIQUE NOT NULL,
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
        );
        CREATE INDEX IF NOT EXISTS idx_team_home_city ON team (home_city);
        
        -- Player table
        CREATE TABLE IF NOT EXISTS player (
            id SERIAL PRIMARY KEY,
            team_id INTEGER REFERENCES team(id),
            player_name VARCHAR(100) NOT NULL,
            age INTEGER,
            batting_style VARCHAR(50),
            bowling_style VARCHAR(50),
            player_role VARCHAR(50),
            is_captain BOOLEAN DEFAULT FALSE,
            is_wicket_keeper BOOLEAN DEFAULT FALSE,
            nationality VARCHAR(50),
            jersey_number INTEGER,
            market_value FLOAT,
            photo_url VARCHAR(200)
        );
        CREATE INDEX IF NOT EXISTS idx_player_player_name ON player (player_name);
        CREATE INDEX IF NOT EXISTS idx_player_nationality ON player (nationality);
        CREATE INDEX IF NOT EXISTS idx_player_player_role ON player (player_role);
        
        -- Event table
        CREATE TABLE IF NOT EXISTS event (
            id SERIAL PRIMARY KEY,
            stadium_id INTEGER REFERENCES stadium(id),
            event_name VARCHAR(100) NOT NULL,
            event_type VARCHAR(50),
            tournament_name VARCHAR(100),
            event_date DATE NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME,
            home_team_id INTEGER REFERENCES team(id),
            away_team_id INTEGER REFERENCES team(id),
            match_status VARCHAR(50) DEFAULT 'Scheduled',
            attendance INTEGER DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_event_event_name ON event (event_name);
        CREATE INDEX IF NOT EXISTS idx_event_event_date ON event (event_date);
        
        -- Seat table
        CREATE TABLE IF NOT EXISTS seat (
            id SERIAL PRIMARY KEY,
            stadium_id INTEGER REFERENCES stadium(id),
            seat_number VARCHAR(20) NOT NULL,
            section VARCHAR(50),
            row_number VARCHAR(10),
            seat_type VARCHAR(50),
            price FLOAT,
            has_shade BOOLEAN DEFAULT FALSE,
            is_available BOOLEAN DEFAULT TRUE
        );
        -- CREATE UNIQUE INDEX IF NOT EXISTS uix_seat_stadium_section_row_seat ON seat (stadium_id, section, row_number, seat_number); -- Temporarily commented out due to timeout
        CREATE INDEX IF NOT EXISTS idx_seat_is_available ON seat (is_available);
        
        -- Booking table
        CREATE TABLE IF NOT EXISTS booking (
            id SERIAL PRIMARY KEY,
            customer_id INTEGER REFERENCES customer(id),
            total_amount FLOAT NOT NULL,
            booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_booking_booking_date ON booking (booking_date);
        
        -- Ticket table
        CREATE TABLE IF NOT EXISTS ticket (
            id SERIAL PRIMARY KEY,
            event_id INTEGER REFERENCES event(id),
            seat_id INTEGER REFERENCES seat(id),
            customer_id INTEGER REFERENCES customer(id),
            booking_id INTEGER REFERENCES booking(id),
            ticket_type VARCHAR(50),
            access_gate VARCHAR(20),
            ticket_status VARCHAR(20) DEFAULT 'Booked',
            qr_code VARCHAR(200) UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_ticket_ticket_status ON ticket (ticket_status);
        CREATE INDEX IF NOT EXISTS idx_ticket_created_at ON ticket (created_at);
        CREATE INDEX IF NOT EXISTS idx_ticket_updated_at ON ticket (updated_at);
        
        -- Concession table
        CREATE TABLE IF NOT EXISTS concession (
            id SERIAL PRIMARY KEY,
            stadium_id INTEGER REFERENCES stadium(id),
            name VARCHAR(100) NOT NULL,
            category VARCHAR(50),
            location_zone VARCHAR(50),
            opening_hours VARCHAR(100),
            description TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_concession_name ON concession (name);
        CREATE INDEX IF NOT EXISTS idx_concession_category ON concession (category);
        
        -- Menu Item table
        CREATE TABLE IF NOT EXISTS menu_item (
            id SERIAL PRIMARY KEY,
            concession_id INTEGER REFERENCES concession(id),
            name VARCHAR(100) NOT NULL,
            description TEXT,
            price FLOAT NOT NULL,
            category VARCHAR(50),
            is_available BOOLEAN DEFAULT TRUE,
            is_vegetarian BOOLEAN DEFAULT TRUE
        );
        CREATE INDEX IF NOT EXISTS idx_menu_item_name ON menu_item (name);
        CREATE INDEX IF NOT EXISTS idx_menu_item_category ON menu_item (category);
        CREATE INDEX IF NOT EXISTS idx_menu_item_is_available ON menu_item (is_available);
        CREATE INDEX IF NOT EXISTS idx_menu_item_is_vegetarian ON menu_item (is_vegetarian);
        
        -- Match table
        CREATE TABLE IF NOT EXISTS match (
            id SERIAL PRIMARY KEY,
            event_id INTEGER REFERENCES event(id) UNIQUE,
            home_team_id INTEGER REFERENCES team(id),
            away_team_id INTEGER REFERENCES team(id),
            toss_winner_id INTEGER REFERENCES team(id),
            toss_decision VARCHAR(10),
            home_score INTEGER DEFAULT 0,
            away_score INTEGER DEFAULT 0,
            home_wickets INTEGER DEFAULT 0,
            away_wickets INTEGER DEFAULT 0,
            home_overs FLOAT DEFAULT 0.0,
            away_overs FLOAT DEFAULT 0.0,
            result_type VARCHAR(20),
            winning_margin VARCHAR(20)
        );
        CREATE INDEX IF NOT EXISTS idx_match_result_type ON match (result_type);
        """
        
        # Execute table creation
        with engine.connect() as connection:
            # Split the SQL into individual statements
            statements = [stmt.strip() for stmt in table_creation_sql.split(';') if stmt.strip()]
            
            for statement in statements:
                stripped_statement = statement.strip()
                if stripped_statement and not stripped_statement.startswith('--'):
                    print(f"Executing: {stripped_statement[:50]}...")
                    connection.execute(text(stripped_statement))
            
            connection.commit()
            print("Database tables created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main initialization function"""
    print("CricVerse Supabase Table Creation")
    print("=" * 50)
    
    # Load environment
    load_environment()
    
    # Test Supabase connection
    if not test_supabase_connection():
        print("❌ Supabase connection failed. Exiting.")
        sys.exit(1)
    
    # Create tables
    if not create_tables_directly():
        print("❌ Table creation failed. Exiting.")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 Supabase table creation complete!")
    print("You can now start the CricVerse application")
    print("   Run: python app.py")

if __name__ == "__main__":
    main()
