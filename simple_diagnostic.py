#!/usr/bin/env python3
"""
Simple Performance Diagnostic for CricVerse
"""

import os
import sys
import time
import psycopg2
from dotenv import load_dotenv

def print_header(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")

def check_database_connection():
    print_header("DATABASE CONNECTION TEST")
    
    # Load environment variables
    if os.path.exists('cricverse.env'):
        load_dotenv('cricverse.env')
        print("✅ Loaded cricverse.env")
    elif os.path.exists('.env'):
        load_dotenv()
        print("✅ Loaded .env")
    else:
        print("⚠️  No environment file found")
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ No DATABASE_URL found in environment")
        return False
    
    try:
        print(f"🔗 Testing Supabase connection...")
        
        # Extract connection details from URL
        if database_url.startswith('postgresql://'):
            import urllib.parse
            parsed = urllib.parse.urlparse(database_url)
            
            conn_params = {
                'host': parsed.hostname,
                'port': parsed.port or 5432,
                'database': parsed.path[1:],  # Remove leading '/'
                'user': parsed.username,
                'password': parsed.password
            }
            
            print(f"📍 Host: {conn_params['host']}")
            print(f"🔌 Port: {conn_params['port']}")
            print(f"🗃️  Database: {conn_params['database']}")
            
            # Test connection with short timeout
            start_time = time.time()
            conn = psycopg2.connect(
                **conn_params,
                connect_timeout=5
            )
            connection_time = time.time() - start_time
            
            # Test a simple query
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")
            active_connections = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            print(f"✅ Connection successful in {connection_time:.2f}s")
            print(f"🔗 Active connections: {active_connections}")
            
            if active_connections > 15:
                print(f"⚠️  HIGH CONNECTION COUNT: {active_connections}")
                print("   This might cause MaxClientsInSessionMode errors")
                return False
            
            return True
            
    except psycopg2.OperationalError as e:
        if "MaxClientsInSessionMode" in str(e):
            print("❌ DATABASE POOL EXHAUSTED!")
            print("💡 The connection pool is full. Wait or reduce pool size.")
        elif "timeout" in str(e):
            print("❌ CONNECTION TIMEOUT!")
            print("💡 Network or server issue. Check connectivity.")
        else:
            print(f"❌ Connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def check_python_environment():
    print_header("PYTHON ENVIRONMENT")
    print(f"🐍 Python version: {sys.version}")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🔍 Python executable: {sys.executable}")
    
    # Check key files
    files_to_check = [
        'app.py',
        'enhanced_models.py', 
        'chatbot.py',
        'cricverse.env',
        'requirements.txt'
    ]
    
    print("\n📋 Key files check:")
    for file in files_to_check:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"✅ {file} ({size} bytes)")
        else:
            print(f"❌ {file} - NOT FOUND")

def main():
    print("🚀 CricVerse Simple Diagnostic")
    print(f"⏰ Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    check_python_environment()
    db_ok = check_database_connection()
    
    print_header("DIAGNOSIS SUMMARY")
    
    if not db_ok:
        print("🔴 CRITICAL: Database connection issues detected")
        print("\n🔧 SOLUTIONS:")
        print("  1. Wait 5-10 minutes for connections to close")
        print("  2. Restart the application")
        print("  3. Check Supabase dashboard for connection limits")
        print("  4. Reduce pool_size in app.py to 3")
    else:
        print("🟢 Database connection is working")
    
    print("\n💡 PERFORMANCE TIPS:")
    print("  ✓ Set debug=False in app.py")
    print("  ✓ Reduce 3D quality for slower devices")
    print("  ✓ Enable browser caching")
    print("  ✓ Use CDN for static assets")
    
    print(f"\n✅ Completed: {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()