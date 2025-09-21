"""
Admin Routes for CricVerse
Comprehensive admin panel with full CRUD operations and advanced analytics
Enhanced for Big Bash League Cricket Platform
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import (
    Customer, Stadium, Event, Booking, Ticket, Seat, 
    Concession, MenuItem, Parking, Team, Player, StadiumAdmin
)
from datetime import datetime, timedelta, date
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

# Enhanced Main Admin Dashboard
@admin_bp.route('/')
@admin_required
def dashboard():
    """Enhanced main admin dashboard with real-time analytics"""
    try:
        # Import analytics service
        from app.services.analytics_service import analytics_service
        
        # Get comprehensive dashboard statistics
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
        
        # Get financial dashboard data
        financial_data = analytics_service.get_financial_dashboard()
        
        # Get recent booking patterns
        booking_patterns = analytics_service.get_booking_patterns()
        
        # Calculate growth metrics
        today = date.today()
        last_month = today - timedelta(days=30)
        
        current_month_bookings = Booking.query.filter(
            Booking.booking_date >= last_month
        ).count()
        
        previous_month_start = last_month - timedelta(days=30)
        previous_month_bookings = Booking.query.filter(
            Booking.booking_date >= previous_month_start,
            Booking.booking_date < last_month
        ).count()
        
        booking_growth = 0
        if previous_month_bookings > 0:
            booking_growth = ((current_month_bookings - previous_month_bookings) / previous_month_bookings) * 100
        
        stats['booking_growth'] = round(booking_growth, 2)
        stats['financial_data'] = financial_data
        stats['booking_patterns'] = booking_patterns
        
        return render_template('admin/enhanced_dashboard.html', stats=stats)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('admin/enhanced_dashboard.html', stats={})

@admin_bp.route('/profile')
@admin_required
def profile():
    """Admin profile page"""
    return render_template('admin/admin_profile.html')

@admin_bp.route('/analytics')
@admin_required
def analytics():
    """Enhanced admin analytics page with comprehensive metrics"""
    try:
        from app.services.analytics_service import analytics_service
        
        # Get date range from request parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        stadium_id = request.args.get('stadium_id', type=int)
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Get comprehensive analytics data
        revenue_analytics = analytics_service.get_revenue_analytics(stadium_id, start_date, end_date)
        customer_analytics = analytics_service.get_customer_analytics(stadium_id, start_date, end_date)
        booking_patterns = analytics_service.get_booking_patterns(stadium_id, start_date, end_date)
        
        # Get stadium utilization if stadium_id is provided
        stadium_utilization = None
        if stadium_id:
            stadium_utilization = analytics_service.get_stadium_utilization(stadium_id, start_date, end_date)
        
        # Get all stadiums for filter dropdown
        stadiums = Stadium.query.all()
        
        analytics_data = {
            'revenue': revenue_analytics,
            'customers': customer_analytics,
            'booking_patterns': booking_patterns,
            'stadium_utilization': stadium_utilization,
            'stadiums': stadiums,
            'selected_stadium_id': stadium_id,
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None
        }
        
        return render_template('admin/enhanced_analytics.html', analytics=analytics_data)
    except Exception as e:
        flash(f'Error loading analytics: {str(e)}', 'error')
        return render_template('admin/enhanced_analytics.html', analytics={})

# Stadium Management
@admin_bp.route('/stadiums')
@admin_required
def stadiums_overview():
    """Enhanced stadiums overview page with analytics"""
    try:
        from app.services.analytics_service import analytics_service
        
        stadiums = Stadium.query.all()
        stadium_analytics = []
        
        for stadium in stadiums:
            # Get basic statistics for each stadium
            events_count = Event.query.filter_by(stadium_id=stadium.id).count()
            total_revenue = db.session.query(db.func.sum(Booking.total_amount)).join(
                Event, Booking.id == Event.id  # This might need adjustment based on your relationship
            ).filter(Event.stadium_id == stadium.id).scalar() or 0
            
            # Get utilization data
            utilization = analytics_service.get_stadium_utilization(stadium.id)
            
            stadium_analytics.append({
                'stadium': stadium,
                'events_count': events_count,
                'total_revenue': float(total_revenue),
                'utilization': utilization
            })
        
        return render_template('admin/enhanced_stadiums_overview.html', stadium_analytics=stadium_analytics)
    except Exception as e:
        flash(f'Error loading stadiums overview: {str(e)}', 'error')
        return render_template('admin/enhanced_stadiums_overview.html', stadium_analytics=[])

@admin_bp.route('/stadiums/<int:stadium_id>/analytics')
@admin_required
def stadium_analytics(stadium_id):
    """Enhanced stadium analytics page with comprehensive metrics"""
    try:
        from app.services.analytics_service import analytics_service
        
        stadium = Stadium.query.get_or_404(stadium_id)
        
        # Get date range from request parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Get comprehensive stadium analytics
        revenue_analytics = analytics_service.get_revenue_analytics(stadium_id, start_date, end_date)
        utilization_data = analytics_service.get_stadium_utilization(stadium_id, start_date, end_date)
        customer_analytics = analytics_service.get_customer_analytics(stadium_id, start_date, end_date)
        booking_patterns = analytics_service.get_booking_patterns(stadium_id, start_date, end_date)
        financial_dashboard = analytics_service.get_financial_dashboard(stadium_id)
        
        analytics_data = {
            'stadium': stadium,
            'revenue': revenue_analytics,
            'utilization': utilization_data,
            'customers': customer_analytics,
            'booking_patterns': booking_patterns,
            'financial': financial_dashboard,
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None
        }
        
        return render_template('admin/stadium_analytics.html', analytics=analytics_data)
    except Exception as e:
        flash(f'Error loading stadium analytics: {str(e)}', 'error')
        return redirect(url_for('admin.stadiums_overview'))

# Event Management
@admin_bp.route('/events')
@admin_required
def events_overview():
    """Events overview page"""
    events = Event.query.order_by(Event.event_date.desc()).all()
    return render_template('admin/events_overview.html', events=events)

@admin_bp.route('/events/add')
@admin_required
def add_event():
    """Add new event page"""
    stadiums = Stadium.query.all()
    teams = Team.query.all()
    return render_template('admin/add_event.html', stadiums=stadiums, teams=teams)

@admin_bp.route('/events/add', methods=['POST'])
@admin_required
def create_event():
    """Create new event"""
    try:
        event = Event(
            event_name=request.form['name'],
            event_date=datetime.strptime(request.form['event_date'], '%Y-%m-%d'),
            stadium_id=int(request.form['stadium_id']),
            home_team_id=request.form.get('home_team_id'),
            away_team_id=request.form.get('away_team_id'),
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
        return render_template('admin/add_event.html', stadiums=stadiums, teams=teams)

# Booking Management
@admin_bp.route('/bookings')
@admin_required
def bookings_overview():
    """Bookings overview page"""
    bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(100).all()
    return render_template('admin/bookings_overview.html', bookings=bookings)

# Concession Management
@admin_bp.route('/concessions')
@admin_required
def concessions_overview():
    """Concessions overview page"""
    concessions = Concession.query.all()
    return render_template('admin/concessions_overview.html', concessions=concessions)

@admin_bp.route('/concessions/add')
@admin_required
def add_concession():
    """Add new concession page"""
    stadiums = Stadium.query.all()
    return render_template('admin/add_concession.html', stadiums=stadiums)

@admin_bp.route('/concessions/add', methods=['POST'])
@admin_required
def create_concession():
    """Create new concession"""
    try:
        concession = Concession(
            name=request.form['name'],
            category=request.form['type'],
            location_zone=request.form['location'],
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
        return render_template('admin/add_concession.html', stadiums=stadiums)

@admin_bp.route('/concessions/<int:concession_id>/menu/add')
@admin_required
def add_menu_item(concession_id):
    """Add menu item page"""
    concession = Concession.query.get_or_404(concession_id)
    return render_template('admin/add_menu_item.html', concession=concession)

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
        return render_template('admin/add_menu_item.html', concession=concession)

# Parking Management
@admin_bp.route('/parking')
@admin_required
def parking_overview():
    """Parking overview page"""
    parking_areas = Parking.query.all()
    return render_template('admin/parking_overview.html', parking_areas=parking_areas)

@admin_bp.route('/parking/add')
@admin_required
def add_parking():
    """Add new parking area page"""
    stadiums = Stadium.query.all()
    return render_template('admin/add_parking.html', stadiums=stadiums)

@admin_bp.route('/parking/add', methods=['POST'])
@admin_required
def create_parking():
    """Create new parking area"""
    try:
        parking = Parking(
            zone=request.form['name'],
            capacity=int(request.form['capacity']),
            rate_per_hour=float(request.form['price_per_hour']),
            stadium_id=int(request.form['stadium_id'])
        )
        db.session.add(parking)
        db.session.commit()
        flash('Parking area created successfully!', 'success')
        return redirect(url_for('admin.parking_overview'))
    except Exception as e:
        flash(f'Error creating parking area: {str(e)}', 'error')
        stadiums = Stadium.query.all()
        return render_template('admin/add_parking.html', stadiums=stadiums)

# Seat Management
@admin_bp.route('/stadiums/<int:stadium_id>/seats/add')
@admin_required
def add_seats(stadium_id):
    """Add seats page"""
    stadium = Stadium.query.get_or_404(stadium_id)
    return render_template('admin/add_seats.html', stadium=stadium)

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
        return render_template('admin/add_seats.html', stadium=stadium)

# User Management
@admin_bp.route('/users')
@admin_required
def user_management():
    """User management page"""
    users = Customer.query.all()
    return render_template('admin/user_management.html', users=users)

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
    stadiums = []
    if current_user.role == 'admin':
        # Admin can see all stadiums
        stadiums = Stadium.query.all()
    else:
        # Stadium owners see only their stadiums
        stadium_ids = [sa.stadium_id for sa in StadiumAdmin.query.filter_by(admin_id=current_user.id).all()]
        if stadium_ids:
            stadiums = Stadium.query.filter(Stadium.id.in_(stadium_ids)).all()
    
    return render_template('stadium_owner_dashboard.html', stadiums=stadiums)

# Enhanced API Endpoints for Admin
@admin_bp.route('/api/stats')
@admin_required
def api_stats():
    """Enhanced API endpoint for dashboard stats with real-time data"""
    try:
        from app.services.analytics_service import analytics_service
        
        # Get current period stats
        today = date.today()
        last_30_days = today - timedelta(days=30)
        
        stats = {
            'customers': Customer.query.count(),
            'stadiums': Stadium.query.count(),
            'events': Event.query.count(),
            'bookings': Booking.query.count(),
            'revenue': float(db.session.query(db.func.sum(Booking.total_amount)).scalar() or 0),
            'recent_bookings': Booking.query.filter(
                Booking.booking_date >= last_30_days
            ).count(),
            'upcoming_events': Event.query.filter(
                Event.event_date >= today
            ).count()
        }
        
        # Add growth metrics
        financial_data = analytics_service.get_financial_dashboard()
        if 'growth_metrics' in financial_data:
            stats['growth_metrics'] = financial_data['growth_metrics']
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/analytics/revenue')
@admin_required
def api_revenue_analytics():
    """API endpoint for revenue analytics"""
    try:
        from app.services.analytics_service import analytics_service
        
        stadium_id = request.args.get('stadium_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        revenue_data = analytics_service.get_revenue_analytics(stadium_id, start_date, end_date)
        return jsonify(revenue_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/analytics/customers')
@admin_required
def api_customer_analytics():
    """API endpoint for customer analytics"""
    try:
        from app.services.analytics_service import analytics_service
        
        stadium_id = request.args.get('stadium_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        customer_data = analytics_service.get_customer_analytics(stadium_id, start_date, end_date)
        return jsonify(customer_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/analytics/utilization/<int:stadium_id>')
@admin_required
def api_stadium_utilization(stadium_id):
    """API endpoint for stadium utilization analytics"""
    try:
        from app.services.analytics_service import analytics_service
        
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        utilization_data = analytics_service.get_stadium_utilization(stadium_id, start_date, end_date)
        return jsonify(utilization_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/bookings/recent')
@admin_required
def api_recent_bookings():
    """Enhanced API endpoint for recent bookings with more details"""
    try:
        limit = request.args.get('limit', 10, type=int)
        bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(limit).all()
        bookings_data = []
        
        for booking in bookings:
            # Get event and stadium information
            tickets = Ticket.query.filter_by(booking_id=booking.id).first()
            event = None
            stadium = None
            
            if tickets and tickets.event_id:
                event = Event.query.get(tickets.event_id)
                if event and event.stadium_id:
                    stadium = Stadium.query.get(event.stadium_id)
            
            bookings_data.append({
                'id': booking.id,
                'customer_name': booking.customer.name if booking.customer else 'Unknown',
                'customer_email': booking.customer.email if booking.customer else 'Unknown',
                'amount': float(booking.total_amount),
                'date': booking.booking_date.isoformat(),
                'status': getattr(booking, 'payment_status', 'confirmed'),
                'event_name': event.event_name if event else 'N/A',
                'stadium_name': stadium.name if stadium else 'N/A',
                'tickets_count': Ticket.query.filter_by(booking_id=booking.id).count()
            })
        return jsonify(bookings_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/events/upcoming')
@admin_required
def api_upcoming_events():
    """API endpoint for upcoming events with analytics"""
    try:
        limit = request.args.get('limit', 10, type=int)
        events = Event.query.filter(
            Event.event_date >= datetime.now()
        ).order_by(Event.event_date).limit(limit).all()
        
        events_data = []
        for event in events:
            # Get booking statistics for each event
            tickets_sold = Ticket.query.filter_by(event_id=event.id).count()
            revenue = db.session.query(db.func.sum(Booking.total_amount)).join(
                Ticket, Booking.id == Ticket.booking_id
            ).filter(Ticket.event_id == event.id).scalar() or 0
            
            stadium = Stadium.query.get(event.stadium_id) if event.stadium_id else None
            
            events_data.append({
                'id': event.id,
                'name': event.event_name,
                'date': event.event_date.isoformat(),
                'stadium_name': stadium.name if stadium else 'TBD',
                'tickets_sold': tickets_sold,
                'revenue': float(revenue),
                'capacity': stadium.capacity if stadium else 0,
                'occupancy_rate': round((tickets_sold / stadium.capacity * 100), 2) if stadium and stadium.capacity > 0 else 0
            })
        
        return jsonify(events_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Real-time Dashboard Updates
@admin_bp.route('/api/dashboard/realtime')
@admin_required
def api_realtime_dashboard():
    """API endpoint for real-time dashboard updates"""
    try:
        # Get real-time metrics
        today = date.today()
        
        realtime_data = {
            'timestamp': datetime.now().isoformat(),
            'today_bookings': Booking.query.filter(
                func.date(Booking.booking_date) == today
            ).count(),
            'today_revenue': float(db.session.query(db.func.sum(Booking.total_amount)).filter(
                func.date(Booking.booking_date) == today
            ).scalar() or 0),
            'active_events': Event.query.filter(
                Event.event_date == today
            ).count(),
            'total_customers': Customer.query.count(),
            'recent_activity': []
        }
        
        # Get recent activity (last 10 bookings)
        recent_bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(5).all()
        for booking in recent_bookings:
            realtime_data['recent_activity'].append({
                'type': 'booking',
                'customer': booking.customer.name if booking.customer else 'Unknown',
                'amount': float(booking.total_amount),
                'time': booking.booking_date.strftime('%H:%M')
            })
        
        return jsonify(realtime_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500