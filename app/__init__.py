from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config
import os
import logging
from admin import init_admin

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
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
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
        from realtime import init_socketio
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

    # Initialize Flask-Admin
    if os.getenv('ENABLE_ADMIN', '0') == '1':
        from app.models import Customer, Event, Booking, Ticket, Stadium, Team, Seat, Concession, Parking, VerificationSubmission
        init_admin(app, db, Customer, Event, Booking, Ticket, Stadium, Team, Seat, Concession, Parking, VerificationSubmission)

    return app

# Expose a module-level app instance for tests importing `from app import app`
try:
    app  # type: ignore[name-defined]
except NameError:  # pragma: no cover
    app = create_app(os.environ.get('FLASK_ENV', 'default'))

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