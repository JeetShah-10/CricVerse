"""
Enhanced Booking Service for CricVerse
Comprehensive booking system using real Supabase database data
No hardcoded data - all operations use live database
Big Bash League Cricket Platform
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
from decimal import Decimal
from flask import current_app
from sqlalchemy import and_, or_, func
from sqlalchemy.exc import SQLAlchemyError
from app import db
from app.models import (
    Customer, Stadium, Event, Match, Booking, Ticket, Seat,
    Parking, ParkingBooking, Concession, MenuItem, Order, Payment, PaymentTransaction
)
from app.services.supabase_service import supabase_service

# Configure logging
logger = logging.getLogger(__name__)

class BookingType(Enum):
    """Types of bookings available"""
    TICKET = "ticket"
    PARKING = "parking"
    CONCESSION = "concession"

@dataclass
class BookingItem:
    """Structure for booking items"""
    item_type: BookingType
    item_id: int
    quantity: int
    price: float
    details: Dict[str, Any] = None

@dataclass
class BookingResult:
    """Result of booking operation"""
    success: bool
    booking_id: Optional[int] = None
    message: str = ""
    error: str = ""
    payment_data: Optional[Dict[str, Any]] = None
    qr_code: Optional[str] = None

class EnhancedBookingService:
    """Service for comprehensive booking operations using real Supabase data"""
    
    def __init__(self):
        self.initialized = False
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.initialized = True
        logger.info("✅ Enhanced booking service initialized with Supabase integration")
    
    # Seat Availability and Selection
    def get_seat_availability(self, event_id: int, section: str = None) -> Dict[str, Any]:
        """Get real-time seat availability from Supabase"""
        try:
            event = Event.query.get(event_id)
            if not event:
                return {'error': 'Event not found', 'event_id': event_id}
            
            # Get all seats for the stadium
            query = Seat.query.filter_by(stadium_id=event.stadium_id)
            if section:
                query = query.filter_by(section=section)
            
            all_seats = query.all()
            
            # Get booked seats for this event
            booked_seats_query = db.session.query(Ticket.seat_id).join(Booking).filter(
                Booking.event_id == event_id,
                Booking.payment_status.in_(['Completed', 'Pending'])
            )
            booked_seat_ids = [row[0] for row in booked_seats_query.all()]
            
            # Organize seats by section
            availability = {}
            for seat in all_seats:
                if seat.section not in availability:
                    availability[seat.section] = {
                        'total_seats': 0,
                        'available_seats': 0,
                        'seats': []
                    }
                
                availability[seat.section]['total_seats'] += 1
                
                is_available = seat.id not in booked_seat_ids
                if is_available:
                    availability[seat.section]['available_seats'] += 1
                
                availability[seat.section]['seats'].append({
                    'id': seat.id,
                    'row_number': seat.row_number,
                    'seat_number': seat.seat_number,
                    'seat_type': seat.seat_type,
                    'price': float(seat.price),
                    'available': is_available
                })
            
            return {
                'event_id': event_id,
                'event_name': event.event_name,
                'stadium_name': event.stadium.name,
                'event_date': event.event_date.isoformat() if event.event_date else None,
                'availability': availability,
                'total_available': sum(section['available_seats'] for section in availability.values()),
                'total_capacity': sum(section['total_seats'] for section in availability.values())
            }
        except Exception as e:
            logger.error(f"Error getting seat availability for event {event_id}: {str(e)}")
            return {'error': str(e), 'event_id': event_id}
    
    def get_seat_details(self, seat_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific seat"""
        try:
            seat = Seat.query.get(seat_id)
            if not seat:
                return None
            
            return {
                'id': seat.id,
                'stadium_id': seat.stadium_id,
                'stadium_name': seat.stadium.name if seat.stadium else 'Unknown',
                'section': seat.section,
                'row_number': seat.row_number,
                'seat_number': seat.seat_number,
                'seat_type': seat.seat_type,
                'price': float(seat.price),
                'amenities': getattr(seat, 'amenities', []),
                'accessibility': getattr(seat, 'accessibility_features', [])
            }
        except Exception as e:
            logger.error(f"Error getting seat details for seat {seat_id}: {str(e)}")
            return None
    
    # Parking Management
    def get_parking_availability(self, event_id: int) -> Dict[str, Any]:
        """Get real parking availability from Supabase"""
        try:
            event = Event.query.get(event_id)
            if not event:
                return {'error': 'Event not found', 'event_id': event_id}
            
            # Get all parking spots for the stadium
            parking_spots = Parking.query.filter_by(stadium_id=event.stadium_id).all()
            
            # Get booked parking for this event
            booked_parking = ParkingBooking.query.filter_by(event_id=event_id).all()
            booked_spot_ids = [booking.parking_id for booking in booked_parking]
            
            # Organize by parking type
            parking_availability = {}
            for spot in parking_spots:
                spot_type = spot.spot_type
                if spot_type not in parking_availability:
                    parking_availability[spot_type] = {
                        'total_spots': 0,
                        'available_spots': 0,
                        'spots': [],
                        'price_range': {'min': float('inf'), 'max': 0}
                    }
                
                parking_availability[spot_type]['total_spots'] += 1
                
                is_available = spot.id not in booked_spot_ids
                if is_available:
                    parking_availability[spot_type]['available_spots'] += 1
                
                # Update price range
                price = float(spot.price)
                if price < parking_availability[spot_type]['price_range']['min']:
                    parking_availability[spot_type]['price_range']['min'] = price
                if price > parking_availability[spot_type]['price_range']['max']:
                    parking_availability[spot_type]['price_range']['max'] = price
                
                parking_availability[spot_type]['spots'].append({
                    'id': spot.id,
                    'spot_number': spot.spot_number,
                    'price': price,
                    'available': is_available,
                    'features': getattr(spot, 'features', [])
                })
            
            # Fix infinite min values
            for spot_type in parking_availability:
                if parking_availability[spot_type]['price_range']['min'] == float('inf'):
                    parking_availability[spot_type]['price_range']['min'] = 0
            
            return {
                'event_id': event_id,
                'event_name': event.event_name,
                'stadium_name': event.stadium.name,
                'parking_availability': parking_availability,
                'total_available': sum(section['available_spots'] for section in parking_availability.values()),
                'total_spots': sum(section['total_spots'] for section in parking_availability.values())
            }
        except Exception as e:
            logger.error(f"Error getting parking availability for event {event_id}: {str(e)}")
            return {'error': str(e), 'event_id': event_id}
    
    # Concession Services
    def get_concession_menu(self, stadium_id: int) -> Dict[str, Any]:
        """Get real concession menu from Supabase"""
        try:
            stadium = Stadium.query.get(stadium_id)
            if not stadium:
                return {'error': 'Stadium not found', 'stadium_id': stadium_id}
            
            # Get all concessions for the stadium
            concessions = Concession.query.filter_by(stadium_id=stadium_id).all()
            
            menu_data = {
                'stadium_id': stadium_id,
                'stadium_name': stadium.name,
                'concessions': []
            }
            
            for concession in concessions:
                # Get menu items for this concession
                menu_items = MenuItem.query.filter_by(concession_id=concession.id).all()
                
                # Organize items by category
                categories = {}
                for item in menu_items:
                    category = getattr(item, 'category', 'Food')
                    if category not in categories:
                        categories[category] = []
                    
                    categories[category].append({
                        'id': item.id,
                        'name': item.name,
                        'description': getattr(item, 'description', ''),
                        'price': float(item.price),
                        'available': getattr(item, 'available', True),
                        'dietary_info': getattr(item, 'dietary_info', []),
                        'preparation_time': getattr(item, 'preparation_time', 5)
                    })
                
                menu_data['concessions'].append({
                    'id': concession.id,
                    'name': concession.name,
                    'location': getattr(concession, 'location', 'Stadium'),
                    'operating_hours': getattr(concession, 'operating_hours', '10:00-22:00'),
                    'categories': categories
                })
            
            return menu_data
        except Exception as e:
            logger.error(f"Error getting concession menu for stadium {stadium_id}: {str(e)}")
            return {'error': str(e), 'stadium_id': stadium_id}
    
    # Comprehensive Booking Creation
    def create_comprehensive_booking(self, customer_id: int, event_id: int, 
                                   booking_items: List[BookingItem]) -> BookingResult:
        """Create a comprehensive booking with tickets, parking, and concessions"""
        try:
            # Validate customer and event
            customer = Customer.query.get(customer_id)
            if not customer:
                return BookingResult(success=False, error="Customer not found")
            
            event = Event.query.get(event_id)
            if not event:
                return BookingResult(success=False, error="Event not found")
            
            # Calculate total amount
            total_amount = sum(item.price * item.quantity for item in booking_items)
            
            # Create main booking record
            booking = Booking(
                customer_id=customer_id,
                event_id=event_id,
                total_amount=total_amount,
                booking_date=datetime.utcnow(),
                payment_status='Pending'
            )
            
            db.session.add(booking)
            db.session.flush()  # Get booking ID
            
            # Process each booking item
            tickets_created = []
            parking_bookings = []
            concession_orders = []
            
            for item in booking_items:
                if item.item_type == BookingType.TICKET:
                    # Create ticket
                    seat = Seat.query.get(item.item_id)
                    if not seat:
                        db.session.rollback()
                        return BookingResult(success=False, error=f"Seat {item.item_id} not found")
                    
                    # Check if seat is still available
                    existing_ticket = Ticket.query.join(Booking).filter(
                        Ticket.seat_id == item.item_id,
                        Booking.event_id == event_id,
                        Booking.payment_status.in_(['Completed', 'Pending'])
                    ).first()
                    
                    if existing_ticket:
                        db.session.rollback()
                        return BookingResult(success=False, error=f"Seat {seat.section}-{seat.row_number}-{seat.seat_number} is no longer available")
                    
                    for _ in range(item.quantity):
                        ticket = Ticket(
                            booking_id=booking.id,
                            seat_id=item.item_id,
                            price=item.price,
                            ticket_status='Booked'
                        )
                        db.session.add(ticket)
                        tickets_created.append(ticket)
                
                elif item.item_type == BookingType.PARKING:
                    # Create parking booking
                    parking_spot = Parking.query.get(item.item_id)
                    if not parking_spot:
                        db.session.rollback()
                        return BookingResult(success=False, error=f"Parking spot {item.item_id} not found")
                    
                    # Check if parking is still available
                    existing_parking = ParkingBooking.query.filter_by(
                        parking_id=item.item_id,
                        event_id=event_id
                    ).first()
                    
                    if existing_parking:
                        db.session.rollback()
                        return BookingResult(success=False, error=f"Parking spot {parking_spot.spot_number} is no longer available")
                    
                    parking_booking = ParkingBooking(
                        customer_id=customer_id,
                        parking_id=item.item_id,
                        event_id=event_id,
                        amount=item.price,
                        booking_date=datetime.utcnow(),
                        payment_status='Pending'
                    )
                    db.session.add(parking_booking)
                    parking_bookings.append(parking_booking)
                
                elif item.item_type == BookingType.CONCESSION:
                    # Create concession order
                    menu_item = MenuItem.query.get(item.item_id)
                    if not menu_item:
                        db.session.rollback()
                        return BookingResult(success=False, error=f"Menu item {item.item_id} not found")
                    
                    order = Order(
                        customer_id=customer_id,
                        concession_id=menu_item.concession_id,
                        total_amount=item.price * item.quantity,
                        order_date=datetime.utcnow(),
                        status='pending',
                        items=[{
                            'menu_item_id': item.item_id,
                            'quantity': item.quantity,
                            'price': item.price
                        }]
                    )
                    db.session.add(order)
                    concession_orders.append(order)
            
            # Create payment record
            payment = Payment(
                booking_id=booking.id,
                amount=total_amount,
                payment_method='pending',
                payment_status='Pending',
                payment_date=datetime.utcnow()
            )
            db.session.add(payment)
            
            # Commit all changes
            db.session.commit()
            
            # Generate QR code (placeholder for now)
            qr_code_data = f"BOOKING-{booking.id}-{event.event_name}-{datetime.utcnow().isoformat()}"
            
            # Prepare payment data
            payment_data = {
                'booking_id': booking.id,
                'amount': float(total_amount),
                'currency': 'AUD',
                'description': f"CricVerse booking for {event.event_name}",
                'customer_email': customer.email,
                'items_summary': {
                    'tickets': len(tickets_created),
                    'parking': len(parking_bookings),
                    'concessions': len(concession_orders)
                }
            }
            
            return BookingResult(
                success=True,
                booking_id=booking.id,
                message=f"Booking created successfully for {event.event_name}",
                payment_data=payment_data,
                qr_code=qr_code_data
            )
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating comprehensive booking: {str(e)}")
            return BookingResult(success=False, error=str(e))
    
    # Booking Management
    def get_booking_details(self, booking_id: int) -> Optional[Dict[str, Any]]:
        """Get comprehensive booking details from Supabase"""
        try:
            booking = Booking.query.get(booking_id)
            if not booking:
                return None
            
            # Get associated tickets
            tickets = Ticket.query.filter_by(booking_id=booking_id).all()
            ticket_details = []
            for ticket in tickets:
                seat = ticket.seat
                ticket_details.append({
                    'id': ticket.id,
                    'seat_id': ticket.seat_id,
                    'section': seat.section if seat else 'N/A',
                    'row_number': seat.row_number if seat else 'N/A',
                    'seat_number': seat.seat_number if seat else 'N/A',
                    'seat_type': seat.seat_type if seat else 'N/A',
                    'price': float(ticket.price),
                    'status': ticket.ticket_status
                })
            
            # Get associated parking
            parking_bookings = ParkingBooking.query.filter_by(
                customer_id=booking.customer_id,
                event_id=booking.event_id
            ).all()
            
            parking_details = []
            for parking in parking_bookings:
                spot = parking.parking
                parking_details.append({
                    'id': parking.id,
                    'spot_number': spot.spot_number if spot else 'N/A',
                    'spot_type': spot.spot_type if spot else 'N/A',
                    'price': float(parking.amount)
                })
            
            # Get associated orders
            orders = Order.query.filter_by(
                customer_id=booking.customer_id
            ).filter(
                func.date(Order.order_date) == func.date(booking.booking_date)
            ).all()
            
            order_details = []
            for order in orders:
                order_details.append({
                    'id': order.id,
                    'concession_id': order.concession_id,
                    'total_amount': float(order.total_amount),
                    'status': order.status,
                    'items': getattr(order, 'items', [])
                })
            
            return {
                'id': booking.id,
                'customer_id': booking.customer_id,
                'customer_name': booking.customer.name if booking.customer else 'Unknown',
                'customer_email': booking.customer.email if booking.customer else 'Unknown',
                'event_id': booking.event_id,
                'event_name': booking.event.event_name if booking.event else 'Unknown',
                'event_date': booking.event.event_date.isoformat() if booking.event and booking.event.event_date else None,
                'stadium_name': booking.event.stadium.name if booking.event and booking.event.stadium else 'Unknown',
                'total_amount': float(booking.total_amount),
                'booking_date': booking.booking_date.isoformat() if booking.booking_date else None,
                'payment_status': booking.payment_status,
                'tickets': ticket_details,
                'parking': parking_details,
                'concessions': order_details
            }
        except Exception as e:
            logger.error(f"Error getting booking details for {booking_id}: {str(e)}")
            return None
    
    def update_booking_status(self, booking_id: int, status: str) -> bool:
        """Update booking payment status"""
        try:
            booking = Booking.query.get(booking_id)
            if not booking:
                return False
            
            booking.payment_status = status
            
            # Update associated records
            if status == 'Completed':
                # Update tickets
                tickets = Ticket.query.filter_by(booking_id=booking_id).all()
                for ticket in tickets:
                    ticket.ticket_status = 'Confirmed'
                
                # Update parking bookings
                parking_bookings = ParkingBooking.query.filter_by(
                    customer_id=booking.customer_id,
                    event_id=booking.event_id
                ).all()
                for parking in parking_bookings:
                    parking.payment_status = 'Completed'
                
                # Update payment record
                payment = Payment.query.filter_by(booking_id=booking_id).first()
                if payment:
                    payment.payment_status = 'Completed'
            
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating booking status for {booking_id}: {str(e)}")
            return False
    
    # Booking Analytics
    def get_booking_analytics(self, stadium_id: int = None, days: int = 30) -> Dict[str, Any]:
        """Get booking analytics from real data"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            # Base query
            query = db.session.query(Booking).filter(
                Booking.booking_date >= start_date,
                Booking.booking_date <= end_date
            )
            
            if stadium_id:
                query = query.join(Event).filter(Event.stadium_id == stadium_id)
            
            bookings = query.all()
            
            # Calculate metrics
            total_bookings = len(bookings)
            completed_bookings = len([b for b in bookings if b.payment_status == 'Completed'])
            total_revenue = sum(float(b.total_amount) for b in bookings if b.payment_status == 'Completed')
            avg_booking_value = total_revenue / completed_bookings if completed_bookings > 0 else 0
            
            # Booking status breakdown
            status_breakdown = {}
            for booking in bookings:
                status = booking.payment_status
                status_breakdown[status] = status_breakdown.get(status, 0) + 1
            
            return {
                'period': f"{start_date.isoformat()} to {end_date.isoformat()}",
                'total_bookings': total_bookings,
                'completed_bookings': completed_bookings,
                'total_revenue': total_revenue,
                'average_booking_value': avg_booking_value,
                'conversion_rate': (completed_bookings / total_bookings * 100) if total_bookings > 0 else 0,
                'status_breakdown': status_breakdown
            }
        except Exception as e:
            logger.error(f"Error getting booking analytics: {str(e)}")
            return {
                'period': f"Last {days} days",
                'total_bookings': 0,
                'completed_bookings': 0,
                'total_revenue': 0,
                'average_booking_value': 0,
                'conversion_rate': 0,
                'status_breakdown': {}
            }

# Global service instance
enhanced_booking_service = EnhancedBookingService()
