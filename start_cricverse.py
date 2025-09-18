#!/usr/bin/env python3
"""
CricVerse Application Startup Script
Handles initialization and graceful startup
"""

import os
import sys
import logging
from datetime import datetime, timezone

def setup_logging():
    """Setup application logging"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'logs/cricverse_{datetime.now().strftime("%Y%m%d")}.log'),
            logging.StreamHandler()
        ]
    )

def check_environment():
    """Check environment setup"""
    logger = logging.getLogger(__name__)
    
    if not os.path.exists('.env'):
        logger.error("No .env file found. Please run fix_all_errors.py first.")
        return False
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("Environment variables loaded successfully")
    except ImportError:
        logger.error("python-dotenv not installed. Please install with: pip install python-dotenv")
        return False
    except Exception as e:
        logger.error(f"Failed to load environment: {e}")
        return False
    
    return True

def main():
    """Main startup function"""
    print("Starting CricVerse Stadium System...") 
    print("=" * 50)
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Check environment
    if not check_environment():
        print("Environment check failed")
        sys.exit(1)
    
    # Import and start the application
    try:
        from app import app
        logger.info("Application modules loaded successfully")
        
        print("CricVerse system ready")
        print("Server starting on http://localhost:5000")
        print("Admin panel: http://localhost:5000/admin")
        print("-" * 50)
        
        # Try to import socketio, fallback to regular Flask if not available
        try:
            from app import socketio
            if socketio:
                socketio.run(
                    app,
                    debug=True,
                    host='0.0.0.0',
                    port=5000,
                    use_reloader=False,
                    log_output=True
                )
            else:
                app.run(
                    debug=True,
                    host='0.0.0.0',
                    port=5000,
                )
        except ImportError:
            # Fallback to regular Flask app
            app.run(
                debug=True,
                host='0.0.0.0',
                port=5000,
            )
        
    except ImportError as e:
        logger.error(f"Failed to import application modules: {e}")
        print("Application startup failed - missing dependencies")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        print(f"Startup error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()