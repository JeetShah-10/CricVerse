from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    from app.models.booking import Customer
    return Customer.query.get(int(user_id))

def create_app(config_name='default'):
    """Application factory pattern implementation."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'booking.login'
    
    # Register blueprints
    from app.routes import booking_routes
    app.register_blueprint(booking_routes.bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app