"""
Enhanced CricVerse Flask Application
Integrates all advanced features: Real-time, Payments, Analytics, etc.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import re
from dotenv import load_dotenv
from functools import wraps
import logging

# Import enhanced features
from realtime import init_socketio, update_match_score, notify_new_booking
from stripe_integration import (
    create_booking_payment_intent, 
    create_parking_payment_intent, 
    handle_stripe_webhook,
    get_payment_status,
    process_refund
)

# Import original utility functions
from utils import (
    validate_email, validate_phone, validate_password_strength,
    sanitize_input, flash_errors, get_user_statistics, get_analytics_data,
    handle_form_errors, REGISTRATION_VALIDATION_RULES, STADIUM_VALIDATION_RULES,
    EVENT_VALIDATION_RULES, get_upcoming_events
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables (prefer local cricverse.env, fallback to .env)
if os.path.exists('cricverse.env'):
    load_dotenv('cricverse.env')
    print("✅ Loaded cricverse.env")
else:
    load_dotenv()
    print("✅ Loaded .env")

app = Flask(__name__)

# Configuration with fallbacks
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'cricverse-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16777216))

# Database configuration with Supabase and fallback support
database_url = os.getenv('DATABASE_URL')

# If no DATABASE_URL is set, try to construct PostgreSQL URL for stadium_db
if not database_url:
    # Try PostgreSQL first with stadium_db database name
    pg_user = os.getenv('POSTGRES_USER', 'postgres')
    pg_password = os.getenv('POSTGRES_PASSWORD', 'admin')
    pg_host = os.getenv('POSTGRES_HOST', 'localhost')
    pg_port = os.getenv('POSTGRES_PORT', '5432')
    pg_database = os.getenv('POSTGRES_DB', 'stadium_db')
    
    # Construct PostgreSQL URL
    database_url = f'postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}'
    print(f"No DATABASE_URL found. Attempting PostgreSQL connection to stadium_db...")
    
    # Test PostgreSQL connection
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=pg_host,
            port=pg_port,
            database=pg_database,
            user=pg_user,
            password=pg_password
        )
        conn.close()
        print(f"[SUCCESS] PostgreSQL connection successful: {pg_database}")
    except Exception as e:
        print(f"[WARNING] PostgreSQL connection failed: {e}")
        print(f"Falling back to SQLite...")
        database_url = 'sqlite:///cricverse.db'

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Database connection pool settings for PostgreSQL
if 'postgresql' in database_url:
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 0
    }

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Initialize real-time features
print("🔌 Initializing real-time features...")
try:
    socketio = init_socketio(app)
    print("✅ Real-time WebSocket features initialized")
except Exception as e:
    print(f"❌ Failed to initialize real-time features: {e}")
    socketio = None

# Database connection info
if 'postgresql' in database_url:
    # Mask password in PostgreSQL URL for display
    display_url = database_url
    if '@' in display_url:
        parts = display_url.split('@')
        if ':' in parts[0]:
            user_pass = parts[0].split('://', 1)[1]
            if ':' in user_pass:
                user, password = user_pass.split(':', 1)
                display_url = display_url.replace(f':{password}@', ':****@')
else:
    display_url = database_url
    
print(f"[DATABASE] Database configured: {display_url}")

# Import all original models
from app import (
    Stadium, Team, Player, Event, Match, Seat, Customer, Booking, Ticket, Payment,
    Umpire, EventUmpire, Concession, MenuItem, Order, Parking, ParkingBooking,
    StadiumAdmin, StadiumOwner, Photo
)

# Import enhanced models
try:
    from enhanced_models import (
        CustomerProfile, PaymentTransaction, QRCode, Notification, MatchUpdate,
        ChatConversation, ChatMessage, BookingAnalytics, SystemLog, WebSocketConnection
    )
    print("✅ Enhanced models imported successfully")
except ImportError as e:
    print(f"⚠️ Enhanced models not found: {e}")

# Authentication decorators (keeping originals)
def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not current_user.is_admin():
            flash('Access denied. Admin privileges required.')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def customer_required(f):
    """Decorator to require customer role (non-admin)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if current_user.is_admin():
            flash('Access denied. This page is for customers only.')
            return redirect(url_for('admin_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(user_id):
    return Customer.query.get(int(user_id))

# ==========================================
# ENHANCED API ROUTES - PAYMENT PROCESSING
# ==========================================

@app.route('/api/create-booking-payment', methods=['POST'])
@login_required
def api_create_booking_payment():
    """Create Stripe payment intent for booking"""
    try:
        data = request.get_json()
        
        # Add current user to the booking data
        data['customer_id'] = current_user.id
        
        result = create_booking_payment_intent(data)
        
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]
        else:
            return jsonify(result)
            
    except Exception as e:
        logger.error(f"Error creating booking payment: {e}")
        return jsonify({'error': 'Payment setup failed'}), 500

@app.route('/api/create-parking-payment', methods=['POST'])
@login_required
def api_create_parking_payment():
    """Create Stripe payment intent for parking"""
    try:
        data = request.get_json()
        
        # Add current user to the parking data
        data['customer_id'] = current_user.id
        
        result = create_parking_payment_intent(data)
        
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]
        else:
            return jsonify(result)
            
    except Exception as e:
        logger.error(f"Error creating parking payment: {e}")
        return jsonify({'error': 'Payment setup failed'}), 500

