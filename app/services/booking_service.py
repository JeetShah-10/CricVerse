from app import db
from app.models.booking import Ticket, Seat, Booking
from datetime import datetime

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
        db.session.rollback()
        return {
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }