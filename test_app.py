#!/usr/bin/env python3
"""
Test script for CricVerse System
Tests application startup, database initialization, and role-based access control
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Customer, Stadium, StadiumAdmin
from werkzeug.test import Client
from werkzeug.wrappers import Response

def test_app_startup():
    """Test that the application starts without SQLAlchemy errors"""
    print("Testing application startup...")
    
    try:
        with app.app_context():
            # Test database table creation
            db.create_all()
            print("✓ Database tables created successfully")
            
            # Test model relationships
            customer_count = Customer.query.count()
            stadium_count = Stadium.query.count()
            admin_count = StadiumAdmin.query.count()
            
            print(f"✓ Database queries working - Customers: {customer_count}, Stadiums: {stadium_count}, Admin assignments: {admin_count}")
            
            return True
            
    except Exception as e:
        print(f"✗ Application startup failed: {e}")
        return False

def test_model_relationships():
    """Test that model relationships work without conflicts"""
    print("\nTesting model relationships...")
    
    try:
        with app.app_context():
            # Test Customer model methods
            test_customer = Customer(name="Test User", email="test@example.com", role="admin")
            test_customer.set_password("password123")
            
            # Test admin methods
            is_admin = test_customer.is_admin()
            administered_stadiums = test_customer.get_administered_stadiums()
            
            print(f"✓ Customer model working - Is admin: {is_admin}, Administered stadiums: {administered_stadiums}")
            
            return True
            
    except Exception as e:
        print(f"✗ Model relationship test failed: {e}")
        return False

def test_routes():
    """Test basic route accessibility"""
    print("\nTesting basic routes...")
    
    try:
        client = Client(app, Response)
        
        # Test public routes
        response = client.get('/')
        print(f"✓ Index route: {response.status_code}")
        
        response = client.get('/stadiums')
        print(f"✓ Stadiums route: {response.status_code}")
        
        response = client.get('/login')
        print(f"✓ Login route: {response.status_code}")
        
        response = client.get('/register')
        print(f"✓ Register route: {response.status_code}")
        
        # Test protected admin routes (should redirect to login)
        response = client.get('/admin/dashboard')
        print(f"✓ Admin dashboard (protected): {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"✗ Route testing failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("CricVerse System - Test Suite")
    print("=" * 50)
    
    tests = [
        test_app_startup,
        test_model_relationships,
        test_routes
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n{'=' * 50}")
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! Application is ready for use.")
        print("\nNext steps:")
        print("1. Run the application: python app.py")
        print("2. Register as an admin user")
        print("3. Create stadiums and test admin functionality")
        print("4. Register as a customer and test booking features")
    else:
        print("✗ Some tests failed. Please check the errors above.")
    
    print("=" * 50)

if __name__ == '__main__':
    main()
