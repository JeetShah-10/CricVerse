#!/usr/bin/env python
"""Integration test for CricVerse API endpoints."""

import os
import sys
import json
import threading
import time
from app import create_app
from app.models.booking import Seat, Booking, Ticket
from app import db

def test_api_endpoint():
    """Test the booking API endpoint."""
    print("Testing API endpoint...")
    
    # Create app and test client
    app = create_app('testing')
    client = app.test_client()
    
    with app.app_context():
        # Create database tables
        db.create_all()
        
        # Create a sample seat
        seat = Seat(
            section='A',
            row_number='1',
            seat_number='1',
            seat_type='Standard',
            price=50.0
        )
        db.session.add(seat)
        db.session.commit()
        
        # Test the booking endpoint
        response = client.post('/api/booking/book-seat', 
                              json={
                                  'seat_id': seat.id,
                                  'event_id': 1,
                                  'customer_id': 1
                              },
                              content_type='application/json')
        
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.get_json()}")
        
        if response.status_code == 200:
            result = response.get_json()
            if result.get('success'):
                print("API endpoint test PASSED")
                return True
            else:
                print("API endpoint test FAILED - booking not successful")
                return False
        else:
            print("API endpoint test FAILED - incorrect status code")
            return False

def test_concurrent_api_calls():
    """Test concurrent API calls to verify concurrency protection."""
    print("Testing concurrent API calls...")
    
    # Create app
    app = create_app('testing')
    
    with app.app_context():
        # Create database tables
        db.create_all()
        
        # Create a sample seat
        seat = Seat(
            section='B',
            row_number='1',
            seat_number='1',
            seat_type='Premium',
            price=100.0
        )
        db.session.add(seat)
        db.session.commit()
        
        # Store seat ID for use in threads
        seat_id = seat.id
    
    # Results storage
    results = []
    # Lock for thread-safe results access
    results_lock = threading.Lock()
    
    def make_booking(client_id):
        """Make a booking request."""
        # Create a new app context for each thread
        with app.app_context():
            client = app.test_client()
            response = client.post('/api/booking/book-seat',
                                  json={
                                      'seat_id': seat_id,
                                      'event_id': 1,
                                      'customer_id': client_id
                                  },
                                  content_type='application/json')
            
            with results_lock:
                results.append((client_id, response.get_json()))
    
    # Create multiple threads to simulate concurrent bookings
    threads = []
    for i in range(3):
        thread = threading.Thread(target=make_booking, args=(i+1,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Check results - only one booking should be successful
    successful_bookings = [result for _, result in results if result and result.get('success')]
    
    print(f"Successful bookings: {len(successful_bookings)}")
    for i, (client_id, result) in enumerate(results):
        print(f"Client {client_id}: {result}")
    
    if len(successful_bookings) == 1:
        print("Concurrent API calls test PASSED - concurrency protection working")
        return True
    else:
        print("Concurrent API calls test FAILED - concurrency protection not working correctly")
        return False

if __name__ == '__main__':
    print("Running CricVerse integration tests...")
    
    # Test single API call
    test1_passed = test_api_endpoint()
    
    # Test concurrent API calls
    test2_passed = test_concurrent_api_calls()
    
    if test1_passed and test2_passed:
        print("\n🎉 All integration tests PASSED!")
    else:
        print("\n❌ Some integration tests FAILED!")