"""
Advanced Analytics Dashboard for CricVerse
Provides comprehensive analytics for stadium owners and admins
"""

import os
import json
import logging
from datetime import datetime, timedelta, date
from sqlalchemy import func, and_, or_, extract, text
from collections import defaultdict
import calendar

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CricVerseAnalytics:
    """Advanced analytics engine for CricVerse"""
    
    def __init__(self):
        self.cache_timeout = 3600  # 1 hour cache
    
    def get_revenue_analytics(self, stadium_id=None, start_date=None, end_date=None):
        """Get comprehensive revenue analytics"""
        try:
            from app import db, Booking, PaymentTransaction, Event
            from enhanced_models import BookingAnalytics
            
            # Default to last 30 days if no date range provided
            if not end_date:
                end_date = date.today()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Base query
            query = db.session.query(
                func.date(Booking.booking_date).label('date'),
                func.sum(Booking.total_amount).label('daily_revenue'),
                func.count(Booking.id).label('daily_bookings'),
                func.avg(Booking.total_amount).label('avg_order_value')
            )
            
            # Filter by stadium if provided
            if stadium_id:
                query = query.join(Event).filter(Event.stadium_id == stadium_id)
            
            # Filter by date range
            query = query.filter(
                func.date(Booking.booking_date).between(start_date, end_date)
            ).group_by(func.date(Booking.booking_date)).order_by(func.date(Booking.booking_date))
            
            daily_data = query.all()
            
            # Calculate summary metrics
            total_revenue = sum(day.daily_revenue or 0 for day in daily_data)
            total_bookings = sum(day.daily_bookings or 0 for day in daily_data)
            avg_daily_revenue = total_revenue / len(daily_data) if daily_data else 0
            
            # Format data for frontend
            revenue_trend = []
            for day in daily_data:
                revenue_trend.append({
                    'date': day.date.isoformat(),
                    'revenue': float(day.daily_revenue or 0),
                    'bookings': int(day.daily_bookings or 0),
                    'avg_order': float(day.avg_order_value or 0)
                })
            
            # Get payment method breakdown
            payment_methods = self._get_payment_method_breakdown(stadium_id, start_date, end_date)
            
            # Get monthly comparison
            monthly_comparison = self._get_monthly_revenue_comparison(stadium_id)
            
            return {
                'summary': {
                    'total_revenue': float(total_revenue),
                    'total_bookings': int(total_bookings),
                    'avg_daily_revenue': float(avg_daily_revenue),
                    'avg_order_value': float(total_revenue / total_bookings) if total_bookings > 0 else 0,
                    'period': f"{start_date} to {end_date}"
                },
                'revenue_trend': revenue_trend,
                'payment_methods': payment_methods,
                'monthly_comparison': monthly_comparison
            }
            
        except Exception as e:
            logger.error(f"Error getting revenue analytics: {e}")
            return {'error': str(e)}
    
    def get_customer_analytics(self, stadium_id=None, start_date=None, end_date=None):
        """Get customer behavior and demographics analytics"""
        try:
            from app import db, Customer, Booking, Event
            
            # Default date range
            if not end_date:
                end_date = date.today()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Customer acquisition over time
            acquisition_query = db.session.query(
                func.date(Customer.id).label('date'),  # Using id as proxy for creation date
                func.count(Customer.id).label('new_customers')
            ).group_by(func.date(Customer.id)).order_by(func.date(Customer.id))
            
            # Customer segments by booking frequency
            booking_frequency = db.session.query(
                Customer.membership_level,
                func.count(Booking.id).label('total_bookings'),
                func.avg(Booking.total_amount).label('avg_spending'),
                func.count(func.distinct(Customer.id)).label('customer_count')
            ).join(Booking, Customer.id == Booking.customer_id)
            
            if stadium_id:
                booking_frequency = booking_frequency.join(Event).filter(Event.stadium_id == stadium_id)
            
            booking_frequency = booking_frequency.filter(
                func.date(Booking.booking_date).between(start_date, end_date)
            ).group_by(Customer.membership_level).all()
            
            # Top customers by spending
            top_customers = db.session.query(
                Customer.name,
                Customer.membership_level,
                func.sum(Booking.total_amount).label('total_spent'),
                func.count(Booking.id).label('booking_count')
            ).join(Booking, Customer.id == Booking.customer_id)
            
            if stadium_id:
                top_customers = top_customers.join(Event).filter(Event.stadium_id == stadium_id)
            
            top_customers = top_customers.filter(
                func.date(Booking.booking_date).between(start_date, end_date)
            ).group_by(Customer.id, Customer.name, Customer.membership_level)\
             .order_by(func.sum(Booking.total_amount).desc()).limit(10).all()
            
            # Customer retention analysis
            retention_data = self._calculate_customer_retention(stadium_id, start_date, end_date)
            
            return {
                'customer_segments': [
                    {
                        'membership_level': seg.membership_level or 'Basic',
                        'customer_count': int(seg.customer_count),
                        'total_bookings': int(seg.total_bookings),
                        'avg_spending': float(seg.avg_spending or 0)
                    } for seg in booking_frequency
                ],
                'top_customers': [
                    {
                        'name': customer.name,
                        'membership_level': customer.membership_level or 'Basic',
                        'total_spent': float(customer.total_spent),
                        'booking_count': int(customer.booking_count)
                    } for customer in top_customers
                ],
                'retention': retention_data
            }
            
        except Exception as e:
            logger.error(f"Error getting customer analytics: {e}")
            return {'error': str(e)}
    
    def get_stadium_utilization(self, stadium_id, start_date=None, end_date=None):
        """Get stadium utilization and occupancy analytics"""
        try:
            from app import db, Stadium, Event, Seat, Ticket
            
            stadium = Stadium.query.get(stadium_id)
            if not stadium:
                return {'error': 'Stadium not found'}
            
            # Default date range
            if not end_date:
                end_date = date.today()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Total stadium capacity
            total_capacity = stadium.capacity
            total_seats = Seat.query.filter_by(stadium_id=stadium_id).count()
            
            # Events and occupancy over time
            events = Event.query.filter(
                Event.stadium_id == stadium_id,
                Event.event_date.between(start_date, end_date)
            ).all()
            
            utilization_data = []
            total_tickets_sold = 0
            total_possible_tickets = 0
            
            for event in events:
                # Get tickets sold for this event
                tickets_sold = Ticket.query.filter(
                    Ticket.event_id == event.id,
                    Ticket.ticket_status == 'Booked'
                ).count()
                
                occupancy_rate = (tickets_sold / total_seats * 100) if total_seats > 0 else 0
                
                utilization_data.append({
                    'event_id': event.id,
                    'event_name': event.event_name,
                    'event_date': event.event_date.isoformat(),
                    'tickets_sold': tickets_sold,
                    'capacity': total_seats,
                    'occupancy_rate': round(occupancy_rate, 2),
                    'revenue': float(sum(ticket.seat.price for ticket in Ticket.query.filter(
                        Ticket.event_id == event.id,
                        Ticket.ticket_status == 'Booked'
                    ).join(Seat).all()) if tickets_sold > 0 else 0)
                })
                
                total_tickets_sold += tickets_sold
                total_possible_tickets += total_seats
            
            # Average utilization
            avg_occupancy = (total_tickets_sold / total_possible_tickets * 100) if total_possible_tickets > 0 else 0
            
            # Section-wise popularity
            section_popularity = self._get_section_popularity(stadium_id, start_date, end_date)
            
            # Peak times analysis
            peak_times = self._get_peak_booking_times(stadium_id, start_date, end_date)
            
            return {
                'stadium_info': {
                    'name': stadium.name,
                    'capacity': total_capacity,
                    'total_seats': total_seats
                },
                'utilization_summary': {
                    'avg_occupancy_rate': round(avg_occupancy, 2),
                    'total_events': len(events),
                    'total_tickets_sold': total_tickets_sold,
                    'revenue_per_event': float(sum(event['revenue'] for event in utilization_data) / len(events)) if events else 0
                },
                'event_utilization': utilization_data,
                'section_popularity': section_popularity,
                'peak_times': peak_times
            }
            
        except Exception as e:
            logger.error(f"Error getting stadium utilization: {e}")
            return {'error': str(e)}
    
    def get_booking_patterns(self, stadium_id=None, start_date=None, end_date=None):
        """Get booking pattern analytics"""
        try:
            from app import db, Booking, Event
            
            # Default date range
            if not end_date:
                end_date = date.today()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Booking timing patterns (how far in advance)
            booking_advance_query = db.session.query(
                func.extract('day', Event.event_date - func.date(Booking.booking_date)).label('days_advance'),
                func.count(Booking.id).label('booking_count')
            ).join(Event, Booking.id == Event.id)  # This might need adjustment based on your relationship
            
            if stadium_id:
                booking_advance_query = booking_advance_query.filter(Event.stadium_id == stadium_id)
            
            advance_bookings = booking_advance_query.filter(
                func.date(Booking.booking_date).between(start_date, end_date)
            ).group_by('days_advance').order_by('days_advance').all()
            
            # Day of week patterns
            dow_patterns = db.session.query(
                func.extract('dow', Booking.booking_date).label('day_of_week'),
                func.count(Booking.id).label('booking_count'),
                func.avg(Booking.total_amount).label('avg_amount')
            )
            
            if stadium_id:
                dow_patterns = dow_patterns.join(Event).filter(Event.stadium_id == stadium_id)
            
            dow_patterns = dow_patterns.filter(
                func.date(Booking.booking_date).between(start_date, end_date)
            ).group_by('day_of_week').order_by('day_of_week').all()
            
            # Hour of day patterns
            hour_patterns = db.session.query(
                func.extract('hour', Booking.booking_date).label('hour'),
                func.count(Booking.id).label('booking_count')
            )
            
            if stadium_id:
                hour_patterns = hour_patterns.join(Event).filter(Event.stadium_id == stadium_id)
            
            hour_patterns = hour_patterns.filter(
                func.date(Booking.booking_date).between(start_date, end_date)
            ).group_by('hour').order_by('hour').all()
            
            # Format the data
            days_of_week = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            
            return {
                'advance_booking': [
                    {
                        'days_advance': int(booking.days_advance),
                        'booking_count': int(booking.booking_count)
                    } for booking in advance_bookings if booking.days_advance is not None
                ],
                'day_of_week': [
                    {
                        'day': days_of_week[int(pattern.day_of_week)],
                        'booking_count': int(pattern.booking_count),
                        'avg_amount': float(pattern.avg_amount or 0)
                    } for pattern in dow_patterns
                ],
                'hourly': [
                    {
                        'hour': int(pattern.hour),
                        'booking_count': int(pattern.booking_count)
                    } for pattern in hour_patterns
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting booking patterns: {e}")
            return {'error': str(e)}
    
    def get_financial_dashboard(self, stadium_id=None):
        """Get comprehensive financial dashboard"""
        try:
            # Current month metrics
            current_month_start = date.today().replace(day=1)
            current_month_end = date.today()
            
            # Previous month for comparison
            if current_month_start.month == 1:
                prev_month_start = current_month_start.replace(year=current_month_start.year - 1, month=12)
                prev_month_end = current_month_start - timedelta(days=1)
            else:
                prev_month_start = current_month_start.replace(month=current_month_start.month - 1)
                prev_month_end = current_month_start - timedelta(days=1)
            
            # Get revenue analytics for both periods
            current_revenue = self.get_revenue_analytics(stadium_id, current_month_start, current_month_end)
            previous_revenue = self.get_revenue_analytics(stadium_id, prev_month_start, prev_month_end)
            
            # Calculate growth rates
            current_total = current_revenue['summary']['total_revenue']
            previous_total = previous_revenue['summary']['total_revenue']
            revenue_growth = ((current_total - previous_total) / previous_total * 100) if previous_total > 0 else 0
            
            # Get top performing events
            top_events = self._get_top_performing_events(stadium_id)
            
            # Get cost analysis (if available)
            cost_breakdown = self._get_cost_breakdown(stadium_id)
            
            # Forecast next month (simple trend-based)
            forecast = self._generate_revenue_forecast(stadium_id)
            
            return {
                'current_month': current_revenue['summary'],
                'previous_month': previous_revenue['summary'],
                'growth_metrics': {
                    'revenue_growth': round(revenue_growth, 2),
                    'booking_growth': round(
                        ((current_revenue['summary']['total_bookings'] - 
                          previous_revenue['summary']['total_bookings']) / 
                         previous_revenue['summary']['total_bookings'] * 100) 
                        if previous_revenue['summary']['total_bookings'] > 0 else 0, 2
                    )
                },
                'top_events': top_events,
                'cost_breakdown': cost_breakdown,
                'forecast': forecast
            }
            
        except Exception as e:
            logger.error(f"Error getting financial dashboard: {e}")
            return {'error': str(e)}
    
    def _get_payment_method_breakdown(self, stadium_id, start_date, end_date):
        """Get payment method breakdown"""
        try:
            from app import db, Booking, Event
            from enhanced_models import PaymentTransaction
            
            query = db.session.query(
                PaymentTransaction.payment_method,
                func.count(PaymentTransaction.id).label('count'),
                func.sum(PaymentTransaction.amount).label('total_amount')
            ).join(Booking, PaymentTransaction.booking_id == Booking.id)
            
            if stadium_id:
                query = query.join(Event).filter(Event.stadium_id == stadium_id)
            
            query = query.filter(
                func.date(Booking.booking_date).between(start_date, end_date),
                PaymentTransaction.payment_status == 'succeeded'
            ).group_by(PaymentTransaction.payment_method)
            
            results = query.all()
            
            return [
                {
                    'method': result.payment_method or 'Card',
                    'count': int(result.count),
                    'amount': float(result.total_amount or 0)
                } for result in results
            ]
            
        except Exception as e:
            logger.error(f"Error getting payment method breakdown: {e}")
            return []
    
    def _get_monthly_revenue_comparison(self, stadium_id):
        """Get monthly revenue comparison for the last 12 months"""
        try:
            from app import db, Booking, Event
            
            end_date = date.today()
            start_date = end_date - timedelta(days=365)
            
            query = db.session.query(
                func.extract('year', Booking.booking_date).label('year'),
                func.extract('month', Booking.booking_date).label('month'),
                func.sum(Booking.total_amount).label('revenue'),
                func.count(Booking.id).label('bookings')
            )
            
            if stadium_id:
                query = query.join(Event).filter(Event.stadium_id == stadium_id)
            
            query = query.filter(
                func.date(Booking.booking_date).between(start_date, end_date)
            ).group_by(
                func.extract('year', Booking.booking_date),
                func.extract('month', Booking.booking_date)
            ).order_by('year', 'month')
            
            results = query.all()
            
            monthly_data = []
            for result in results:
                month_name = calendar.month_name[int(result.month)]
                monthly_data.append({
                    'month': f"{month_name} {int(result.year)}",
                    'revenue': float(result.revenue or 0),
                    'bookings': int(result.bookings or 0)
                })
            
            return monthly_data
            
        except Exception as e:
            logger.error(f"Error getting monthly comparison: {e}")
            return []
    
    def _calculate_customer_retention(self, stadium_id, start_date, end_date):
        """Calculate customer retention metrics"""
        try:
            from app import db, Customer, Booking, Event
            
            # This is a simplified retention calculation
            # In a real implementation, you'd want more sophisticated cohort analysis
            
            # Get customers who made bookings in the period
            query = db.session.query(Customer.id).join(Booking)
            
            if stadium_id:
                query = query.join(Event).filter(Event.stadium_id == stadium_id)
            
            period_customers = set(customer.id for customer in query.filter(
                func.date(Booking.booking_date).between(start_date, end_date)
            ).distinct().all())
            
            # Get customers who made bookings before the period
            prev_start = start_date - timedelta(days=30)
            prev_customers = set(customer.id for customer in query.filter(
                func.date(Booking.booking_date).between(prev_start, start_date)
            ).distinct().all())
            
            # Calculate retention
            retained_customers = period_customers.intersection(prev_customers)
            retention_rate = (len(retained_customers) / len(prev_customers) * 100) if prev_customers else 0
            
            return {
                'retention_rate': round(retention_rate, 2),
                'total_customers': len(period_customers),
                'retained_customers': len(retained_customers),
                'new_customers': len(period_customers - prev_customers)
            }
            
        except Exception as e:
            logger.error(f"Error calculating retention: {e}")
            return {'retention_rate': 0, 'total_customers': 0, 'retained_customers': 0, 'new_customers': 0}
    
    def _get_section_popularity(self, stadium_id, start_date, end_date):
        """Get section-wise popularity"""
        try:
            from app import db, Seat, Ticket, Event
            
            query = db.session.query(
                Seat.section,
                func.count(Ticket.id).label('tickets_sold'),
                func.avg(Seat.price).label('avg_price')
            ).join(Ticket, Seat.id == Ticket.seat_id).join(Event, Ticket.event_id == Event.id)
            
            query = query.filter(
                Seat.stadium_id == stadium_id,
                Event.event_date.between(start_date, end_date),
                Ticket.ticket_status == 'Booked'
            ).group_by(Seat.section).order_by(func.count(Ticket.id).desc())
            
            results = query.all()
            
            return [
                {
                    'section': result.section,
                    'tickets_sold': int(result.tickets_sold),
                    'avg_price': float(result.avg_price or 0)
                } for result in results
            ]
            
        except Exception as e:
            logger.error(f"Error getting section popularity: {e}")
            return []
    
    def _get_peak_booking_times(self, stadium_id, start_date, end_date):
        """Get peak booking times"""
        try:
            from app import db, Booking, Event
            
            query = db.session.query(
                func.extract('hour', Booking.booking_date).label('hour'),
                func.count(Booking.id).label('booking_count')
            )
            
            if stadium_id:
                query = query.join(Event).filter(Event.stadium_id == stadium_id)
            
            query = query.filter(
                func.date(Booking.booking_date).between(start_date, end_date)
            ).group_by('hour').order_by(func.count(Booking.id).desc())
            
            results = query.limit(5).all()
            
            return [
                {
                    'hour': int(result.hour),
                    'booking_count': int(result.booking_count)
                } for result in results if result.hour is not None
            ]
            
        except Exception as e:
            logger.error(f"Error getting peak times: {e}")
            return []
    
    def _get_top_performing_events(self, stadium_id):
        """Get top performing events by revenue"""
        try:
            from app import db, Event, Booking
            
            query = db.session.query(
                Event.event_name,
                Event.event_date,
                func.sum(Booking.total_amount).label('total_revenue'),
                func.count(Booking.id).label('booking_count')
            ).join(Booking)  # This might need adjustment based on relationships
            
            if stadium_id:
                query = query.filter(Event.stadium_id == stadium_id)
            
            # Get events from last 90 days
            start_date = date.today() - timedelta(days=90)
            query = query.filter(Event.event_date >= start_date)
            
            query = query.group_by(Event.id, Event.event_name, Event.event_date)\
                         .order_by(func.sum(Booking.total_amount).desc()).limit(10)
            
            results = query.all()
            
            return [
                {
                    'event_name': result.event_name,
                    'event_date': result.event_date.isoformat(),
                    'revenue': float(result.total_revenue or 0),
                    'bookings': int(result.booking_count or 0)
                } for result in results
            ]
            
        except Exception as e:
            logger.error(f"Error getting top events: {e}")
            return []
    
    def _get_cost_breakdown(self, stadium_id):
        """Get cost breakdown (placeholder for future implementation)"""
        # This would integrate with accounting systems or cost tracking
        return {
            'operational_costs': 15000,
            'maintenance': 5000,
            'staff': 20000,
            'utilities': 3000,
            'marketing': 2000
        }
    
    def _generate_revenue_forecast(self, stadium_id):
        """Generate simple revenue forecast"""
        try:
            # Get last 3 months of revenue data
            end_date = date.today()
            start_date = end_date - timedelta(days=90)
            
            revenue_data = self.get_revenue_analytics(stadium_id, start_date, end_date)
            
            if not revenue_data.get('revenue_trend'):
                return {'forecast_revenue': 0, 'confidence': 0}
            
            # Simple moving average forecast
            recent_revenues = [day['revenue'] for day in revenue_data['revenue_trend'][-30:]]
            avg_daily_revenue = sum(recent_revenues) / len(recent_revenues) if recent_revenues else 0
            
            # Forecast next month (30 days)
            forecast_revenue = avg_daily_revenue * 30
            
            # Simple confidence based on revenue stability
            revenue_std = (sum((x - avg_daily_revenue) ** 2 for x in recent_revenues) / len(recent_revenues)) ** 0.5 if recent_revenues else 0
            confidence = max(0, min(100, 100 - (revenue_std / avg_daily_revenue * 100))) if avg_daily_revenue > 0 else 0
            
            return {
                'forecast_revenue': round(forecast_revenue, 2),
                'confidence': round(confidence, 2)
            }
            
        except Exception as e:
            logger.error(f"Error generating forecast: {e}")
            return {'forecast_revenue': 0, 'confidence': 0}


# Initialize global analytics instance
cricverse_analytics = CricVerseAnalytics()


# Flask route handlers for analytics API
def get_analytics_data(analytics_type, stadium_id=None):
    """Main analytics data retrieval function"""
    try:
        if analytics_type == 'revenue':
            return cricverse_analytics.get_revenue_analytics(stadium_id)
        elif analytics_type == 'customers':
            return cricverse_analytics.get_customer_analytics(stadium_id)
        elif analytics_type == 'utilization':
            return cricverse_analytics.get_stadium_utilization(stadium_id)
        elif analytics_type == 'patterns':
            return cricverse_analytics.get_booking_patterns(stadium_id)
        elif analytics_type == 'financial':
            return cricverse_analytics.get_financial_dashboard(stadium_id)
        else:
            return {'error': f'Unknown analytics type: {analytics_type}'}
    
    except Exception as e:
        logger.error(f"Error getting analytics data: {e}")
        return {'error': str(e)}