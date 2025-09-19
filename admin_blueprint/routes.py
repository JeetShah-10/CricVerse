"""
Admin Routes for CricVerse Stadium System
"""

from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from app import db, User, Event, Booking, Ticket, Stadium, Team, Seat, Concession, Parking
from admin.views import MyModelView, EventModelView, BookingModelView, TicketModelView, StadiumModelView, TeamModelView

# Create admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
@login_required
def before_request():
    """Ensure user is admin before accessing admin routes"""
    if not current_user.is_admin:
        flash('Access denied. Administrator privileges required.', 'error')
        return redirect(url_for('main.index'))

@admin_bp.route('/')
def dashboard():
    """Admin dashboard overview"""
    # Get statistics
    total_users = User.query.count()
    total_events = Event.query.count()
    total_bookings = Booking.query.count()
    total_tickets = Ticket.query.count()
    total_stadiums = Stadium.query.count()
    
    # Get recent bookings
    recent_bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(5).all()
    
    return render_template('admin/admin_dashboard.html',
                         total_users=total_users,
                         total_events=total_events,
                         total_bookings=total_bookings,
                         total_tickets=total_tickets,
                         total_stadiums=total_stadiums,
                         recent_bookings=recent_bookings)

# Admin setup function
def setup_admin(app):
    """Setup Flask-Admin for the application"""
    admin = Admin(app, name='CricVerse Admin', template_mode='bootstrap4')
    
    # Add model views
    admin.add_view(MyModelView(User, db.session))
    admin.add_view(EventModelView(Event, db.session))
    admin.add_view(BookingModelView(Booking, db.session))
    admin.add_view(TicketModelView(Ticket, db.session))
    admin.add_view(StadiumModelView(Stadium, db.session))
    admin.add_view(TeamModelView(Team, db.session))
    
    return admin