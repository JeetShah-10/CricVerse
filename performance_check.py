#!/usr/bin/env python3
"""
Performance Diagnostic Script for CricVerse Stadium System
Checks database connectivity, resource usage, and identifies bottlenecks
"""

import os
import sys
import time
import psutil
import psycopg2
from dotenv import load_dotenv

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def check_system_resources():
    print_header("SYSTEM RESOURCES")
    
    # CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    print(f"🖥️  CPU Usage: {cpu_percent}%")
    
    # Memory usage
    memory = psutil.virtual_memory()
    print(f"💾 Memory Usage: {memory.percent}% ({memory.used / 1024**3:.1f}GB / {memory.total / 1024**3:.1f}GB)")
    
    # Disk usage
    disk = psutil.disk_usage('/')
    print(f"💿 Disk Usage: {disk.percent}% ({disk.used / 1024**3:.1f}GB / {disk.total / 1024**3:.1f}GB)")
    
    # Network
    net = psutil.net_io_counters()
    print(f"🌐 Network: Sent {net.bytes_sent / 1024**2:.1f}MB, Received {net.bytes_recv / 1024**2:.1f}MB")

def check_database_connection():
    print_header("DATABASE CONNECTION TEST")
    
    # Load environment variables
    if os.path.exists('cricverse.env'):
        load_dotenv('cricverse.env')
    else:
        load_dotenv()
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ No DATABASE_URL found in environment")
        return False
    
    try:
        # Parse the database URL
        print(f"🔗 Testing connection to Supabase...")
        
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
            print(f"👤 User: {conn_params['user']}")
            
            # Test connection with timeout
            start_time = time.time()
            conn = psycopg2.connect(
                **conn_params,
                connect_timeout=10
            )
            connection_time = time.time() - start_time
            
            # Test a simple query
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            db_version = cursor.fetchone()[0]
            
            # Check active connections
            cursor.execute("""
                SELECT count(*) as active_connections 
                FROM pg_stat_activity 
                WHERE state = 'active'
            """)
            active_connections = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            print(f"✅ Connection successful in {connection_time:.2f}s")
            print(f"🗄️  Database version: {db_version[:50]}...")
            print(f"🔗 Active connections: {active_connections}")
            
            if active_connections > 10:
                print(f"⚠️  Warning: High number of active connections ({active_connections})")
            
            return True
            
    except psycopg2.OperationalError as e:
        if "MaxClientsInSessionMode" in str(e):
            print("❌ Database connection pool exhausted!")
            print("💡 Solution: Reduce pool size or wait for connections to close")
        else:
            print(f"❌ Database connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def check_python_processes():
    print_header("PYTHON PROCESSES")
    
    python_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
        if 'python' in proc.info['name'].lower():
            python_processes.append(proc)
    
    if python_processes:
        print(f"Found {len(python_processes)} Python processes:")
        for proc in python_processes:
            memory_mb = proc.info['memory_info'].rss / 1024**2
            print(f"  PID {proc.info['pid']}: {memory_mb:.1f}MB RAM, {proc.info['cpu_percent']:.1f}% CPU")
            if proc.info['cmdline']:
                cmdline = ' '.join(proc.info['cmdline'])
                if 'app.py' in cmdline:
                    print(f"    📋 {cmdline[:80]}...")
    else:
        print("No Python processes found")

def main():
    print("🚀 CricVerse Performance Diagnostic Tool")
    print(f"⏰ Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    check_system_resources()
    check_python_processes()
    db_ok = check_database_connection()
    
    print_header("RECOMMENDATIONS")
    
    if not db_ok:
        print("🔧 Database Issues Detected:")
        print("  1. Check if Supabase connection limit is reached")
        print("  2. Reduce database pool size in app.py")
        print("  3. Close unused database connections")
        print("  4. Consider upgrading Supabase plan")
    
    print("\n💡 Performance Tips:")
    print("  1. Disable debug mode for production")
    print("  2. Use connection pooling")
    print("  3. Minimize database queries")
    print("  4. Enable caching")
    print("  5. Use lazy loading for 3D assets")
    
    print(f"\n✅ Diagnostic completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()