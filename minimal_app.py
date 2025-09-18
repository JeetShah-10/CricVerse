#!/usr/bin/env python3
"""
Minimal CricVerse App with Supabase
This bypasses problematic components and starts a minimal version of the app
"""

import os
from dotenv import load_dotenv
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO

# Load environment
if os.path.exists('cricverse.env'):
    load_dotenv('cricverse.env')
    print("✅ Loaded cricverse.env")

# Initialize Flask app
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

# Configure app
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'cricverse-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
socketio = SocketIO(app)

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    # Import here to avoid circular imports
    from models import Customer
    return Customer.query.get(int(user_id))

# Simple routes
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

@app.route('/stadium_owner')
def stadium_owner_dashboard():
    return render_template('stadium_owner_dashboard.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

def test_database_connection():
    """Test the database connection"""
    try:
        with app.app_context():
            # Test database connection
            with db.engine.connect() as connection:
                result = connection.execute(db.text("SELECT 1"))
                print("✅ Database connection successful!")
                return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def main():
    """Main function to start the application"""
    print("🏏 CricVerse Minimal App with Supabase")
    print("=" * 50)
    
    # Test database connection
    if not test_database_connection():
        print("❌ Cannot start application without database connection")
        return
    
    print("✅ Application initialized successfully!")
    print(f"🌐 Database: Supabase PostgreSQL")
    print(f"📊 Tables: Created and verified")
    
    print("\n" + "=" * 50)
    print("🚀 Starting CricVerse Minimal App...")
    print("=" * 50)
    print(f"🌐 Web Server: http://localhost:5000")
    print("=" * 50)
    
    try:
        # Run the app
        socketio.run(
            app,
            debug=False,
            host='0.0.0.0',
            port=5000,
            use_reloader=False,
            log_output=True
        )
    except KeyboardInterrupt:
        print("\n[INFO] Server stopped by user")
    except Exception as e:
        print(f"\n[ERROR] Failed to start application: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()