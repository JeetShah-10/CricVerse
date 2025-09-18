"""
CricVerse app using regular Flask development server (not SocketIO)
This version should work reliably for HTTP requests.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("[DEBUG] Starting CricVerse with Flask server...")

try:
    # Import the main app but not the socketio instance
    from app import app, db, init_db, init_admin
    from models import Customer, Event, Booking, Ticket, Stadium, Team, Seat, Concession, Parking, VerificationSubmission
    
    print("[DEBUG] App imported successfully")
    
    if __name__ == '__main__':
        print("[DEBUG] Starting app initialization...")
        
        with app.app_context():
            print("[DEBUG] Initializing database...")
            # Initialize database with retry logic
            db_success = init_db()
            if not db_success:
                print("[WARN] Database initialization had issues, but continuing...")
            else:
                print("[DEBUG] Database initialized successfully")
        
        # Initialize Flask-Admin
        try:
            print("[DEBUG] Initializing Flask-Admin...")
            admin = init_admin(app, db, Customer, Event, Booking, Ticket, Stadium, Team, Seat, Concession, Parking, VerificationSubmission)
            print("[PASS] Flask-Admin initialized")
        except Exception as e:
            print(f"[WARN] Flask-Admin initialization failed: {e}")
        
        # Start the application with regular Flask development server
        print("[START] Starting CricVerse with Flask development server...")
        print(f"[WEB] Server will be available at: http://localhost:5000")
        print(f"[WEB] Also accessible at: http://127.0.0.1:5000")
        print(f"[NOTE] Using regular Flask server instead of SocketIO for better compatibility")
        
        # Use Flask development server (like our successful test_app_simple.py)
        app.run(
            debug=False,  # Disable debug to match the SocketIO config 
            host='0.0.0.0', 
            port=5000,
            use_reloader=False,  # Disable auto-reloader
            threaded=True  # Enable threading for better performance
        )

except Exception as e:
    print(f"[ERROR] Failed to start app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)