#!/usr/bin/env python
"""Entry point for the CricVerse application (enhanced).

Features:
- Loads environment variables from cricverse.env/.env
- Preflight Supabase configuration + connection check (logs-only, non-fatal)
- Starts Flask with SocketIO if available
"""

import os
import logging
from dotenv import load_dotenv

# Load environment early
if os.path.exists('cricverse.env'):
    load_dotenv('cricverse.env')
else:
    load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cricverse.run")

# Preflight Supabase checks (best-effort; app still starts if they fail)
try:
    from supabase_config import SupabaseConfig
    supa = SupabaseConfig()
    if not supa.validate_config():
        logger.warning("Supabase config invalid or incomplete. The app will still start; mock/fallbacks may be used.")
    else:
        if supa.test_connection():
            logger.info("Supabase connection OK.")
        else:
            logger.warning("Supabase connection test failed. The app will still start; features may use fallbacks.")
except Exception as e:
    logger.warning(f"Supabase preflight skipped or failed: {e}")

from app import create_app
try:
    # socketio is set in app.__init__ during create_app
    from app import socketio  # type: ignore
except Exception:
    socketio = None

# Determine the configuration to use
config_name = os.environ.get('FLASK_ENV', 'default')

# Create the application instance
app = create_app(config_name)

if __name__ == '__main__':
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'

    logger.info(f"Starting CricVerse on http://{host}:{port} (debug={debug})")
    # Prefer SocketIO server if available
    if socketio is not None:
        socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)
    else:
        app.run(host=host, port=port, debug=debug)