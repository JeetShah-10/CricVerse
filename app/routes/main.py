from flask import Blueprint, render_template, redirect, url_for, current_app, send_from_directory, jsonify, request, flash
import os
from pathlib import Path
from flask_login import current_user
from app.models.stadium import Stadium, Concession, Parking, MenuItem
from app.models.match import Event, Team, Player
from app.models.booking import Ticket, Seat
from app import db
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Optionally show featured teams/events on the homepage
    teams = Team.query.limit(8).all()
    events = Event.query.order_by(Event.event_date.asc()).limit(10).all()
    stadiums = Stadium.query.limit(8).all()
    return render_template('index.html', teams=teams, events=events, stadiums=stadiums)

@main_bp.route('/events')
def events():
    events = Event.query.order_by(Event.event_date.asc()).all()
    return render_template('events.html', events=events)

@main_bp.route('/event/<int:event_id>')
def event_detail(event_id: int):
    # Render detailed event page if template/relations are available
    event = Event.query.get_or_404(event_id)
    return render_template('event_detail.html', event=event)

@main_bp.route('/teams')
def teams():
    # Transform ORM Team into dicts expected by templates (name, logo_url, etc.)
    orm_teams = Team.query.order_by(Team.team_name.asc()).all()
    teams = []
    for t in orm_teams:
        teams.append({
            'id': t.id,
            'name': getattr(t, 'team_name', None),
            'logo_url': getattr(t, 'team_logo', None),
            'city': getattr(t, 'home_city', None),
            'about': None,
            'founding_year': None,
            'championships_won': None,
            'home_ground': getattr(t, 'home_ground', None),
            'color1': '#0ea5e9',
            'color2': '#1e293b',
        })
    return render_template('teams.html', teams=teams)

@main_bp.route('/team/<int:team_id>')
def team_detail(team_id: int):
    orm_team = Team.query.get_or_404(team_id)
    # Build a view model with safe defaults for template fields
    team = {
        'id': orm_team.id,
        'team_name': getattr(orm_team, 'team_name', None),
        'team_logo': getattr(orm_team, 'team_logo', None),
        'tagline': getattr(orm_team, 'tagline', None) or '',
        'home_city': getattr(orm_team, 'home_city', None),
        'home_ground': getattr(orm_team, 'home_ground', None),
        'color1': '#0ea5e9',
        'color2': '#1e293b',
        'coach_name': getattr(orm_team, 'coach_name', None),
        'manager': getattr(orm_team, 'manager', None),
        'owner_name': getattr(orm_team, 'owner_name', None),
        'about': getattr(orm_team, 'about', None),
        'founding_year': getattr(orm_team, 'founding_year', None),
        'championships_won': getattr(orm_team, 'championships_won', None),
        'players': [
            {
                'id': p.id,
                'player_name': getattr(p, 'player_name', None),
                'player_role': getattr(p, 'player_role', None),
                'image_url': getattr(p, 'image_url', None),
                # Optional fields used in template fallbacks
                'highlight': getattr(p, 'highlight', None),
                'role': getattr(p, 'player_role', None),
                'name': getattr(p, 'player_name', None),
            } for p in getattr(orm_team, 'players', [])
        ]
    }
    # Try to find the home stadium by name (if available)
    stadium = None
    if team.get('home_ground'):
        stadium = Stadium.query.filter(Stadium.name == team['home_ground']).first()
    return render_template('team_detail.html', team=team, stadium=stadium)

@main_bp.route('/stadiums')
def stadiums():
    stadiums = Stadium.query.order_by(Stadium.name.asc()).all()
    return render_template('stadiums.html', stadiums=stadiums)

@main_bp.route('/stadium/<int:stadium_id>')
def stadium_detail(stadium_id: int):
    stadium = Stadium.query.get_or_404(stadium_id)
    # Attach dynamic attributes expected by template
    try:
        from app.models.match import Event
        from app.models.stadium import Photo
        stadium.photos = Photo.query.filter_by(stadium_id=stadium.id).all()
        stadium.upcoming_matches = Event.query.filter(Event.stadium_id == stadium.id).order_by(Event.event_date.asc()).limit(10).all()
    except Exception:
        stadium.photos = []
        stadium.upcoming_matches = []
    return render_template('stadium_detail.html', stadium=stadium)

