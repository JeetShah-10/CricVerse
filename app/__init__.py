from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config
import os
from admin import init_admin

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

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
    
    

    # Initialize Flask-Admin
    if os.getenv('ENABLE_ADMIN', '0') == '1':
        from app.models import Customer, Event, Booking, Ticket, Stadium, Team, Seat, Concession, Parking, VerificationSubmission
        init_admin(app, db, Customer, Event, Booking, Ticket, Stadium, Team, Seat, Concession, Parking, VerificationSubmission)

    return app