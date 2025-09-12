"""
Supabase PostgreSQL Integration for CricVerse
Handles connection to Supabase PostgreSQL database for production deployment
"""

import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SupabaseConfig:
    """Supabase configuration and connection management"""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.supabase_service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.database_url = os.getenv('DATABASE_URL')
        
    def validate_config(self):
        """Validate that all required Supabase configuration is present"""
        missing_configs = []
        
        if not self.supabase_url:
            missing_configs.append('SUPABASE_URL')
        if not self.supabase_key:
            missing_configs.append('SUPABASE_KEY')
        if not self.database_url or 'supabase.co' not in self.database_url:
            missing_configs.append('DATABASE_URL (with supabase.co)')
            
        if missing_configs:
            logger.error(f"Missing Supabase configuration: {', '.join(missing_configs)}")
            return False
            
        logger.info("✅ Supabase configuration validated successfully")
        return True
    
    def test_connection(self):
        """Test connection to Supabase PostgreSQL database"""
        if not self.validate_config():
            return False
            
        try:
            # Create engine for testing
            engine = create_engine(self.database_url)
            
            # Test connection
            with engine.connect() as connection:
                result = connection.execute(text("SELECT version(), current_database(), current_user"))
                row = result.fetchone()
                
                logger.info("✅ Supabase connection successful!")
                logger.info(f"   Database: {row[1]}")
                logger.info(f"   User: {row[2]}")
                logger.info(f"   PostgreSQL Version: {row[0].split(',')[0]}")
                
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"❌ Supabase connection failed: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error testing Supabase connection: {e}")
            return False
    
    def create_database_schema(self):
        """Create initial database schema in Supabase"""
        if not self.validate_config():
            return False
            
        try:
            from app import app, db
            
            with app.app_context():
                logger.info("🏗️ Creating database schema in Supabase...")
                
                # Create all tables
                db.create_all()
                
                # Import enhanced models and create those tables too
                from enhanced_models import create_enhanced_tables
                create_enhanced_tables()
                
                logger.info("✅ Database schema created successfully in Supabase!")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to create database schema: {e}")
            return False
    
    def migrate_local_data(self, local_db_url=None):
        """Migrate data from local PostgreSQL to Supabase"""
        if not local_db_url:
            # Construct local database URL
            pg_user = os.getenv('POSTGRES_USER', 'postgres')
            pg_password = os.getenv('POSTGRES_PASSWORD', 'admin')
            pg_host = os.getenv('POSTGRES_HOST', 'localhost')
            pg_port = os.getenv('POSTGRES_PORT', '5432')
            pg_database = os.getenv('POSTGRES_DB', 'stadium_db')
            local_db_url = f'postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}'
        
        try:
            # Create engines for both databases
            local_engine = create_engine(local_db_url)
            supabase_engine = create_engine(self.database_url)
            
            logger.info("🔄 Starting data migration from local to Supabase...")
            
            # List of tables to migrate (in dependency order)
            tables_to_migrate = [
                'team', 'stadium', 'player', 'customer', 'event', 'match',
                'seat', 'booking', 'ticket', 'payment', 'umpire', 'event_umpire',
                'concession', 'menu_item', 'order', 'parking', 'parking_booking',
                'stadium_admin', 'stadium_owner', 'photo'
            ]
            
            migration_stats = {}
            
            for table_name in tables_to_migrate:
                try:
                    # Get data from local database
                    with local_engine.connect() as local_conn:
                        result = local_conn.execute(text(f"SELECT * FROM {table_name}"))
                        rows = result.fetchall()
                        columns = result.keys()
                    
                    if rows:
                        # Insert data into Supabase
                        with supabase_engine.connect() as supabase_conn:
                            # Clear existing data
                            supabase_conn.execute(text(f"DELETE FROM {table_name}"))
                            
                            # Insert new data
                            placeholders = ', '.join(['%s'] * len(columns))
                            insert_query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                            
                            for row in rows:
                                supabase_conn.execute(text(insert_query), row)
                            
                            supabase_conn.commit()
                        
                        migration_stats[table_name] = len(rows)
                        logger.info(f"   ✅ Migrated {len(rows)} rows from {table_name}")
                    else:
                        migration_stats[table_name] = 0
                        logger.info(f"   ⚪ No data to migrate from {table_name}")
                        
                except Exception as e:
                    logger.error(f"   ❌ Failed to migrate {table_name}: {e}")
                    migration_stats[table_name] = f"Error: {e}"
            
            logger.info("✅ Data migration completed!")
            logger.info("📊 Migration Summary:")
            for table, count in migration_stats.items():
                logger.info(f"   {table}: {count}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Data migration failed: {e}")
            return False
    
    def setup_row_level_security(self):
        """Set up Row Level Security policies in Supabase"""
        if not self.validate_config():
            return False
            
        try:
            engine = create_engine(self.database_url)
            
            with engine.connect() as connection:
                logger.info("🔒 Setting up Row Level Security policies...")
                
                # Enable RLS on sensitive tables
                rls_tables = ['customer', 'booking', 'ticket', 'payment_transaction', 'notification']
                
                for table in rls_tables:
                    # Enable RLS
                    connection.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;"))
                    
                    # Create policy for users to access their own data
                    policy_name = f"{table}_user_policy"
                    connection.execute(text(f"""
                        CREATE POLICY {policy_name} ON {table}
                        FOR ALL USING (
                            auth.uid()::text = customer_id::text OR 
                            auth.jwt() ->> 'role' = 'admin'
                        );
                    """))
                
                connection.commit()
                logger.info("✅ Row Level Security policies created!")
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup RLS policies: {e}")
            return False
    
    def create_supabase_functions(self):
        """Create custom PostgreSQL functions for Supabase"""
        if not self.validate_config():
            return False
            
        try:
            engine = create_engine(self.database_url)
            
            with engine.connect() as connection:
                logger.info("⚡ Creating custom PostgreSQL functions...")
                
                # Function to update booking analytics
                analytics_function = """
                CREATE OR REPLACE FUNCTION update_booking_analytics()
                RETURNS TRIGGER AS $$
                BEGIN
                    -- Update daily analytics when a booking is created
                    INSERT INTO booking_analytics (stadium_id, event_id, date, total_bookings, total_revenue, unique_customers)
                    VALUES (
                        (SELECT stadium_id FROM event WHERE id = NEW.event_id),
                        NEW.event_id,
                        NEW.booking_date::date,
                        1,
                        NEW.total_amount,
                        1
                    )
                    ON CONFLICT (stadium_id, event_id, date)
                    DO UPDATE SET
                        total_bookings = booking_analytics.total_bookings + 1,
                        total_revenue = booking_analytics.total_revenue + NEW.total_amount,
                        unique_customers = booking_analytics.unique_customers + 1;
                    
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
                """
                
                connection.execute(text(analytics_function))
                
                # Create trigger for the analytics function
                trigger_sql = """
                DROP TRIGGER IF EXISTS booking_analytics_trigger ON booking;
                CREATE TRIGGER booking_analytics_trigger
                    AFTER INSERT ON booking
                    FOR EACH ROW
                    EXECUTE FUNCTION update_booking_analytics();
                """
                
                connection.execute(text(trigger_sql))
                
                # Function to generate QR codes
                qr_function = """
                CREATE OR REPLACE FUNCTION generate_qr_code(prefix TEXT)
                RETURNS TEXT AS $$
                DECLARE
                    qr_code TEXT;
                BEGIN
                    -- Generate a unique QR code with timestamp and random component
                    qr_code := prefix || '_' || 
                              EXTRACT(EPOCH FROM NOW())::TEXT || '_' ||
                              SUBSTRING(MD5(RANDOM()::TEXT) FROM 1 FOR 8);
                    RETURN qr_code;
                END;
                $$ LANGUAGE plpgsql;
                """
                
                connection.execute(text(qr_function))
                
                connection.commit()
                logger.info("✅ Custom PostgreSQL functions created!")
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create custom functions: {e}")
            return False


def setup_supabase():
    """Main setup function for Supabase integration"""
    logger.info("🚀 Starting Supabase setup for CricVerse...")
    
    supabase = SupabaseConfig()
    
    # Step 1: Validate configuration
    if not supabase.validate_config():
        logger.error("❌ Supabase setup failed - invalid configuration")
        return False
    
    # Step 2: Test connection
    if not supabase.test_connection():
        logger.error("❌ Supabase setup failed - connection test failed")
        return False
    
    # Step 3: Create database schema
    if not supabase.create_database_schema():
        logger.error("❌ Supabase setup failed - schema creation failed")
        return False
    
    # Step 4: Create custom functions
    if not supabase.create_supabase_functions():
        logger.warning("⚠️ Warning: Custom functions creation failed")
    
    # Step 5: Setup RLS (optional, might fail if not using Supabase Auth)
    try:
        supabase.setup_row_level_security()
    except:
        logger.warning("⚠️ Warning: RLS setup skipped (requires Supabase Auth)")
    
    logger.info("✅ Supabase setup completed successfully!")
    logger.info("🎉 Your CricVerse application is ready for production!")
    
    return True


if __name__ == "__main__":
    # Run setup if called directly
    setup_supabase()