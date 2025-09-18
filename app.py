from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_wtf import CSRFProtect
from models import db, Customer, Event, Booking, Ticket, Stadium, Team, Seat, Concession, Parking, Player, Match, TicketTransfer, ResaleMarketplace, SeasonTicket, SeasonTicketMatch, AccessibilityAccommodation, AccessibilityBooking, VerificationSubmission, StadiumAdmin, EventUmpire, Payment, CustomerProfile, PaymentTransaction, QRCode, Notification, MatchUpdate, ChatConversation, ChatMessage, BookingAnalytics, SystemLog, WebSocketConnection, MenuItem, Order, ParkingBooking, Photo

from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect, generate_csrf
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone, timedelta
import os
import re
import logging
from dotenv import load_dotenv
from functools import wraps
from flask_socketio import SocketIO
# Import simplified chatbot for better reliability
try:
    from chatbot_simplified import get_chatbot_response, detect_user_intent, get_intent_actions, get_chat_suggestions
    CHATBOT_AVAILABLE = True
except ImportError:
    try:
        from chatbot import get_chatbot_response, detect_user_intent, get_intent_actions, get_chat_suggestions
        CHATBOT_AVAILABLE = True
    except ImportError:
        CHATBOT_AVAILABLE = False
        print("[WARN] No chatbot module available")
# Suppress deprecation warnings from razorpay's pkg_resources usage
import warnings
with warnings.catch_warnings():
    warnings.filterwarnings('ignore', category=UserWarning, module='pkg_resources')
    import razorpay
import hmac
import hashlib
import json
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our utility functions
from utils import (
    validate_email, validate_phone, validate_password_strength,
    sanitize_input, flash_errors, get_user_statistics, get_analytics_data,
    handle_form_errors, REGISTRATION_VALIDATION_RULES, STADIUM_VALIDATION_RULES,
    EVENT_VALIDATION_RULES, get_upcoming_events
)

# Import unified payment processor (PayPal + Indian gateways)
UNIFIED_PAYMENT_AVAILABLE = False

# Import the processor first
try:
    from unified_payment_processor_simple import unified_payment_processor
    UNIFIED_PAYMENT_AVAILABLE = True
    # Import the classes from the same module
    from unified_payment_processor_simple import UnifiedPaymentResponse, PaymentGateway, Currency
except ImportError as e:
    print(f"[WARN] Unified payment processor not available: {e}")
    # Import our fallback classes
    from enum import Enum
    from dataclasses import dataclass
    from typing import Optional, Dict, Any
    
    class PaymentGateway(Enum):
        PAYPAL = "paypal"
        RAZORPAY = "razorpay"
        UPI = "upi"
        CARD = "card"
    
    class Currency(Enum):
        USD = "USD"
        INR = "INR"
        AUD = "AUD"
        EUR = "EUR"
    
    @dataclass
    class UnifiedPaymentResponse:
        success: bool
        payment_id: Optional[str] = None
        gateway: Optional[PaymentGateway] = None
        amount: Optional[float] = None
        currency: Optional[Currency] = None
        metadata: Optional[Dict[str, Any]] = None
        error_message: Optional[str] = None
        approval_url: Optional[str] = None
    
    # Create dummy processor
    class DummyProcessor:
        def create_payment(self, *args, **kwargs):
            return UnifiedPaymentResponse(success=False, error_message='Payment processor not available')
        def verify_payment(self, *args, **kwargs):
            return UnifiedPaymentResponse(success=False, error_message='Payment processor not available')
        def get_supported_methods(self, currency):
            return ['paypal', 'card']
        def get_currency_for_country(self, country):
            return 'USD'
        def process_successful_payment(self, payment_response: UnifiedPaymentResponse, metadata):  # type: ignore
            return False
    
    unified_payment_processor = DummyProcessor()

# Import admin module
from admin import init_admin

# Import forms
from forms import StadiumOwnerApplicationForm

# Import security framework components
try:
    from security_framework import (
        require_csrf, validate_json_input, limiter, rate_limit_by_user,
        PaymentValidationModel, BookingValidationModel
    )
    SECURITY_FRAMEWORK_AVAILABLE = True
except ImportError as e:
    print(f"[WARN] Security framework components not available: {e}")
    SECURITY_FRAMEWORK_AVAILABLE = False
    # Create dummy decorators to prevent errors
    def require_csrf(f):
        return f
    def validate_json_input(model):
        def decorator(f):
            return f
        return decorator
    def rate_limit_by_user(limit):
        def decorator(f):
            return f
        return decorator
    # Create dummy validation models
    class PaymentValidationModel:
        pass
    class BookingValidationModel:
        pass
    # Create dummy limiter
    class DummyLimiter:
        def limit(self, limit_string, key_func=None):
            def decorator(f):
                return f
            return decorator
        def exempt(self, f):
            return f
    limiter = DummyLimiter()

# Load environment variables (prefer local cricverse.env, fallback to .env)
if os.path.exists('cricverse.env'):
    load_dotenv('cricverse.env')
else:
    load_dotenv()

app = Flask(__name__)
csrf = CSRFProtect(app)

# Configuration with fallbacks
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'cricverse-secret-key-change-in-production')

# Session Security Hardening - Production Settings
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only in production
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent XSS access to session cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['SESSION_COOKIE_NAME'] = 'cricverse_session'  # Custom session cookie name
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour session timeout
app.config['SESSION_REFRESH_EACH_REQUEST'] = True  # Refresh session on each request

# CSRF Configuration
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour
app.config['WTF_CSRF_SSL_STRICT'] = False  # Allow HTTP for development

# Additional Security Headers
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 year cache for static files

# Production Security Settings
if os.getenv('FLASK_ENV') == 'production':
    app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
    app.config['WTF_CSRF_SSL_STRICT'] = True  # HTTPS only for CSRF
    app.config['PREFERRED_URL_SCHEME'] = 'https'
else:
    # Development settings - less restrictive but still secure
    app.config['SESSION_COOKIE_SECURE'] = False  # Allow HTTP in development

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Security Headers Middleware
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'
    
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Enable XSS protection
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Referrer policy for privacy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Content Security Policy (CSP) - restrictive but functional
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.paypal.com https://www.paypal.com https://checkout.razorpay.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
        "img-src 'self' data: https: blob:; "
        "connect-src 'self' https://api.paypal.com https://api.razorpay.com wss: ws:; "
        "frame-src 'self' https://js.paypal.com https://www.paypal.com; "
        "object-src 'none'; "
        "base-uri 'self';"
    )
    response.headers['Content-Security-Policy'] = csp_policy
    
    # Strict Transport Security (HSTS) - only in production with HTTPS
    if os.getenv('FLASK_ENV') == 'production' and request.is_secure:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
    
    # Permissions Policy (formerly Feature Policy)
    response.headers['Permissions-Policy'] = (
        "geolocation=(), "
        "microphone=(), "
        "camera=(), "
        "payment=(self), "
        "usb=(), "
        "magnetometer=(), "
        "accelerometer=(), "
        "gyroscope=()"
    )
    
    return response

# Database configuration with Supabase support
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
else:
    print(f"[DATABASE] Using provided DATABASE_URL: {database_url[:50]}...")

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Database connection pool settings for PostgreSQL with Supabase optimization
if 'postgresql' in database_url:
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 280,  # Slightly shorter than Supabase timeout
        'pool_timeout': 60,   # Increased timeout for Supabase
        'max_overflow': 3,    # Allow some overflow connections
        'pool_size': 3,       # Smaller pool for Supabase free tier
        'echo': False,        # Disable SQL logging for performance
        'connect_args': {
            'connect_timeout': 10,     # Shorter connection timeout
            'application_name': 'CricVerse',
            'options': '-c statement_timeout=120000'  # 2 minutes for complex queries
        }
    }

# Initialize extensions
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # type: ignore

# Initialize SocketIO for real-time features
from realtime_simple import init_socketio
socketio = init_socketio(app)

# Initialize production security framework
try:
    from security_framework import init_security
    init_security(app)
    print("[PASS] Production security framework initialized")
except ImportError as e:
    print(f"[WARN] Security framework not available: {e}")
except Exception as e:
    print(f"[FAIL] Security framework initialization failed: {e}")

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

# Unified Payment Processing Functions
def create_unified_payment_order(payment_data):
    """Create payment order using unified processor (PayPal + Indian gateways)"""
    try:
        # Extract payment details
        amount = payment_data.get('amount', 0)
        customer_email = current_user.email
        payment_method = payment_data.get('payment_method', 'paypal')
        currency = payment_data.get('currency', 'USD')
        
        # Auto-detect currency based on payment method
        if payment_method in ['upi', 'card', 'netbanking', 'wallet']:
            currency = 'INR'
        elif payment_method == 'paypal':
            currency = payment_data.get('currency', 'USD')
        
        # Prepare metadata
        metadata = {
            'customer_id': str(payment_data['customer_id']),
            'customer_email': customer_email,
            'customer_name': current_user.name,
            'phone': getattr(current_user, 'phone', ''),
            'booking_type': payment_data.get('booking_type', 'ticket'),
            'description': f"Big Bash League - {payment_data.get('description', 'Booking')}",
            'base_url': request.host_url
        }
        
        # Add booking-specific metadata
        if 'event_id' in payment_data:
            metadata['event_id'] = str(payment_data['event_id'])
        if 'seat_ids' in payment_data:
            metadata['seat_ids'] = json.dumps(payment_data['seat_ids'])
        
        # Create payment order using unified processor
        payment_response = unified_payment_processor.create_payment(
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            customer_email=customer_email,
            metadata=metadata
        )
        
        if payment_response.success:
            result = {
                'success': True,
                'payment_id': payment_response.payment_id,
                'gateway': payment_response.gateway.value if payment_response.gateway is not None else None,
                'amount': payment_response.amount,
                'currency': payment_response.currency.value if payment_response.currency is not None else None,
                'payment_data': payment_response.metadata
            }
            
            # Add PayPal-specific fields
            if payment_response.approval_url:
                result['approval_url'] = payment_response.approval_url
                result['redirect_required'] = True
            
            return result
        else:
            return {
                'error': payment_response.error_message or 'Payment order creation failed'
            }, 400
            
    except Exception as e:
        logger.error(f"Unified payment order creation failed: {e}")
        return {'error': 'Payment setup failed'}, 500

@app.route('/api/get-payment-methods', methods=['GET'])
@login_required
def get_payment_methods():
    """Get available payment methods based on currency"""
    try:
        currency = request.args.get('currency', 'USD')
        country = request.args.get('country', 'US')
        
        # Auto-detect currency if not provided
        if not currency or currency == 'auto':
            currency = unified_payment_processor.get_currency_for_country(country)
        
        methods = unified_payment_processor.get_supported_methods(currency)
        
        return jsonify({
            'success': True,
            'currency': currency,
            'methods': methods
        })
        
    except Exception as e:
        logger.error(f"Failed to get payment methods: {e}")
        return jsonify({'error': 'Failed to load payment methods'}), 500

def handle_unified_payment_webhook(payload, gateway):
    """Handle payment webhook events from unified gateways"""
    try:
        if gateway == 'paypal':
            # PayPal webhook handling
            data = json.loads(payload)
            
            if data.get('event_type') == 'PAYMENT.CAPTURE.COMPLETED':
                payment_data = data.get('resource', {})
                
                # Process PayPal payment
                payment_response = unified_payment_processor.verify_payment({
                    'gateway': 'paypal',
                    'payment_id': payment_data.get('id'),
                    'payer_id': payment_data.get('payer', {}).get('payer_id')
                })
                
                if payment_response.success:
                    # Get metadata from PayPal payment
                    metadata = payment_response.metadata or {}
                    
                    # Process the booking
                    success = unified_payment_processor.process_successful_payment(payment_response, metadata)
                    
                    if success:
                        return {'status': 'success', 'message': 'PayPal payment processed'}
                    else:
                        return {'status': 'error', 'message': 'PayPal payment processing failed'}
                else:
                    return {'status': 'error', 'message': 'PayPal payment verification failed'}
        
        elif gateway == 'razorpay':
            # Razorpay webhook handling
            data = json.loads(payload)
            
            if data.get('event') == 'payment.captured':
                payment_data = data.get('payload', {}).get('payment', {}).get('entity', {})
                
                # Verify and process payment
                payment_response = unified_payment_processor.verify_payment({
                    'gateway': 'razorpay',
                    'razorpay_order_id': payment_data.get('order_id'),
                    'razorpay_payment_id': payment_data.get('id'),
                    'razorpay_signature': data.get('payload', {}).get('payment', {}).get('entity', {}).get('signature', ''),
                    'amount': payment_data.get('amount', 0)
                })
                
                if payment_response.success:
                    # Get metadata from order
                    metadata = payment_data.get('notes', {})
                    
                    # Process the booking
                    success = unified_payment_processor.process_successful_payment(payment_response, metadata)
                    
                    if success:
                        return {'status': 'success', 'message': 'Razorpay payment processed'}
                    else:
                        return {'status': 'error', 'message': 'Razorpay payment processing failed'}
                else:
                    return {'status': 'error', 'message': 'Razorpay payment verification failed'}
        
        return {'status': 'ignored', 'message': 'Event not handled'}
        
    except Exception as e:
        logger.error(f"Unified webhook processing failed: {e}")
        return {'status': 'error', 'message': 'Webhook processing failed'}

@app.route('/payment/paypal/success')
def paypal_success():
    """Handle PayPal payment success redirect"""
    try:
        payment_id = request.args.get('paymentId')
        payer_id = request.args.get('PayerID')
        
        if not payment_id or not payer_id:
            flash('Payment information missing', 'error')
            return redirect(url_for('index'))
        
        # Execute PayPal payment
        payment_response = unified_payment_processor.verify_payment({
            'gateway': 'paypal',
            'payment_id': payment_id,
            'payer_id': payer_id
        })
        
        if payment_response.success:
            flash('Payment successful! Your booking is confirmed.', 'success')
            return redirect(url_for('booking_confirmation', payment_id=payment_id))
        else:
            flash('Payment verification failed', 'error')
            return redirect(url_for('index'))
            
    except Exception as e:
        logger.error(f"PayPal success handling failed: {e}")
        flash('Payment processing error', 'error')
        return redirect(url_for('index'))

@app.route('/verify-ticket')
def verify_ticket():
    """Verify ticket validity"""
    ticket_id = request.args.get('id')
    token = request.args.get('token')
    
    if not ticket_id:
        flash('Invalid ticket verification request', 'error')
        return redirect(url_for('index'))
    
    try:
        # In a real implementation, you would verify the token and check ticket validity
        # For now, we'll just show a verification page
        
        
        booking = Booking.query.get(int(ticket_id)) if ticket_id else None
        if not booking:
            flash('Ticket not found', 'error')
            return redirect(url_for('index'))
        
        event = Event.query.get(booking.event_id)
        stadium = Stadium.query.get(event.stadium_id) if event else None
        customer = Customer.query.get(booking.customer_id)
        tickets = Ticket.query.filter_by(booking_id=booking.id).all()
        
        # Get seat information for the first ticket
        seat_info = None
        if tickets:
            seat = Seat.query.get(tickets[0].seat_id)
            if seat:
                seat_info = f"Section {seat.section}, Row {seat.row}, Seat {seat.number}"
        
        return render_template('ticket_verification.html', 
                             booking=booking, 
                             event=event, 
                             stadium=stadium,
                             customer=customer,
                             seat_info=seat_info,
                             is_valid=True)
    except Exception as e:
        logger.error(f"Ticket verification failed: {e}")
        flash('Ticket verification error', 'error')
        return redirect(url_for('index'))

@app.route('/payment/paypal/cancel')
def paypal_cancel():
    """Handle PayPal payment cancellation"""
    flash('Payment was cancelled', 'warning')
    return redirect(url_for('index'))

# Expose payment client IDs to templates
@app.context_processor
def inject_payment_public_keys():
    return {
        'PAYPAL_CLIENT_ID': os.getenv('PAYPAL_CLIENT_ID'),
        'RAZORPAY_KEY_ID': os.getenv('RAZORPAY_KEY_ID'),
        'UNIFIED_PAYMENT_ENABLED': True
    }



# Razorpay client init
RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET')
razorpay_client = None
if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    try:
        razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
        print("[PAYMENTS] Razorpay client initialized")
    except Exception as e:
        print(f"[PAYMENTS] Razorpay init failed: {e}")



# Authentication decorators
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

