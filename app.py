#!/usr/bin/env python3
"""
CricVerse - Modular Application Entry Point
Enhanced stadium management and digital ticketing platform for the Big Bash League (BBL)
"""

import os
import sys
from app import create_app

# Create application using the new modular structure
app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    # Run the application
    app.run(
        host=os.environ.get('HOST', '127.0.0.1'),
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    )