@main_bp.route('/players')
def players():
    players = Player.query.order_by(Player.player_name.asc()).all()
    return render_template('players.html', players=players)

@main_bp.route('/player/<int:player_id>')
def player_detail(player_id: int):
    player = Player.query.get_or_404(player_id)
    return render_template('player_detail.html', player=player)

@main_bp.route('/concessions')
def concessions():
    # Filters
    selected_stadium_id = request.args.get('stadium_id', type=int)
    selected_category = request.args.get('category', type=str)

    q = Concession.query
    if selected_stadium_id:
        q = q.filter(Concession.stadium_id == selected_stadium_id)
    if selected_category:
        q = q.filter(Concession.category == selected_category)

    # Preload relationships for template grouping
    concessions_list = q.join(Stadium).all()

    # Build stadiums and categories for filters
    stadiums = Stadium.query.order_by(Stadium.name.asc()).all()
    cat_rows = Concession.query.with_entities(Concession.category).distinct().all()
    categories = sorted([c[0] for c in cat_rows if c and c[0]])

    return render_template(
        'concessions.html',
        concessions=concessions_list,
        stadiums=stadiums,
        categories=categories,
        selected_stadium_id=selected_stadium_id,
        selected_category=selected_category,
    )

@main_bp.route('/concessions/<int:concession_id>/order', methods=['POST'])
def order_concession(concession_id: int):
    # Minimal order creation to enable flow; enhance with quantities/items later
    if not current_user.is_authenticated:
        flash('Please login to place an order.', 'info')
        return redirect(url_for('auth.login'))
    try:
        from app.models.stadium import Order as ConcessionOrder
        order = ConcessionOrder(
            concession_id=concession_id,
            customer_id=getattr(current_user, 'id', None),
            total_amount=0.0,
            payment_status='Pending'
        )
        db.session.add(order)
        db.session.commit()
        flash('Order placed successfully. Proceed to payment from your Dashboard.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.warning(f"Order creation failed: {e}")
        flash('Failed to place order. Please try again later.', 'danger')
    return redirect(url_for('main.concessions'))

@main_bp.route('/parking')
def parking():
    # Provide both stadiums and parking_zones as the template expects
    stadiums = Stadium.query.order_by(Stadium.name.asc()).all()
    parking_zones = Parking.query.all()
    return render_template('parking.html', stadiums=stadiums, parking_zones=parking_zones)

@main_bp.route('/parking/book/<int:stadium_id>', methods=['GET', 'POST'])
def book_parking(stadium_id: int):
    if request.method == 'GET':
        stadium = Stadium.query.get_or_404(stadium_id)
        parking_zones = Parking.query.filter_by(stadium_id=stadium_id).all()
        return render_template('book_parking.html', stadium=stadium, parking_zones=parking_zones)
    # POST
    if not current_user.is_authenticated:
        flash('Please login to book parking.', 'info')
        return redirect(url_for('auth.login'))
    try:
        from app.models.stadium import ParkingBooking
        parking_id = request.form.get('parking_id', type=int)
        vehicle_number = request.form.get('vehicle_number', '').strip()
        arrival_time = request.form.get('arrival_time')
        departure_time = request.form.get('departure_time')
        arrival_dt = datetime.fromisoformat(arrival_time) if arrival_time else None
        departure_dt = datetime.fromisoformat(departure_time) if departure_time else None
        booking = ParkingBooking(
            parking_id=parking_id,
            customer_id=getattr(current_user, 'id', None),
            vehicle_number=vehicle_number,
            arrival_time=arrival_dt,
            departure_time=departure_dt,
            amount_paid=0.0,
            payment_status='Pending'
        )
        db.session.add(booking)
        db.session.commit()
        flash('Parking booked successfully. Payment pending.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.warning(f"Parking booking failed: {e}")
        flash('Failed to book parking. Please try again.', 'danger')
    return redirect(url_for('main.parking'))

@main_bp.route('/tickets')
def tickets():
    tickets = Ticket.query.order_by(Ticket.created_at.desc()).limit(100).all()
    return render_template('tickets.html', tickets=tickets)

@main_bp.route('/seats')
def seats():
    seats = Seat.query.limit(500).all()
    return render_template('seats.html', seats=seats)

@main_bp.route('/checkout')
def checkout():
    # Minimal checkout page renderer; client-side JS will orchestrate payment
    return render_template('checkout.html')

@main_bp.route('/payment/confirm')
def payment_confirm():
    """Finalize a payment for an order or parking booking.
    Expects query params: type=order|parking, order_id|booking_id, amount
    """
    try:
        ptype = request.args.get('type')
        amount = request.args.get('amount', type=float) or 0.0
        if ptype == 'order':
            oid = request.args.get('order_id', type=int)
            from app.models.stadium import Order as ConcessionOrder
            order = ConcessionOrder.query.get_or_404(oid)
            order.total_amount = amount
            order.payment_status = 'Completed'
            db.session.commit()
            flash('Payment successful. Your concession order is confirmed.', 'success')
        elif ptype == 'parking':
            bid = request.args.get('booking_id', type=int)
            from app.models.stadium import ParkingBooking
            booking = ParkingBooking.query.get_or_404(bid)
            booking.amount_paid = amount
            booking.payment_status = 'Completed'
            db.session.commit()
            flash('Payment successful. Your parking booking is confirmed.', 'success')
        else:
            flash('Unknown payment type.', 'warning')
    except Exception as e:
        db.session.rollback()
        current_app.logger.warning(f"Payment confirmation failed: {e}")
        flash('Failed to confirm payment. Please contact support.', 'danger')
    return redirect(url_for('user.dashboard'))

@main_bp.route('/ai_options')
def ai_options():
    return render_template('ai_options.html')

@main_bp.route('/chat')
def chat_interface():
    return render_template('chat.html')

# Removed ai_assistant route - template deleted

# Removed duplicate realtime route

@main_bp.route('/stadium_owner')
def stadium_owner_dashboard():
    return render_template('stadium_owner_dashboard.html')

@main_bp.route('/about')
def about():
    return render_template('about.html')

# -------------------- Utility & API helpers --------------------
@main_bp.route('/logos/<slug>.png')
def team_logo(slug: str):
    """Serve team logos from static with smart fallbacks.
    Expected slugs: thunder, heat, renegades, strikers, hurricanes, stars, scorchers, sixers
    """
    # Known mappings to actual filenames in static/img/teams when available
    mapping = {
        'stars': 'Melbourne_Stars_logo.png',
        'sixers': 'Sydney_Sixers_logo.svg.png',
        'scorchers': 'Perth Scorchers.png',
        'heat': 'Brisbane Heat.png',
        'hurricanes': 'Hobart Hurricanes.png',
        'strikers': 'Adelaide Striker.png',
        'renegades': 'Melbourne Renegades.png',
        'thunder': 'Sydney Thunder.png',
    }
    teams_dir = Path(current_app.static_folder) / 'img' / 'teams'
    candidates = []
    # 1) mapped filename if present
    if slug in mapping:
        candidates.append(mapping[slug])
    # 2) common variants
    candidates += [
        f"{slug}.png",
        f"{slug}.svg.png",
        f"{slug.capitalize()}.png",
        f"{slug.title()}.png",
    ]
    for name in candidates:
        file_path = teams_dir / name
        if file_path.exists():
            return send_from_directory(teams_dir, name)
    # Fallback placeholder
    placeholder = teams_dir / 'placeholder_team.png'
    if placeholder.exists():
        return send_from_directory(teams_dir, 'placeholder_team.png')
    # Last resort: 404
    return ("", 404)

@main_bp.route('/api/realtime/stats')
def realtime_stats():
    """Lightweight stats endpoint to avoid 404s in UI probes."""
    return jsonify({
        'status': 'ok',
        'clients': None,  # could be wired to SocketIO metrics later
        'uptime': None,
        'ts': request.headers.get('Date')
    })

@main_bp.route('/realtime')
def realtime():
    """Real-time updates page."""
    return render_template('realtime.html')

@main_bp.route('/contact')
def contact():
    """Contact page."""
    return render_template('contact.html')

@main_bp.route('/privacy')
def privacy():
    """Privacy policy page."""
    return render_template('privacy.html')

@main_bp.route('/terms')
def terms():
    """Terms of service page."""
    return render_template('terms.html')

@main_bp.route('/chatbot')
def chatbot():
    """Chatbot page."""
    return render_template('chatbot.html')

@main_bp.route('/live-scores')
def live_scores():
    """Live scores page."""
    return render_template('live_scores.html')

@main_bp.route('/match-center')
def match_center():
    """Match center page."""
    return render_template('match_center.html')

@main_bp.route('/booking')
def booking():
    """Main booking page."""
    return render_template('booking.html')

@main_bp.route('/booking/select-seats')
def select_seats():
    """Seat selection page."""
    return render_template('select_seats.html')

@main_bp.route('/booking/checkout')
def booking_checkout():
    """Booking checkout page."""
    return render_template('checkout.html')

@main_bp.route('/booking/confirmation')
def confirmation():
    """Booking confirmation page."""
    return render_template('confirmation.html')

@main_bp.route('/bbl-action-hub')
def bbl_action_hub():
    """BBL Action Hub page."""
    return render_template('bbl_action_hub.html')

@main_bp.route('/qr-demo')
def qr_demo():
    """QR code demo page."""
    return render_template('qr_demo.html')

@main_bp.route('/generate-qr')
def generate_qr():
    """QR generation page."""
    return render_template('generate_qr.html')

@main_bp.route('/analytics')
def analytics():
    """Analytics dashboard."""
    return render_template('analytics.html')

@main_bp.route('/insights')
def insights():
    """Cricket insights page."""
    return render_template('insights.html')

@main_bp.route('/statistics')
def statistics():
    """Statistics page."""
    return render_template('statistics.html')

@main_bp.route('/api/health')
def health_check():
    """Health check API endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@main_bp.route('/api/csrf-token')
def csrf_token():
    """CSRF token API endpoint."""
    return jsonify({
        'csrf_token': 'test-csrf-token',
        'timestamp': datetime.now().isoformat()
    })

@main_bp.route('/api/generate-qr', methods=['POST'])
def generate_qr_api():
    """QR generation API."""
    data = request.get_json()
    if not data or not data.get('data'):
        return jsonify({'error': 'Data is required'}), 400
    
    return jsonify({
        'success': True,
        'qr_data': data.get('data'),
        'qr_url': f'/qr/{data.get("data")}',
        'timestamp': datetime.now().isoformat()
    })

# Removed routes for deleted templates

@main_bp.route('/payment-success')
def payment_success():
    """Payment success page."""
    return render_template('payment_success.html')

@main_bp.route('/seat-selection')
def seat_selection():
    """Seat selection page."""
    return render_template('seat_selection.html')

@main_bp.route('/concession-menu')
def concession_menu():
    """Concession menu page."""
    return render_template('concession_menu.html')

@main_bp.route('/concession/<int:concession_id>/menu')
def concession_menu_detail(concession_id):
    """Concession menu detail page."""
    concession = Concession.query.get_or_404(concession_id)
    menu_items = MenuItem.query.filter_by(concession_id=concession_id).all()
    return render_template('concession_menu.html', concession=concession, menu_items=menu_items)

# Removed special feature routes - templates don't exist

# Payment routes
@main_bp.route('/payment/paypal/success')
def paypal_success():
    """PayPal payment success."""
    return render_template('payment_success.html', payment_method='PayPal')

@main_bp.route('/payment/paypal/cancel')
def paypal_cancel():
    """PayPal payment cancelled."""
    flash('Payment was cancelled.', 'info')
    return redirect(url_for('main.index'))

@main_bp.route('/payment/razorpay/success')
def razorpay_success():
    """Razorpay payment success."""
    return render_template('payment_success.html', payment_method='Razorpay')

@main_bp.route('/payment/razorpay/cancel')
def razorpay_cancel():
    """Razorpay payment cancelled."""
    flash('Payment was cancelled.', 'info')
    return redirect(url_for('main.index'))

# Missing basic templates
@main_bp.route('/dashboard')
def dashboard():
    """User dashboard (redirect to user routes)."""
    return redirect(url_for('user.dashboard'))

@main_bp.route('/profile')
def profile():
    """User profile (redirect to user routes)."""
    return redirect(url_for('user.profile'))
