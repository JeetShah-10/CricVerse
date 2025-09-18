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
            
        # Test teams route
        response = client.get('/teams')
        print(f"Teams page status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Teams route working")
        else:
            print("❌ Teams route failed")
            
        # Test stadiums route
        response = client.get('/stadiums')
        print(f"Stadiums page status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Stadiums route working")
        else:
            print("❌ Stadiums route failed")
            
        # Test players route
        response = client.get('/players')
        print(f"Players page status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Players route working")
        else:
            print("❌ Players route failed")
            
        # Test events route
        response = client.get('/events')
        print(f"Events page status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Events route working")
        else:
            print("❌ Events route failed")
            
        # Test AI assistant routes
        response = client.get('/ai_options')
        print(f"AI Options page status: {response.status_code}")
        if response.status_code == 200:
            print("✅ AI Options route working")
        else:
            print("❌ AI Options route failed")
            
        # Test chat route
        response = client.get('/chat')
        print(f"Chat page status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Chat route working")
        else:
            print("❌ Chat route failed")
            
        # Test realtime route
        response = client.get('/realtime')
        print(f"Realtime page status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Realtime route working")
        else:
            print("❌ Realtime route failed")

if __name__ == '__main__':
    test_routes()