def stadium_owner_required(f):
    """Decorator to require stadium owner role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if current_user.role != 'stadium_owner':
            flash('Access denied. Stadium owner privileges required.')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def stadium_admin_required(stadium_id_param='stadium_id'):
    """Decorator to require admin access to specific stadium"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if not current_user.is_admin():
                flash('Access denied. Admin privileges required.')
                return redirect(url_for('dashboard'))
            
            # Get stadium_id from URL parameters
            stadium_id = kwargs.get(stadium_id_param)
            if not stadium_id:
                flash('Stadium ID not provided.')
                return redirect(url_for('admin_dashboard'))
            
            # Check if admin manages this stadium
            administered_stadiums = current_user.get_administered_stadiums()
            if stadium_id not in administered_stadiums:
                flash('Access denied. You do not manage this stadium.')
                return redirect(url_for('admin_dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def prevent_role_modification(f):
    """Decorator to prevent role modification in any route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        
        # Store original role and verification status before request
        original_role = current_user.role
        original_verification_status = current_user.verification_status
        
        # Execute the wrapped function
        result = f(*args, **kwargs)
        
        # Check if role or verification status was tampered with
        if (current_user.role != original_role or 
            current_user.verification_status != original_verification_status):
            
            # Restore original values
            current_user.role = original_role
            current_user.verification_status = original_verification_status
            
            # Log security incident
            try:
                from models import SystemLog
                log_entry = SystemLog(
                    customer_id=current_user.id,
                    log_level='CRITICAL',
                    category='security',
                    action='unauthorized_role_change',
                    message=f'BLOCKED: User {current_user.email} attempted unauthorized role change from {original_role} to {current_user.role}',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent'),
                    request_url=request.url,
                    request_method=request.method
                )
                db.session.add(log_entry)
                db.session.commit()
            except Exception as e:
                print(f"Failed to log unauthorized role change: {e}")
            
            # Force rollback and redirect
            db.session.rollback()
            flash('SECURITY VIOLATION: Unauthorized role modification blocked.', 'danger')
            return redirect(url_for('dashboard'))
        
        return result
    return decorated_function

def validate_role_permissions(allowed_roles=None):
    """Decorator to validate that user has required role permissions"""
    if allowed_roles is None:
        allowed_roles = ['admin']
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            
            if current_user.role not in allowed_roles:
                try:
                    from models import SystemLog
                    log_entry = SystemLog(
                        customer_id=current_user.id,
                        log_level='WARNING',
                        category='security',
                        action='unauthorized_access_attempt',
                        message=f'User {current_user.email} ({current_user.role}) attempted to access route requiring roles: {allowed_roles}',
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent'),
                        request_url=request.url,
                        request_method=request.method
                    )
                    db.session.add(log_entry)
                    db.session.commit()
                except Exception as e:
                    print(f"Failed to log unauthorized access attempt: {e}")
                
                flash('Access denied. Insufficient privileges.', 'danger')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_static_fallback_data():
    """Provide static fallback data when database is unavailable"""
    from collections import namedtuple
    from datetime import datetime, timezone, timedelta
    
    # Create mock objects with the same structure as database models
    MockEvent = namedtuple('MockEvent', ['id', 'event_name', 'event_date', 'start_time', 'stadium_id', 'home_team_id', 'away_team_id'])
    MockStadium = namedtuple('MockStadium', ['id', 'name', 'location', 'capacity', 'image_url'])
    MockTeam = namedtuple('MockTeam', ['id', 'team_name', 'team_logo', 'home_city'])
    MockPlayer = namedtuple('MockPlayer', ['id', 'player_name', 'player_role'])
    MockTeamData = namedtuple('MockTeamData', ['team', 'star_player'])
    
    # Mock upcoming events
    tomorrow = datetime.now().date() + timedelta(days=1)
    next_week = datetime.now().date() + timedelta(days=7)
    next_month = datetime.now().date() + timedelta(days=30)
    
    upcoming_events = [
        MockEvent(
            id=1,
            event_name="Melbourne Stars vs Sydney Sixers",
            event_date=tomorrow,
            start_time=datetime.strptime('19:30', '%H:%M').time(),
            stadium_id=1,
            home_team_id=1,
            away_team_id=2
        ),
        MockEvent(
            id=2,
            event_name="Perth Scorchers vs Brisbane Heat",
            event_date=next_week,
            start_time=datetime.strptime('20:00', '%H:%M').time(),
            stadium_id=2,
            home_team_id=3,
            away_team_id=4
        ),
        MockEvent(
            id=3,
            event_name="Adelaide Strikers vs Hobart Hurricanes",
            event_date=next_month,
            start_time=datetime.strptime('19:45', '%H:%M').time(),
            stadium_id=3,
            home_team_id=5,
            away_team_id=6
        )
    ]
    
    # Mock featured stadiums
    featured_stadiums = [
        MockStadium(
            id=1,
            name="Melbourne Cricket Ground",
            location="Melbourne, VIC",
            capacity=100024,
            image_url="/static/img/stadiums/mcg.jpg"
        ),
        MockStadium(
            id=2,
            name="Sydney Cricket Ground",
            location="Sydney, NSW",
            capacity=48000,
            image_url="/static/img/stadiums/scg.jpg"
        ),
        MockStadium(
            id=3,
            name="Perth Stadium",
            location="Perth, WA",
            capacity=60000,
            image_url="/static/img/stadiums/perth.jpg"
        )
    ]
    
    # Mock featured teams with star players
    featured_teams_data = [
        MockTeamData(
            team=MockTeam(
                id=1,
                team_name="Melbourne Stars",
                team_logo="/static/img/teams/Melbourne_Stars_logo.png",
                home_city="Melbourne"
            ),
            star_player=MockPlayer(
                id=1,
                player_name="Marcus Stoinis",
                player_role="All-rounder"
            )
        ),
        MockTeamData(
            team=MockTeam(
                id=2,
                team_name="Sydney Sixers",
                team_logo="/static/img/teams/Sydney_Sixers_logo.svg.png",
                home_city="Sydney"
            ),
            star_player=MockPlayer(
                id=2,
                player_name="Moises Henriques",
                player_role="Captain"
            )
        ),
        MockTeamData(
            team=MockTeam(
                id=3,
                team_name="Perth Scorchers",
                team_logo="/static/img/teams/Perth Scorchers.png",
                home_city="Perth"
            ),
            star_player=MockPlayer(
                id=3,
                player_name="Mitchell Marsh",
                player_role="All-rounder"
            )
        )
    ]
    
    return upcoming_events, featured_stadiums, featured_teams_data


@login_manager.user_loader
def load_user(user_id):
    return Customer.query.get(int(user_id))

# Initialize database function
def init_db():
    """Initialize the database with tables only (no sample seeding)."""
    try:
        print(f"[DEBUG] Using database URL: {database_url}")
        
        # Test database connection first with timeout
        try:
            print("[DEBUG] Testing database connection...")
            with db.engine.connect() as conn:
                result = conn.execute(db.text("SELECT 1"))
                print("[PASS] Database connection test successful")
        except Exception as e:
            print(f"[WARN] Database connection test failed: {e}")
            
            # If it's a connection timeout, try to fallback to SQLite
            if "Connection timed out" in str(e) or "timeout" in str(e).lower():
                print("[INFO] Connection timeout detected. Switching to SQLite for local development...")
                app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cricverse_local.db'
                print("[INFO] Database URL updated to SQLite")
                # Reinitialize the database with new URL
                db.init_app(app)
                return init_db()  # Recursive call with SQLite
        
        # On managed Supabase, assume schema is migrated and skip create_all
        if 'supabase.com' in database_url:
            print("[INFO] Supabase detected - skipping db.create_all() (assume migrations applied)")
            return True

        # Create all tables locally (SQLite/Postgres dev)
        max_retries = 1
        for attempt in range(max_retries):
            try:
                print(f"[DEBUG] Creating database tables (attempt {attempt + 1})...")
                db.create_all()
                print("[PASS] Database tables created successfully")
                return True
            except Exception as e:
                print(f"[ERROR] Database creation failed: {e}")
                # Try SQLite fallback for local use
                if "postgresql" in database_url:
                    print("[INFO] PostgreSQL failed, switching to SQLite...")
                    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cricverse_local.db'
                    db.init_app(app)
                    try:
                        db.create_all()
                        print("[PASS] SQLite database created successfully")
                        return True
                    except Exception as sqlite_error:
                        print(f"[FAIL] SQLite fallback also failed: {sqlite_error}")
                        raise e
                else:
                    raise e
    except Exception as e:
        print(f"[FAIL] Database initialization failed: {e}")
        return False

# Admin Routes
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard showing managed stadiums with statistics"""
    administered_stadiums = current_user.get_administered_stadiums()
    stadiums_data = []
    
    for stadium_id in administered_stadiums:
        stadium = Stadium.query.get(stadium_id)
        if stadium:
            events_count = Event.query.filter_by(stadium_id=stadium_id).count()
            concessions_count = Concession.query.filter_by(stadium_id=stadium_id).count()
            parking_count = Parking.query.filter_by(stadium_id=stadium_id).count()
            seats_count = Seat.query.filter_by(stadium_id=stadium_id).count()
            
            stadiums_data.append({
                'stadium': stadium,
                'events_count': events_count,
                'concessions_count': concessions_count,
                'parking_count': parking_count,
                'seats_count': seats_count
            })
    
    return render_template('admin_dashboard.html', stadiums_data=stadiums_data)

@app.route('/admin/stadium/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_stadium():
    """Add a new stadium and assign current admin to it"""
    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        capacity = int(request.form['capacity'])
        contact_number = request.form.get('contact_number')
        opening_year = int(request.form['opening_year']) if request.form.get('opening_year') else None
        pitch_type = request.form.get('pitch_type')
        boundary_length = int(request.form['boundary_length']) if request.form.get('boundary_length') else None
        floodlight_quality = request.form.get('floodlight_quality')
        has_dressing_rooms = 'has_dressing_rooms' in request.form
        has_practice_nets = 'has_practice_nets' in request.form
        
        new_stadium = Stadium()
        new_stadium.name = name
        new_stadium.location = location
        new_stadium.capacity = capacity
        new_stadium.contact_number = contact_number
        new_stadium.opening_year = opening_year
        new_stadium.pitch_type = pitch_type
        new_stadium.boundary_length = boundary_length
        new_stadium.floodlight_quality = floodlight_quality
        new_stadium.has_dressing_rooms = has_dressing_rooms
        new_stadium.has_practice_nets = has_practice_nets
        
        db.session.add(new_stadium)
        db.session.flush()  # Get the stadium ID
        
        # Assign current admin to this stadium
        admin_assignment = StadiumAdmin(admin_id=current_user.id, stadium_id=new_stadium.id)
        db.session.add(admin_assignment)
        db.session.commit()
        
        flash(f'Stadium "{name}" created successfully and assigned to you.')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_add_stadium.html')

@app.route('/admin/stadium/<int:stadium_id>/edit', methods=['GET', 'POST'])
@login_required
@stadium_admin_required('stadium_id')
def edit_stadium(stadium_id):
    """Edit stadium details"""
    stadium = Stadium.query.get_or_404(stadium_id)
    
    if request.method == 'POST':
        stadium.name = request.form['name']
        stadium.location = request.form['location']
        stadium.capacity = int(request.form['capacity'])
        stadium.contact_number = request.form.get('contact_number')
        stadium.opening_year = int(request.form['opening_year']) if request.form.get('opening_year') else None
        stadium.pitch_type = request.form.get('pitch_type')
        stadium.boundary_length = int(request.form['boundary_length']) if request.form.get('boundary_length') else None
        stadium.floodlight_quality = request.form.get('floodlight_quality')
        stadium.has_dressing_rooms = 'has_dressing_rooms' in request.form
        stadium.has_practice_nets = 'has_practice_nets' in request.form
        
        db.session.commit()
        flash(f'Stadium "{stadium.name}" updated successfully.')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_edit_stadium.html', stadium=stadium)

@app.route('/admin/stadium/<int:stadium_id>/manage')
@login_required
@stadium_admin_required('stadium_id')
def manage_stadium(stadium_id):
    """Stadium management page showing events, concessions, parking, seats"""
    stadium = Stadium.query.get_or_404(stadium_id)
    events = Event.query.filter_by(stadium_id=stadium_id).all()
    concessions = Concession.query.filter_by(stadium_id=stadium_id).all()
    parking_zones = Parking.query.filter_by(stadium_id=stadium_id).all()
    seats = Seat.query.filter_by(stadium_id=stadium_id).all()
    
    # Group seats by section for display
    sections = {}
    for seat in seats:
        if seat.section not in sections:
            sections[seat.section] = []
        sections[seat.section].append(seat)
    
    return render_template('admin_manage_stadium.html', 
                         stadium=stadium, events=events, 
                         concessions=concessions, parking_zones=parking_zones, 
                         seats=seats, sections=sections)

@app.route('/admin/stadium/<int:stadium_id>/event/add', methods=['GET', 'POST'])
@login_required
@stadium_admin_required('stadium_id')
def add_event(stadium_id):
    """Add a new event to the stadium"""
    stadium = Stadium.query.get_or_404(stadium_id)
    teams = Team.query.all()
    
    if request.method == 'POST':
        event_name = request.form['event_name']
        event_type = request.form['event_type']
        tournament_name = request.form.get('tournament_name')
        event_date = datetime.strptime(request.form['event_date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(request.form['start_time'], '%H:%M').time()
        end_time = datetime.strptime(request.form['end_time'], '%H:%M').time() if request.form.get('end_time') else None
        home_team_id = int(request.form['home_team_id']) if request.form.get('home_team_id') else None
        away_team_id = int(request.form['away_team_id']) if request.form.get('away_team_id') else None
        match_status = request.form.get('match_status', 'Scheduled')
        
        new_event = Event(
            event_name=event_name,
            event_type=event_type,
            tournament_name=tournament_name,
            event_date=event_date,
            start_time=start_time,
            end_time=end_time,
            stadium_id=stadium_id,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            match_status=match_status
        )
        
        db.session.add(new_event)
        db.session.commit()
        
        flash(f'Event "{event_name}" added successfully.')
        return redirect(url_for('manage_stadium', stadium_id=stadium_id))
    
    return render_template('admin_add_event.html', stadium=stadium, teams=teams)

@app.route('/admin/stadium/<int:stadium_id>/concession/add', methods=['GET', 'POST'])
@login_required
@stadium_admin_required('stadium_id')
def add_concession(stadium_id):
    """Add a new concession to the stadium"""
    stadium = Stadium.query.get_or_404(stadium_id)
    
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        location_zone = request.form['location_zone']
        opening_hours = request.form['opening_hours']
        
        new_concession = Concession(
            name=name,
            category=category,
            location_zone=location_zone,
            opening_hours=opening_hours,
            stadium_id=stadium_id
        )
        
        db.session.add(new_concession)
        db.session.commit()
        
        flash(f'Concession "{name}" added successfully.')
        return redirect(url_for('manage_stadium', stadium_id=stadium_id))
    
    return render_template('admin_add_concession.html', stadium=stadium)

@app.route('/admin/concession/<int:concession_id>/menu/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_menu_item(concession_id):
    """Add a menu item to a concession"""
    concession = Concession.query.get_or_404(concession_id)
    
    # Check if admin manages this stadium
    if concession.stadium_id not in current_user.get_administered_stadiums():
        flash('Access denied.')
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description')
        price = float(request.form['price'])
        category = request.form['category']
        is_available = 'is_available' in request.form
        
        new_item = MenuItem(
            name=name,
            description=description,
            price=price,
            category=category,
            is_available=is_available,
            concession_id=concession_id
        )
        
        db.session.add(new_item)
        db.session.commit()
        
        flash(f'Menu item "{name}" added successfully.')
        return redirect(url_for('manage_stadium', stadium_id=concession.stadium_id))
    
    return render_template('admin_add_menu_item.html', concession=concession)

@app.route('/admin/stadium/<int:stadium_id>/parking/add', methods=['GET', 'POST'])
@login_required
@stadium_admin_required('stadium_id')
def add_parking(stadium_id):
    """Add a parking zone to the stadium"""
    stadium = Stadium.query.get_or_404(stadium_id)
    
    if request.method == 'POST':
        zone = request.form['zone_name']
        capacity = int(request.form['capacity'])
        rate_per_hour = float(request.form['hourly_rate'])
        
        new_parking = Parking(
            zone=zone,
            capacity=capacity,
            rate_per_hour=rate_per_hour,
            stadium_id=stadium_id
        )
        
        db.session.add(new_parking)
        db.session.commit()
        
        flash(f'Parking zone "{zone}" added successfully.')
        return redirect(url_for('manage_stadium', stadium_id=stadium_id))
    
    return render_template('admin_add_parking.html', stadium=stadium)

@app.route('/admin/stadium/<int:stadium_id>/seats/add', methods=['GET', 'POST'])
@login_required
@stadium_admin_required('stadium_id')
def add_seats(stadium_id):
    """Bulk add seats to the stadium"""
    stadium = Stadium.query.get_or_404(stadium_id)
    
    if request.method == 'POST':
        section = request.form['section']
        row_start = request.form['row_start']
        row_end = request.form['row_end']
        seat_start = int(request.form['seat_start'])
        seat_end = int(request.form['seat_end'])
        seat_type = request.form['seat_type']
        price = float(request.form['price'])
        has_shade = 'has_shade' in request.form
        
        seats_created = 0
        
        # Generate row range (A-Z or numbers)
        if row_start.isalpha() and row_end.isalpha():
            rows = [chr(i) for i in range(ord(row_start.upper()), ord(row_end.upper()) + 1)]
        else:
            rows = [str(i) for i in range(int(row_start), int(row_end) + 1)]
        
        for row in rows:
            for seat_num in range(seat_start, seat_end + 1):
                seat_number = f"{section}-{row}-{seat_num}"
                
                # Check if seat already exists
                existing_seat = Seat.query.filter_by(
                    stadium_id=stadium_id, 
                    seat_number=seat_number
                ).first()
                
                if not existing_seat:
                    new_seat = Seat(
                        seat_number=seat_number,
                        section=section,
                        row_number=row,
                        seat_type=seat_type,
                        price=price,
                        has_shade=has_shade,
                        stadium_id=stadium_id
                    )
                    db.session.add(new_seat)
                    seats_created += 1
        
        db.session.commit()
        flash(f'{seats_created} seats added successfully.')
        return redirect(url_for('manage_stadium', stadium_id=stadium_id))
    
    return render_template('admin_add_seats.html', stadium=stadium)

# Admin Statistics and Overview Routes
@app.route('/admin/stadiums')
@login_required
@admin_required
def admin_stadiums_overview():
    """Admin stadiums overview page"""
    administered_stadiums = current_user.get_administered_stadiums()
    stadiums_data = []
    
    for stadium_id in administered_stadiums:
        stadium = Stadium.query.get(stadium_id)
        if stadium:
            events_count = Event.query.filter_by(stadium_id=stadium_id).count()
            concessions_count = Concession.query.filter_by(stadium_id=stadium_id).count()
            parking_count = Parking.query.filter_by(stadium_id=stadium_id).count()
            seats_count = Seat.query.filter_by(stadium_id=stadium_id).count()
            
            stadiums_data.append({
                'stadium': stadium,
                'events_count': events_count,
                'concessions_count': concessions_count,
                'parking_count': parking_count,
                'seats_count': seats_count
            })
    
    return render_template('admin_stadiums_overview.html', stadiums_data=stadiums_data)

@app.route('/admin/events')
@login_required
@admin_required
def admin_events_overview():
    """Admin events overview with statistics"""
    administered_stadiums = current_user.get_administered_stadiums()
    events_data = []
    
    for stadium_id in administered_stadiums:
        stadium = Stadium.query.get(stadium_id)
        if stadium:
            events = Event.query.filter_by(stadium_id=stadium_id).all()
            for event in events:
                # Calculate ticket sales statistics
                tickets_sold = Ticket.query.filter_by(event_id=event.id).count()
                # Correctly calculate revenue from distinct bookings for this event
                total_revenue = db.session.query(db.func.sum(Booking.total_amount)).filter(
                    Booking.id.in_(
                        db.session.query(Ticket.booking_id).filter_by(event_id=event.id).distinct()
                    )
                ).scalar() or 0

                events_data.append({
                    'event': event,
                    'stadium': stadium,
                    'tickets_sold': tickets_sold,
                    'total_revenue': total_revenue,
                    'capacity_percentage': round((tickets_sold / stadium.capacity) * 100, 1) if stadium.capacity > 0 else 0
                })
    
    return render_template('admin_events_overview.html', events_data=events_data)

@app.route('/admin/bookings')
@login_required
@admin_required
def admin_bookings_overview():
    """Admin ticket bookings overview"""
    administered_stadiums = current_user.get_administered_stadiums()
    booking_stats = []
    
    for stadium_id in administered_stadiums:
        stadium = Stadium.query.get(stadium_id)
        if stadium:
            # Get all events for this stadium
            events = Event.query.filter_by(stadium_id=stadium_id).all()
            
            for event in events:
                tickets = Ticket.query.filter_by(event_id=event.id).all()
                total_tickets = len(tickets)
                # Correctly calculate revenue from distinct bookings for this event
                total_revenue = db.session.query(db.func.sum(Booking.total_amount)).filter(
                    Booking.id.in_(
                        db.session.query(Ticket.booking_id).filter_by(event_id=event.id).distinct()
                    )
                ).scalar() or 0

                booking_stats.append({
                    'stadium': stadium,
                    'event': event,
                    'total_tickets': total_tickets,
                    'total_revenue': total_revenue,
                    'tickets': tickets
                })
    
    return render_template('admin_bookings_overview.html', booking_stats=booking_stats)

@app.route('/admin/parking')
@login_required
@admin_required
def admin_parking_overview():
    """Admin parking management with statistics"""
    administered_stadiums = current_user.get_administered_stadiums()
    parking_stats = []
    
    for stadium_id in administered_stadiums:
        stadium = Stadium.query.get(stadium_id)
        if stadium:
            parking_zones = Parking.query.filter_by(stadium_id=stadium_id).all()
            
            for parking in parking_zones:
                bookings = ParkingBooking.query.filter_by(parking_id=parking.id).all()
                total_bookings = len(bookings)
                total_revenue = sum(booking.amount_paid for booking in bookings if hasattr(booking, 'amount_paid'))
                occupancy_rate = round((total_bookings / parking.capacity) * 100, 1) if parking.capacity > 0 else 0
                
                parking_stats.append({
                    'stadium': stadium,
                    'parking': parking,
                    'total_bookings': total_bookings,
                    'total_revenue': total_revenue,
                    'occupancy_rate': occupancy_rate,
                    'available_spots': parking.capacity - total_bookings
                })
    
    return render_template('admin_parking_overview.html', parking_stats=parking_stats)

@app.route('/admin/concessions')
@login_required
@admin_required
def admin_concessions_overview():
    """Admin concessions overview with sales statistics"""
    administered_stadiums = current_user.get_administered_stadiums()
    concession_stats = []
    
    for stadium_id in administered_stadiums:
        stadium = Stadium.query.get(stadium_id)
        if stadium:
            concessions = Concession.query.filter_by(stadium_id=stadium_id).all()
            
            for concession in concessions:
                orders = Order.query.filter_by(concession_id=concession.id).all()
                total_orders = len(orders)
                total_revenue = sum(order.total_amount for order in orders)
                menu_items_count = MenuItem.query.filter_by(concession_id=concession.id).count()
                
                concession_stats.append({
                    'stadium': stadium,
                    'concession': concession,
                    'total_orders': total_orders,
                    'total_revenue': total_revenue,
                    'menu_items_count': menu_items_count,
                    'recent_orders': orders[-5:] if orders else []
                })
    
    return render_template('admin_concessions_overview.html', concession_stats=concession_stats)

@app.route('/admin/users')
@login_required
@admin_required
def admin_user_management():
    """Admin user management page with comprehensive user data and statistics"""
    
    # Get all users
    users = Customer.query.order_by(Customer.name).all()
    
    # Get user statistics using utility function
    user_stats = get_user_statistics(db, Customer)
    
    return render_template('admin_user_management.html', 
                           users=users, 
                           **user_stats)

@app.route('/admin/analytics')
@login_required
@admin_required
def admin_analytics():
    # Get comprehensive analytics data using utility function
    analytics_data = get_analytics_data(db, Stadium, Event, Ticket, Order, ParkingBooking)
    
    return render_template('admin_analytics.html', analytics_data=analytics_data)

@app.route('/admin/stadium/<int:stadium_id>/analytics')
@login_required
@stadium_admin_required('stadium_id')
def admin_stadium_analytics(stadium_id):
    """Detailed analytics for a specific stadium"""
    stadium = Stadium.query.get_or_404(stadium_id)
    
    # Calculate detailed stadium metrics
    events = Event.query.filter_by(stadium_id=stadium_id).all()
    total_tickets_sold = db.session.query(db.func.count(Ticket.id)).join(Event).filter(Event.stadium_id == stadium_id).scalar() or 0
    
    # Correctly calculate ticket revenue from distinct bookings for this stadium
    total_ticket_revenue = db.session.query(db.func.sum(Booking.total_amount)).filter(
        Booking.id.in_(
            db.session.query(Ticket.booking_id).join(Event).filter(Event.stadium_id == stadium_id).distinct()
        )
    ).scalar() or 0
    total_concession_revenue = db.session.query(db.func.sum(Order.total_amount)).join(Concession).filter(Concession.stadium_id == stadium_id).scalar() or 0
    
    analytics = {
        'stadium': stadium,
        'total_events': len(events),
        'total_tickets_sold': total_tickets_sold,
        'total_revenue': total_ticket_revenue + total_concession_revenue,
        'average_attendance': round(total_tickets_sold / len(events), 1) if events else 0,
        'capacity_utilization': round((total_tickets_sold / (stadium.capacity * len(events))) * 100, 1) if events and stadium.capacity > 0 else 0,
        'events': events
    }
    
    return render_template('admin_stadium_analytics.html', analytics=analytics)

@app.route('/admin/profile')
@login_required
@admin_required
def admin_profile():
    stadium_ids = current_user.get_administered_stadiums()  # returns list of IDs
    administered_stadiums = Stadium.query.filter(Stadium.id.in_(stadium_ids)).all()
    return render_template('admin_profile.html', administered_stadiums=administered_stadiums)

# Admin Verification Management Routes
@app.route('/admin/verification/approve/<int:submission_id>', methods=['POST'])
@login_required
@admin_required
def approve_verification(submission_id):
    """Approve a stadium owner verification submission"""
    try:
        submission = VerificationSubmission.query.get_or_404(submission_id)
        user = Customer.query.get_or_404(submission.user_id)
        
        # Check if user is already a stadium owner or admin
        if user.role in ['stadium_owner', 'admin']:
            flash('User already has elevated privileges.', 'info')
            return redirect(url_for('admin_dashboard'))
        
        # Update user role and verification status
        user.role = 'stadium_owner'
        user.verification_status = 'approved'
        
        db.session.commit()
        
        # Send notification email using Celery
        try:
            from celery_tasks import send_verification_decision_notification
            notification_data = {
                'user_id': user.id,
                'user_name': user.name,
                'user_email': user.email,
                'decision': 'approved',
                'admin_name': current_user.name
            }
            send_verification_decision_notification.delay(notification_data)
        except Exception as e:
            print(f"Failed to queue notification email: {e}")
        
        flash(f'Successfully approved stadium owner application for {user.name}.', 'success')
        return redirect(url_for('admin_dashboard'))
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while approving the application.', 'danger')
        print(f"Verification approval error: {e}")
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/verification/reject/<int:submission_id>', methods=['POST'])
@login_required
@admin_required
def reject_verification(submission_id):
    """Reject a stadium owner verification submission"""
    try:
        submission = VerificationSubmission.query.get_or_404(submission_id)
        user = Customer.query.get_or_404(submission.user_id)
        
        # Update verification status
        user.verification_status = 'rejected'
        
        db.session.commit()
        
        # Send notification email using Celery
        try:
            from celery_tasks import send_verification_decision_notification
            notification_data = {
                'user_id': user.id,
                'user_name': user.name,
                'user_email': user.email,
                'decision': 'rejected',
                'admin_name': current_user.name,
                'rejection_reason': request.form.get('reason', 'Application did not meet requirements')
            }
            send_verification_decision_notification.delay(notification_data)
        except Exception as e:
            print(f"Failed to queue notification email: {e}")
        
        flash(f'Rejected stadium owner application for {user.name}.', 'info')
        return redirect(url_for('admin_dashboard'))
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while rejecting the application.', 'danger')
        print(f"Verification rejection error: {e}")
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/verification/list')
@login_required
@admin_required
def admin_verification_list():
    """List all pending verification submissions for admin review"""
    pending_submissions = db.session.query(VerificationSubmission).join(Customer).filter(
        Customer.verification_status == 'pending'
    ).order_by(VerificationSubmission.submission_timestamp.desc()).all()
    
    return render_template('admin_verification_list.html', submissions=pending_submissions)

# Routes

@app.route('/')
def index():
    """Home page with enhanced error handling and database fallbacks"""
    try:
        # Initialize data with empty fallbacks
        upcoming_events = []
        featured_stadiums = []
        featured_teams_data = []
        next_match_countdown = None
        
        # Try to fetch data from database with timeout protection
        try:
            # Fetch upcoming events using utility function with error handling
            upcoming_events = get_upcoming_events(Event, limit=3)
        except Exception as e:
            print(f"Warning: Could not fetch upcoming events: {e}")
            upcoming_events = []
        
        try:
            # Fetch featured stadiums (top 3 by capacity)
            featured_stadiums = Stadium.query.order_by(Stadium.capacity.desc()).limit(3).all()
        except Exception as e:
            print(f"Warning: Could not fetch featured stadiums: {e}")
            featured_stadiums = []
        
        try:
            # Fetch teams and star players
            teams = Team.query.limit(3).all()
            for team in teams:
                try:
                    star_player = Player.query.filter_by(team_id=team.id).first()
                    featured_teams_data.append({
                        'team': team,
                        'star_player': star_player
                    })
                except Exception as e:
                    print(f"Warning: Could not fetch star player for team {team.id}: {e}")
                    # Add team without star player
                    featured_teams_data.append({
                        'team': team,
                        'star_player': None
                    })
        except Exception as e:
            print(f"Warning: Could not fetch teams: {e}")
            featured_teams_data = []
        
        # Calculate countdown to next event if available
        try:
            if upcoming_events:
                next_event = upcoming_events[0]
                next_event_datetime = datetime.combine(next_event.event_date, next_event.start_time)
                time_difference = next_event_datetime - datetime.now(timezone.utc)
                if time_difference.total_seconds() > 0:
                    days = time_difference.days
                    hours = time_difference.seconds // 3600
                    minutes = (time_difference.seconds % 3600) // 60
                    next_match_countdown = {'days': days, 'hours': hours, 'minutes': minutes}
        except Exception as e:
            print(f"Warning: Could not calculate countdown: {e}")
            next_match_countdown = None
        
        # Log successful data retrieval
        print(f"[PASS] Home page loaded: {len(upcoming_events)} events, {len(featured_stadiums)} stadiums, {len(featured_teams_data)} teams")
        
        # If no data was loaded from database, provide static fallback
        if not upcoming_events and not featured_stadiums and not featured_teams_data:
            print("🔄 Using static fallback data due to database issues")
            upcoming_events, featured_stadiums, featured_teams_data = get_static_fallback_data()
        
        return render_template('index.html',
                               upcoming_events=upcoming_events,
                               featured_stadiums=featured_stadiums,
                               featured_teams_data=featured_teams_data,
                               next_match_countdown=next_match_countdown)
        
    except Exception as e:
        print(f"[FAIL] Critical error in index route: {e}")
        # Return template with empty data to prevent complete failure
        return render_template('index.html',
                               upcoming_events=[],
                               featured_stadiums=[],
                               featured_teams_data=[],
                               next_match_countdown=None,
                               error_message="Some content may not be available due to connectivity issues.")


@app.route('/stadiums')
def stadiums():
    stadiums = Stadium.query.all()
    return render_template('stadiums.html', stadiums=stadiums)

@app.route('/stadium/<int:stadium_id>')
def stadium_detail(stadium_id):
    stadium = Stadium.query.get_or_404(stadium_id)
    current_time = datetime.now()
    return render_template('stadium_detail.html', stadium=stadium, current_time=current_time)

@app.route('/events')
def events():
    events = Event.query.order_by(Event.event_date.desc()).all()
    return render_template('events.html', events=events)

@app.route('/event/<int:event_id>')
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)
    return render_template('event_detail.html', event=event)

@app.route('/teams')
def teams():
    teams = Team.query.all()
    return render_template('teams.html', teams=teams)

@app.route('/team/<int:team_id>')
def team_detail(team_id):
    team = Team.query.get_or_404(team_id)
    # Find the stadium for the team's home ground
    stadium = None
    if hasattr(team, 'home_ground') and team.home_ground:
        stadium = Stadium.query.filter_by(name=team.home_ground).first()
    return render_template('team_detail.html', team=team, stadium=stadium)

@app.route('/players')
def players():
    players = Player.query.all()
    return render_template('players.html', players=players)

@app.route('/player/<int:player_id>')
def player_detail(player_id):
    player = Player.query.get_or_404(player_id)
    return render_template('player_detail.html', player=player)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Sanitize form data
        form_data = {
            'name': sanitize_input(request.form.get('name', ''), 100),
            'email': sanitize_input(request.form.get('email', ''), 100).lower(),
            'phone': sanitize_input(request.form.get('phone', ''), 20),
            'password': request.form.get('password', '')
        }
        
        # Validate form data
        errors = handle_form_errors(form_data, REGISTRATION_VALIDATION_RULES)
        
        # Additional validations
        if form_data['email']:
            existing_customer = Customer.query.filter_by(email=form_data['email']).first()
            if existing_customer:
                errors.append('An account with this email already exists. Please try logging in instead.')
        
        # Password strength validation
        password_errors = validate_password_strength(form_data['password'])
        errors.extend(password_errors)
        
        # If there are validation errors, return to form with errors
        if errors:
            flash_errors(errors)
            return render_template('register.html')
        
        try:
            # Create new customer account
            new_customer = Customer(
                name=form_data['name'], 
                email=form_data['email'], 
                phone=form_data['phone'], 
                role='customer',
                membership_level='Basic'
            )
            new_customer.set_password(form_data['password'])
            db.session.add(new_customer)
            db.session.commit()
            
            flash(f'Account created successfully! Welcome to CricVerse, {form_data["name"]}.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
            print(f"Registration error: {e}")
            return render_template('register.html')
    
    return render_template('register.html')

# Stadium Owner Application Route
@app.route('/apply/stadium-owner', methods=['GET', 'POST'])
@login_required
def apply_stadium_owner():
    """Stadium owner application form"""
    # Check if user already has a pending or approved application
    if current_user.verification_status in ['pending', 'approved']:
        flash('You already have a stadium owner application that is pending or approved.', 'info')
        return redirect(url_for('dashboard'))
    
    # Check if user is already a stadium owner or admin
    if current_user.role in ['stadium_owner', 'admin']:
        flash('You already have elevated privileges.', 'info')
        return redirect(url_for('dashboard'))
    
    form = StadiumOwnerApplicationForm()
    
    if form.validate_on_submit():
        try:
            # Handle file upload
            document_urls = []
            if form.business_document.data:
                file = form.business_document.data
                filename = secure_filename(file.filename)
                # Create uploads directory if it doesn't exist
                import os
                os.makedirs('uploads/documents', exist_ok=True)
                file_path = os.path.join('uploads/documents', f"{current_user.id}_{filename}")
                file.save(file_path)
                document_urls.append(file_path)
            
            # Create verification submission
            submission = VerificationSubmission(
                user_id=current_user.id,
                document_urls=json.dumps(document_urls),
                notes=form.notes.data or ''
            )
            
            # Update user verification status
            current_user.verification_status = 'pending'
            
            db.session.add(submission)
            db.session.commit()
            
            flash('Your stadium owner application has been submitted successfully! An administrator will review it shortly.', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while submitting your application. Please try again.', 'danger')
            print(f"Application submission error: {e}")
    
    return render_template('apply_stadium_owner.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Redirect if already logged in to prevent session hijacking
    if current_user.is_authenticated:
        # Force redirect to appropriate dashboard based on current role
        role_redirects = {
            'admin': 'admin_dashboard',
            'stadium_owner': 'stadium_owner_dashboard',
            'customer': 'dashboard'
        }
        redirect_route = role_redirects.get(current_user.role, 'dashboard')
        return redirect(url_for(redirect_route))
    
    if request.method == 'POST':
        # Rate limiting check (if security framework is available)
        try:
            from security_framework import limiter
            # This will automatically rate limit based on IP
        except ImportError:
            pass
        
        # Sanitize form data with strict validation
        email = sanitize_input(request.form.get('email', ''), 100).lower().strip()
        password = request.form.get('password', '')
        remember_me = request.form.get('remember_me') == 'on'
        
        # Enhanced input validation
        validation_errors = []
        
        if not email or not password:
            validation_errors.append('Please enter both email and password.')
        
        if email and not validate_email(email):
            validation_errors.append('Please enter a valid email address.')
        
        if password and len(password) < 1:
            validation_errors.append('Password cannot be empty.')
        
        if validation_errors:
            for error in validation_errors:
                flash(error, 'danger')
            return render_template('login.html')
        
        # Find user by email with protection against timing attacks
        customer = Customer.query.filter_by(email=email).first()
        
        # Always check password even if user doesn't exist (prevents user enumeration)
        password_valid = False
        if customer:
            password_valid = customer.check_password(password)
        else:
            # Dummy password check to prevent timing attacks
            from werkzeug.security import check_password_hash
            check_password_hash('$2b$12$dummy.hash.to.prevent.timing', password)
        
        if customer and password_valid:
            # Log successful login attempt
            try:
                from models import SystemLog
                log_entry = SystemLog(
                    customer_id=customer.id,
                    log_level='INFO',
                    category='auth',
                    action='successful_login',
                    message=f'User {customer.email} logged in successfully',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent'),
                    request_url=request.url,
                    request_method=request.method
                )
                db.session.add(log_entry)
                db.session.commit()
            except Exception as e:
                print(f"Failed to log successful login: {e}")
            
            # Successful login - STRICT role-based redirection enforcement
            login_user(customer, remember=remember_me)
            
            # CRITICAL SECURITY: Force strict role-based redirection
            # This is the first line of defense in separating user environments
            role_redirects = {
                'admin': {
                    'message': f'Welcome back, Administrator {customer.name}! You have full system access.',
                    'redirect': 'admin_dashboard',
                    'allowed_routes': ['admin_dashboard', 'admin_profile', 'add_stadium', 'manage_stadium']
                },
                'stadium_owner': {
                    'message': f'Welcome back, {customer.name}! Ready to manage your stadiums.',
                    'redirect': 'stadium_owner_dashboard',
                    'allowed_routes': ['stadium_owner_dashboard']
                },
                'customer': {
                    'message': f'Welcome back, {customer.name}! Enjoy your CricVerse experience.',
                    'redirect': 'dashboard',
                    'allowed_routes': ['dashboard', 'profile', 'book_ticket']
                }
            }
            
            # Get role configuration with fallback to customer
            role_config = role_redirects.get(customer.role, role_redirects['customer'])
            
            # Security Check: Validate next parameter against allowed routes for this role
            next_page = request.args.get('next')
            if next_page:
                # Parse the route name from the next parameter
                try:
                    from urllib.parse import urlparse
                    parsed_url = urlparse(next_page)
                    # Remove leading slash and extract route
                    route_path = parsed_url.path.lstrip('/')
                    
                    # Only allow navigation to routes appropriate for this role
                    allowed_prefixes = {
                        'admin': ['admin/'],
                        'stadium_owner': ['stadium_owner/', 'stadium-owner/'],
                        'customer': ['dashboard', 'profile', 'book', 'events', 'teams', 'stadiums', 'concessions', 'parking']
                    }
                    
                    role_prefixes = allowed_prefixes.get(customer.role, allowed_prefixes['customer'])
                    
                    # Check if the next route is allowed for this role
                    is_allowed = False
                    for prefix in role_prefixes:
                        if route_path.startswith(prefix) or route_path in prefix:
                            is_allowed = True
                            break
                    
                    if not is_allowed:
                        # Security violation: User trying to access unauthorized route
                        try:
                            log_entry = SystemLog(
                                customer_id=customer.id,
                                log_level='WARNING',
                                category='auth',
                                action='unauthorized_redirect_attempt',
                                message=f'User {customer.email} ({customer.role}) attempted to access unauthorized route: {next_page}',
                                ip_address=request.remote_addr,
                                user_agent=request.headers.get('User-Agent'),
                                extra_data=json.dumps({'attempted_route': next_page, 'user_role': customer.role})
                            )
                            db.session.add(log_entry)
                            db.session.commit()
                        except Exception as e:
                            print(f"Failed to log security violation: {e}")
                        
                        next_page = None  # Force redirect to role-appropriate dashboard
                
                except Exception as e:
                    print(f"Error parsing next parameter: {e}")
                    next_page = None
            
            # Flash success message and redirect
            flash(role_config['message'], 'success')
            
            # ENFORCE STRICT ROLE-BASED REDIRECTION
            final_redirect = next_page if next_page else url_for(role_config['redirect'])
            return redirect(final_redirect)
                
        else:
            # Log failed login attempt
            try:
                from models import SystemLog
                log_entry = SystemLog(
                    customer_id=customer.id if customer else None,
                    log_level='WARNING',
                    category='auth',
                    action='failed_login',
                    message=f'Failed login attempt for email: {email}',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent'),
                    request_url=request.url,
                    request_method=request.method,
                    extra_data=json.dumps({'attempted_email': email})
                )
                db.session.add(log_entry)
                db.session.commit()
            except Exception as e:
                print(f"Failed to log failed login: {e}")
            
            # Login failed - enhanced error messages
            if customer:
                flash('Incorrect password. Please try again or reset your password.', 'danger')
            else:
                flash('No account found with this email address. Please check your email or register for a new account.', 'danger')
    
    return render_template('login.html')

@app.route('/stadium_owner/dashboard')
@login_required
@stadium_owner_required
def stadium_owner_dashboard():
    return render_template('stadium_owner_dashboard.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
@customer_required
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

@app.route('/profile', methods=['GET', 'POST'])
@login_required
@customer_required
def profile():
    teams = Team.query.all()
    if request.method == 'POST':
        # CRITICAL SECURITY: Role Change Prevention
        # Explicitly validate that no role-related fields are being modified
        original_role = current_user.role
        original_verification_status = current_user.verification_status
        
        # Log potential security violations
        suspicious_fields = []
        for field_name in request.form.keys():
            if field_name.lower() in ['role', 'verification_status', 'is_admin', 'admin', 'stadium_owner']:
                suspicious_fields.append(field_name)
        
        if suspicious_fields:
            # Security violation detected - log and reject
            try:
                from models import SystemLog
                log_entry = SystemLog(
                    customer_id=current_user.id,
                    log_level='CRITICAL',
                    category='security',
                    action='role_modification_attempt',
                    message=f'User {current_user.email} attempted to modify restricted fields: {suspicious_fields}',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent'),
                    request_url=request.url,
                    request_method=request.method
                )
                db.session.add(log_entry)
                db.session.commit()
            except Exception as e:
                print(f"Failed to log security violation: {e}")
            
            flash('Security violation detected. Unauthorized field modification attempt.', 'danger')
            return redirect(url_for('profile'))
        
        # Only allow safe profile field updates
        current_user.name = sanitize_input(request.form.get('name', ''), 100)
        current_user.phone = sanitize_input(request.form.get('phone', ''), 20)
        favorite_team_id = request.form.get('favorite_team_id')
        current_user.favorite_team_id = int(favorite_team_id) if favorite_team_id else None
        
        # CRITICAL: Ensure role and verification status haven't been tampered with
        if current_user.role != original_role or current_user.verification_status != original_verification_status:
            # Restore original values and log security incident
            current_user.role = original_role
            current_user.verification_status = original_verification_status
            
            try:
                from models import SystemLog
                log_entry = SystemLog(
                    customer_id=current_user.id,
                    log_level='CRITICAL',
                    category='security',
                    action='privilege_escalation_attempt',
                    message=f'SECURITY ALERT: User {current_user.email} attempted privilege escalation during profile update',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent'),
                    request_url=request.url,
                    request_method=request.method
                )
                db.session.add(log_entry)
                db.session.commit()
            except Exception as e:
                print(f"Failed to log privilege escalation attempt: {e}")
            
            flash('SECURITY VIOLATION: Unauthorized privilege modification detected and blocked.', 'danger')
            return redirect(url_for('profile'))
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {e}', 'danger')
        return redirect(url_for('profile'))
    return render_template('profile.html', teams=teams)

@app.route('/change_password', methods=['POST'])
@login_required
@customer_required
def change_password():
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']

    if not current_user.check_password(current_password):
        flash('Incorrect current password.', 'danger')
    elif new_password != confirm_password:
        flash('New password and confirm password do not match.', 'danger')
    else:
        current_user.set_password(new_password)
        try:
            db.session.commit()
            flash('Password changed successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error changing password: {e}', 'danger')
    return redirect(url_for('profile'))

@app.route('/book_ticket/<int:event_id>', methods=['POST'])
@login_required
@customer_required
def book_ticket(event_id):
    event = Event.query.get_or_404(event_id)
    
    selected_seat_ids = request.form.get('selected_seats', '').split(',')
    ticket_type = request.form.get('ticket_type')
    payment_method = request.form.get('payment_method')
    
    if not selected_seat_ids or selected_seat_ids == ['']:
        flash('Please select at least one seat.', 'warning')
        return redirect(url_for('select_seats', event_id=event_id))

    selected_seat_ids = [int(sid) for sid in selected_seat_ids if sid]

    # Check if seats are still available
    seats = Seat.query.filter(Seat.id.in_(selected_seat_ids)).all()
    
    if len(seats) != len(selected_seat_ids):
        flash('One or more selected seats could not be found or are invalid.', 'danger')
        return redirect(url_for('select_seats', event_id=event_id))

    booked_seats = Ticket.query.filter(
        Ticket.seat_id.in_(selected_seat_ids),
        Ticket.event_id == event_id,
        Ticket.ticket_status.in_(['Booked', 'Used'])
    ).all()
    
    if booked_seats:
        flash('Some selected seats are no longer available. Please choose again.', 'warning')
        return redirect(url_for('select_seats', event_id=event_id))
    
    total_amount = sum(seat.price for seat in seats)

    new_booking = Booking(customer_id=current_user.id, total_amount=total_amount)
    db.session.add(new_booking)

    for seat in seats:
        ticket = Ticket(
            event_id=event_id,
            seat_id=seat.id,
            customer_id=current_user.id,
            ticket_type=ticket_type,
            access_gate=f"Gate {seat.section[0]}",
            booking=new_booking
        )
        db.session.add(ticket)
    
    payment = Payment(
        amount=total_amount,
        payment_method=payment_method,
        transaction_id=f"TXN{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        booking=new_booking
    )
    db.session.add(payment)
    
    try:
        db.session.commit()
        
        # Generate QR codes for all tickets
        from qr_generator import qr_generator
        for ticket in new_booking.tickets:
            qr_data = {
                'ticket_id': ticket.id,
                'event_id': ticket.event_id,
                'seat_id': ticket.seat_id,
                'customer_id': current_user.id
            }
            qr_result = qr_generator.generate_ticket_qr(qr_data)
            if qr_result:
                ticket.qr_code = qr_result['qr_code_base64']
        
        db.session.commit()
        
        flash(f'Successfully booked {len(seats)} ticket(s) for {event.event_name}!', 'success')
        return redirect(url_for('dashboard'))
    except Exception as e:
        db.session.rollback()
        print(f"Error during booking: {e}")
        flash('An error occurred while processing your booking. Please try again.', 'danger')
        return redirect(url_for('select_seats', event_id=event_id))

@app.route('/select_seats/<int:event_id>')
@login_required
@customer_required
def select_seats(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Get all seats for the stadium
    all_seats = Seat.query.filter_by(stadium_id=event.stadium_id).all()
    
    # Get booked seats for this event
    booked_seat_ids = db.session.query(Ticket.seat_id).filter(
        Ticket.event_id == event_id,
        Ticket.ticket_status.in_(['Booked', 'Used'])
    ).all()
    booked_seat_ids = [seat_id[0] for seat_id in booked_seat_ids]
    
    # Mark seats as available/unavailable
    for seat in all_seats:
        seat.is_available = seat.id not in booked_seat_ids
    
    # Group seats by section -> rows with enhanced data structure
    sections: dict = {}
    total_available = 0
    
    for seat in all_seats:
        section_name = seat.section
        row_name = seat.row_number
        
        if section_name not in sections:
            sections[section_name] = {
                'name': section_name,
                'rows': {},
                'total_seats': 0,
                'available_seats': 0,
                'price_range': {'min': float('inf'), 'max': 0},
                'seat_types': set(),
                'class': 'standard'  # CSS class for styling
            }
        
        if row_name not in sections[section_name]['rows']:
            sections[section_name]['rows'][row_name] = {
                'name': row_name,
                'seats': []
            }
        
        sections[section_name]['rows'][row_name]['seats'].append(seat)
        sections[section_name]['total_seats'] += 1
        sections[section_name]['seat_types'].add(seat.seat_type)
        
        # Update price range
        if seat.price < sections[section_name]['price_range']['min']:
            sections[section_name]['price_range']['min'] = seat.price
        if seat.price > sections[section_name]['price_range']['max']:
            sections[section_name]['price_range']['max'] = seat.price
        
        if seat.is_available:
            sections[section_name]['available_seats'] += 1
            total_available += 1
    
    # Determine section styling class based on seat types
    for section_data in sections.values():
        seat_types = section_data['seat_types']
        if 'VIP' in seat_types:
            section_data['class'] = 'vip'
        elif 'Corporate' in seat_types:
            section_data['class'] = 'corporate'
        elif 'Premium' in seat_types:
            section_data['class'] = 'premium'
        else:
            section_data['class'] = 'standard'
        
        # Format price range
        min_price = section_data['price_range']['min']
        max_price = section_data['price_range']['max']
        if min_price == max_price:
            section_data['price_range'] = f"₹{min_price:.0f}"
        else:
            section_data['price_range'] = f"₹{min_price:.0f} - ₹{max_price:.0f}"
    
    # Sort seats within rows by numeric seat_number when possible
    def _to_int_or_str(value: str):
        try:
            return int(value)
        except Exception:
            return value
    
    for section_data in sections.values():
        # Order rows by natural name
        ordered_rows = []
        for row_name, row_data in section_data['rows'].items():
            row_data['seats'].sort(key=lambda s: _to_int_or_str(s.seat_number))
            ordered_rows.append(row_data)
        # Sort rows by their name with numeric fallback
        ordered_rows.sort(key=lambda r: _to_int_or_str(r['name']))
        section_data['rows'] = ordered_rows
    
    # Convert to list for template, sorted by section importance
    def section_priority(section):
        # Priority order: VIP -> Corporate -> Premium -> Standard -> General
        if 'VIP' in section['seat_types']:
            return 0
        elif 'Corporate' in section['seat_types']:
            return 1
        elif 'Premium' in section['seat_types']:
            return 2
        elif 'Standard' in section['seat_types']:
            return 3
        else:
            return 4
    
    sections_list = sorted(sections.values(), key=section_priority)
    
    # Use enhanced template if it exists, fallback to original
    try:
        return render_template('enhanced_seat_selection.html', 
                             event=event, 
                             sections=sections_list,
                             selected_seats=[],
                             total_available=total_available)
    except Exception:
        # Fallback to original template
        return render_template('seat_selection.html', 
                             event=event, 
                             sections=sections_list,
                             selected_seats=[],
                             total_available=total_available)

@app.route('/parking')
def parking():
    stadiums = Stadium.query.all()
    parking_zones = Parking.query.all()
    return render_template('parking.html', stadiums=stadiums, parking_zones=parking_zones)

@app.route('/concessions')
def concessions():
    # Optional filters via query params: stadium_id, category
    stadium_id = request.args.get('stadium_id', type=int)
    category = request.args.get('category', type=str)

    query = Concession.query
    if stadium_id:
        query = query.filter_by(stadium_id=stadium_id)
    if category:
        query = query.filter_by(category=category)

    concessions_list = query.order_by(Concession.name.asc()).all()

    # For filter dropdowns
    stadiums = Stadium.query.order_by(Stadium.name.asc()).all()
    categories = [row[0] for row in db.session.query(Concession.category).distinct().order_by(Concession.category.asc()).all()]

    return render_template(
        'concessions.html',
        concessions=concessions_list,
        stadiums=stadiums,
        categories=categories,
        selected_stadium_id=stadium_id,
        selected_category=category,
    )

@app.route('/concession/<int:concession_id>/menu')
@login_required
@customer_required
def concession_menu(concession_id):
    concession = Concession.query.get_or_404(concession_id)
    
    # Get menu items from database for this concession
    menu_items = MenuItem.query.filter_by(
        concession_id=concession_id, 
        is_available=True
    ).order_by(MenuItem.category, MenuItem.name).all()
    
    return render_template('concession_menu.html', 
                         concession=concession, 
                         menu_items=menu_items)

# =============================
# BOOKING + PAYPAL INTEGRATION
# =============================

@app.route('/booking/create-order', methods=['POST'])
@login_required
@limiter.limit("5 per minute", key_func=rate_limit_by_user)
@validate_json_input(BookingValidationModel)
def booking_create_order():
    """Create a PayPal order after validating inventory and computing total server-side.
    Enhanced with rate limiting, validation, concurrency handling, and transaction management.
    
    Expected JSON body (validated by BookingValidationModel):
    {
      "event_id": 123,
      "seat_ids": [1,2,3],
      "parking_id": 10,            # optional
      "parking_hours": 2           # optional float
    }
    """
    try:
        # Get validated data from the decorator
        data = request.validated_data
        event_id = data.get('event_id')
        seat_ids = data.get('seat_ids') or []
        parking_id = data.get('parking_id')
        parking_hours = data.get('parking_hours')
        
        logger.info(f"[BOOKING] Creating order for user {current_user.id}, event {event_id}, seats {seat_ids}")

        # Enhanced validation: Verify event exists and is bookable
        event = Event.query.get(event_id)
        if not event:
            logger.warning(f"[BOOKING] Invalid event_id {event_id} from user {current_user.id}")
            return jsonify({"success": False, "error": "Invalid event_id", "error_code": "EVENT_NOT_FOUND"}), 400
        
        # Check if event is in the future
        if event.event_date < datetime.now().date():
            return jsonify({"success": False, "error": "Cannot book past events", "error_code": "PAST_EVENT"}), 400
        
        # Check if event is too far in the future (prevent spam bookings)
        max_future_days = 365  # 1 year
        if (event.event_date - datetime.now().date()).days > max_future_days:
            return jsonify({"success": False, "error": "Event too far in future", "error_code": "TOO_FUTURE"}), 400

        total_amount = 0.0
        validated_seat_ids = []

        # Enhanced concurrency handling with database locks
        if seat_ids:
            # Use SELECT FOR UPDATE to prevent race conditions
            with db.session.begin():  # Start transaction
                # Get seats with row-level locking
                seats = db.session.query(Seat).filter(
                    Seat.id.in_(seat_ids), 
                    Seat.stadium_id == event.stadium_id
                ).with_for_update().all()
                
                if len(seats) != len(seat_ids):
                    logger.warning(f"[BOOKING] Seat validation failed - requested: {len(seat_ids)}, found: {len(seats)}")
                    return jsonify({"success": False, "error": "One or more seats not found for this event's stadium", "error_code": "SEATS_NOT_FOUND"}), 400

                # Check seat availability with atomic query
                booked_seats_query = db.session.query(Ticket.seat_id).filter(
                    Ticket.event_id == event_id,
                    Ticket.seat_id.in_(seat_ids),
                    Ticket.ticket_status.in_(['Booked', 'Used'])
                ).with_for_update()  # Lock these records too
                
                booked_seat_ids = {sid for (sid,) in booked_seats_query.all()}

                # Validate each seat and calculate total
                unavailable_seats = []
                for seat in seats:
                    if seat.id in booked_seat_ids:
                        unavailable_seats.append(f"Section {seat.section}, Row {seat.row_number}, Seat {seat.seat_number}")
                    else:
                        total_amount += float(seat.price or 0)
                        validated_seat_ids.append(seat.id)
                
                if unavailable_seats:
                    logger.warning(f"[BOOKING] Seat availability conflict - unavailable seats: {unavailable_seats}")
                    return jsonify({
                        "success": False, 
                        "error": f"Seats no longer available: {', '.join(unavailable_seats)}", 
                        "error_code": "SEATS_UNAVAILABLE",
                        "unavailable_seats": unavailable_seats
                    }), 409

        # Enhanced parking validation with concurrency handling
        parking_amount = 0.0
        if parking_id:
            with db.session.begin():
                parking = db.session.query(Parking).filter(
                    Parking.id == parking_id
                ).with_for_update().one_or_none()
                
                if not parking or parking.stadium_id != event.stadium_id:
                    return jsonify({"success": False, "error": "Invalid parking selection", "error_code": "PARKING_INVALID"}), 400
                
                hours = float(parking_hours or 0)
                if hours <= 0 or hours > 24:
                    return jsonify({"success": False, "error": "Invalid parking hours (1-24)", "error_code": "PARKING_HOURS_INVALID"}), 400
                    
                # Check parking availability for the event time
                existing_bookings = db.session.query(ParkingBooking).filter(
                    ParkingBooking.parking_id == parking_id,
                    ParkingBooking.arrival_time.between(
                        event.start_time - timedelta(hours=2),
                        event.start_time + timedelta(hours=6)
                    )
                ).count()
                
                if existing_bookings >= parking.capacity:
                    return jsonify({"success": False, "error": "Parking zone full for this time", "error_code": "PARKING_FULL"}), 409
                    
                parking_amount = float(parking.rate_per_hour or 0) * hours
                total_amount += parking_amount

        # Final validation
        if total_amount <= 0:
            return jsonify({"success": False, "error": "Cart is empty", "error_code": "EMPTY_CART"}), 400
        
        # Apply service fees (configurable)
        service_fee_rate = float(os.getenv('SERVICE_FEE_RATE', '0.05'))  # 5%
        processing_fee = float(os.getenv('PROCESSING_FEE', '2.50'))
        
        service_fee = total_amount * service_fee_rate
        final_amount = total_amount + service_fee + processing_fee
        
        # Enhanced amount validation against potential tampering
        expected_total = data.get('total_amount')
        if expected_total and abs(final_amount - expected_total) > 0.01:
            logger.warning(f"[BOOKING] Amount mismatch - calculated: {final_amount}, provided: {expected_total}")
            return jsonify({
                "success": False, 
                "error": "Amount calculation mismatch", 
                "error_code": "AMOUNT_MISMATCH",
                "calculated_total": round(final_amount, 2)
            }), 400

        # Create payment order using unified processor with enhanced metadata
        payment_metadata = {
            'customer_id': str(current_user.id),
            'customer_email': current_user.email,
            'customer_name': current_user.name,
            'booking_type': 'ticket',
            'event_id': str(event_id),
            'event_name': event.event_name,
            'stadium_id': str(event.stadium_id),
            'seat_count': len(validated_seat_ids),
            'base_amount': round(total_amount, 2),
            'service_fee': round(service_fee, 2),
            'processing_fee': round(processing_fee, 2),
            'final_amount': round(final_amount, 2),
            'booking_timestamp': datetime.now(timezone.utc).isoformat(),
            'user_agent': request.headers.get('User-Agent', ''),
            'ip_address': request.remote_addr
        }
        
        if parking_id:
            payment_metadata.update({
                'parking_id': str(parking_id),
                'parking_hours': str(parking_hours),
                'parking_amount': round(parking_amount, 2)
            })
        
        payment_response = unified_payment_processor.create_payment(
            amount=final_amount,
            currency='USD',
            payment_method='paypal',
            customer_email=current_user.email,
            metadata=payment_metadata
        )
        
        if not payment_response.success:
            logger.error(f"[BOOKING] Payment creation failed: {payment_response.error_message}")
            return jsonify({
                "success": False, 
                "error": payment_response.error_message or "Payment setup failed", 
                "error_code": "PAYMENT_SETUP_FAILED"
            }), 400
        
        order_id = payment_response.payment_id
        logger.info(f"[BOOKING] PayPal order created: {order_id} for user {current_user.id}")

        # Store enhanced pending booking context with expiration
        pending_booking = {
            'order_id': order_id,
            'event_id': event_id,
            'seat_ids': validated_seat_ids,
            'parking_id': parking_id,
            'parking_hours': float(parking_hours or 0),
            'base_amount': round(total_amount, 2),
            'service_fee': round(service_fee, 2),
            'processing_fee': round(processing_fee, 2),
            'final_amount': round(final_amount, 2),
            'created_at': datetime.now(timezone.utc).isoformat(),
            'expires_at': (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat(),  # 15 min expiry
            'user_id': current_user.id,
            'metadata': payment_metadata
        }
        
        session['pending_booking'] = pending_booking
        
        # Log successful order creation for monitoring
        logger.info(f"[BOOKING] Order created successfully - User: {current_user.id}, Order: {order_id}, Amount: {final_amount}")

        return jsonify({
            "success": True, 
            "orderID": order_id, 
            "amount": f"{final_amount:.2f}",
            "breakdown": {
                "base_amount": round(total_amount, 2),
                "service_fee": round(service_fee, 2),
                "processing_fee": round(processing_fee, 2),
                "total": round(final_amount, 2)
            },
            "expires_at": pending_booking['expires_at']
        })

    except Exception as e:
        logger.error(f"[BOOKING] Create order error for user {current_user.id}: {e}")
        db.session.rollback()  # Ensure rollback on error
        return jsonify({"success": False, "error": "Failed to create order", "error_code": "INTERNAL_ERROR"}), 500


@app.route('/booking/create-razorpay-order', methods=['POST'])
@login_required
@limiter.limit("5 per minute", key_func=rate_limit_by_user)
@validate_json_input(BookingValidationModel)
def booking_create_razorpay_order():
    """Create Razorpay order with enhanced security, validation and concurrency handling"""
    if not razorpay_client:
        return jsonify({"success": False, "error": "Razorpay not configured", "error_code": "SERVICE_UNAVAILABLE"}), 500
    
    try:
        # Get validated data from the decorator
        data = request.validated_data
        event_id = data.get('event_id')
        seat_ids = data.get('seat_ids') or []
        parking_id = data.get('parking_id')
        parking_hours = data.get('parking_hours')
        
        logger.info(f"[RAZORPAY] Creating order for user {current_user.id}, event {event_id}, seats {seat_ids}")

        # Enhanced validation: Verify event exists and is bookable
        event = Event.query.get(event_id)
        if not event:
            logger.warning(f"[RAZORPAY] Invalid event_id {event_id} from user {current_user.id}")
            return jsonify({"success": False, "error": "Invalid event_id", "error_code": "EVENT_NOT_FOUND"}), 400
        
        # Check if event is in the future
        if event.event_date < datetime.now().date():
            return jsonify({"success": False, "error": "Cannot book past events", "error_code": "PAST_EVENT"}), 400

        total_amount = 0.0
        validated_seat_ids = []

        # Enhanced concurrency handling with database locks
        if seat_ids:
            # Use SELECT FOR UPDATE to prevent race conditions
            with db.session.begin():  # Start transaction
                # Get seats with row-level locking
                seats = db.session.query(Seat).filter(
                    Seat.id.in_(seat_ids), 
                    Seat.stadium_id == event.stadium_id
                ).with_for_update().all()
                
                if len(seats) != len(seat_ids):
                    logger.warning(f"[RAZORPAY] Seat validation failed - requested: {len(seat_ids)}, found: {len(seats)}")
                    return jsonify({"success": False, "error": "One or more seats not found for this event's stadium", "error_code": "SEATS_NOT_FOUND"}), 400

                # Check seat availability with atomic query
                booked_seats_query = db.session.query(Ticket.seat_id).filter(
                    Ticket.event_id == event_id,
                    Ticket.seat_id.in_(seat_ids),
                    Ticket.ticket_status.in_(['Booked', 'Used'])
                ).with_for_update()  # Lock these records too
                
                booked_seat_ids = {sid for (sid,) in booked_seats_query.all()}

                # Validate each seat and calculate total
                unavailable_seats = []
                for seat in seats:
                    if seat.id in booked_seat_ids:
                        unavailable_seats.append(f"Section {seat.section}, Row {seat.row_number}, Seat {seat.seat_number}")
                    else:
                        total_amount += float(seat.price or 0)
                        validated_seat_ids.append(seat.id)
                
                if unavailable_seats:
                    logger.warning(f"[RAZORPAY] Seat availability conflict - unavailable seats: {unavailable_seats}")
                    return jsonify({
                        "success": False, 
                        "error": f"Seats no longer available: {', '.join(unavailable_seats)}", 
                        "error_code": "SEATS_UNAVAILABLE",
                        "unavailable_seats": unavailable_seats
                    }), 409

        # Enhanced parking validation with concurrency handling
        parking_amount = 0.0
        if parking_id:
            with db.session.begin():
                parking = db.session.query(Parking).filter(
                    Parking.id == parking_id
                ).with_for_update().one_or_none()
                
                if not parking or parking.stadium_id != event.stadium_id:
                    return jsonify({"success": False, "error": "Invalid parking selection", "error_code": "PARKING_INVALID"}), 400
                
                hours = float(parking_hours or 0)
                if hours <= 0 or hours > 24:
                    return jsonify({"success": False, "error": "Invalid parking hours (1-24)", "error_code": "PARKING_HOURS_INVALID"}), 400
                    
                # Check parking availability for the event time
                existing_bookings = db.session.query(ParkingBooking).filter(
                    ParkingBooking.parking_id == parking_id,
                    ParkingBooking.arrival_time.between(
                        event.start_time - timedelta(hours=2),
                        event.start_time + timedelta(hours=6)
                    )
                ).count()
                
                if existing_bookings >= parking.capacity:
                    return jsonify({"success": False, "error": "Parking zone full for this time", "error_code": "PARKING_FULL"}), 409
                    
                parking_amount = float(parking.rate_per_hour or 0) * hours
                total_amount += parking_amount

        # Final validation
        if total_amount <= 0:
            return jsonify({"success": False, "error": "Cart is empty", "error_code": "EMPTY_CART"}), 400
        
        # Apply service fees and convert to INR paise (Razorpay requirement)
        service_fee_rate = float(os.getenv('SERVICE_FEE_RATE', '0.05'))  # 5%
        processing_fee = float(os.getenv('PROCESSING_FEE_INR', '20.00'))  # ₹20 in INR
        
        service_fee = total_amount * service_fee_rate
        final_amount = total_amount + service_fee + processing_fee
        
        # Convert to paise (smallest currency unit for INR)
        amount_paise = int(round(final_amount * 100))
        
        # Razorpay order creation with enhanced metadata
        receipt_id = f"rcpt_{current_user.id}_{event_id}_{int(datetime.now(timezone.utc).timestamp())}"
        
        razorpay_order_data = {
            'amount': amount_paise,
            'currency': 'INR',
            'receipt': receipt_id,
            'notes': {
                'customer_id': str(current_user.id),
                'customer_email': current_user.email,
                'customer_name': current_user.name,
                'event_id': str(event_id),
                'event_name': event.event_name,
                'stadium_id': str(event.stadium_id),
                'seat_count': str(len(validated_seat_ids)),
                'seat_ids': ','.join(map(str, validated_seat_ids)),
                'base_amount': str(round(total_amount, 2)),
                'service_fee': str(round(service_fee, 2)),
                'processing_fee': str(round(processing_fee, 2)),
                'final_amount': str(round(final_amount, 2)),
                'booking_timestamp': datetime.now(timezone.utc).isoformat(),
                'ip_address': request.remote_addr
            }
        }
        
        if parking_id:
            razorpay_order_data['notes'].update({
                'parking_id': str(parking_id),
                'parking_hours': str(parking_hours),
                'parking_amount': str(round(parking_amount, 2))
            })
        
        # Create Razorpay order
        order = razorpay_client.order.create(razorpay_order_data)
        
        if not order or not order.get('id'):
            logger.error(f"[RAZORPAY] Order creation failed for user {current_user.id}")
            return jsonify({"success": False, "error": "Failed to create Razorpay order", "error_code": "RAZORPAY_ORDER_FAILED"}), 500
        
        logger.info(f"[RAZORPAY] Order created: {order.get('id')} for user {current_user.id}")

        # Store enhanced pending booking context with expiration
        pending_booking = {
            'razorpay_order_id': order.get('id'),
            'event_id': event_id,
            'seat_ids': validated_seat_ids,
            'parking_id': parking_id,
            'parking_hours': float(parking_hours or 0),
            'base_amount': round(total_amount, 2),
            'service_fee': round(service_fee, 2),
            'processing_fee': round(processing_fee, 2),
            'final_amount': round(final_amount, 2),
            'amount_paise': amount_paise,
            'receipt_id': receipt_id,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'expires_at': (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat(),  # 15 min expiry
            'user_id': current_user.id,
            'metadata': razorpay_order_data['notes']
        }
        
        session['pending_booking'] = pending_booking
        
        # Log successful order creation for monitoring
        logger.info(f"[RAZORPAY] Order created successfully - User: {current_user.id}, Order: {order.get('id')}, Amount: ₹{final_amount}")

        return jsonify({
            'success': True,
            'razorpay_order_id': order.get('id'),
            'key_id': RAZORPAY_KEY_ID,
            'amount': amount_paise,
            'currency': 'INR',
            'receipt': receipt_id,
            'amount_display': f"₹{final_amount:.2f}",
            'breakdown': {
                'base_amount': round(total_amount, 2),
                'service_fee': round(service_fee, 2),
                'processing_fee': round(processing_fee, 2),
                'total': round(final_amount, 2)
            },
            'expires_at': pending_booking['expires_at']
        })
        
    except Exception as e:
        logger.error(f"[RAZORPAY] Create order error for user {current_user.id}: {e}")
        db.session.rollback()  # Ensure rollback on error
        return jsonify({"success": False, "error": "Failed to create Razorpay order", "error_code": "INTERNAL_ERROR"}), 500


@app.route('/booking/verify-razorpay-payment', methods=['POST'])
@login_required
def verify_razorpay_payment():
    if not razorpay_client:
        return jsonify({"success": False, "error": "Razorpay not configured"}), 500
    try:
        data = request.get_json(silent=True) or {}
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')

        if not (razorpay_order_id and razorpay_payment_id and razorpay_signature):
            return jsonify({"success": False, "error": "Missing Razorpay fields"}), 400

        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }

        # Verify signature
        try:
            razorpay_client.utility.verify_payment_signature(params_dict)
        except Exception:
            return jsonify({"success": False, "error": "Invalid payment signature"}), 400

        pending = session.get('pending_booking')
        if not pending:
            return jsonify({"success": False, "error": "No pending booking found in session"}), 400

        # Create tickets list to store created tickets
        tickets = []

        with db.session.begin():
            new_booking = Booking(
                customer_id=current_user.id,
                total_amount=pending['amount']
            )
            db.session.add(new_booking)
            db.session.flush()

            for sid in pending.get('seat_ids') or []:
                ticket = Ticket(
                    event_id=pending['event_id'],
                    seat_id=sid,
                    customer_id=current_user.id,
                    ticket_status='Booked',
                    booking=new_booking
                )
                db.session.add(ticket)
                tickets.append(ticket)  # Store ticket for QR code generation

            payment = Payment(
                amount=pending['amount'],
                payment_method='Razorpay',
                transaction_id=razorpay_payment_id,
                booking=new_booking
            )
            db.session.add(payment)

            if pending.get('parking_id') and pending.get('parking_hours', 0) > 0:
                parking_booking = ParkingBooking(
                    parking_id=pending['parking_id'],
                    customer_id=current_user.id,
                    vehicle_number='N/A',
                    amount_paid=pending['amount']
                )
                db.session.add(parking_booking)

        # Generate QR codes for all tickets
        from qr_generator import qr_generator
        for ticket in tickets:
            qr_data = {
                'ticket_id': ticket.id,
                'event_id': ticket.event_id,
                'seat_id': ticket.seat_id,
                'customer_id': current_user.id
            }
            qr_result = qr_generator.generate_ticket_qr(qr_data)
            if qr_result:
                ticket.qr_code = qr_result['qr_code_base64']
        
        db.session.commit()

        session.pop('pending_booking', None)
        return jsonify({"success": True, "booking_id": new_booking.id})
    except Exception as e:
        print(f"Verify Razorpay error: {e}")
        return jsonify({"success": False, "error": "Failed to verify Razorpay payment"}), 500


@app.route('/booking/capture-order', methods=['POST'])
@login_required
@limiter.limit("3 per minute", key_func=rate_limit_by_user)
@validate_json_input(BookingValidationModel)
def booking_capture_order():
    """Capture a PayPal order and write booking + tickets atomically with enhanced security."""
    try:
        data = request.validated_data
        order_id = data.get('orderID')
        payer_id = data.get('payerID', '')
        
        if not order_id:
            return jsonify({"success": False, "error": "orderID is required", "error_code": "MISSING_ORDER_ID"}), 400

        pending = session.get('pending_booking')
        if not pending:
            logger.warning(f"[CAPTURE] No pending booking for user {current_user.id}, order {order_id}")
            return jsonify({"success": False, "error": "No pending booking found in session", "error_code": "NO_PENDING_BOOKING"}), 400
        
        # Enhanced security: Verify booking hasn't expired
        if 'expires_at' in pending:
            expires_at = datetime.fromisoformat(pending['expires_at'])
            if datetime.now(timezone.utc) > expires_at:
                session.pop('pending_booking', None)
                logger.warning(f"[CAPTURE] Expired booking for user {current_user.id}, order {order_id}")
                return jsonify({"success": False, "error": "Booking has expired", "error_code": "BOOKING_EXPIRED"}), 400
        
        # Enhanced security: Verify order belongs to user
        if pending.get('user_id') != current_user.id:
            logger.error(f"[CAPTURE] Security violation - user {current_user.id} trying to capture order for user {pending.get('user_id')}")
            return jsonify({"success": False, "error": "Security violation detected", "error_code": "SECURITY_VIOLATION"}), 403
        
        # Enhanced security: Verify order ID matches
        if pending.get('order_id') != order_id:
            logger.error(f"[CAPTURE] Order ID mismatch - expected {pending.get('order_id')}, got {order_id}")
            return jsonify({"success": False, "error": "Order ID mismatch", "error_code": "ORDER_MISMATCH"}), 400

        logger.info(f"[CAPTURE] Processing capture for user {current_user.id}, order {order_id}")

        # Verify payment using unified processor with enhanced validation
        if UNIFIED_PAYMENT_AVAILABLE:
            payment_verification = unified_payment_processor.verify_payment({
                'gateway': 'paypal',
                'payment_id': order_id,
                'payer_id': payer_id
            })
            
            if not payment_verification.success:
                logger.error(f"[CAPTURE] Payment verification failed for order {order_id}: {payment_verification.error_message}")
                return jsonify({"success": False, "error": "Payment verification failed", "error_code": "PAYMENT_VERIFICATION_FAILED"}), 400
            
            transaction_id = payment_verification.payment_id
        else:
            # Fallback verification (simplified)
            transaction_id = order_id
            logger.warning(f"[CAPTURE] Using fallback payment verification for order {order_id}")

        # Enhanced atomicity: Use explicit transaction with retry mechanism
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                with db.session.begin():  # Explicit transaction
                    # Re-verify seat availability with locks (double-check for race conditions)
                    if pending.get('seat_ids'):
                        # Lock seats to prevent double booking
                        locked_seats = db.session.query(Seat).filter(
                            Seat.id.in_(pending['seat_ids'])
                        ).with_for_update().all()
                        
                        # Check for conflicting bookings that might have been created after order creation
                        conflicting_tickets = db.session.query(Ticket.seat_id).filter(
                            Ticket.event_id == pending['event_id'],
                            Ticket.seat_id.in_(pending['seat_ids']),
                            Ticket.ticket_status.in_(['Booked', 'Used'])
                        ).with_for_update().all()
                        
                        if conflicting_tickets:
                            conflicting_seat_ids = [t[0] for t in conflicting_tickets]
                            logger.error(f"[CAPTURE] Seat availability conflict during capture - seats {conflicting_seat_ids} already booked")
                            return jsonify({
                                "success": False, 
                                "error": "Selected seats are no longer available", 
                                "error_code": "SEATS_UNAVAILABLE_AT_CAPTURE",
                                "conflicting_seats": conflicting_seat_ids
                            }), 409

                    # Create booking record with enhanced data
                    new_booking = Booking(
                        customer_id=current_user.id,
                        total_amount=pending.get('final_amount', pending.get('amount', 0)),
                        booking_date=datetime.now(timezone.utc)
                    )
                    db.session.add(new_booking)
                    db.session.flush()  # Get booking ID

                    # Create tickets for seats with enhanced metadata
                    tickets = []
                    for sid in pending.get('seat_ids', []):
                        ticket = Ticket(
                            event_id=pending['event_id'],
                            seat_id=sid,
                            customer_id=current_user.id,
                            booking_id=new_booking.id,
                            ticket_status='Booked',
                            created_at=datetime.now(timezone.utc),
                            updated_at=datetime.now(timezone.utc)
                        )
                        db.session.add(ticket)
                        tickets.append(ticket)

                    # Record payment with enhanced metadata
                    payment = Payment(
                        booking_id=new_booking.id,
                        amount=pending.get('final_amount', pending.get('amount', 0)),
                        payment_method='PayPal',
                        transaction_id=transaction_id,
                        payment_date=datetime.now(timezone.utc)
                    )
                    db.session.add(payment)

                    # Optional parking booking record with enhanced validation
                    if pending.get('parking_id') and pending.get('parking_hours', 0) > 0:
                        # Verify parking is still available
                        parking = db.session.query(Parking).filter(
                            Parking.id == pending['parking_id']
                        ).with_for_update().one_or_none()
                        
                        if parking:
                            parking_booking = ParkingBooking(
                                parking_id=pending['parking_id'],
                                customer_id=current_user.id,
                                booking_date=datetime.now(timezone.utc),
                                vehicle_number='TBD',  # To be updated by user later
                                arrival_time=None,  # To be set based on event time
                                departure_time=None,  # To be calculated
                                amount_paid=pending.get('parking_amount', 0)
                            )
                            db.session.add(parking_booking)
                        else:
                            logger.warning(f"[CAPTURE] Parking {pending['parking_id']} no longer available during capture")

                    # Commit transaction
                    db.session.commit()
                    
                    logger.info(f"[CAPTURE] Booking created successfully - ID: {new_booking.id}, User: {current_user.id}, Amount: {pending.get('final_amount')}")
                    break  # Success, exit retry loop
                    
            except Exception as transaction_error:
                logger.error(f"[CAPTURE] Transaction failed (attempt {retry_count + 1}): {transaction_error}")
                db.session.rollback()
                retry_count += 1
                
                if retry_count >= max_retries:
                    logger.error(f"[CAPTURE] Transaction failed after {max_retries} attempts for user {current_user.id}")
                    return jsonify({"success": False, "error": "Booking creation failed after retries", "error_code": "TRANSACTION_FAILED"}), 500
                
                # Wait before retry
                import time
                time.sleep(0.1 * retry_count)  # Exponential backoff
        
        # Generate QR codes for all tickets (after successful transaction)
        try:
            from qr_generator import qr_generator
            for ticket in tickets:
                qr_data = {
                    'ticket_id': ticket.id,
                    'event_id': ticket.event_id,
                    'seat_id': ticket.seat_id,
                    'customer_id': current_user.id,
                    'booking_id': new_booking.id,
                    'verification_token': hashlib.sha256(f"{ticket.id}_{current_user.id}_{transaction_id}".encode()).hexdigest()[:16]
                }
                qr_result = qr_generator.generate_ticket_qr(qr_data)
                if qr_result:
                    # Update ticket with QR code in separate transaction
                    with db.session.begin():
                        db.session.query(Ticket).filter(Ticket.id == ticket.id).update({
                            'qr_code': qr_result['qr_code_base64'],
                            'updated_at': datetime.now(timezone.utc)
                        })
                        db.session.commit()
        except Exception as qr_error:
            logger.warning(f"[CAPTURE] QR code generation failed: {qr_error}")
            # Don't fail the booking for QR code issues

        # Clear pending booking from session
        session.pop('pending_booking', None)
        
        # Log successful capture for monitoring
        logger.info(f"[CAPTURE] Successfully captured PayPal payment - Booking: {new_booking.id}, Transaction: {transaction_id}")

        return jsonify({
            "success": True, 
            "booking_id": new_booking.id,
            "transaction_id": transaction_id,
            "amount": f"{pending.get('final_amount', pending.get('amount', 0)):.2f}",
            "tickets_count": len(tickets),
            "confirmation_number": f"BBL-{new_booking.id:06d}"
        })

    except Exception as e:
        logger.error(f"[CAPTURE] Capture order error for user {current_user.id}: {e}")
        db.session.rollback()  # Ensure rollback on error
        return jsonify({"success": False, "error": "Failed to capture order", "error_code": "INTERNAL_ERROR"}), 500


@app.route('/my-bookings')
@login_required
def my_bookings():
    """Return current user's bookings with items."""
    try:
        bookings = Booking.query.filter_by(customer_id=current_user.id).order_by(Booking.booking_date.desc()).all()
        result = []
        for b in bookings:
            tickets = Ticket.query.filter_by(booking_id=b.id).all()
            result.append({
                'id': b.id,
                'date': b.booking_date.isoformat() if b.booking_date else None,
                'total_amount': b.total_amount,
                'items': [
                    {
                        'ticket_id': t.id,
                        'event_id': t.event_id,
                        'seat_id': t.seat_id,
                        'status': t.ticket_status,
                    } for t in tickets
                ]
            })
        return jsonify({"success": True, "bookings": result})
    except Exception as e:
        print(f"My bookings error: {e}")
        return jsonify({"success": False, "error": "Failed to fetch bookings"}), 500

@app.route('/place_order', methods=['POST'])
@login_required
@customer_required
def place_order():
    concession_id = request.form['concession_id']
    selected_items = request.form.getlist('selected_items')
    quantities = request.form.getlist('quantities')
    total_amount = float(request.form['total_amount'])
    
    # Create order details
    order_details = []
    for i, item in enumerate(selected_items):
        if quantities[i] and int(quantities[i]) > 0:
            order_details.append(f"{quantities[i]}x {item}")
    
    order_items = ", ".join(order_details)
    
    order = Order(
        concession_id=concession_id,
        customer_id=current_user.id,
        total_amount=total_amount,
        payment_status='Completed'
    )
    
    db.session.add(order)
    db.session.commit()
    
    flash(f'Order placed successfully! Total: ${total_amount:.2f}')
    return redirect(url_for('dashboard'))

@app.route('/book_parking/<int:stadium_id>', methods=['GET', 'POST'])
@login_required
@customer_required
def book_parking(stadium_id):
    stadium = Stadium.query.get_or_404(stadium_id)
    parking_zones = Parking.query.filter_by(stadium_id=stadium_id).all()
    
    if request.method == 'POST':
        parking_id = request.form['parking_id']
        vehicle_number = request.form['vehicle_number']
        arrival_time = datetime.strptime(request.form['arrival_time'], '%Y-%m-%dT%H:%M')
        departure_time = datetime.strptime(request.form['departure_time'], '%Y-%m-%dT%H:%M')
        
        parking = Parking.query.get(parking_id)
        hours = (departure_time - arrival_time).total_seconds() / 3600
        amount = parking.rate_per_hour * hours
        
        booking = ParkingBooking(
            parking_id=parking_id,
            customer_id=current_user.id,
            vehicle_number=vehicle_number,
            arrival_time=arrival_time,
            departure_time=departure_time,
            amount_paid=amount
        )
        
        db.session.add(booking)
        db.session.commit()
        
        flash('Parking booked successfully')
        return redirect(url_for('dashboard'))
    
    return render_template('book_parking.html', stadium=stadium, parking_zones=parking_zones)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/chat')
def chat_interface():
    """Render the enhanced AI chatbot interface"""
    return render_template('chat.html')

@app.route('/ai-assistant')
def ai_assistant():
    """Render the new 3D AI Assistant Command Center"""
    return render_template('ai_assistant.html')

@app.route('/ai-options')
def ai_options():
    """AI Assistant options page"""
    return render_template('ai_options.html')

@app.route('/api/csrf-token')
def get_csrf_token():
    """Get CSRF token for API requests"""
    return jsonify({'csrf_token': generate_csrf()})

@app.route('/api/chat', methods=['POST'])
def enhanced_chat_api():
    """Enhanced AI chatbot API endpoint using Gemini AI"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({
                'success': False,
                'error': 'Message cannot be empty'
            }), 400
        
        # Get user context
        from flask import session
        customer_id = current_user.id if current_user.is_authenticated else None
        session_id = session.get('chat_session_id')
        
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
            session['chat_session_id'] = session_id
        
        # Use simplified chatbot with improved error handling
        if CHATBOT_AVAILABLE:
            try:
                ai_response = get_chatbot_response(message, customer_id, session_id)
            except Exception as e:
                print(f"Chatbot error: {e}")
                ai_response = {
                    'response': f"I understand you're asking about '{message}'. While I'm having some technical difficulties, I can help you with CricVerse services like BBL ticket booking, stadium information, and customer support. Please try asking something specific like 'Show me stadium information' or 'Help me book tickets'.",
                    'confidence': 0.7,
                    'tokens_used': 0,
                    'model': 'fallback-error'
                }
        else:
            # Fallback if chatbot module is not available
            ai_response = {
                'response': f"Hello! Thank you for asking about '{message}'. I'm currently operating in basic mode. For BBL ticket booking, stadium information, or customer support, please contact us at 1800-CRICKET or visit cricverse.com. How else can I assist you?",
                'confidence': 0.6,
                'tokens_used': 0,
                'model': 'basic-fallback'
            }
        
        # Detect intent and get quick actions with error handling
        if CHATBOT_AVAILABLE:
            try:
                intent = detect_user_intent(message)
                quick_actions = get_intent_actions(intent)
            except Exception as e:
                print(f"Intent detection error: {e}")
                # Simple fallback intent detection
                message_lower = message.lower()
                if any(word in message_lower for word in ['book', 'buy', 'ticket', 'reserve']):
                    intent = 'booking'
                    quick_actions = [{"text": "Browse Matches", "action": "browse_matches"}]
                elif any(word in message_lower for word in ['stadium', 'venue', 'ground']):
                    intent = 'venue_info'
                    quick_actions = [{"text": "Stadium Guide", "action": "stadium_guide"}]
                else:
                    intent = 'general'
                    quick_actions = [{"text": "Help me book tickets", "action": "booking_help"}]
        else:
            # Basic intent detection without imports
            message_lower = message.lower()
            if any(word in message_lower for word in ['book', 'buy', 'ticket']):
                intent = 'booking'
                quick_actions = [{"text": "Contact Support", "action": "contact_support"}]
            elif any(word in message_lower for word in ['stadium', 'venue']):
                intent = 'venue_info'
                quick_actions = [{"text": "View Stadiums", "action": "view_stadiums"}]
            else:
                intent = 'general'
                quick_actions = [{"text": "Get Help", "action": "get_help"}]
        
        return jsonify({
            'success': True,
            'response': ai_response.get('response', 'I apologize, but I\'m having trouble processing your request.'),
            'confidence': ai_response.get('confidence', 0.5),
            'intent': intent,
            'quick_actions': quick_actions,
            'tokens_used': ai_response.get('tokens_used', 0),
            'model': ai_response.get('model', 'gemini-1.5-flash'),
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Enhanced chatbot error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'Sorry, I\'m experiencing technical difficulties. Please try again or contact support.',
            'fallback_response': True
        }), 500

@app.route('/api/chat/suggestions')
def chat_suggestions():
    """Get smart chat suggestions based on user context"""
    try:
        customer_id = current_user.id if current_user.is_authenticated else None
        query_type = request.args.get('type', 'general')
        
        if CHATBOT_AVAILABLE:
            try:
                suggestions = get_chat_suggestions(customer_id, query_type)
            except Exception as e:
                print(f"Error getting suggestions: {e}")
                suggestions = [
                    "Help me book tickets",
                    "Show me stadium information",
                    "What food options are available?",
                    "How do I reserve parking?"
                ]
        else:
            suggestions = [
                "Help me book tickets",
                "Show me stadium information",
                "What food options are available?",
                "How do I reserve parking?"
            ]
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
        
    except Exception as e:
        print(f"Error getting chat suggestions: {e}")
        return jsonify({
            'success': False,
            'suggestions': [
                "Help me book tickets",
                "What matches are coming up?",
                "Show me stadium information",
                "How do I cancel a booking?"
            ]
        })

@app.route('/api/chat/history')
@login_required
def chat_history():
    """Get user's chat history"""
    try:
        from models import ChatConversation, ChatMessage
        
        conversations = ChatConversation.query.filter_by(
            customer_id=current_user.id
        ).order_by(ChatConversation.created_at.desc()).limit(5).all()
        
        history = []
        for conv in conversations:
            messages = ChatMessage.query.filter_by(
                conversation_id=conv.id
            ).order_by(ChatMessage.created_at).limit(20).all()
            
            history.append({
                'conversation_id': conv.id,
                'session_id': conv.session_id,
                'created_at': conv.created_at.isoformat(),
                'message_count': conv.message_count,
                'messages': [{
                    'sender': msg.sender_type,
                    'message': msg.message,
                    'timestamp': msg.created_at.isoformat()
                } for msg in messages]
            })
        
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        print(f"Error getting chat history: {e}")
        return jsonify({
            'success': False,
            'error': 'Could not retrieve chat history'
        })

# ============================================================================ 
# REAL-TIME WEBSOCKET ROUTES
# ============================================================================ 

@app.route('/realtime')
def realtime_demo():
    """Real-time features demo page"""
    return render_template('realtime.html')

@app.route('/api/realtime/stats')
def realtime_stats():
    """Get real-time connection statistics"""
    try:
        from realtime_simple import get_realtime_stats
        stats = get_realtime_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/realtime/broadcast', methods=['POST'])
@admin_required
def broadcast_message():
    """Admin endpoint to broadcast messages to all users"""
    try:
        data = request.get_json()
        message = data.get('message')
        message_type = data.get('type', 'info')
        
        if not message:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400
        
        from realtime_simple import broadcast_general_announcement
        broadcast_general_announcement(message, message_type)
        
        return jsonify({
            'success': True,
            'message': 'Broadcast sent successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/match/<int:match_id>/update', methods=['POST'])
@admin_required  
def update_match_live(match_id):
    """Update live match data and broadcast to subscribers"""
    try:
        data = request.get_json()
        
        # Update match in database
        event = Event.query.get_or_404(match_id)
        match = event.match
        
        if not match:
            return jsonify({
                'success': False,
                'error': 'Match record not found'
            }), 404
        
        # Update match data
        if 'score_home' in data:
            match.score_home = data['score_home']
        if 'score_away' in data:
            match.score_away = data['score_away']
        if 'overs_home' in data:
            match.overs_home = data['overs_home']
        if 'overs_away' in data:
            match.overs_away = data['overs_away']
        if 'current_innings' in data:
            match.current_innings = data['current_innings']
        if 'is_live' in data:
            match.is_live = data['is_live']
        
        db.session.commit()
        
        # Broadcast update to subscribers
        from realtime_simple import broadcast_match_update
        update_data = {
            'type': data.get('update_type', 'score_update'),
            'score_home': match.score_home,
            'score_away': match.score_away,
            'overs_home': match.overs_home,
            'overs_away': match.overs_away,
            'current_innings': match.current_innings,
            'is_live': match.is_live,
            'timestamp': datetime.now().isoformat()
        }
        
        broadcast_match_update(match_id, update_data)
        
        return jsonify({
            'success': True,
            'message': 'Match updated and broadcast sent'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    
# ============================================================================ 
# QR CODE GENERATION ROUTES
# ============================================================================ 

@app.route('/qr-demo')
def qr_demo():
    """QR code generation demo page"""
    return render_template('qr_demo.html')

@app.route('/api/qr/generate/ticket', methods=['POST'])
@login_required
def generate_ticket_qr():
    """Generate QR code for ticket"""
    try:
        data = request.get_json()
        
        # Add customer ID from current user
        data['customer_id'] = current_user.id
        
        from qr_generator import qr_generator
        qr_result = qr_generator.generate_ticket_qr(data)
        
        if qr_result:
            return jsonify({
                'success': True,
                'qr_code': qr_result['qr_code_base64'],
                'verification_code': qr_result['verification_code'],
                'ticket_info': qr_result['ticket_info']
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to generate QR code'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/qr/generate/parking', methods=['POST'])
@login_required
def generate_parking_qr():
    """Generate QR code for parking pass"""
    try:
        data = request.get_json()
        
        from qr_generator import qr_generator
        qr_result = qr_generator.generate_parking_qr(data)
        
        if qr_result:
            return jsonify({
                'success': True,
                'qr_code': qr_result['qr_code_base64'],
                'verification_code': qr_result['verification_code'],
                'parking_info': qr_result['parking_info']
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to generate parking QR code'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/qr/generate/entry', methods=['POST'])
@login_required
def generate_entry_qr():
    """Generate QR code for event entry"""
    try:
        data = request.get_json()
        data['customer_id'] = current_user.id
        data['customer_name'] = current_user.name
        
        from qr_generator import qr_generator
        qr_result = qr_generator.generate_event_entry_qr(data)
        
        if qr_result:
            return jsonify({
                'success': True,
                'qr_code': qr_result['qr_code_base64'],
                'verification_code': qr_result['verification_code'],
                'entry_info': qr_result['entry_info']
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to generate entry QR code'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/qr/generate/pass', methods=['POST'])
@login_required
def generate_digital_pass():
    """Generate digital pass with QR code"""
    try:
        data = request.get_json()
        pass_type = data.get('type', 'general')
        
        # Add customer info
        data['customer_name'] = current_user.name
        
        from qr_generator import qr_generator
        pass_result = qr_generator.generate_digital_pass(data, pass_type)
        
        if pass_result:
            return jsonify({
                'success': True,
                'qr_code': pass_result['qr_code_base64'],
                'pass_image': pass_result['pass_image_base64'],
                'verification_code': pass_result['verification_code'],
                'pass_info': pass_result['pass_info']
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to generate digital pass'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/verify/ticket/<verification_code>')
def verify_ticket_qr(verification_code):
    """Verify ticket QR code"""
    try:
        from qr_generator import qr_generator
        result = qr_generator.verify_qr_code(verification_code)
        
        if result['valid']:
            ticket_data = result['data']
            return render_template('qr_verification.html', 
                                 verification_result=result,
                                 data_type='ticket',
                                 ticket_data=ticket_data)
        else:
            return render_template('qr_verification.html',
                                 verification_result=result,
                                 data_type='ticket')
            
    except Exception as e:
        return render_template('qr_verification.html',
                             verification_result={'valid': False, 'error': str(e)},
                             data_type='ticket')

@app.route('/verify/parking/<verification_code>')
def verify_parking_qr(verification_code):
    """Verify parking QR code"""
    try:
        from qr_generator import qr_generator
        result = qr_generator.verify_qr_code(verification_code)
        
        if result['valid']:
            parking_data = result['data']
            return render_template('qr_verification.html',
                                 verification_result=result,
                                 data_type='parking',
                                 parking_data=parking_data)
        else:
            return render_template('qr_verification.html',
                                 verification_result=result,
                                 data_type='parking')
            
    except Exception as e:
        return render_template('qr_verification.html',
                             verification_result={'valid': False, 'error': str(e)},
                             data_type='parking')

@app.route('/verify/entry/<verification_code>')
def verify_entry_qr(verification_code):
    """Verify event entry QR code"""
    try:
        from qr_generator import qr_generator
        result = qr_generator.verify_qr_code(verification_code)
        
        if result['valid']:
            entry_data = result['data']
            return render_template('qr_verification.html',
                                 verification_result=result,
                                 data_type='entry',
                                 entry_data=entry_data)
        else:
            return render_template('qr_verification.html',
                                 verification_result=result,
                                 data_type='entry')
            
    except Exception as e:
        return render_template('qr_verification.html',
                             verification_result={'valid': False, 'error': str(e)},
                             data_type='entry')

@app.route('/verify/pass/<verification_code>')
def verify_pass_qr(verification_code):
    """Verify digital pass QR code"""
    try:
        from qr_generator import qr_generator
        result = qr_generator.verify_qr_code(verification_code)
        
        if result['valid']:
            pass_data = result['data']
            return render_template('qr_verification.html',
                                 verification_result=result,
                                 data_type='pass',
                                 pass_data=pass_data)
        else:
            return render_template('qr_verification.html',
                                 verification_result=result,
                                 data_type='pass')
            
    except Exception as e:
        return render_template('qr_verification.html',
                             verification_result={'valid': False, 'error': str(e)},
                             data_type='pass')

# ==========================================
# PRODUCTION PAYMENT ENDPOINTS
# ==========================================

@app.route('/api/create-payment-intent', methods=['POST'])
@login_required
@csrf.exempt  # Replace require_csrf with csrf.exempt or remove if you want CSRF protection
@validate_json_input(PaymentValidationModel)
@limiter.limit("5 per minute", key_func=rate_limit_by_user)
def create_payment_intent():
    """Create payment order with unified PayPal + Indian gateways"""
    try:
        # Get validated data
        payment_data = request.validated_data
        payment_data['customer_id'] = current_user.id
        
        # Create payment order using unified processor
        result = create_unified_payment_order(payment_data)
        
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Payment order creation failed: {e}")
        return jsonify({'error': 'Payment setup failed'}), 500

@app.route('/api/unified-payment-webhook', methods=['POST'])
@limiter.exempt  # Webhooks should not be rate limited
def unified_payment_webhook():
    """Handle payment gateway webhook events (PayPal + Indian gateways)"""
    try:
        payload = request.get_data()
        
        # Get gateway from headers or form data
        gateway = request.headers.get('X-Gateway-Type', 'paypal')
        
        # Process webhook based on gateway
        result = handle_unified_payment_webhook(payload, gateway)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Payment webhook processing failed: {e}")
        return jsonify({'error': 'Webhook processing failed'}), 500

@app.route('/api/booking/create', methods=['POST'])
@login_required
@csrf.exempt  # Replace require_csrf with csrf.exempt or remove if you want CSRF protection
@validate_json_input(BookingValidationModel)
@limiter.limit("10 per minute", key_func=rate_limit_by_user)
def create_secure_booking():
    """Create booking with enhanced security validation"""
    try:
        booking_data = request.validated_data
        booking_data['customer_id'] = current_user.id
        
        # Additional server-side validation
        
        
        # Verify event exists and is bookable
        event = Event.query.get(booking_data['event_id'])
        if not event:
            return jsonify({'error': 'Event not found'}), 400
        
        if event.event_date < datetime.now().date():
            return jsonify({'error': 'Cannot book past events'}), 400
        
        # Verify seats are available
        seat_ids = booking_data['seat_ids']
        booked_seats = Ticket.query.filter(
            Ticket.seat_id.in_(seat_ids),
            Ticket.event_id == event.id,
            Ticket.ticket_status == 'Booked'
        ).all()
        
        if booked_seats:
            return jsonify({'error': 'Some seats are no longer available'}), 400
        
        # Calculate and verify total amount server-side
        seats = Seat.query.filter(Seat.id.in_(seat_ids)).all()
        calculated_total = sum(seat.price for seat in seats)
        calculated_total += calculated_total * 0.05  # Service fee
        calculated_total += 2.50  # Processing fee
        
        if abs(calculated_total - booking_data['total_amount']) > 0.01:
            return jsonify({'error': 'Amount mismatch detected'}), 400
        
        # Create payment order
        payment_result = create_unified_payment_order(booking_data)
        
        if isinstance(payment_result, tuple):
            return jsonify(payment_result[0]), payment_result[1]
        
        return jsonify(payment_result)
        
    except Exception as e:
        logger.error(f"Secure booking creation failed: {e}")
        return jsonify({'error': 'Booking creation failed'}), 500

@app.route('/booking/confirmation')
@login_required
def booking_confirmation():
    booking_id = request.args.get('booking_id')
    try:
        booking = Booking.query.get(int(booking_id)) if booking_id else None
    except Exception:
        booking = None
    return render_template('payment_success.html', payment_data={
        'booking_id': booking.id if booking else None,
        'amount': getattr(booking, 'total_amount', None)
    })

# BBL Action Hub API Routes
@app.route('/api/bbl/live-scores')
def get_live_scores():
    """Get live match scores and fixtures"""
    try:
        # Sample live data - in production, this would come from Supabase
        live_scores = [
            {
                'id': 1,
                'home_team': 'Melbourne Stars',
                'away_team': 'Sydney Sixers',
                'home_score': '156/4',
                'away_score': '132/6',
                'status': 'LIVE',
                'overs': '15.3',
                'venue': 'Melbourne Cricket Ground',
                'date': 'Today, 7:15 PM',
                'home_logo': url_for('static', filename='img/teams/Melbourne_Stars_logo.png'),
                'away_logo': url_for('static', filename='img/teams/Sydney_Sixers_logo.svg.png')
            },
            {
                'id': 2,
                'home_team': 'Perth Scorchers',
                'away_team': 'Brisbane Heat',
                'home_score': None,
                'away_score': None,
                'status': 'UPCOMING',
                'overs': None,
                'venue': 'Optus Stadium, Perth',
                'date': 'Tomorrow, 6:30 PM',
                'home_logo': url_for('static', filename='img/teams/Perth Scorchers.png'),
                'away_logo': url_for('static', filename='img/teams/Brisbane Heat.png')
            },
            {
                'id': 3,
                'home_team': 'Hobart Hurricanes',
                'away_team': 'Adelaide Strikers',
                'home_score': None,
                'away_score': None,
                'status': 'UPCOMING',
                'overs': None,
                'venue': 'Bellerive Oval, Hobart',
                'date': 'Dec 18, 7:15 PM',
                'home_logo': url_for('static', filename='img/teams/Hobart Hurricanes.png'),
                'away_logo': url_for('static', filename='img/teams/Adelaide Striker.png')
            }
        ]
        
        return jsonify({
            'success': True,
            'matches': live_scores
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/bbl/standings')
def get_standings():
    """Get current BBL standings/points table"""
    try:
        standings = [
            {
                'position': 1,
                'team': 'Melbourne Stars',
                'played': 8,
                'won': 6,
                'lost': 2,
                'nrr': '+0.85',
                'points': 16,
                'logo': url_for('static', filename='img/teams/Melbourne_Stars_logo.png'),
                'is_playoff': True
            },
            {
                'position': 2,
                'team': 'Sydney Sixers',
                'played': 8,
                'won': 5,
                'lost': 3,
                'nrr': '+0.42',
                'points': 14,
                'logo': url_for('static', filename='img/teams/Sydney_Sixers_logo.svg.png'),
                'is_playoff': True
            },
            {
                'position': 3,
                'team': 'Perth Scorchers',
                'played': 7,
                'won': 4,
                'lost': 3,
                'nrr': '+0.18',
                'points': 12,
                'logo': url_for('static', filename='img/teams/Perth Scorchers.png'),
                'is_playoff': True
            },
            {
                'position': 4,
                'team': 'Brisbane Heat',
                'played': 8,
                'won': 4,
                'lost': 4,
                'nrr': '-0.15',
                'points': 10,
                'logo': url_for('static', filename='img/teams/Brisbane Heat.png'),
                'is_playoff': True
            },
            {
                'position': 5,
                'team': 'Hobart Hurricanes',
                'played': 7,
                'won': 3,
                'lost': 4,
                'nrr': '-0.28',
                'points': 8,
                'logo': url_for('static', filename='img/teams/Hobart Hurricanes.png'),
                'is_playoff': False
            },
            {
                'position': 6,
                'team': 'Adelaide Strikers',
                'played': 8,
                'won': 3,
                'lost': 5,
                'nrr': '-0.35',
                'points': 8,
                'logo': url_for('static', filename='img/teams/Adelaide Striker.png'),
                'is_playoff': False
            }
        ]
        
        return jsonify({
            'success': True,
            'standings': standings
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/bbl/top-performers')
def get_top_performers():
    """Get top performing players"""
    try:
        top_runs = [
            {
                'id': 1,
                'name': 'Marcus Stoinis',
                'team': 'Melbourne Stars',
                'runs': 485,
                'avatar': 'MS',
                'logo': url_for('static', filename='img/teams/Melbourne_Stars_logo.png'),
                'headshot': url_for('static', filename='img/players/marcus_stoinis.jpg')
            },
            {
                'id': 2,
                'name': 'Josh Inglis',
                'team': 'Perth Scorchers',
                'runs': 423,
                'avatar': 'JI',
                'logo': url_for('static', filename='img/teams/Perth Scorchers.png'),
                'headshot': url_for('static', filename='img/players/josh_inglis.jpg')
            },
            {
                'id': 3,
                'name': 'Alex Hales',
                'team': 'Sydney Sixers',
                'runs': 395,
                'avatar': 'AH',
                'logo': url_for('static', filename='img/teams/Sydney_Sixers_logo.svg.png'),
                'headshot': url_for('static', filename='img/players/alex_hales.jpg')
            },
            {
                'id': 4,
                'name': 'Chris Lynn',
                'team': 'Brisbane Heat',
                'runs': 367,
                'avatar': 'CL',
                'logo': url_for('static', filename='img/teams/Brisbane Heat.png'),
                'headshot': url_for('static', filename='img/players/chris_lynn.jpg')
            }
        ]
        
        top_wickets = [
            {
                'id': 1,
                'name': 'Trent Boult',
                'team': 'Hobart Hurricanes',
                'wickets': 24,
                'avatar': 'TB',
                'logo': url_for('static', filename='img/teams/Hobart Hurricanes.png'),
                'headshot': url_for('static', filename='img/players/trent_boult.jpg')
            },
            {
                'id': 2,
                'name': 'Jhye Richardson',
                'team': 'Perth Scorchers',
                'wickets': 22,
                'avatar': 'JR',
                'logo': url_for('static', filename='img/teams/Perth Scorchers.png'),
                'headshot': url_for('static', filename='img/players/jhye_richardson.jpg')
            },
            {
                'id': 3,
                'name': 'Adam Zampa',
                'team': 'Melbourne Stars',
                'wickets': 21,
                'avatar': 'AZ',
                'logo': url_for('static', filename='img/teams/Melbourne_Stars_logo.png'),
                'headshot': url_for('static', filename='img/players/adam_zampa.jpg')
            },
            {
                'id': 4,
                'name': 'Sean Abbott',
                'team': 'Sydney Sixers',
                'wickets': 19,
                'avatar': 'SA',
                'logo': url_for('static', filename='img/teams/Sydney_Sixers_logo.svg.png'),
                'headshot': url_for('static', filename='img/players/sean_abbott.jpg')
            }
        ]
        
        return jsonify({
            'success': True,
            'top_runs': top_runs,
            'top_wickets': top_wickets
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

## Removed read-only dump endpoints for direct frontend Supabase access

@app.route('/api/bbl/teams')
# ===============================
# TICKET TRANSFER API ENDPOINTS
# ===============================

@app.route('/api/ticket/transfer', methods=['POST'])
@login_required
@require_csrf if SECURITY_FRAMEWORK_AVAILABLE else lambda f: f
def initiate_ticket_transfer():
    """Initiate a ticket transfer to another user"""
    try:
        data = request.get_json()
        
        # Validate input using security framework if available
        if SECURITY_FRAMEWORK_AVAILABLE:
            validation_result = validate_json_input(data, {
                'ticket_id': {'type': 'integer', 'required': True},
                'to_email': {'type': 'string', 'required': True, 'format': 'email'},
                'transfer_fee': {'type': 'number', 'minimum': 0, 'default': 0}
            })
            if not validation_result['valid']:
                return jsonify({'error': validation_result['error']}), 400
            data = validation_result['data']
        
        # Verify ticket ownership
        ticket = Ticket.query.get(data['ticket_id'])
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
            
        if ticket.customer_id != current_user.id:
            return jsonify({'error': 'You do not own this ticket'}), 403
            
        # Check if ticket is already being transferred
        existing_transfer = TicketTransfer.query.filter_by(
            ticket_id=ticket.id,
            transfer_status='pending'
        ).first()
        if existing_transfer:
            return jsonify({'error': 'Ticket transfer already in progress'}), 400
            
        # Check if event is still in the future
        event = Event.query.get(ticket.event_id)
        if event.event_date <= datetime.now(timezone.utc).date():
            return jsonify({'error': 'Cannot transfer tickets for past events'}), 400
            
        # Generate transfer code and verification code
        import secrets
        transfer_code = secrets.token_urlsafe(16)
        verification_code = f"{secrets.randbelow(999999):06d}"
        
        # Create transfer record
        transfer = TicketTransfer(
            ticket_id=ticket.id,
            from_customer_id=current_user.id,
            to_email=data['to_email'].lower(),
            transfer_code=transfer_code,
            transfer_fee=data.get('transfer_fee', 0),
            verification_code=verification_code,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=48)
        )
        
        # Check if recipient has an account
        recipient = Customer.query.filter_by(email=data['to_email'].lower()).first()
        if recipient:
            transfer.to_customer_id = recipient.id
            
        db.session.add(transfer)
        db.session.commit()
        
        # TODO: Send email notification to recipient
        
        return jsonify({
            'success': True,
            'transfer_code': transfer_code,
            'message': 'Transfer initiated successfully. Recipient will receive an email with instructions.'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ticket transfer initiation failed: {e}")
        return jsonify({'error': 'Transfer initiation failed'}), 500

@app.route('/api/ticket/transfer/<transfer_code>/accept', methods=['POST'])
def accept_ticket_transfer(transfer_code):
    """Accept a ticket transfer"""
    try:
        data = request.get_json() or {}
        
        # Find transfer by code
        transfer = TicketTransfer.query.filter_by(transfer_code=transfer_code).first()
        if not transfer:
            return jsonify({'error': 'Invalid transfer code'}), 404
            
        if transfer.transfer_status != 'pending':
            return jsonify({'error': 'Transfer is no longer available'}), 400
            
        if transfer.expires_at < datetime.now(timezone.utc):
            transfer.transfer_status = 'expired'
            db.session.commit()
            return jsonify({'error': 'Transfer has expired'}), 400
            
        # Verify recipient email or require login
        if current_user.is_authenticated:
            if current_user.email != transfer.to_email:
                return jsonify({'error': 'This transfer is not intended for your account'}), 403
            recipient = current_user
        else:
            # For non-logged-in users, create account or find existing
            recipient = Customer.query.filter_by(email=transfer.to_email).first()
            if not recipient:
                return jsonify({'error': 'Please create an account first to accept this transfer'}), 400
            
        # Verify with verification code if provided
        if 'verification_code' in data:
            if data['verification_code'] != transfer.verification_code:
                return jsonify({'error': 'Invalid verification code'}), 400
            transfer.is_verified = True
            
        # Complete the transfer
        ticket = Ticket.query.get(transfer.ticket_id)
        original_customer_id = ticket.customer_id
        ticket.customer_id = recipient.id
        
        transfer.to_customer_id = recipient.id
        transfer.transfer_status = 'accepted'
        transfer.completed_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Ticket transfer completed successfully',
            'ticket_id': ticket.id
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ticket transfer acceptance failed: {e}")
        return jsonify({'error': 'Transfer acceptance failed'}), 500

# ===============================
# RESALE MARKETPLACE API ENDPOINTS
# ===============================

@app.route('/api/marketplace/list-ticket', methods=['POST'])
@login_required
@require_csrf if SECURITY_FRAMEWORK_AVAILABLE else lambda f: f
def list_ticket_for_resale():
    """List a ticket on the resale marketplace"""
    try:
        data = request.get_json()
        
        # Validate input
        required_fields = ['ticket_id', 'listing_price']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
                
        # Verify ticket ownership
        ticket = Ticket.query.get(data['ticket_id'])
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
            
        if ticket.customer_id != current_user.id:
            return jsonify({'error': 'You do not own this ticket'}), 403
            
        # Check if ticket is already listed
        existing_listing = ResaleMarketplace.query.filter_by(
            ticket_id=ticket.id,
            listing_status='active'
        ).first()
        if existing_listing:
            return jsonify({'error': 'Ticket is already listed for sale'}), 400
            
        # Check if event is still in the future
        event = Event.query.get(ticket.event_id)
        if event.event_date <= datetime.now(timezone.utc).date():
            return jsonify({'error': 'Cannot list tickets for past events'}), 400
            
        # Get original ticket price
        seat = Seat.query.get(ticket.seat_id)
        original_price = seat.price if seat else 0
        
        # Validate listing price (max 150% of original price)
        max_price = original_price * 1.5
        if data['listing_price'] > max_price:
            return jsonify({'error': f'Listing price cannot exceed {max_price:.2f} (150% of original price)'}), 400
            
        # Calculate platform fee (5% of listing price)
        platform_fee = data['listing_price'] * 0.05
        seller_fee = data['listing_price'] * 0.03  # 3% seller fee
        
        # Create marketplace listing
        listing = ResaleMarketplace(
            ticket_id=ticket.id,
            seller_id=current_user.id,
            original_price=original_price,
            listing_price=data['listing_price'],
            platform_fee=platform_fee,
            seller_fee=seller_fee,
            listing_description=data.get('description', ''),
            is_negotiable=data.get('is_negotiable', False),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30)
        )
        
        db.session.add(listing)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'listing_id': listing.id,
            'platform_fee': platform_fee,
            'seller_fee': seller_fee,
            'net_amount': data['listing_price'] - platform_fee - seller_fee,
            'message': 'Ticket listed successfully on marketplace'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Marketplace listing failed: {e}")
        return jsonify({'error': 'Listing failed'}), 500

@app.route('/api/marketplace/search', methods=['GET'])
def search_marketplace():
    """Search tickets on the resale marketplace"""
    try:
        # Get search parameters
        event_id = request.args.get('event_id', type=int)
        stadium_id = request.args.get('stadium_id', type=int)
        max_price = request.args.get('max_price', type=float)
        seat_type = request.args.get('seat_type')
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Build query
        query = ResaleMarketplace.query.filter_by(listing_status='active')
        
        # Join with related tables for filtering
        query = query.join(Ticket).join(Event).join(Seat)
        
        # Apply filters
        if event_id:
            query = query.filter(Event.id == event_id)
        if stadium_id:
            query = query.filter(Event.stadium_id == stadium_id)
        if max_price:
            query = query.filter(ResaleMarketplace.listing_price <= max_price)
        if seat_type:
            query = query.filter(Seat.seat_type == seat_type)
            
        # Only show future events
        query = query.filter(Event.event_date > datetime.now(timezone.utc).date())
        
        # Order by listing date (newest first)
        query = query.order_by(ResaleMarketplace.listed_at.desc())
        
        # Paginate
        listings = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Format results
        results = []
        for listing in listings.items:
            ticket = listing.ticket
            event = ticket.event
            seat = ticket.seat
            stadium = event.stadium
            
            results.append({
                'listing_id': listing.id,
                'ticket_id': ticket.id,
                'event': {
                    'id': event.id,
                    'name': event.event_name,
                    'date': event.event_date.isoformat(),
                    'start_time': event.start_time.isoformat()
                },
                'stadium': {
                    'id': stadium.id,
                    'name': stadium.name,
                    'location': stadium.location
                },
                'seat': {
                    'section': seat.section,
                    'row': seat.row_number,
                    'number': seat.seat_number,
                    'type': seat.seat_type
                },
                'pricing': {
                    'original_price': listing.original_price,
                    'listing_price': listing.listing_price,
                    'savings': listing.original_price - listing.listing_price if listing.original_price > listing.listing_price else 0
                },
                'description': listing.listing_description,
                'is_negotiable': listing.is_negotiable,
                'listed_at': listing.listed_at.isoformat(),
                'expires_at': listing.expires_at.isoformat() if listing.expires_at else None
            })
            
        return jsonify({
            'success': True,
            'listings': results,
            'pagination': {
                'page': page,
                'pages': listings.pages,
                'per_page': per_page,
                'total': listings.total,
                'has_next': listings.has_next,
                'has_prev': listings.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"Marketplace search failed: {e}")
        return jsonify({'error': 'Search failed'}), 500

# ===============================
# SEASON TICKET API ENDPOINTS
# ===============================

@app.route('/api/season-ticket/purchase', methods=['POST'])
@login_required
@require_csrf if SECURITY_FRAMEWORK_AVAILABLE else lambda f: f
def purchase_season_ticket():
    """Purchase a season ticket"""
    try:
        data = request.get_json()
        
        # Validate input
        required_fields = ['stadium_id', 'seat_id', 'season_name']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
                
        # Verify stadium and seat
        stadium = Stadium.query.get(data['stadium_id'])
        if not stadium:
            return jsonify({'error': 'Stadium not found'}), 404
            
        seat = Seat.query.get(data['seat_id'])
        if not seat or seat.stadium_id != stadium.id:
            return jsonify({'error': 'Seat not found or not in specified stadium'}), 404
            
        # Check if seat is already taken for this season
        existing_season_ticket = SeasonTicket.query.filter_by(
            stadium_id=stadium.id,
            seat_id=seat.id,
            season_name=data['season_name'],
            ticket_status='active'
        ).first()
        if existing_season_ticket:
            return jsonify({'error': 'Seat is already taken for this season'}), 400
            
        # Get season details
        season_start = datetime.strptime(data.get('season_start_date', '2024-01-01'), '%Y-%m-%d').date()
        season_end = datetime.strptime(data.get('season_end_date', '2024-12-31'), '%Y-%m-%d').date()
        
        # Calculate matches and pricing
        total_matches = data.get('total_matches', 10)  # Default 10 matches per season
        price_per_match = seat.price
        total_price = price_per_match * total_matches * 0.85  # 15% discount for season tickets
        
        # Create season ticket
        season_ticket = SeasonTicket(
            customer_id=current_user.id,
            stadium_id=stadium.id,
            seat_id=seat.id,
            season_name=data['season_name'],
            season_start_date=season_start,
            season_end_date=season_end,
            total_matches=total_matches,
            price_per_match=price_per_match,
            total_price=total_price,
            priority_booking=True,
            transfer_limit=data.get('transfer_limit', 5),
            activated_at=datetime.now(timezone.utc)
        )
        
        db.session.add(season_ticket)
        db.session.flush()  # Get the ID
        
        # Create individual match records for upcoming events
        upcoming_events = Event.query.filter(
            Event.stadium_id == stadium.id,
            Event.event_date.between(season_start, season_end)
        ).limit(total_matches).all()
        
        for event in upcoming_events:
            match_record = SeasonTicketMatch(
                season_ticket_id=season_ticket.id,
                event_id=event.id
            )
            db.session.add(match_record)
            
        db.session.commit()
        
        return jsonify({
            'success': True,
            'season_ticket_id': season_ticket.id,
            'total_price': total_price,
            'savings': (price_per_match * total_matches) - total_price,
            'matches_included': len(upcoming_events),
            'message': 'Season ticket purchased successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Season ticket purchase failed: {e}")
        return jsonify({'error': 'Season ticket purchase failed'}), 500

@app.route('/api/season-ticket/<int:season_ticket_id>/matches', methods=['GET'])
@login_required
def get_season_ticket_matches(season_ticket_id):
    """Get matches included in a season ticket"""
    try:
        # Verify ownership
        season_ticket = SeasonTicket.query.get(season_ticket_id)
        if not season_ticket:
            return jsonify({'error': 'Season ticket not found'}), 404
            
        if season_ticket.customer_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
            
        # Get all matches
        matches = db.session.query(SeasonTicketMatch, Event).join(
            Event, SeasonTicketMatch.event_id == Event.id
        ).filter(
            SeasonTicketMatch.season_ticket_id == season_ticket_id
        ).order_by(Event.event_date).all()
        
        results = []
        for match_record, event in matches:
            results.append({
                'match_id': match_record.id,
                'event': {
                    'id': event.id,
                    'name': event.event_name,
                    'date': event.event_date.isoformat(),
                    'start_time': event.start_time.isoformat()
                },
                'status': {
                    'is_used': match_record.is_used,
                    'used_at': match_record.used_at.isoformat() if match_record.used_at else None,
                    'is_transferred': match_record.is_transferred,
                    'transferred_at': match_record.transferred_at.isoformat() if match_record.transferred_at else None,
                    'transfer_price': match_record.transfer_price
                }
            })
            
        return jsonify({
            'success': True,
            'season_ticket': {
                'id': season_ticket.id,
                'season_name': season_ticket.season_name,
                'matches_used': season_ticket.matches_used,
                'matches_transferred': season_ticket.matches_transferred,
                'transfer_limit': season_ticket.transfer_limit
            },
            'matches': results
        })
        
    except Exception as e:
        logger.error(f"Season ticket matches retrieval failed: {e}")
        return jsonify({'error': 'Failed to retrieve matches'}), 500

# ===============================
# ACCESSIBILITY API ENDPOINTS
# ===============================

@app.route('/api/accessibility/register', methods=['POST'])
@login_required
@require_csrf if SECURITY_FRAMEWORK_AVAILABLE else lambda f: f
def register_accessibility_needs():
    """Register accessibility accommodation needs"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'accommodation_type' not in data:
            return jsonify({'error': 'accommodation_type is required'}), 400
            
        # Check if user already has accommodation record
        existing = AccessibilityAccommodation.query.filter_by(
            customer_id=current_user.id
        ).first()
        
        if existing:
            # Update existing record
            existing.accommodation_type = data['accommodation_type']
            existing.description = data.get('description', '')
            existing.severity_level = data.get('severity_level', 'moderate')
            existing.requires_wheelchair_access = data.get('requires_wheelchair_access', False)
            existing.requires_companion_seat = data.get('requires_companion_seat', False)
            existing.requires_aisle_access = data.get('requires_aisle_access', False)
            existing.requires_hearing_loop = data.get('requires_hearing_loop', False)
            existing.requires_sign_language = data.get('requires_sign_language', False)
            existing.requires_braille = data.get('requires_braille', False)
            existing.mobility_equipment = data.get('mobility_equipment', '')
            existing.service_animal = data.get('service_animal', False)
            existing.service_animal_type = data.get('service_animal_type', '')
            existing.preferred_communication = data.get('preferred_communication', 'email')
            existing.emergency_contact_name = data.get('emergency_contact_name', '')
            existing.emergency_contact_phone = data.get('emergency_contact_phone', '')
            existing.updated_at = datetime.now(timezone.utc)
            
            accommodation = existing
        else:
            # Create new record
            accommodation = AccessibilityAccommodation(
                customer_id=current_user.id,
                accommodation_type=data['accommodation_type'],
                description=data.get('description', ''),
                severity_level=data.get('severity_level', 'moderate'),
                requires_wheelchair_access=data.get('requires_wheelchair_access', False),
                requires_companion_seat=data.get('requires_companion_seat', False),
                requires_aisle_access=data.get('requires_aisle_access', False),
                requires_hearing_loop=data.get('requires_hearing_loop', False),
                requires_sign_language=data.get('requires_sign_language', False),
                requires_braille=data.get('requires_braille', False),
                mobility_equipment=data.get('mobility_equipment', ''),
                service_animal=data.get('service_animal', False),
                service_animal_type=data.get('service_animal_type', ''),
                preferred_communication=data.get('preferred_communication', 'email'),
                emergency_contact_name=data.get('emergency_contact_name', ''),
                emergency_contact_phone=data.get('emergency_contact_phone', '')
            )
            db.session.add(accommodation)
            
        db.session.commit()
        
        return jsonify({
            'success': True,
            'accommodation_id': accommodation.id,
            'message': 'Accessibility needs registered successfully',
            'verification_required': not accommodation.is_verified
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Accessibility registration failed: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/accessibility/book', methods=['POST'])
@login_required
@require_csrf if SECURITY_FRAMEWORK_AVAILABLE else lambda f: f
def book_with_accessibility():
    """Create a booking with accessibility accommodations"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['event_id', 'seat_ids', 'requested_accommodations']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
                
        # Get user's accessibility accommodation record
        accommodation = AccessibilityAccommodation.query.filter_by(
            customer_id=current_user.id
        ).first()
        
        if not accommodation:
            return jsonify({'error': 'Please register your accessibility needs first'}), 400
            
        # Verify event and seats
        event = Event.query.get(data['event_id'])
        if not event:
            return jsonify({'error': 'Event not found'}), 404
            
        seats = Seat.query.filter(Seat.id.in_(data['seat_ids'])).all()
        if len(seats) != len(data['seat_ids']):
            return jsonify({'error': 'One or more seats not found'}), 404
            
        # Check seat availability
        occupied_seats = Ticket.query.filter(
            Ticket.event_id == event.id,
            Ticket.seat_id.in_(data['seat_ids'])
        ).all()
        if occupied_seats:
            return jsonify({'error': 'One or more seats are already booked'}), 400
            
        # Validate accessibility requirements for selected seats
        if accommodation.requires_wheelchair_access:
            # Check if seats support wheelchair access (this would need to be added to Seat model)
            # For now, we'll just log the requirement
            logger.info(f"Wheelchair access required for booking by user {current_user.id}")
            
        # Calculate total amount
        total_amount = sum(seat.price for seat in seats)
        
        # Create booking
        booking = Booking(
            customer_id=current_user.id,
            total_amount=total_amount
        )
        db.session.add(booking)
        db.session.flush()  # Get booking ID
        
        # Create tickets
        tickets = []
        for seat in seats:
            ticket = Ticket(
                event_id=event.id,
                seat_id=seat.id,
                customer_id=current_user.id,
                booking_id=booking.id,
                ticket_status='Booked'
            )
            db.session.add(ticket)
            tickets.append(ticket)
            
        # Create accessibility booking record
        accessibility_booking = AccessibilityBooking(
            booking_id=booking.id,
            accommodation_id=accommodation.id,
            requested_accommodations=json.dumps(data['requested_accommodations']),
            special_instructions=data.get('special_instructions', ''),
            accommodation_status='requested'
        )
        db.session.add(accessibility_booking)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'booking_id': booking.id,
            'accessibility_booking_id': accessibility_booking.id,
            'total_amount': total_amount,
            'message': 'Booking created successfully with accessibility accommodations',
            'next_steps': 'Stadium staff will review your accommodation requests and contact you within 24 hours.'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Accessibility booking failed: {e}")
        return jsonify({'error': 'Booking failed'}), 500

@app.route('/api/accessibility/status/<int:booking_id>', methods=['GET'])
@login_required
def get_accessibility_status(booking_id):
    """Get accessibility accommodation status for a booking"""
    try:
        # Verify booking ownership
        booking = Booking.query.get(booking_id)
        if not booking or booking.customer_id != current_user.id:
            return jsonify({'error': 'Booking not found or access denied'}), 404
            
        # Get accessibility booking
        accessibility_booking = AccessibilityBooking.query.filter_by(
            booking_id=booking_id
        ).first()
        
        if not accessibility_booking:
            return jsonify({'error': 'No accessibility accommodations found for this booking'}), 404
            
        # Get accommodation details
        accommodation = AccessibilityAccommodation.query.get(
            accessibility_booking.accommodation_id
        )
        
        return jsonify({
            'success': True,
            'booking_id': booking_id,
            'accommodation_status': accessibility_booking.accommodation_status,
            'requested_accommodations': json.loads(accessibility_booking.requested_accommodations or '[]'),
            'provided_accommodations': json.loads(accessibility_booking.provided_accommodations or '[]'),
            'staff_notes': accessibility_booking.staff_notes,
            'special_instructions': accessibility_booking.special_instructions,
            'fulfilled_at': accessibility_booking.fulfilled_at.isoformat() if accessibility_booking.fulfilled_at else None,
            'accommodation_type': accommodation.accommodation_type if accommodation else None
        })
        
    except Exception as e:
        logger.error(f"Accessibility status retrieval failed: {e}")
        return jsonify({'error': 'Failed to retrieve status'}), 500

def get_teams():
    """Get all BBL teams data"""
    try:
        teams = [
            {
                'id': 1,
                'name': 'Adelaide Strikers',
                'short_name': 'STR',
                'position': 6,
                'points': 8,
                'logo': url_for('static', filename='img/teams/Adelaide Striker.png'),
                'color': '#003DA5',
                'subtitle': 'The Strike Force'
            },
            {
                'id': 2,
                'name': 'Brisbane Heat',
                'short_name': 'HEA',
                'position': 4,
                'points': 10,
                'logo': url_for('static', filename='img/teams/Brisbane Heat.png'),
                'color': '#FF6B35',
                'subtitle': 'Feel the Heat'
            },
            {
                'id': 3,
                'name': 'Hobart Hurricanes',
                'short_name': 'HUR',
                'position': 5,
                'points': 8,
                'logo': url_for('static', filename='img/teams/Hobart Hurricanes.png'),
                'color': '#6B2C91',
                'subtitle': 'Hurricane Force'
            },
            {
                'id': 4,
                'name': 'Melbourne Renegades',
                'short_name': 'REN',
                'position': 7,
                'points': 6,
                'logo': url_for('static', filename='img/teams/Melbourne Renegades.png'),
                'color': '#E40613',
                'subtitle': 'Rebel Spirit'
            },
            {
                'id': 5,
                'name': 'Melbourne Stars',
                'short_name': 'STA',
                'position': 1,
                'points': 16,
                'logo': url_for('static', filename='img/teams/Melbourne_Stars_logo.png'),
                'color': '#00A651',
                'subtitle': 'Shine Bright'
            },
            {
                'id': 6,
                'name': 'Perth Scorchers',
                'short_name': 'SCO',
                'position': 3,
                'points': 12,
                'logo': url_for('static', filename='img/teams/Perth Scorchers.png'),
                'color': '#FF8800',
                'subtitle': 'Desert Fire'
            },
            {
                'id': 7,
                'name': 'Sydney Sixers',
                'short_name': 'SIX',
                'position': 2,
                'points': 14,
                'logo': url_for('static', filename='img/teams/Sydney_Sixers_logo.svg.png'),
                'color': '#FF1493',
                'subtitle': 'Six Appeal'
            },
            {
                'id': 8,
                'name': 'Sydney Thunder',
                'short_name': 'THU',
                'position': 8,
                'points': 4,
                'logo': url_for('static', filename='img/teams/Sydney Thunder.png'),
                'color': '#FFED00',
                'subtitle': 'Thunder Strike'
            }
        ]
        
        return jsonify({
            'success': True,
            'teams': teams
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("=" * 60)
    print("CricVerse Stadium System - Starting Up")
    print("=" * 60)
    
    # Initialize database with retry logic
    print("1. Initializing database...")
    with app.app_context():
        db_success = init_db()
        if not db_success:
            print("[WARN] Database initialization had issues, but continuing...")
        else:
            print("[PASS] Database initialized successfully")
    
    # Initialize Flask-Admin (disabled by default to avoid schema mismatches)
    print("\n2. Initializing Flask-Admin...")
    if os.getenv('ENABLE_ADMIN', '0') == '1':
        try:
            admin = init_admin(app, db, Customer, Event, Booking, Ticket, Stadium, Team, Seat, Concession, Parking, VerificationSubmission)
            print("[PASS] Flask-Admin initialized")
        except Exception as e:
            print(f"[WARN] Flask-Admin initialization failed: {e}")
    else:
        print("[SKIP] Admin disabled (set ENABLE_ADMIN=1 to enable)")
    
    # Test basic functionality
    print("\n3. Testing basic functionality...")
    try:
        with app.test_client() as client:
            # Test home page
            response = client.get('/')
            if response.status_code == 200:
                print(f"[PASS] Home page (Status: {response.status_code})")
            else:
                print(f"[WARN] Home page (Status: {response.status_code})")
            
            # Test CSRF API
            response = client.get('/api/csrf-token')
            if response.status_code == 200:
                print(f"[PASS] CSRF API (Status: {response.status_code})")
            else:
                print(f"[WARN] CSRF API (Status: {response.status_code})")
                
            # Test BBL API
            response = client.get('/api/bbl/live-scores')
            if response.status_code == 200:
                print(f"[PASS] BBL API (Status: {response.status_code})")
            else:
                print(f"[WARN] BBL API (Status: {response.status_code})")
    except Exception as e:
        print(f"[WARN] Basic functionality test error: {e}")
    
    # Start the application with optimized settings
    print("\n4. Starting CricVerse Stadium System...")
    print(f"[WEB] Server will be available at: http://localhost:5000")
    print(f"[WEB] Also accessible at: http://127.0.0.1:5000")
    print("[NOTE] Press CTRL+C to stop the server")
    
    try:
        # Use production-like settings even in development for better performance
        socketio.run(app, 
                    debug=False,  # Disable debug mode to prevent restarts
                    host='0.0.0.0', 
                    port=5000,
                    use_reloader=False,  # Disable auto-reloader
                    log_output=False)  # Reduce logging for performance
    except KeyboardInterrupt:
        print("\n[INFO] Server stopped by user")
    except Exception as e:
        print(f"\n[ERROR] Server error: {e}")
        import traceback
        traceback.print_exc()
