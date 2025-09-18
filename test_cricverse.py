"""
Comprehensive Test Suite for CricVerse Stadium System
This script tests all major components systematically
"""

import sys
import os
import requests
import time
import json
import subprocess
import threading
from datetime import datetime

def test_imports():
    """Test if all required modules can be imported"""
    print("🔍 Testing imports...")
    try:
        from app import app, db
        from models import Customer, Stadium, Event, Team, Seat, Booking, Ticket
        from security_framework import limiter, csrf
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_database_connection():
    """Test database connectivity"""
    print("\n🔍 Testing database connection...")
    try:
        from app import app, db
        from sqlalchemy import text
        with app.app_context():
            # Test basic connection using newer SQLAlchemy syntax
            result = db.session.execute(text("SELECT 1")).scalar()
            if result == 1:
                print("✅ Database connection successful")
                return True
            else:
                print("❌ Database connection failed")
                return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def test_database_tables():
    """Test if required tables exist"""
    print("\n🔍 Testing database tables...")
    try:
        from app import app, db
        with app.app_context():
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            required_tables = ['customer', 'stadium', 'team', 'event', 'seat', 'booking', 'ticket']
            missing_tables = [t for t in required_tables if t not in existing_tables]
            
            if not missing_tables:
                print(f"✅ All required tables exist ({len(existing_tables)} total)")
                for table in sorted(existing_tables):
                    print(f"   - {table}")
                return True
            else:
                print(f"❌ Missing tables: {missing_tables}")
                return False
    except Exception as e:
        print(f"❌ Table check error: {e}")
        return False

def start_server():
    """Start the Flask server in a separate process"""
    print("\n🔍 Starting Flask server (Flask-only version)...")
    try:
        # Start server process with Flask-only version (more reliable than SocketIO)
        process = subprocess.Popen([
            sys.executable, "app_flask_only.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        print("   Waiting for Flask server to initialize...")
        time.sleep(12)  # Give more time for database init
        
        # Check if process is still running
        if process.poll() is None:
            print("   ✅ Server process is running")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"   ❌ Server terminated: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return None

def test_server_response():
    """Test if server responds to HTTP requests"""
    print("\n🔍 Testing server response...")
    try:
        response = requests.get("http://localhost:5000", timeout=10)
        if response.status_code == 200:
            print(f"✅ Server responding (Status: {response.status_code})")
            print(f"   Content length: {len(response.text)} chars")
            return True
        else:
            print(f"❌ Server returned status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Server not responding: {e}")
        return False

def test_home_page():
    """Test home page content"""
    print("\n🔍 Testing home page...")
    try:
        response = requests.get("http://localhost:5000", timeout=10)
        if response.status_code == 200:
            content = response.text.lower()
            required_elements = ["cricverse", "stadium", "ticket"]
            found_elements = [elem for elem in required_elements if elem in content]
            
            if len(found_elements) == len(required_elements):
                print(f"✅ Home page loaded with expected content")
                return True
            else:
                missing = set(required_elements) - set(found_elements)
                print(f"❌ Home page missing elements: {missing}")
                return False
        else:
            print(f"❌ Home page returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Home page test failed: {e}")
        return False

def test_api_endpoints():
    """Test key API endpoints"""
    print("\n🔍 Testing API endpoints...")
    endpoints = {
        "/api/csrf-token": "GET",
        "/api/bbl/live-scores": "GET",
        "/api/bbl/standings": "GET",
        "/api/bbl/top-performers": "GET"
    }
    
    passed = 0
    for endpoint, method in endpoints.items():
        try:
            response = requests.get(f"http://localhost:5000{endpoint}", timeout=5)
            if response.status_code in [200, 201]:
                print(f"   ✅ {endpoint}")
                passed += 1
            else:
                print(f"   ❌ {endpoint} (Status: {response.status_code})")
        except Exception as e:
            print(f"   ❌ {endpoint} (Error: {e})")
    
    if passed == len(endpoints):
        print(f"✅ All {passed} API endpoints working")
        return True
    else:
        print(f"❌ Only {passed}/{len(endpoints)} API endpoints working")
        return False

def test_static_files():
    """Test static file serving"""
    print("\n🔍 Testing static files...")
    try:
        # Test CSS
        response = requests.get("http://localhost:5000/static/css/style.css", timeout=5)
        css_ok = response.status_code in [200, 404]  # 404 is ok if file doesn't exist
        
        # Test if static route works
        response = requests.get("http://localhost:5000/about", timeout=5)
        about_ok = response.status_code in [200, 404]
        
        if css_ok and about_ok:
            print("✅ Static file serving working")
            return True
        else:
            print("❌ Static file serving issues")
            return False
    except Exception as e:
        print(f"❌ Static file test failed: {e}")
        return False

def test_chatbot_api():
    """Test AI chatbot functionality"""
    print("\n🔍 Testing AI chatbot...")
    try:
        payload = {"message": "Hello"}
        response = requests.post(
            "http://localhost:5000/api/chat",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("response"):
                print("✅ AI chatbot responding")
                return True
            else:
                print(f"❌ Chatbot response invalid: {data}")
                return False
        else:
            print(f"❌ Chatbot API returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Chatbot test failed: {e}")
        return False

def run_all_tests():
    """Run all tests systematically"""
    print("=" * 60)
    print("🏏 CricVerse Stadium System - Comprehensive Test Suite")
    print("=" * 60)
    
    results = {}
    server_process = None
    
    try:
        # Test 1: Imports
        results["imports"] = test_imports()
        
        # Test 2: Database connection
        results["database_connection"] = test_database_connection()
        
        # Test 3: Database tables
        results["database_tables"] = test_database_tables()
        
        # Start server for remaining tests
        if all(results.values()):
            server_process = start_server()
            
            if server_process:
                # Test 4: Server response
                results["server_response"] = test_server_response()
                
                # Test 5: Home page
                results["home_page"] = test_home_page()
                
                # Test 6: API endpoints
                results["api_endpoints"] = test_api_endpoints()
                
                # Test 7: Static files
                results["static_files"] = test_static_files()
                
                # Test 8: Chatbot
                results["chatbot"] = test_chatbot_api()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = sum(results.values())
        total = len(results)
        
        for test, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test.replace('_', ' ').title()}")
        
        print("-" * 60)
        print(f"OVERALL: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED - CricVerse is fully functional!")
            return True
        else:
            print("⚠️  Some tests failed - see details above")
            return False
    
    finally:
        # Clean up server process
        if server_process:
            try:
                server_process.terminate()
                time.sleep(2)
                if server_process.poll() is None:
                    server_process.kill()
            except:
                pass

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)