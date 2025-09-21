#!/usr/bin/env python3
"""
CricVerse - Optimized Startup Script
"""

import os
from app import create_app, db

def main():
    """Optimized application startup."""
    # Create Flask application
    app = create_app(os.environ.get('FLASK_ENV', 'development'))
    
    # Create database tables
    with app.app_context():
        db.create_all()
        print("Database initialized successfully")
    
    # Run the application
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"CricVerse running on http://127.0.0.1:{port}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )

if __name__ == '__main__':
    main()
