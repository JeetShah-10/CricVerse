from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config
import os

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
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'index'
    
    # Register blueprints
    from app.routes import booking_routes
    app.register_blueprint(booking_routes.bp)
    
    # Register main site routes directly (not in blueprint)
    from flask import render_template
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/events')
    def events():
        return render_template('events.html')
    
    @app.route('/teams')
    def teams():
        return render_template('teams.html')
    
    @app.route('/stadiums')
    def stadiums():
        return render_template('stadiums.html')
    
    @app.route('/players')
    def players():
        return render_template('players.html')
    
    @app.route('/dashboard')
    def dashboard():
        return render_template('dashboard.html')
    
    @app.route('/login')
    def login():
        return render_template('login.html')
    
    @app.route('/register')
    def register():
        return render_template('register.html')
    
    @app.route('/ai_options')
    def ai_options():
        return render_template('ai_options.html')
    
    @app.route('/chat')
    def chat_interface():
        return render_template('chat.html')
    
    @app.route('/ai_assistant')
    def ai_assistant():
        return render_template('ai_assistant.html')
    
    @app.route('/realtime')
    def realtime_demo():
        return render_template('realtime.html')
    
    @app.route('/profile')
    def profile():
        return render_template('profile.html')
    
    @app.route('/logout')
    def logout():
        # This would normally handle logout logic
        return "Logout successful", 200
    
    @app.route('/admin')
    def admin_dashboard():
        return render_template('admin/admin_dashboard.html')
    
    @app.route('/stadium_owner')
    def stadium_owner_dashboard():
        return render_template('stadium_owner_dashboard.html')
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app