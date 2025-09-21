"""
Admin Routes for CricVerse
Comprehensive admin panel with full CRUD operations
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import (
    Customer, Stadium, Event, Booking, Ticket, Seat, 
    Concession, MenuItem, Parking, Team, Player
)
from datetime import datetime, timedelta
import json

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access the admin panel.', 'error')
            return redirect(url_for('auth.login'))
        
        if not hasattr(current_user, 'role') or current_user.role not in ['admin', 'stadium_owner']:
            flash('Admin access required.', 'error')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function

def stadium_owner_required(f):
    """Decorator to require stadium owner access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this area.', 'error')
            return redirect(url_for('auth.login'))
        
        if not hasattr(current_user, 'role') or current_user.role not in ['admin', 'stadium_owner']:
            flash('Stadium owner access required.', 'error')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function

# Main Admin Dashboard
@admin_bp.route('/')
@admin_required
def dashboard():
    """Main admin dashboard"""
    try:
        # Get dashboard statistics
        stats = {
            'total_customers': Customer.query.count(),
            'total_stadiums': Stadium.query.count(),
            'total_events': Event.query.count(),
            'total_bookings': Booking.query.count(),
            'total_tickets': Ticket.query.count(),
            'total_revenue': db.session.query(db.func.sum(Booking.total_amount)).scalar() or 0,
            'recent_bookings': Booking.query.order_by(Booking.booking_date.desc()).limit(10).all(),
            'upcoming_events': Event.query.filter(Event.event_date >= datetime.now()).order_by(Event.event_date).limit(5).all()
        }
        return render_template('admin_dashboard.html', stats=stats)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('admin_dashboard.html', stats={})

@admin_bp.route('/profile')
@admin_required
def profile():
    """Admin profile page"""
    return render_template('admin_profile.html')

@admin_bp.route('/analytics')
@admin_required
def analytics():
    """Admin analytics page"""
    try:
        # Calculate analytics data
        analytics_data = {
            'bookings_by_month': [],
            'revenue_by_stadium': [],
            'popular_events': [],
            'customer_growth': []
        }
        
        # Get bookings by month for the last 12 months
        for i in range(12):
            month_start = datetime.now().replace(day=1) - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            bookings_count = Booking.query.filter(
                Booking.booking_date >= month_start,
                Booking.booking_date < month_end
            ).count()
            analytics_data['bookings_by_month'].append({
                'month': month_start.strftime('%B %Y'),
                'bookings': bookings_count
            })
        
        return render_template('admin_analytics.html', analytics=analytics_data)
    except Exception as e:
        flash(f'Error loading analytics: {str(e)}', 'error')
        return render_template('admin_analytics.html', analytics={})

# Stadium Management
@admin_bp.route('/stadiums')
@admin_required
def stadiums_overview():
    """Stadiums overview page"""
    stadiums = Stadium.query.all()
    return render_template('admin_stadiums_overview.html', stadiums=stadiums)

@admin_bp.route('/stadiums/add')
@admin_required
def add_stadium():
    """Add new stadium page"""
    return render_template('admin_add_stadium.html')

@admin_bp.route('/stadiums/add', methods=['POST'])
@admin_required
def create_stadium():
    """Create new stadium"""
    try:
        stadium = Stadium(
            name=request.form['name'],
            location=request.form['location'],
            capacity=int(request.form['capacity']),
            facilities=request.form.get('facilities', ''),
            description=request.form.get('description', '')
        )
        db.session.add(stadium)
        db.session.commit()
        flash('Stadium created successfully!', 'success')
        return redirect(url_for('admin.stadiums_overview'))
    except Exception as e:
        flash(f'Error creating stadium: {str(e)}', 'error')
        return render_template('admin_add_stadium.html')

@admin_bp.route('/stadiums/<int:stadium_id>/edit')
@admin_required
def edit_stadium(stadium_id):
    """Edit stadium page"""
    stadium = Stadium.query.get_or_404(stadium_id)
    return render_template('admin_edit_stadium.html', stadium=stadium)

@admin_bp.route('/stadiums/<int:stadium_id>/edit', methods=['POST'])
@admin_required
def update_stadium(stadium_id):
    """Update stadium"""
    try:
        stadium = Stadium.query.get_or_404(stadium_id)
        stadium.name = request.form['name']
        stadium.location = request.form['location']
        stadium.capacity = int(request.form['capacity'])
        stadium.facilities = request.form.get('facilities', '')
        stadium.description = request.form.get('description', '')
        db.session.commit()
        flash('Stadium updated successfully!', 'success')
        return redirect(url_for('admin.stadiums_overview'))
    except Exception as e:
        flash(f'Error updating stadium: {str(e)}', 'error')
        return redirect(url_for('admin.edit_stadium', stadium_id=stadium_id))

