import os
from dotenv import load_dotenv
from flask_migrate import Migrate
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_compress import Compress
from flask_login import LoginManager
import logging

# Load environment variables as early as possible
load_dotenv()

"""
CricVerse - Big Bash League Stadium System
Streamlined main application file
"""

# Configure logging
logger = logging.getLogger(__name__)

# Initialize extensions globally but without app context initially
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

# Initialize SocketIO and notification services globally
socketio = None
notification_service = None

# Import config after db and migrate are initialized
from config import config

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    from app.models import Customer
    return Customer.query.get(int(user_id))

def create_app(config_name='default'):
    """Application factory pattern implementation."""
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='./static')
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
    migrate.init_app(app, db) # Initialize migrate with app and db

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

    # Inject enhanced services status into templates
    @app.context_processor
    def inject_services_status():
        try:
            from app.services import get_services_health
            return {'services_status': get_services_health()}
        except Exception:
            return {'services_status': {'error': 'Services status unavailable'}}

    # Register blueprints
    from app.routes import booking_routes
    app.register_blueprint(booking_routes.bp)
    from app.routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp)
    from app.routes.user import bp as user_bp
    app.register_blueprint(user_bp)
    from app.routes.ticketing import bp as ticketing_bp
    app.register_blueprint(ticketing_bp)

    # Register main site routes blueprint
    from app.routes.main import main_bp
    app.register_blueprint(main_bp)
    
    # Register admin routes blueprint
    from app.routes.admin import admin_bp
    app.register_blueprint(admin_bp)
    
    # Register enhanced features blueprint
    try:
        from app.routes.enhanced_features import enhanced_bp
        app.register_blueprint(enhanced_bp)
        logger.info("✅ Enhanced features routes registered")
    except Exception as e:
        logger.warning(f"⚠️ Failed to register enhanced features routes: {e}")
    
    # Register live cricket scoring blueprint
    try:
        from app.routes.live_cricket import live_cricket_bp
        app.register_blueprint(live_cricket_bp)
        logger.info("✅ Live cricket routes registered")
    except Exception as e:
        logger.warning(f"⚠️ Failed to register live cricket routes: {e}")
    
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

    # Initialize Enhanced Services with Supabase Integration
    logger.info("🚀 Initializing CricVerse Enhanced Services with Supabase...")
    try:
        from app.services import init_services
        init_services(app, socketio_instance=socketio)
        
        # Initialize BBL Data Service after other services and env vars are loaded
        from supabase_bbl_integration import BBLDataService # Import the class, not the instance

        # Get Supabase credentials from environment variables
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')

        # Initialize BBLDataService with credentials
        app.bbl_data_service = BBLDataService(supabase_url, supabase_anon_key)
        
        logger.info("✅ All enhanced services initialized successfully with Supabase")
    except Exception as e:
        logger.error(f"❌ Failed to initialize enhanced services: {str(e)}")
    
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

    # Enhanced caching and performance headers
    @app.after_request
    def add_enhanced_headers(response):
        try:
            path = request.path or ''
            
            # Static file caching
            if path.startswith('/static/'):
                # 30 days immutable caching for versioned assets
                response.headers.setdefault('Cache-Control', 'public, max-age=2592000, immutable')
            
            # Security headers (from security service)
            try:
                from app.services.security_service import security_service
                if hasattr(security_service, 'security_headers'):
                    headers = security_service.security_headers.get_security_headers()
                    for key, value in headers.items():
                        response.headers.setdefault(key, value)
            except Exception:
                # Fallback security headers
                response.headers.setdefault('X-Content-Type-Options', 'nosniff')
                response.headers.setdefault('X-Frame-Options', 'DENY')
                response.headers.setdefault('X-XSS-Protection', '1; mode=block')
            
            # Performance monitoring
            try:
                from app.services.performance_service import performance_service
                if hasattr(performance_service, 'performance_monitor'):
                    performance_service.performance_monitor.record_request(
                        request.endpoint or 'unknown',
                        request.method,
                        response.status_code
                    )
            except Exception:
                pass  # Performance monitoring is optional
            
            return response
        except Exception:
            return response

    # Add enhanced error handlers
    @app.errorhandler(429)
    def rate_limit_handler(e):
        """Handle rate limit errors"""
        return {'error': 'Rate limit exceeded. Please try again later.'}, 429
    
    @app.errorhandler(400)
    def bad_request_handler(e):
        """Handle bad request errors"""
        return {'error': 'Bad request. Please check your input.'}, 400
    
    @app.errorhandler(500)
    def internal_error_handler(e):
        """Handle internal server errors"""
        logger.error(f"Internal server error: {str(e)}")
        return {'error': 'Internal server error. Please try again later.'}, 500

    # Add health check endpoint for enhanced services
    @app.route('/health/services')
    def services_health_check():
        """Health check endpoint for all enhanced services"""
        try:
            from app.services import get_services_health
            status = get_services_health()
            
            # Determine overall health
            all_healthy = True
            if 'services' in status:
                for service_name, service_status in status['services'].items():
                    if isinstance(service_status, dict):
                        service_health = service_status.get('status', 'unknown')
                        if service_health not in ['healthy', 'active']:
                            all_healthy = False
                            break
            
            return {
                'status': 'healthy' if all_healthy else 'degraded',
                'services': status,
                'timestamp': '2025-09-21T18:09:04+05:30'
            }, 200 if all_healthy else 503
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': '2025-09-21T18:09:04+05:30'
            }, 503

    # Add Supabase database health check endpoint
    @app.route('/health/database')
    def database_health_check():
        """Health check endpoint for Supabase database"""
        try:
            from app.services.supabase_service import supabase_service
            health_status = supabase_service.health_check()
            
            return {
                'database': health_status,
                'timestamp': '2025-09-21T18:09:04+05:30'
            }, 200 if health_status.get('status') == 'healthy' else 503
            
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': '2025-09-21T18:09:04+05:30'
            }, 503

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

    logger.info("🎉 CricVerse Flask Application initialized with Supabase integration!")
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