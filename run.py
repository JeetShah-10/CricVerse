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