@admin_bp.route('/stadiums/<int:stadium_id>/manage')
@admin_required
def manage_stadium(stadium_id):
    """Manage stadium page"""
    stadium = Stadium.query.get_or_404(stadium_id)
    return render_template('admin_manage_stadium.html', stadium=stadium)

@admin_bp.route('/stadiums/<int:stadium_id>/analytics')
@admin_required
def stadium_analytics(stadium_id):
    """Stadium analytics page"""
    stadium = Stadium.query.get_or_404(stadium_id)
    # Get stadium-specific analytics
    analytics = {
        'total_events': Event.query.filter_by(stadium_id=stadium_id).count(),
        'total_bookings': Booking.query.join(Event).filter(Event.stadium_id == stadium_id).count(),
        'total_revenue': db.session.query(db.func.sum(Booking.total_amount)).join(Event).filter(Event.stadium_id == stadium_id).scalar() or 0,
        'capacity_utilization': 0  # Calculate based on bookings vs capacity
    }
    return render_template('admin_stadium_analytics.html', stadium=stadium, analytics=analytics)

# Event Management
@admin_bp.route('/events')
@admin_required
def events_overview():
    """Events overview page"""
    events = Event.query.order_by(Event.event_date.desc()).all()
    return render_template('admin_events_overview.html', events=events)

@admin_bp.route('/events/add')
@admin_required
def add_event():
    """Add new event page"""
    stadiums = Stadium.query.all()
    teams = Team.query.all()
    return render_template('admin_add_event.html', stadiums=stadiums, teams=teams)

@admin_bp.route('/events/add', methods=['POST'])
@admin_required
def create_event():
    """Create new event"""
    try:
        event = Event(
            name=request.form['name'],
            event_date=datetime.strptime(request.form['event_date'], '%Y-%m-%d'),
            stadium_id=int(request.form['stadium_id']),
            home_team_id=request.form.get('home_team_id'),
            away_team_id=request.form.get('away_team_id'),
            ticket_price=float(request.form['ticket_price']),
            description=request.form.get('description', '')
        )
        db.session.add(event)
        db.session.commit()
        flash('Event created successfully!', 'success')
        return redirect(url_for('admin.events_overview'))
    except Exception as e:
        flash(f'Error creating event: {str(e)}', 'error')
        stadiums = Stadium.query.all()
        teams = Team.query.all()
        return render_template('admin_add_event.html', stadiums=stadiums, teams=teams)

# Booking Management
@admin_bp.route('/bookings')
@admin_required
def bookings_overview():
    """Bookings overview page"""
    bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(100).all()
    return render_template('admin_bookings_overview.html', bookings=bookings)

# Concession Management
@admin_bp.route('/concessions')
@admin_required
def concessions_overview():
    """Concessions overview page"""
    concessions = Concession.query.all()
    return render_template('admin_concessions_overview.html', concessions=concessions)

@admin_bp.route('/concessions/add')
@admin_required
def add_concession():
    """Add new concession page"""
    stadiums = Stadium.query.all()
    return render_template('admin_add_concession.html', stadiums=stadiums)

@admin_bp.route('/concessions/add', methods=['POST'])
@admin_required
def create_concession():
    """Create new concession"""
    try:
        concession = Concession(
            name=request.form['name'],
            type=request.form['type'],
            location=request.form['location'],
            stadium_id=int(request.form['stadium_id']),
            description=request.form.get('description', '')
        )
        db.session.add(concession)
        db.session.commit()
        flash('Concession created successfully!', 'success')
        return redirect(url_for('admin.concessions_overview'))
    except Exception as e:
        flash(f'Error creating concession: {str(e)}', 'error')
        stadiums = Stadium.query.all()
        return render_template('admin_add_concession.html', stadiums=stadiums)

@admin_bp.route('/concessions/<int:concession_id>/menu/add')
@admin_required
def add_menu_item(concession_id):
    """Add menu item page"""
    concession = Concession.query.get_or_404(concession_id)
    return render_template('admin_add_menu_item.html', concession=concession)

@admin_bp.route('/concessions/<int:concession_id>/menu/add', methods=['POST'])
@admin_required
def create_menu_item(concession_id):
    """Create new menu item"""
    try:
        menu_item = MenuItem(
            name=request.form['name'],
            category=request.form['category'],
            price=float(request.form['price']),
            concession_id=concession_id,
            description=request.form.get('description', '')
        )
        db.session.add(menu_item)
        db.session.commit()
        flash('Menu item created successfully!', 'success')
        return redirect(url_for('admin.concessions_overview'))
    except Exception as e:
        flash(f'Error creating menu item: {str(e)}', 'error')
        concession = Concession.query.get_or_404(concession_id)
        return render_template('admin_add_menu_item.html', concession=concession)

