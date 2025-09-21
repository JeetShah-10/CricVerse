from flask import Flask, request
from flask_compress import Compress
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config
import os
import logging
# Removed admin import - not needed

# Configure logging
logger = logging.getLogger(__name__)

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

# Initialize SocketIO and notification services globally
socketio = None
notification_service = None

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    from app.models import Customer
    return Customer.query.get(int(user_id))

def create_app(config_name='default'):
    """Application factory pattern implementation."""
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')
    app.config.from_object(config[config_name])
    
    # If running under pytest, force testing-friendly SQLite in-memory DB
    if os.getenv('PYTEST_CURRENT_TEST') or config_name == 'testing':
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Strong browser caching for static files to improve load times
    # Note: During active development, you may want to reduce this value.
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 60 * 60 * 24 * 30  # 30 days
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    # Enable gzip compression for text-based responses
    Compress(app)
    
    # Inject Supabase configuration into all templates
    @app.context_processor
    def inject_supabase_env():
        supabase_url = os.getenv('SUPABASE_URL', '')
        # Prefer explicit anon key; fallback to SUPABASE_KEY if provided
        supabase_anon = os.getenv('SUPABASE_ANON_KEY') or os.getenv('SUPABASE_KEY', '')
        return {
            'SUPABASE_URL': supabase_url,
            'SUPABASE_ANON_KEY': supabase_anon,
        }
    
    # Register blueprints
    from app.routes import booking_routes
    app.register_blueprint(booking_routes.bp)
    from app.routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp)
    from app.routes.user import bp as user_bp
    app.register_blueprint(user_bp)
    from app.routes.ticketing import bp as ticketing_bp
    app.register_blueprint(ticketing_bp)
    from app.routes.chat import chat_bp
    app.register_blueprint(chat_bp)

    # Register main site routes blueprint
    from app.routes.main import main_bp
    app.register_blueprint(main_bp)
    
    # Register admin routes blueprint
    from app.routes.admin import admin_bp
    app.register_blueprint(admin_bp)
    
    # Register BBL API routes
    try:
        from app.routes.bbl import bbl_bp
        app.register_blueprint(bbl_bp)
        logger.info("✅ BBL API routes registered")
    except Exception as e:
        logger.warning(f"⚠️ Failed to register BBL API routes: {e}")
    
    # Initialize WebSocket and real-time features
    global socketio, notification_service
    try:
        from realtime_server import init_socketio
        socketio = init_socketio(app)
        logger.info("✅ WebSocket integration completed")
    except Exception as e:
        logger.warning(f"⚠️ WebSocket initialization failed: {e}")
    
    # Initialize notification services
    try:
        from notification import email_service, sms_service
        notification_service = {
            'email': email_service,
            'sms': sms_service
        }
        logger.info("✅ Notification services integrated")
    except Exception as e:
        logger.warning(f"⚠️ Notification services initialization failed: {e}")

    # Add caching headers for static assets (defense-in-depth alongside SEND_FILE_MAX_AGE_DEFAULT)
    @app.after_request
    def add_caching_headers(response):
        try:
            path = request.path or ''
            if path.startswith('/static/'):
                # 30 days immutable caching for versioned assets
                response.headers.setdefault('Cache-Control', 'public, max-age=2592000, immutable')
            return response
        except Exception:
            return response

    # Admin functionality handled by custom admin routes

    # In testing or pytest environment, ensure all tables are created
    if config_name == 'testing' or app.config.get('TESTING'):
        try:
            with app.app_context():
                # Import models so SQLAlchemy is aware of metadata before creating tables
                from app import models  # noqa: F401
                db.create_all()
                logger.info("✅ Created all database tables for testing environment")
        except Exception as e:
            logger.warning(f"⚠️ Failed to auto-create tables in testing environment: {e}")

    return app

# Expose a module-level app instance for tests importing `from app import app`
# This ensures tests get a Flask app instance, not the module
# Only create if not in testing mode to avoid conflicts
if not os.environ.get('PYTEST_CURRENT_TEST'):
    app = create_app(os.environ.get('FLASK_ENV', 'default'))
else:
    app = None  # Will be created by test fixtures

# Backward-compatibility: expose common ORM models at module level so
# imports like `from app import Stadium` continue to work.
try:
    from app.models import (
        Customer,
        Event,
        Booking,
        Ticket,
        Stadium,
        Team,
        Seat,
        Concession,
        MenuItem,
        Match,
    )
except Exception:
    # During early import or migrations, models might not be importable.
    # Downstream code typically handles this at runtime within app context.
    pass

# Provide a Razorpay client handle for tests importing `from app import razorpay_client`
try:
    import razorpay  # noqa: F401
    _key_id = os.getenv('RAZORPAY_KEY_ID')
    _key_secret = os.getenv('RAZORPAY_KEY_SECRET')
    if _key_id and _key_secret:
        razorpay_client = __import__('razorpay').Client(auth=(_key_id, _key_secret))
    else:
        razorpay_client = None
except Exception:
    razorpay_client = None