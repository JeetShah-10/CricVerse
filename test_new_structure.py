#!/usr/bin/env python
"""Test script to verify the new modular structure works without conflicts."""

from app import create_app
from app.models.booking import Customer, Booking, Ticket, Seat
from app import db

def test_new_structure():
    """Test that the new modular structure works correctly."""
    print("Testing new modular structure...")
    
    # Create app with testing config
    app = create_app('testing')
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully")
        
        # Test creating a customer
        customer = Customer(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
        customer.set_password('password123')
        
        db.session.add(customer)
        db.session.commit()
        print("✅ Customer created successfully")
        
        # Test creating a seat
        seat = Seat(
            section='A',
            row_number='1',
            seat_number='1',
            seat_type='Standard',
            price=50.0
        )
        db.session.add(seat)
        db.session.commit()
        print("✅ Seat created successfully")
        
        # Test creating a booking
        booking = Booking(
            customer_id=customer.id,
            total_amount=50.0
        )
        db.session.add(booking)
        db.session.commit()
        print("✅ Booking created successfully")
        
        # Test creating a ticket
        ticket = Ticket(
            event_id=1,
            seat_id=seat.id,
            customer_id=customer.id,
            booking_id=booking.id,
            ticket_type='Standard',
            ticket_status='Booked',
            access_gate='Gate A'
        )
        db.session.add(ticket)
        db.session.commit()
        print("✅ Ticket created successfully")
        
        # Test querying data
        retrieved_customer = Customer.query.filter_by(username='testuser').first()
        print(f"✅ Customer query successful: {retrieved_customer.username}")
        
        retrieved_booking = Booking.query.filter_by(customer_id=customer.id).first()
        print(f"✅ Booking query successful: Booking ID {retrieved_booking.id}")
        
        retrieved_ticket = Ticket.query.filter_by(booking_id=booking.id).first()
        print(f"✅ Ticket query successful: Ticket ID {retrieved_ticket.id}")
        
        print("\n🎉 All tests passed! New modular structure is working correctly.")

if __name__ == '__main__':
    test_new_structure()