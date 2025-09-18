from app import db
from app.models.booking import Ticket, Seat, Booking
from datetime import datetime
from flask import session
import time
import random
from app.models.payment import Payment

def book_seat(seat_id, event_id, customer_id):
    """
    Concurrency-safe seat booking function.
    
    Args:
        seat_id (int): ID of the seat to book
        event_id (int): ID of the event
        customer_id (int): ID of the customer booking the seat
        
    Returns:
        dict: Result of the booking operation with success status and message
    """
    try:
        # Use SELECT... FOR UPDATE to lock the seat row during the transaction
        seat = db.session.query(Seat).with_for_update().get(seat_id)
        
        if not seat:
            return {
                'success': False,
                'message': 'Seat not found'
            }
        
        # Check if the seat is already booked for this event
        existing_ticket = db.session.query(Ticket).filter(
            Ticket.seat_id == seat_id,
            Ticket.event_id == event_id,
            Ticket.ticket_status.in_(['Booked', 'Used'])
        ).with_for_update().first()
        
        if existing_ticket:
            return {
                'success': False,
                'message': 'Seat is already booked for this event'
            }
        
        # Get seat price
        seat_price = getattr(seat, 'price', 0) or 0
        
        # Create booking record
        booking = Booking(
            customer_id=customer_id,
            total_amount=seat_price,
            booking_date=datetime.utcnow()
        )
        db.session.add(booking)
        db.session.flush()  # Get the booking ID without committing
        
        # Create ticket record
        ticket = Ticket(
            event_id=event_id,
            seat_id=seat_id,
            customer_id=customer_id,
            booking_id=booking.id,
            ticket_status='Booked',
            access_gate=f"Gate {getattr(seat, 'section', 'A')[0]}" if hasattr(seat, 'section') else 'Gate A'
        )
        db.session.add(ticket)
        
        # Update seat status if it has a status field
        if hasattr(seat, 'status'):
            seat.status = 'Booked'
        
        # Commit the transaction
        db.session.commit()
        
        # If we reach here, the transaction was successful
        return {
            'success': True,
            'message': 'Seat booked successfully',
            'booking_id': booking.id,
            'ticket_id': ticket.id
        }
        
    except Exception as e:
        # Handle any errors
        try:
            db.session.rollback()
        except:
            # If rollback fails, just continue
            pass
        return {
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }

def create_payment_order(event_id, seat_ids, customer_id):
    """
    Verifies seats, calculates total, and creates a mock payment order.
    Stores pending booking in session.
    """
    try:
        # Start a transaction
        with db.session.begin():
            # Lock and validate all seats at once
            seats = db.session.query(Seat).filter(Seat.id.in_(seat_ids)).with_for_update().all()

            if len(seats) != len(seat_ids):
                return {'success': False, 'message': 'One or more seats not found.'}

            # Check if any of the selected seats are already booked for this event
            existing_tickets = db.session.query(Ticket.seat_id).filter(
                Ticket.event_id == event_id,
                Ticket.seat_id.in_(seat_ids)
            ).all()

            if existing_tickets:
                booked_seat_ids = {t[0] for t in existing_tickets}
                return {'success': False, 'message': f'Seats {booked_seat_ids} are already booked.'}

            # Calculate total amount
            total_amount = sum(seat.price for seat in seats if seat.price)

            # Mock creating an order with a payment provider
            mock_order_id = f"MOCK_ORDER_{int(time.time())}_{random.randint(1000, 9999)}"

            # Store pending booking in session
            pending_booking = {
                'order_id': mock_order_id,
                'event_id': event_id,
                'seat_ids': seat_ids,
                'total_amount': total_amount,
                'customer_id': customer_id
            }
            session['pending_booking'] = pending_booking

            return {
                'success': True,
                'orderID': mock_order_id,
                'amount': total_amount
            }

    except Exception as e:
        return {'success': False, 'message': f'An error occurred: {str(e)}'}


def capture_payment_and_create_booking(order_id, customer_id):
    """
    "Captures" the payment and creates the booking records atomically.
    """
    pending_booking = session.get('pending_booking')

    # Validations
    if not pending_booking:
        return {'success': False, 'message': 'No pending booking found in session.'}
    if pending_booking.get('order_id') != order_id:
        return {'success': False, 'message': 'Order ID mismatch.'}
    if pending_booking.get('customer_id') != customer_id:
        return {'success': False, 'message': 'Customer ID mismatch.'}

    try:
        # Re-verify that seats are still available (final check)
        seat_ids = pending_booking['seat_ids']
        existing_tickets = db.session.query(Ticket.seat_id).filter(
            Ticket.event_id == pending_booking['event_id'],
            Ticket.seat_id.in_(seat_ids)
        ).with_for_update().all()

        if existing_tickets:
            return {'success': False, 'message': 'Seats became unavailable during payment.'}

        # Create the booking
        new_booking = Booking(
            customer_id=customer_id,
            total_amount=pending_booking['total_amount'],
            booking_date=datetime.utcnow(),
            payment_status='Completed'
        )
        db.session.add(new_booking)
        db.session.flush() # Get the new_booking.id

        # Create the tickets
        for seat_id in seat_ids:
            ticket = Ticket(
                event_id=pending_booking['event_id'],
                seat_id=seat_id,
                customer_id=customer_id,
                booking_id=new_booking.id,
                ticket_status='Booked'
            )
            db.session.add(ticket)
        
        # Create a payment record
        payment = Payment(
            booking_id=new_booking.id,
            amount=pending_booking['total_amount'],
            payment_method='MockPayPal',
            transaction_id=order_id,
            payment_status='Completed'
        )
        db.session.add(payment)

        # Commit all changes
        db.session.commit()

        # Clear the pending booking from the session
        session.pop('pending_booking', None)

        return {
            'success': True,
            'message': 'Booking successful!',
            'booking_id': new_booking.id
        }

    except Exception as e:
        try:
            db.session.rollback()
        except:
            # If rollback fails, just continue
            pass
        return {'success': False, 'message': f'An error occurred during final booking: {str(e)}'}