@app.route('/api/stripe-webhook', methods=['POST'])
def api_stripe_webhook():
    """Handle Stripe webhooks"""
    return handle_stripe_webhook()

@app.route('/api/payment-status/<payment_intent_id>')
@login_required
def api_payment_status(payment_intent_id):
    """Get payment status"""
    try:
        result = get_payment_status(payment_intent_id)
        
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]
        else:
            return jsonify(result)
            
    except Exception as e:
        logger.error(f"Error getting payment status: {e}")
        return jsonify({'error': 'Failed to get payment status'}), 500

@app.route('/api/refund-payment', methods=['POST'])
@login_required
@admin_required
def api_refund_payment():
    """Process refund (admin only)"""
    try:
        data = request.get_json()
        payment_intent_id = data.get('payment_intent_id')
        amount = data.get('amount')
        reason = data.get('reason', 'requested_by_customer')
        
        result = process_refund(payment_intent_id, amount, reason)
        
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]
        else:
            return jsonify(result)
            
    except Exception as e:
        logger.error(f"Error processing refund: {e}")
        return jsonify({'error': 'Refund processing failed'}), 500

# ==========================================
# ENHANCED API ROUTES - REAL-TIME FEATURES
# ==========================================

@app.route('/api/realtime-stats')
@login_required
@admin_required
def api_realtime_stats():
    """Get real-time statistics"""
    try:
        from realtime import get_realtime_stats
        stats = get_realtime_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting real-time stats: {e}")
        return jsonify({'error': 'Failed to get statistics'}), 500

@app.route('/api/update-match-score', methods=['POST'])
@login_required
@admin_required
def api_update_match_score():
    """Update match score (admin only)"""
    try:
        data = request.get_json()
        match_id = data.get('match_id')
        home_score = data.get('home_score')
        away_score = data.get('away_score')
        home_wickets = data.get('home_wickets')
        away_wickets = data.get('away_wickets')
        current_over = data.get('current_over')
        
        # Update the score in real-time
        update_match_score(match_id, home_score, away_score, home_wickets, away_wickets, current_over)
        
        # Also update database
        match = Match.query.filter_by(event_id=match_id).first()
        if match:
            match.home_score = home_score
            match.away_score = away_score
            if home_wickets is not None:
                match.home_wickets = home_wickets
            if away_wickets is not None:
                match.away_wickets = away_wickets
            if current_over is not None:
                match.home_overs = current_over
                match.away_overs = current_over
            
            db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'Score updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating match score: {e}")
        return jsonify({'error': 'Failed to update score'}), 500

# ==========================================
# ENHANCED BOOKING ROUTES WITH PAYMENTS
# ==========================================

@app.route('/book-tickets-enhanced/<int:event_id>')
@login_required
@customer_required
def book_tickets_enhanced(event_id):
    """Enhanced ticket booking with Stripe payments"""
    try:
        event = Event.query.get_or_404(event_id)
        stadium = Stadium.query.get(event.stadium_id)
        
        # Get available seats
        available_seats = Seat.query.filter_by(stadium_id=event.stadium_id).all()
        booked_seat_ids = [ticket.seat_id for ticket in Ticket.query.filter_by(event_id=event_id, ticket_status='Booked').all()]
        available_seats = [seat for seat in available_seats if seat.id not in booked_seat_ids]
        
        return render_template('enhanced_ticket_booking.html', 
                             event=event, 
                             stadium=stadium, 
                             available_seats=available_seats,
                             stripe_publishable_key=os.getenv('STRIPE_PUBLISHABLE_KEY'))
                             
    except Exception as e:
        logger.error(f"Error in enhanced booking: {e}")
        flash('Error loading booking page')
        return redirect(url_for('events'))

@app.route('/book-parking-enhanced/<int:stadium_id>')
@login_required
@customer_required
def book_parking_enhanced(stadium_id):
    """Enhanced parking booking with Stripe payments"""
    try:
        stadium = Stadium.query.get_or_404(stadium_id)
        parking_zones = Parking.query.filter_by(stadium_id=stadium_id).all()
        
        return render_template('enhanced_parking_booking.html', 
                             stadium=stadium, 
                             parking_zones=parking_zones,
                             stripe_publishable_key=os.getenv('STRIPE_PUBLISHABLE_KEY'))
                             
    except Exception as e:
        logger.error(f"Error in enhanced parking booking: {e}")
        flash('Error loading parking booking page')
        return redirect(url_for('stadiums'))

@app.route('/payment/success')
@login_required
def payment_success():
    """Payment success page"""
    payment_intent_id = request.args.get('payment_intent')
    
    if payment_intent_id:
        try:
            # Get payment status
            status_result = get_payment_status(payment_intent_id)
            
            if isinstance(status_result, tuple):
                status_data = status_result[0]
            else:
                status_data = status_result
                
        except Exception as e:
            logger.error(f"Error getting payment status: {e}")
            status_data = None
    else:
        status_data = None
    
    return render_template('payment_success.html', payment_data=status_data)

