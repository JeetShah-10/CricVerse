#!/usr/bin/env python3
"""
CricVerse - Modular Application Entry Point
Enhanced stadium management and digital ticketing platform for the Big Bash League (BBL)
"""

import os
from app import create_app

# Create application using the new modular structure
app = create_app(os.environ.get('FLASK_ENV', 'development'))

# This block is typically for development server only. For WSGI servers like Waitress or Gunicorn,
# they will import the 'app' object directly. We remove the if __name__ == '__main__': block
# to ensure 'app' is always available when imported.
# If you need to run a development server, you can use 'flask run' or a separate script.
