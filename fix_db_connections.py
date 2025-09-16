#!/usr/bin/env python3
"""
Database Connection Pool Fix for CricVerse
This script helps resolve Supabase connection pool exhaustion
"""

import psycopg2
import time
from dotenv import load_dotenv
import os

def kill_idle_connections():
    """Kill idle database connections to free up pool space"""
    
    # Load environment
    if os.path.exists('cricverse.env'):
        load_dotenv('cricverse.env')
    else:
        load_dotenv()
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ No DATABASE_URL found")
        return False
    
    try:
        import urllib.parse
        parsed = urllib.parse.urlparse(database_url)
        
        conn_params = {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'database': parsed.path[1:],
            'user': parsed.username,
            'password': parsed.password
        }
        
        print("🔗 Connecting to database to clean up connections...")
        conn = psycopg2.connect(**conn_params, connect_timeout=10)
        cursor = conn.cursor()
        
        # Check current connections
        cursor.execute("""
            SELECT count(*) as total_connections,
                   count(*) FILTER (WHERE state = 'active') as active,
                   count(*) FILTER (WHERE state = 'idle') as idle
            FROM pg_stat_activity
        """)
        
        total, active, idle = cursor.fetchone()
        print(f"📊 Current connections: {total} total, {active} active, {idle} idle")
        
        if idle > 5:
            print(f"🧹 Cleaning up {idle} idle connections...")
            
            # Kill idle connections older than 5 minutes
            cursor.execute("""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE state = 'idle'
                  AND state_change < now() - interval '5 minutes'
                  AND pid != pg_backend_pid()
            """)
            
            killed = cursor.rowcount
            print(f"✅ Killed {killed} idle connections")
        
        cursor.close()
        conn.close()
        
        print("✅ Database cleanup completed")
        return True
        
    except Exception as e:
        print(f"❌ Failed to clean database connections: {e}")
        return False

def main():
    print("🔧 CricVerse Database Connection Pool Fixer")
    print(f"⏰ Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = kill_idle_connections()
    
    if success:
        print("\n💡 Next steps:")
        print("  1. Try starting the application again")
        print("  2. The app should now connect successfully")
        print("  3. Consider reducing pool_size in app.py to 3-5")
    else:
        print("\n🔄 Alternative solutions:")
        print("  1. Wait 10-15 minutes for connections to timeout")
        print("  2. Restart your internet connection")
        print("  3. Contact Supabase support")
    
    print(f"✅ Completed: {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()