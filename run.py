#!/usr/bin/env python
"""Entry point for the CricVerse application."""

import os
from app import create_app

# Determine the configuration to use
config_name = os.environ.get('FLASK_ENV', 'default')

# Create the application instance
app = create_app(config_name)

if __name__ == '__main__':
    # Run the application
    app.run(
        host=os.environ.get('HOST', '127.0.0.1'),
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    )