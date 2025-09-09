# CricVerse Utility Functions
# Common functions to reduce code redundancy

import re
from flask import flash, request
from functools import wraps
from datetime import datetime
from sqlalchemy import func

def validate_email(email):
    """Validate email format"""
    email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return re.match(email_regex, email) is not None

def validate_phone(phone):
    """Validate phone number format"""
    if not phone:
        return True  # Optional field
    clean_phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    return len(clean_phone) >= 10

def validate_password_strength(password):
    """Validate password strength and return errors if any"""
    errors = []
    
    if len(password) < 8:
        errors.append('Password must be at least 8 characters long.')
    
    if not re.search(r'[A-Z]', password):
        errors.append('Password must contain at least one uppercase letter.')
    
    if not re.search(r'[a-z]', password):
        errors.append('Password must contain at least one lowercase letter.')
    
    if not re.search(r'[0-9]', password):
        errors.append('Password must contain at least one number.')
    
    return errors

def sanitize_input(text, max_length=None):
    """Clean and sanitize text input"""
    if not text:
        return ""
    
    # Strip whitespace
    text = text.strip()
    
    # Truncate if max_length specified
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text

def flash_errors(errors, category='danger'):
    """Flash multiple error messages"""
    for error in errors:
        flash(error, category)

def get_user_statistics(db, Customer):
    """Get comprehensive user statistics"""
    total_users = Customer.query.count()
    admin_users = Customer.query.filter_by(role='admin').count()
    stadium_owner_users = Customer.query.filter_by(role='stadium_owner').count()
    customer_users = Customer.query.filter_by(role='customer').count()
    
    return {
        'total_users': total_users,
        'admin_users': admin_users,
        'stadium_owner_users': stadium_owner_users,
        'customer_users': customer_users,
        'active_users': total_users  # For now, all users are considered active
    }

def get_analytics_data(db, Stadium, Event, Ticket, Order, ParkingBooking):
    """Get comprehensive analytics data"""
    from sqlalchemy import func
    
    # Basic counts
    total_stadiums = Stadium.query.count()
    total_events = Event.query.count()
    total_tickets_sold = Ticket.query.count()
    
    # Revenue calculations
    ticket_revenue = db.session.query(func.sum(Ticket.seat.has(price=func.coalesce(Ticket.seat.has().price, 0)))).scalar() or 0
    concession_revenue = db.session.query(func.sum(Order.total_amount)).scalar() or 0
    parking_revenue = db.session.query(func.sum(ParkingBooking.amount_paid)).scalar() or 0
    total_revenue = ticket_revenue + concession_revenue + parking_revenue
    
    # Stadium performance
    stadium_performance = []
    stadiums = Stadium.query.all()
    
    for stadium in stadiums:
        events_count = Event.query.filter_by(stadium_id=stadium.id).count()
        tickets_count = db.session.query(Ticket).join(Event).filter(Event.stadium_id == stadium.id).count()
        
        # Calculate utilization rate (simplified)
        utilization_rate = min(100, (tickets_count / max(stadium.capacity * events_count, 1)) * 100) if events_count > 0 else 0
        
        # Calculate revenue for this stadium (simplified)
        stadium_revenue = db.session.query(func.sum(Order.total_amount)).join(Event).filter(Event.stadium_id == stadium.id).scalar() or 0
        
        stadium_performance.append({
            'stadium': stadium,
            'utilization_rate': round(utilization_rate, 1),
            'revenue': stadium_revenue,
            'events_count': events_count,
            'tickets_sold': tickets_count
        })
    
    return {
        'total_stadiums': total_stadiums,
        'total_events': total_events,
        'total_tickets_sold': total_tickets_sold,
        'total_revenue': total_revenue,
        'ticket_revenue': ticket_revenue,
        'concession_revenue': concession_revenue,
        'parking_revenue': parking_revenue,
        'stadium_performance': stadium_performance,
        'avg_revenue_per_ticket': round(total_revenue / max(total_tickets_sold, 1), 2),
        'avg_attendance_per_event': round(total_tickets_sold / max(total_events, 1), 2)
    }

def calculate_pagination(total_items, page, per_page=10):
    """Calculate pagination parameters"""
    total_pages = (total_items + per_page - 1) // per_page
    offset = (page - 1) * per_page
    
    return {
        'total_pages': total_pages,
        'offset': offset,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_num': page - 1 if page > 1 else None,
        'next_num': page + 1 if page < total_pages else None
    }

def format_currency(amount):
    """Format currency consistently"""
    return f"${amount:,.2f}"

def format_datetime(dt, format_type='full'):
    """Format datetime consistently"""
    if not dt:
        return ""
    
    if format_type == 'date':
        return dt.strftime('%Y-%m-%d')
    elif format_type == 'time':
        return dt.strftime('%H:%M')
    elif format_type == 'short':
        return dt.strftime('%m/%d/%Y %H:%M')
    else:  # full
        return dt.strftime('%B %d, %Y at %H:%M')

def get_upcoming_events(Event, limit=5):
    """Get upcoming events consistently"""
    return Event.query.filter(
        Event.event_date >= datetime.utcnow().date()
    ).order_by(Event.event_date, Event.start_time).limit(limit).all()

def handle_form_errors(form_data, validation_rules):
    """Generic form validation handler"""
    errors = []
    
    for field, rules in validation_rules.items():
        value = form_data.get(field, '').strip()
        
        if rules.get('required') and not value:
            errors.append(f"{field.replace('_', ' ').title()} is required.")
            continue
        
        if not value:
            continue  # Skip validation for empty optional fields
        
        if 'min_length' in rules and len(value) < rules['min_length']:
            errors.append(f"{field.replace('_', ' ').title()} must be at least {rules['min_length']} characters long.")
        
        if 'max_length' in rules and len(value) > rules['max_length']:
            errors.append(f"{field.replace('_', ' ').title()} must be no more than {rules['max_length']} characters long.")
        
        if 'type' in rules:
            if rules['type'] == 'email' and not validate_email(value):
                errors.append(f"Please enter a valid email address.")
            elif rules['type'] == 'phone' and not validate_phone(value):
                errors.append(f"Please enter a valid phone number.")
    
    return errors

# Common validation rules
REGISTRATION_VALIDATION_RULES = {
    'name': {'required': True, 'min_length': 2, 'max_length': 100},
    'email': {'required': True, 'type': 'email', 'max_length': 100},
    'phone': {'type': 'phone', 'max_length': 20},
    'password': {'required': True, 'min_length': 8}
}

STADIUM_VALIDATION_RULES = {
    'name': {'required': True, 'min_length': 2, 'max_length': 100},
    'location': {'required': True, 'min_length': 2, 'max_length': 100},
    'capacity': {'required': True},
    'contact_number': {'type': 'phone', 'max_length': 20}
}

EVENT_VALIDATION_RULES = {
    'event_name': {'required': True, 'min_length': 2, 'max_length': 100},
    'event_date': {'required': True},
    'start_time': {'required': True},
    'stadium_id': {'required': True}
}