# Parking Management
@admin_bp.route('/parking')
@admin_required
def parking_overview():
    """Parking overview page"""
    parking_areas = Parking.query.all()
    return render_template('admin_parking_overview.html', parking_areas=parking_areas)

@admin_bp.route('/parking/add')
@admin_required
def add_parking():
    """Add new parking area page"""
    stadiums = Stadium.query.all()
    return render_template('admin_add_parking.html', stadiums=stadiums)

@admin_bp.route('/parking/add', methods=['POST'])
@admin_required
def create_parking():
    """Create new parking area"""
    try:
        parking = Parking(
            name=request.form['name'],
            location=request.form['location'],
            capacity=int(request.form['capacity']),
            price_per_hour=float(request.form['price_per_hour']),
            stadium_id=int(request.form['stadium_id'])
        )
        db.session.add(parking)
        db.session.commit()
        flash('Parking area created successfully!', 'success')
        return redirect(url_for('admin.parking_overview'))
    except Exception as e:
        flash(f'Error creating parking area: {str(e)}', 'error')
        stadiums = Stadium.query.all()
        return render_template('admin_add_parking.html', stadiums=stadiums)

# Seat Management
@admin_bp.route('/stadiums/<int:stadium_id>/seats/add')
@admin_required
def add_seats(stadium_id):
    """Add seats page"""
    stadium = Stadium.query.get_or_404(stadium_id)
    return render_template('admin_add_seats.html', stadium=stadium)

@admin_bp.route('/stadiums/<int:stadium_id>/seats/add', methods=['POST'])
@admin_required
def create_seats(stadium_id):
    """Create seats in bulk"""
    try:
        section = request.form['section']
        start_row = int(request.form['start_row'])
        end_row = int(request.form['end_row'])
        seats_per_row = int(request.form['seats_per_row'])
        seat_type = request.form['seat_type']
        price = float(request.form['price'])
        
        seats_created = 0
        for row in range(start_row, end_row + 1):
            for seat_num in range(1, seats_per_row + 1):
                seat = Seat(
                    section=section,
                    row_number=str(row),
                    seat_number=str(seat_num),
                    seat_type=seat_type,
                    price=price,
                    stadium_id=stadium_id
                )
                db.session.add(seat)
                seats_created += 1
        
        db.session.commit()
        flash(f'{seats_created} seats created successfully!', 'success')
        return redirect(url_for('admin.manage_stadium', stadium_id=stadium_id))
    except Exception as e:
        flash(f'Error creating seats: {str(e)}', 'error')
        stadium = Stadium.query.get_or_404(stadium_id)
        return render_template('admin_add_seats.html', stadium=stadium)

# User Management
@admin_bp.route('/users')
@admin_required
def user_management():
    """User management page"""
    users = Customer.query.all()
    return render_template('admin_user_management.html', users=users)

@admin_bp.route('/users/<int:user_id>/role', methods=['POST'])
@admin_required
def update_user_role(user_id):
    """Update user role"""
    try:
        user = Customer.query.get_or_404(user_id)
        new_role = request.form['role']
        if new_role in ['customer', 'stadium_owner', 'admin']:
            user.role = new_role
            db.session.commit()
            flash(f'User role updated to {new_role}!', 'success')
        else:
            flash('Invalid role specified!', 'error')
    except Exception as e:
        flash(f'Error updating user role: {str(e)}', 'error')
    
    return redirect(url_for('admin.user_management'))

# Stadium Owner Dashboard
@admin_bp.route('/stadium-owner')
@stadium_owner_required
def stadium_owner_dashboard():
    """Stadium owner dashboard"""
    if current_user.role == 'admin':
        # Admin can see all stadiums
        stadiums = Stadium.query.all()
    else:
        # Stadium owners see only their stadiums
        stadiums = Stadium.query.filter_by(owner_id=current_user.id).all()
    
    return render_template('stadium_owner_dashboard.html', stadiums=stadiums)

# API Endpoints for Admin
@admin_bp.route('/api/stats')
@admin_required
def api_stats():
    """API endpoint for dashboard stats"""
    try:
        stats = {
            'customers': Customer.query.count(),
            'stadiums': Stadium.query.count(),
            'events': Event.query.count(),
            'bookings': Booking.query.count(),
            'revenue': float(db.session.query(db.func.sum(Booking.total_amount)).scalar() or 0)
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/bookings/recent')
@admin_required
def api_recent_bookings():
    """API endpoint for recent bookings"""
    try:
        bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(10).all()
        bookings_data = []
        for booking in bookings:
            bookings_data.append({
                'id': booking.id,
                'customer_name': booking.customer.name if booking.customer else 'Unknown',
                'amount': float(booking.total_amount),
                'date': booking.booking_date.isoformat(),
                'status': getattr(booking, 'status', 'confirmed')
            })
        return jsonify(bookings_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
