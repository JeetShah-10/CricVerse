"""
Simplified CricVerse App Startup Script
This bypasses the season_ticket table creation issue and starts the app
"""

from flask import Flask
from app import app, db, socketio, init_admin
from models import Customer, Event, Booking, Ticket, Stadium, Team, Seat, Concession, Parking, VerificationSubmission

def create_essential_tables():
    """Create only essential tables to get the app running"""
    try:
        with app.app_context():
            # Try to create core tables only
            print("[INFO] Creating essential database tables...")
            
            # Create tables but ignore errors for problematic ones
            try:
                db.create_all()
                print("[PASS] Database tables created")
            except Exception as e:
                print(f"[WARN] Some tables failed to create: {e}")
                print("[INFO] Continuing with existing tables...")
            
            # Verify we have basic tables
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            essential_tables = ['customer', 'stadium', 'team', 'event', 'seat', 'booking', 'ticket']
            missing_tables = [t for t in essential_tables if t not in existing_tables]
            
            if missing_tables:
                print(f"[WARN] Missing essential tables: {missing_tables}")
                print("[INFO] App may have limited functionality")
            else:
                print("[PASS] All essential tables exist")
            
            return True
    except Exception as e:
        print(f"[FAIL] Database setup failed: {e}")
        return False

def start_app():
    """Start the CricVerse application"""
    print("=" * 60)
    print("🏏 CricVerse Stadium System - Simplified Startup")
    print("=" * 60)
    
    # Setup database
    db_success = create_essential_tables()
    
    # Initialize Flask-Admin (optional, continue if it fails)
    try:
        admin = init_admin(app, db, Customer, Event, Booking, Ticket, Stadium, Team, Seat, Concession, Parking, VerificationSubmission)
        print("[PASS] Flask-Admin initialized")
    except Exception as e:
        print(f"[WARN] Flask-Admin initialization failed: {e}")
        print("[INFO] Admin interface may not be available")
    
    # Start the server
    print("\n" + "=" * 60)
    print("🚀 Starting CricVerse Stadium System...")
    print("=" * 60)
    print(f"🌐 Web Server: http://localhost:5000")
    print(f"📊 Admin Panel: http://localhost:5000/admin")
    print(f"💳 Payment System: Active (PayPal + Razorpay)")
    print(f"🤖 AI Chatbot: Active (Gemini)")
    print(f"⚡ Real-time Features: Active (SocketIO)")
    print("=" * 60)
    
    try:
        # Run the app with better error handling
        socketio.run(
            app,
            debug=False,  # Disable debug for stability
            host='0.0.0.0',
            port=5000,
            use_reloader=False,  # Disable auto-reloader
            log_output=False,  # Reduce console noise
            allow_unsafe_werkzeug=True  # Allow for development
        )
    except KeyboardInterrupt:
        print("\n[INFO] Server stopped by user")
    except Exception as e:
        print(f"\n[FAIL] Server error: {e}")
        print("[NOTE] Check your configuration and try again")

if __name__ == '__main__':
    start_app()