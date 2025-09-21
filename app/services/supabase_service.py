"""
Supabase Integration Service for CricVerse
Handles all database operations using Supabase PostgreSQL
Eliminates all hardcoded data and provides real database integration
Big Bash League Cricket Platform
"""

import os
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, date
from flask import current_app
from sqlalchemy import text, func
from sqlalchemy.exc import SQLAlchemyError
from app import db
from app.models import (
    Customer, Stadium, Event, Match, Team, Player, Booking, Ticket, Seat,
    Parking, ParkingBooking, Concession, MenuItem, Order, Payment, PaymentTransaction,
    QRCode, Notification, MatchUpdate, BookingAnalytics
)

# Configure logging
logger = logging.getLogger(__name__)

class SupabaseService:
    """Service for all Supabase database operations"""
    
    def __init__(self):
        self.supabase_url = None
        self.supabase_key = None
        self.initialized = False
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.supabase_url = app.config.get('SUPABASE_URL')
        self.supabase_key = app.config.get('SUPABASE_KEY')
        
        if self.supabase_url and self.supabase_key:
            self.initialized = True
            logger.info("✅ Supabase service initialized successfully")
        else:
            logger.warning("⚠️ Supabase configuration missing")
    
    # Stadium Operations
    def get_all_stadiums(self) -> List[Dict[str, Any]]:
        """Get all stadiums from Supabase"""
        try:
            stadiums = Stadium.query.all()
            return [{
                'id': stadium.id,
                'name': stadium.name,
                'location': stadium.location,
                'capacity': stadium.capacity,
                'description': getattr(stadium, 'description', ''),
                'facilities': getattr(stadium, 'facilities', [])
            } for stadium in stadiums]
        except Exception as e:
            logger.error(f"Error fetching stadiums: {str(e)}")
            return []
    
    def get_stadium_by_id(self, stadium_id: int) -> Optional[Dict[str, Any]]:
        """Get stadium by ID"""
        try:
            stadium = Stadium.query.get(stadium_id)
            if stadium:
                return {
                    'id': stadium.id,
                    'name': stadium.name,
                    'location': stadium.location,
                    'capacity': stadium.capacity,
                    'description': getattr(stadium, 'description', ''),
                    'facilities': getattr(stadium, 'facilities', [])
                }
            return None
        except Exception as e:
            logger.error(f"Error fetching stadium {stadium_id}: {str(e)}")
            return None
    
    # Event Operations
    def get_all_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all events from Supabase"""
        try:
            events = Event.query.order_by(Event.event_date.desc()).limit(limit).all()
            return [{
                'id': event.id,
                'event_name': event.event_name,
                'event_date': event.event_date.isoformat() if event.event_date else None,
                'stadium_id': event.stadium_id,
                'stadium_name': event.stadium.name if event.stadium else 'Unknown',
                'status': getattr(event, 'status', 'scheduled'),
                'description': getattr(event, 'description', '')
            } for event in events]
        except Exception as e:
            logger.error(f"Error fetching events: {str(e)}")
            return []
    
    def get_upcoming_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get upcoming events"""
        try:
            today = date.today()
            events = Event.query.filter(
                Event.event_date >= today
            ).order_by(Event.event_date.asc()).limit(limit).all()
            
            return [{
                'id': event.id,
                'event_name': event.event_name,
                'event_date': event.event_date.isoformat() if event.event_date else None,
                'stadium_id': event.stadium_id,
                'stadium_name': event.stadium.name if event.stadium else 'Unknown',
                'status': getattr(event, 'status', 'scheduled')
            } for event in events]
        except Exception as e:
            logger.error(f"Error fetching upcoming events: {str(e)}")
            return []
    
    # Match Operations
    def get_live_matches(self) -> List[Dict[str, Any]]:
        """Get live matches"""
        try:
            matches = Match.query.filter_by(status='live').all()
            return [{
                'id': match.id,
                'team1': match.team1.name if match.team1 else 'Team 1',
                'team2': match.team2.name if match.team2 else 'Team 2',
                'team1_score': getattr(match, 'team1_score', 0),
                'team2_score': getattr(match, 'team2_score', 0),
                'status': match.status,
                'event_id': match.event_id,
                'current_over': getattr(match, 'current_over', '0.0'),
                'venue': match.event.stadium.name if match.event and match.event.stadium else 'Unknown'
            } for match in matches]
        except Exception as e:
            logger.error(f"Error fetching live matches: {str(e)}")
            return []
    
    def get_match_by_id(self, match_id: int) -> Optional[Dict[str, Any]]:
        """Get match details by ID"""
        try:
            match = Match.query.get(match_id)
            if match:
                return {
                    'id': match.id,
                    'team1': match.team1.name if match.team1 else 'Team 1',
                    'team2': match.team2.name if match.team2 else 'Team 2',
                    'team1_score': getattr(match, 'team1_score', 0),
                    'team2_score': getattr(match, 'team2_score', 0),
                    'status': match.status,
                    'event_id': match.event_id,
                    'current_over': getattr(match, 'current_over', '0.0'),
                    'venue': match.event.stadium.name if match.event and match.event.stadium else 'Unknown'
                }
            return None
        except Exception as e:
            logger.error(f"Error fetching match {match_id}: {str(e)}")
            return None
    
    # Customer Operations
    def get_customer_by_id(self, customer_id: int) -> Optional[Dict[str, Any]]:
        """Get customer by ID"""
        try:
            customer = Customer.query.get(customer_id)
            if customer:
                return {
                    'id': customer.id,
                    'name': customer.name,
                    'email': customer.email,
                    'phone': getattr(customer, 'phone', ''),
                    'membership_level': getattr(customer, 'membership_level', 'Standard'),
                    'created_at': customer.created_at.isoformat() if hasattr(customer, 'created_at') and customer.created_at else None
                }
            return None
        except Exception as e:
            logger.error(f"Error fetching customer {customer_id}: {str(e)}")
            return None
    
    def get_customer_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get customer by email"""
        try:
            customer = Customer.query.filter_by(email=email).first()
            if customer:
                return {
                    'id': customer.id,
                    'name': customer.name,
                    'email': customer.email,
                    'phone': getattr(customer, 'phone', ''),
                    'membership_level': getattr(customer, 'membership_level', 'Standard')
                }
            return None
        except Exception as e:
            logger.error(f"Error fetching customer by email {email}: {str(e)}")
            return None
    
    # Booking Operations
    def get_customer_bookings(self, customer_id: int) -> List[Dict[str, Any]]:
        """Get all bookings for a customer"""
        try:
            bookings = Booking.query.filter_by(customer_id=customer_id).order_by(Booking.booking_date.desc()).all()
            return [{
                'id': booking.id,
                'total_amount': float(booking.total_amount),
                'booking_date': booking.booking_date.isoformat() if booking.booking_date else None,
                'payment_status': booking.payment_status,
                'event_name': booking.event.event_name if hasattr(booking, 'event') and booking.event else 'Unknown Event',
                'tickets_count': len(booking.tickets) if hasattr(booking, 'tickets') else 0
            } for booking in bookings]
        except Exception as e:
            logger.error(f"Error fetching bookings for customer {customer_id}: {str(e)}")
            return []
    
    def get_booking_by_id(self, booking_id: int) -> Optional[Dict[str, Any]]:
        """Get booking details by ID"""
        try:
            booking = Booking.query.get(booking_id)
            if booking:
                return {
                    'id': booking.id,
                    'customer_id': booking.customer_id,
                    'total_amount': float(booking.total_amount),
                    'booking_date': booking.booking_date.isoformat() if booking.booking_date else None,
                    'payment_status': booking.payment_status,
                    'customer_name': booking.customer.name if booking.customer else 'Unknown',
                    'tickets': [{
                        'id': ticket.id,
                        'seat_number': ticket.seat.seat_number if ticket.seat else 'N/A',
                        'section': ticket.seat.section if ticket.seat else 'N/A',
                        'price': float(ticket.price) if hasattr(ticket, 'price') else 0.0
                    } for ticket in booking.tickets] if hasattr(booking, 'tickets') else []
                }
            return None
        except Exception as e:
            logger.error(f"Error fetching booking {booking_id}: {str(e)}")
            return None
    
    # Seat Operations
    def get_available_seats(self, event_id: int, section: str = None) -> List[Dict[str, Any]]:
        """Get available seats for an event"""
        try:
            # Get event to find stadium
            event = Event.query.get(event_id)
            if not event:
                return []
            
            # Base query for seats in the stadium
            query = Seat.query.filter_by(stadium_id=event.stadium_id)
            
            # Filter by section if provided
            if section:
                query = query.filter_by(section=section)
            
            # Get all seats
            all_seats = query.all()
            
            # Get booked seat IDs for this event
            booked_seat_ids = db.session.query(Ticket.seat_id).join(Booking).filter(
                Booking.event_id == event_id,
                Booking.payment_status == 'Completed'
            ).subquery()
            
            # Filter out booked seats
            available_seats = [seat for seat in all_seats if seat.id not in [row[0] for row in booked_seat_ids]]
            
            return [{
                'id': seat.id,
                'section': seat.section,
                'row_number': seat.row_number,
                'seat_number': seat.seat_number,
                'seat_type': seat.seat_type,
                'price': float(seat.price)
            } for seat in available_seats]
        except Exception as e:
            logger.error(f"Error fetching available seats for event {event_id}: {str(e)}")
            return []
    
    # Parking Operations
    def get_parking_availability(self, event_id: int) -> Dict[str, Any]:
        """Get parking availability for an event"""
        try:
            event = Event.query.get(event_id)
            if not event:
                return {'available': 0, 'total': 0, 'spots': []}
            
            # Get all parking spots for the stadium
            parking_spots = Parking.query.filter_by(stadium_id=event.stadium_id).all()
            
            # Get booked parking for this event
            booked_parking = ParkingBooking.query.filter_by(event_id=event_id).all()
            booked_spot_ids = [booking.parking_id for booking in booked_parking]
            
            available_spots = [spot for spot in parking_spots if spot.id not in booked_spot_ids]
            
            return {
                'available': len(available_spots),
                'total': len(parking_spots),
                'spots': [{
                    'id': spot.id,
                    'spot_number': spot.spot_number,
                    'spot_type': spot.spot_type,
                    'price': float(spot.price)
                } for spot in available_spots]
            }
        except Exception as e:
            logger.error(f"Error fetching parking availability for event {event_id}: {str(e)}")
            return {'available': 0, 'total': 0, 'spots': []}
    
    # Concession Operations
    def get_concession_menu(self, stadium_id: int) -> List[Dict[str, Any]]:
        """Get concession menu for a stadium"""
        try:
            concessions = Concession.query.filter_by(stadium_id=stadium_id).all()
            menu_items = []
            
            for concession in concessions:
                items = MenuItem.query.filter_by(concession_id=concession.id).all()
                for item in items:
                    menu_items.append({
                        'id': item.id,
                        'name': item.name,
                        'description': getattr(item, 'description', ''),
                        'price': float(item.price),
                        'category': getattr(item, 'category', 'Food'),
                        'available': getattr(item, 'available', True),
                        'concession_name': concession.name
                    })
            
            return menu_items
        except Exception as e:
            logger.error(f"Error fetching concession menu for stadium {stadium_id}: {str(e)}")
            return []
    
    # Analytics Operations
    def get_revenue_analytics(self, start_date: date = None, end_date: date = None) -> Dict[str, Any]:
        """Get revenue analytics from real data"""
        try:
            query = db.session.query(
                func.sum(Booking.total_amount).label('total_revenue'),
                func.count(Booking.id).label('total_bookings'),
                func.avg(Booking.total_amount).label('avg_booking_value')
            ).filter(Booking.payment_status == 'Completed')
            
            if start_date:
                query = query.filter(Booking.booking_date >= start_date)
            if end_date:
                query = query.filter(Booking.booking_date <= end_date)
            
            result = query.first()
            
            return {
                'total_revenue': float(result.total_revenue or 0),
                'total_bookings': int(result.total_bookings or 0),
                'average_booking_value': float(result.avg_booking_value or 0)
            }
        except Exception as e:
            logger.error(f"Error fetching revenue analytics: {str(e)}")
            return {'total_revenue': 0, 'total_bookings': 0, 'average_booking_value': 0}
    
    def get_popular_events(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get most popular events by booking count"""
        try:
            popular_events = db.session.query(
                Event.id,
                Event.event_name,
                func.count(Booking.id).label('booking_count'),
                func.sum(Booking.total_amount).label('total_revenue')
            ).join(Booking, Event.id == Booking.event_id)\
             .filter(Booking.payment_status == 'Completed')\
             .group_by(Event.id, Event.event_name)\
             .order_by(func.count(Booking.id).desc())\
             .limit(limit).all()
            
            return [{
                'event_id': event.id,
                'event_name': event.event_name,
                'booking_count': int(event.booking_count),
                'total_revenue': float(event.total_revenue or 0)
            } for event in popular_events]
        except Exception as e:
            logger.error(f"Error fetching popular events: {str(e)}")
            return []
    
    # Database Health Check
    def health_check(self) -> Dict[str, Any]:
        """Check database connection health"""
        try:
            # Test basic query
            result = db.session.execute(text('SELECT 1')).scalar()
            
            # Get table counts
            table_counts = {}
            models = [Customer, Stadium, Event, Match, Booking, Ticket, Seat]
            
            for model in models:
                try:
                    count = model.query.count()
                    table_counts[model.__tablename__] = count
                except Exception as e:
                    table_counts[model.__tablename__] = f"Error: {str(e)}"
            
            return {
                'status': 'healthy',
                'connection': 'active',
                'supabase_url': self.supabase_url,
                'table_counts': table_counts,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'connection': 'failed',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

# Global service instance
supabase_service = SupabaseService()
