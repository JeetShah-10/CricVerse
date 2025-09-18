#!/usr/bin/env python
"""Test script to verify CricVerse functionality."""

import os
import sys
import json
from app import create_app
from app.models.booking import Seat, Booking, Ticket
from app import db
from app.services.booking_service import book_seat

def test_database_creation():
    """Test that database tables can be created."""
    print("Testing database creation...")
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        print("Database tables created successfully")

def test_booking_service():
    """Test the booking service functionality."""
    print("Testing booking service...")
    app = create_app('testing')
    with app.app_context():
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
        
        # Test booking the seat
        result = book_seat(seat.id, 1, 1)
        print(f"Booking result: {result}")
        
        if result['success']:
            print("Booking service test PASSED")
        else:
            print("Booking service test FAILED")

def test_chatbot_service():
    """Test the chatbot service functionality."""
    print("Testing chatbot service...")
    from app.services.chatbot_service import ask_gemini
    
    # Test with a simple prompt
    result = ask_gemini("Hello, what is cricket?")
    print(f"Chatbot response: {result}")
    print("Chatbot service test COMPLETED (response may vary based on API availability)")

if __name__ == '__main__':
    print("Running CricVerse functionality tests...")
    test_database_creation()
    test_booking_service()
    test_chatbot_service()
    print("All tests completed!")