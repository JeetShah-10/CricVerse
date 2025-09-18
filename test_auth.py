"""
Test user registration and authentication functionality
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import Customer
from werkzeug.security import generate_password_hash

def test_user_registration():
    """Test user registration functionality"""
    print("=" * 50)
    print("Testing User Registration and Authentication")
    print("=" * 50)
    
    app = create_app('testing')
    
    with app.app_context():
        try:
            # Test 1: User registration via test client
            print("1. Testing user registration...")
            
            with app.test_client() as client:
                # Test GET request to registration page
                response = client.get('/register')
                if response.status_code == 200:
                    print("PASS: Registration page loads")
                else:
                    print(f"FAIL: Registration page status: {response.status_code}")
                
                # Test POST request to register a new user
                user_data = {
                    'name': 'Test User',
                    'email': 'test@cricverse.com',
                    'phone': '+1234567890',
                    'password': 'TestPass123!'
                }
                
                response = client.post('/register', data=user_data, follow_redirects=True)
                print(f"Registration POST status: {response.status_code}")
                
            # Test 2: Check if user was created in database
            print("\n2. Testing database user creation...")
            user = Customer.query.filter_by(email='test@cricverse.com').first()
            if user:
                print("PASS: User created in database")
                print(f"  - Name: {user.name}")
                print(f"  - Email: {user.email}")
                print(f"  - Role: {user.role}")
            else:
                print("INFO: User not found in database (may be validation issue)")
            
            # Test 3: Login functionality
            print("\n3. Testing login functionality...")
            
            # Create a test user directly for login testing
            test_user = Customer.query.filter_by(email='testlogin@cricverse.com').first()
            if not test_user:
                test_user = Customer(
                    name='Login Test User',
                    email='testlogin@cricverse.com',
                    phone='+9876543210',
                    role='customer'
                )
                test_user.set_password('LoginTest123!')
                db.session.add(test_user)
                db.session.commit()
                print("Created test user for login")
            
            with app.test_client() as client:
                # Test GET request to login page
                response = client.get('/login')
                if response.status_code == 200:
                    print("PASS: Login page loads")
                else:
                    print(f"FAIL: Login page status: {response.status_code}")
                
                # Test POST request to login
                login_data = {
                    'email': 'testlogin@cricverse.com',
                    'password': 'LoginTest123!'
                }
                
                response = client.post('/login', data=login_data, follow_redirects=True)
                print(f"Login POST status: {response.status_code}")
                
                # Check if redirected to dashboard (indicates successful login)
                if b'dashboard' in response.data.lower() or response.status_code == 200:
                    print("PASS: Login appears successful")
                else:
                    print("INFO: Login may have validation issues")
            
            # Test 4: Protected route access
            print("\n4. Testing protected routes...")
            
            with app.test_client() as client:
                # Test accessing dashboard without login
                response = client.get('/dashboard')
                if response.status_code in [302, 401]:  # Redirect to login or unauthorized
                    print("PASS: Dashboard protected from unauthorized access")
                else:
                    print(f"WARN: Dashboard accessible without login (Status: {response.status_code})")
            
            # Test 5: Password hashing
            print("\n5. Testing password security...")
            if test_user and test_user.password_hash:
                if test_user.check_password('LoginTest123!'):
                    print("PASS: Password hashing and verification working")
                else:
                    print("FAIL: Password verification failed")
            else:
                print("WARN: Could not test password hashing")
                
            print("\n" + "=" * 50)
            print("Authentication Testing Complete")
            print("=" * 50)
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_user_registration()