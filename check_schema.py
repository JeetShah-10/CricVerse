"""
Check actual database schema vs model definitions
"""

from app import app, db
from sqlalchemy import text
import sys

def check_database_schema():
    """Check the actual database schema"""
    with app.app_context():
        try:
            print("Checking customer table schema...")
            
            # Get actual columns in customer table
            result = db.session.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'customer'
                ORDER BY ordinal_position;
            """))
            
            print("Actual columns in customer table:")
            print("-" * 60)
            print(f"{'Column Name':<20} {'Data Type':<15} {'Nullable':<10} {'Default':<15}")
            print("-" * 60)
            
            for row in result:
                print(f"{row.column_name:<20} {row.data_type:<15} {row.is_nullable:<10} {str(row.column_default):<15}")
                
            # Check if we need to add missing columns
            print("\nChecking for missing columns...")
            
            # Check verification_status column
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'customer' AND column_name = 'verification_status';
            """))
            
            if not result.fetchone():
                print("MISSING: verification_status column")
                
                # Add the missing column
                try:
                    db.session.execute(text("""
                        ALTER TABLE customer 
                        ADD COLUMN verification_status VARCHAR(20) DEFAULT 'not_verified';
                    """))
                    db.session.commit()
                    print("ADDED: verification_status column")
                except Exception as e:
                    print(f"ERROR adding verification_status: {e}")
                    
            # Check created_at column
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'customer' AND column_name = 'created_at';
            """))
            
            if not result.fetchone():
                print("MISSING: created_at column")
                
                try:
                    db.session.execute(text("""
                        ALTER TABLE customer 
                        ADD COLUMN created_at TIMESTAMP DEFAULT NOW();
                    """))
                    db.session.commit()
                    print("ADDED: created_at column")
                except Exception as e:
                    print(f"ERROR adding created_at: {e}")
                    
            # Check updated_at column
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'customer' AND column_name = 'updated_at';
            """))
            
            if not result.fetchone():
                print("MISSING: updated_at column")
                
                try:
                    db.session.execute(text("""
                        ALTER TABLE customer 
                        ADD COLUMN updated_at TIMESTAMP DEFAULT NOW();
                    """))
                    db.session.commit()
                    print("ADDED: updated_at column")
                except Exception as e:
                    print(f"ERROR adding updated_at: {e}")
                    
            print("\nSchema check complete!")
            return True
            
        except Exception as e:
            print(f"Error checking schema: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("=" * 60)
    print("Database Schema Checker")
    print("=" * 60)
    check_database_schema()