@app.route('/payment/cancel')
@login_required
def payment_cancel():
    """Payment cancel page"""
    return render_template('payment_cancel.html')

# ==========================================
# ENHANCED ADMIN ROUTES WITH REAL-TIME
# ==========================================

@app.route('/admin/live-dashboard')
@login_required
@admin_required
def admin_live_dashboard():
    """Admin live dashboard with real-time features"""
    try:
        from realtime import get_realtime_stats
        
        # Get administered stadiums
        administered_stadiums = current_user.get_administered_stadiums()
        stadiums_data = []
        
        for stadium_id in administered_stadiums:
            stadium = Stadium.query.get(stadium_id)
            if stadium:
                # Get today's events with live status
                today_events = Event.query.filter(
                    Event.stadium_id == stadium_id,
                    Event.event_date == datetime.utcnow().date()
                ).all()
                
                # Get real-time occupancy
                total_seats = Seat.query.filter_by(stadium_id=stadium_id).count()
                booked_seats = 0
                
                for event in today_events:
                    booked_seats += Ticket.query.join(Seat).filter(
                        Ticket.event_id == event.id,
                        Seat.stadium_id == stadium_id,
                        Ticket.ticket_status == 'Booked'
                    ).count()
                
                occupancy_percentage = (booked_seats / total_seats * 100) if total_seats > 0 else 0
                
                stadiums_data.append({
                    'stadium': stadium,
                    'today_events': today_events,
                    'occupancy_percentage': round(occupancy_percentage, 2),
                    'total_seats': total_seats,
                    'booked_seats': booked_seats
                })
        
        # Get real-time stats
        realtime_stats = get_realtime_stats()
        
        return render_template('admin_live_dashboard.html', 
                             stadiums_data=stadiums_data,
                             realtime_stats=realtime_stats)
                             
    except Exception as e:
        logger.error(f"Error in live dashboard: {e}")
        flash('Error loading live dashboard')
        return redirect(url_for('admin_dashboard'))

# ==========================================
# ORIGINAL ROUTES (Import from existing app.py)
# ==========================================

# Import and register all your existing routes here
# For now, I'll add the essential ones

@app.route('/')
def index():
    """Home page with enhanced features"""
    try:
        # Get upcoming events
        upcoming_events = Event.query.filter(
            Event.event_date >= datetime.utcnow().date()
        ).order_by(Event.event_date).limit(6).all()
        
        # Get featured stadiums
        stadiums = Stadium.query.limit(4).all()
        
        return render_template('index.html', 
                             upcoming_events=upcoming_events, 
                             stadiums=stadiums)
    except Exception as e:
        logger.error(f"Error loading home page: {e}")
        return render_template('index.html', 
                             upcoming_events=[], 
                             stadiums=[])

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard with enhanced features"""
    if current_user.is_admin():
        return redirect(url_for('admin_live_dashboard'))
    
    try:
        # Get user's bookings with payment status
        user_bookings = Booking.query.filter_by(customer_id=current_user.id).all()
        
        # Get user's tickets
        user_tickets = Ticket.query.filter_by(customer_id=current_user.id).all()
        
        # Get upcoming events for recommendations
        upcoming_events = Event.query.filter(
            Event.event_date >= datetime.utcnow().date()
        ).order_by(Event.event_date).limit(4).all()
        
        return render_template('dashboard.html',
                             bookings=user_bookings,
                             tickets=user_tickets,
                             upcoming_events=upcoming_events)
                             
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        flash('Error loading dashboard')
        return render_template('dashboard.html', bookings=[], tickets=[], upcoming_events=[])

# ==========================================
# DATABASE INITIALIZATION
# ==========================================

def init_enhanced_db():
    """Initialize database with enhanced features"""
    try:
        print("🏗️ Initializing enhanced database...")
        
        # Create original tables
        db.create_all()
        
        # Create enhanced tables
        try:
            from enhanced_models import create_enhanced_tables
            create_enhanced_tables()
            print("✅ Enhanced tables created")
        except Exception as e:
            print(f"⚠️ Enhanced tables creation failed: {e}")
        
        print("✅ Database initialization complete")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

# ==========================================
# APPLICATION STARTUP
# ==========================================

if __name__ == '__main__':
    # Initialize enhanced database
    with app.app_context():
        if not init_enhanced_db():
            print("❌ Database initialization failed. Exiting.")
            exit(1)
    
    # Start the application
    if socketio:
        print("🚀 Starting CricVerse with real-time features...")
        socketio.run(app, 
                    debug=os.getenv('DEBUG', 'False').lower() == 'true',
                    host='0.0.0.0',
                    port=int(os.getenv('PORT', 5000)))
    else:
        print("🚀 Starting CricVerse without real-time features...")
        app.run(debug=os.getenv('DEBUG', 'False').lower() == 'true',
                host='0.0.0.0',
                port=int(os.getenv('PORT', 5000)))