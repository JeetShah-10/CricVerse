"""
Simple CricVerse app test without Unicode characters
"""

import sys
import os
import traceback

def test_app_components():
    """Test all app components systematically"""
    print("=" * 60)
    print("CricVerse Application Test Suite")
    print("=" * 60)
    
    # Test imports
    print("1. Testing imports...")
    try:
        from app import app, db, socketio
        print("PASS: All imports successful")
    except Exception as e:
        print(f"FAIL: Import error: {e}")
        return False
    
    # Test database
    print("\n2. Testing database...")
    try:
        with app.app_context():
            from sqlalchemy import text
            result = db.session.execute(text("SELECT 1")).scalar()
            print("PASS: Database connection working")
    except Exception as e:
        print(f"FAIL: Database error: {e}")
    
    # Test routes using test client
    print("\n3. Testing routes...")
    try:
        with app.test_client() as client:
            # Test home page
            response = client.get('/')
            if response.status_code == 200:
                print(f"PASS: Home page (Status: {response.status_code})")
            else:
                print(f"FAIL: Home page (Status: {response.status_code})")
            
            # Test API endpoints
            response = client.get('/api/csrf-token')
            if response.status_code == 200:
                print(f"PASS: CSRF API (Status: {response.status_code})")
            else:
                print(f"FAIL: CSRF API (Status: {response.status_code})")
                
            response = client.get('/api/bbl/live-scores')
            if response.status_code == 200:
                print(f"PASS: BBL API (Status: {response.status_code})")
            else:
                print(f"FAIL: BBL API (Status: {response.status_code})")
    except Exception as e:
        print(f"FAIL: Route test error: {e}")
        traceback.print_exc()
    
    # Test actual server startup
    print("\n4. Testing server startup...")
    try:
        print("Starting server on port 5003...")
        socketio.run(
            app,
            host='127.0.0.1',
            port=5003,
            debug=False,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("Server stopped by user")
    except Exception as e:
        print(f"Server error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_app_components()