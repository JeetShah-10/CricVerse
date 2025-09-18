from flask import Blueprint, render_template
from flask_login import login_required
from app.models import Event, Seat, Ticket
from app import db

bp = Blueprint('ticketing', __name__)

@bp.route('/event/<int:event_id>/select-seats')
@login_required
def select_seats(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Get all seats for the stadium
    all_seats = Seat.query.filter_by(stadium_id=event.stadium_id).order_by(Seat.section, Seat.row_number, Seat.seat_number).all()
    
    # Get booked seats for this event
    booked_seat_ids = {s.seat_id for s in Ticket.query.filter_by(event_id=event_id).all()}
    
    # Group seats by section and prepare data for template
    sections = {}
    total_available = 0
    
    for seat in all_seats:
        seat.is_available = seat.id not in booked_seat_ids
        if seat.is_available:
            total_available += 1

        section_name = seat.section or 'General'
        if section_name not in sections:
            sections[section_name] = {
                'name': section_name,
                'rows': {},
                'price_range': {'min': float('inf'), 'max': 0},
                'seat_types': set()
            }

        row_name = seat.row_number or 'N/A'
        if row_name not in sections[section_name]['rows']:
            sections[section_name]['rows'][row_name] = []
        
        sections[section_name]['rows'][row_name].append(seat)
        if seat.price:
            sections[section_name]['price_range']['min'] = min(sections[section_name]['price_range']['min'], seat.price)
            sections[section_name]['price_range']['max'] = max(sections[section_name]['price_range']['max'], seat.price)
        if seat.seat_type:
            sections[section_name]['seat_types'].add(seat.seat_type)

    # Use enhanced template if it exists, fallback to original
    try:
        return render_template('enhanced_seat_selection.html', 
                             event=event, 
                             sections=sections,
                             total_available=total_available)
    except Exception:
        # Fallback to original template
        return render_template('seat_selection.html', 
                             event=event, 
                             sections=sections,
                             total_available=total_available)
