from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Ticket, Order, ParkingBooking, Booking, Team, Event
from datetime import datetime, timezone

bp = Blueprint('user', __name__)

@bp.route('/dashboard')
@login_required
def dashboard():
    # Get user's data with ordering for a better display
    tickets = Ticket.query.filter_by(customer_id=current_user.id).join(Event).order_by(Event.event_date.desc()).all()
    orders = Order.query.filter_by(customer_id=current_user.id).order_by(Order.order_date.desc()).all()
    parking_bookings = ParkingBooking.query.filter_by(customer_id=current_user.id).order_by(ParkingBooking.booking_date.desc()).all()

    # --- Calculate stats for the summary cards ---
    total_tickets = len(tickets)
    
    # Calculate total spent from all sources
    ticket_spend = db.session.query(db.func.sum(Booking.total_amount)).filter(
        Booking.customer_id == current_user.id
    ).scalar() or 0
    order_spend = db.session.query(db.func.sum(Order.total_amount)).filter_by(customer_id=current_user.id).scalar() or 0
    parking_spend = db.session.query(db.func.sum(ParkingBooking.amount_paid)).filter_by(customer_id=current_user.id).scalar() or 0
    
    total_spent = ticket_spend + order_spend + parking_spend
    
    # Find upcoming events from the user's tickets
    upcoming_events_count = db.session.query(Ticket).join(Event).filter(
        Ticket.customer_id == current_user.id,
        Event.event_date >= datetime.now(timezone.utc).date()
    ).count()

    stats = {
        'total_tickets': total_tickets,
        'total_spent': total_spent,
        'upcoming_events': upcoming_events_count,
        'total_orders': len(orders)
    }

    return render_template('dashboard.html', 
                           tickets=tickets, 
                           orders=orders, 
                           parking_bookings=parking_bookings,
                           stats=stats)

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    teams = Team.query.all()
    if request.method == 'POST':
        # The Customer model uses 'username', not 'name'. 
        # We will update the username field from the form's 'name' input.
        current_user.username = request.form.get('name', '')
        current_user.phone = request.form.get('phone', '')
        
        # The new Customer model does not have a favorite_team_id, skipping for now.

        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {e}', 'danger')
        return redirect(url_for('user.profile'))
        
    return render_template('profile.html', teams=teams)
