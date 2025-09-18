#!/usr/bin/env python
"""Test script to verify routes work correctly."""

from app import create_app

def test_routes():
    """Test that routes work correctly."""
    print("Testing routes...")
    
    # Create app
    app = create_app()
    
    with app.test_client() as client:
        # Test homepage route
        response = client.get('/')
        print(f"Homepage status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Homepage route working")
        else:
            print("❌ Homepage route failed")
            
        # Test booking API route
        response = client.post('/api/booking/book-seat', 
                              json={'seat_id': 1, 'event_id': 1, 'customer_id': 1},
                              content_type='application/json')
        print(f"Booking API status: {response.status_code}")
        if response.status_code == 200 or response.status_code == 400:
            print("✅ Booking API route working")
        else:
            print("❌ Booking API route failed")

if __name__ == '__main__':
    test_routes()