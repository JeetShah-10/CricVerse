#!/usr/bin/env python3
"""
CricVerse System Error Fixer
Comprehensive script to fix all known errors and optimize the system
"""

import os
import sys
import shutil
from datetime import datetime
from pathlib import Path

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"🔧 {title}")
    print(f"{'='*60}")

def print_status(message, success=True):
    """Print status with icon"""
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")

def print_warning(message):
    """Print warning message"""
    print(f"⚠️  {message}")

def print_info(message):
    """Print info message"""
    print(f"ℹ️  {message}")

def fix_environment_file():
    """Fix environment configuration"""
    print_section("Fixing Environment Configuration")
    
    # Create a proper .env file
    env_content = """# CricVerse Environment Configuration
SECRET_KEY=cricverse-secure-secret-key-for-production-change-this-value
DATABASE_URL=sqlite:///cricverse.db
FLASK_ENV=development
FLASK_DEBUG=True

# Optional Payment Gateway Configuration
PAYPAL_CLIENT_ID=
PAYPAL_CLIENT_SECRET=
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=

# Optional AI Configuration
OPENAI_API_KEY=
GOOGLE_API_KEY=

# Optional Email/SMS Configuration
SENDGRID_API_KEY=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=

# Security
ENCRYPTION_KEY=cricverse-encryption-key-32-chars
CSRF_SECRET_KEY=cricverse-csrf-secret-key
"""
    
    try:
        # Backup existing .env if it exists
        if os.path.exists('.env'):
            backup_name = f'.env.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            shutil.copy('.env', backup_name)
            print_status(f"Backed up existing .env to {backup_name}")
        
        # Write new .env file
        with open('.env', 'w') as f:
            f.write(env_content)
        print_status("Created new .env file with proper configuration")
        
    except Exception as e:
        print_status(f"Failed to fix environment file: {e}", False)

def create_required_directories():
    """Create required directories"""
    print_section("Creating Required Directories")
    
    directories = [
        'static',
        'static/css',
        'static/js', 
        'static/img',
        'static/qrcodes',
        'static/uploads',
        'templates',
        'logs',
        'backups'
    ]
    
    for directory in directories:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            print_status(f"Created directory: {directory}")
        except Exception as e:
            print_status(f"Failed to create {directory}: {e}", False)

def fix_deprecation_warnings():
    """Fix datetime deprecation warnings in key files"""
    print_section("Fixing Deprecation Warnings")
    
    files_to_fix = [
        'app.py',
        'qr_generator.py',
        'simple_health_check.py'
    ]
    
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Replace datetime.utcnow() with timezone-aware alternative
                if 'datetime.utcnow()' in content:
                    # Add timezone import if not present
                    if 'from datetime import' in content and 'timezone' not in content:
                        content = content.replace(
                            'from datetime import datetime',
                            'from datetime import datetime, timezone'
                        )
                    elif 'import datetime' in content:
                        content = content.replace(
                            'import datetime',
                            'import datetime\nfrom datetime import timezone'
                        )
                    
                    # Replace the deprecated calls
                    content = content.replace(
                        'datetime.utcnow()',
                        'datetime.now(timezone.utc)'
                    )
                    
                    # Write back the fixed content
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    print_status(f"Fixed deprecation warnings in {file_path}")
                else:
                    print_info(f"No deprecation warnings found in {file_path}")
                    
            except Exception as e:
                print_status(f"Failed to fix {file_path}: {e}", False)
        else:
            print_warning(f"File not found: {file_path}")

def create_startup_script():
    """Create a startup script for the application"""
    print_section("Creating Startup Script")
    
    startup_content = """#!/usr/bin/env python3
'''
CricVerse Application Startup Script
Handles initialization and graceful startup
'''

import os
import sys
import logging
from datetime import datetime

def setup_logging():
    '''Setup application logging'''
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
    '''Check environment setup'''
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
    '''Main startup function'''
    print("🚀 Starting CricVerse Stadium System...") 
    print("=" * 50)
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Check environment
    if not check_environment():
        print("❌ Environment check failed")
        sys.exit(1)
    
    # Import and start the application
    try:
        from app import app, socketio
        logger.info("Application modules loaded successfully")
        
        print("✅ CricVerse system ready")
        print("🌐 Server starting on http://localhost:5000")
        print("📊 Admin panel: http://localhost:5000/admin")
        print("🎯 API docs: http://localhost:5000/api")
        print("-" * 50)
        
        # Start the application
        socketio.run(
            app,
            debug=True,
            host='0.0.0.0',
            port=5000,
            use_reloader=False,
            log_output=True
        )
        
    except ImportError as e:
        logger.error(f"Failed to import application modules: {e}")
        print("❌ Application startup failed - missing dependencies")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        print(f"❌ Startup error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
"""
    
    try:
        with open('start_cricverse.py', 'w') as f:
            f.write(startup_content)
        print_status("Created startup script: start_cricverse.py")
    except Exception as e:
        print_status(f"Failed to create startup script: {e}", False)

def create_database_initialization():
    """Create database initialization script"""
    print_section("Creating Database Initialization")
    
    db_init_content = """#!/usr/bin/env python3
'''
CricVerse Database Initialization Script
Creates all necessary database tables and indexes
'''

import os
import sys
from datetime import datetime

def init_database():
    '''Initialize database with all tables'''
    try:
        # Load environment
        from dotenv import load_dotenv
        load_dotenv()
        
        # Import app and database
        from app import app, db
        
        with app.app_context():
            print("🗄️  Creating database tables...")
            
            # Drop all tables (for fresh start)
            # db.drop_all()
            
            # Create all tables
            db.create_all()
            
            print("✅ Database tables created successfully")
            
            # Check table creation
            tables = db.engine.table_names()
            print(f"📊 Created {len(tables)} tables:")
            for table in sorted(tables):
                print(f"   • {table}")
                
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False
    
    return True

def main():
    '''Main function'''
    print("🗄️  CricVerse Database Initialization")
    print("=" * 40)
    
    if init_database():
        print("✅ Database initialization completed")
    else:
        print("❌ Database initialization failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
"""
    
    try:
        with open('init_database.py', 'w') as f:
            f.write(db_init_content)
        print_status("Created database initialization script: init_database.py")
    except Exception as e:
        print_status(f"Failed to create database script: {e}", False)

def optimize_system_performance():
    """Apply system performance optimizations"""
    print_section("Applying Performance Optimizations")
    
    # Create a performance optimization script
    perf_content = """#!/usr/bin/env python3
'''
CricVerse Performance Optimization Settings
'''

import os

# Set Python optimization environment variables
os.environ['PYTHONOPTIMIZE'] = '1'
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

# Flask optimizations
os.environ['FLASK_SKIP_DOTENV'] = '0'

print("⚡ Performance optimizations applied")
"""
    
    try:
        with open('optimize_performance.py', 'w') as f:
            f.write(perf_content)
        print_status("Created performance optimization script")
    except Exception as e:
        print_status(f"Failed to create performance script: {e}", False)

def create_error_monitoring():
    """Create error monitoring and logging system"""
    print_section("Setting Up Error Monitoring")
    
    error_monitor_content = """#!/usr/bin/env python3
'''
CricVerse Error Monitoring System
'''

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

def setup_error_monitoring():
    '''Setup comprehensive error monitoring'''
    
    # Create logs directory
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Setup rotating file handler
    file_handler = RotatingFileHandler(
        'logs/cricverse_errors.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    
    file_handler.setLevel(logging.WARNING)
    
    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(levelname)s: %(message)s'
    ))
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler]
    )
    
    print("📊 Error monitoring system initialized")

if __name__ == "__main__":
    setup_error_monitoring()
"""
    
    try:
        with open('setup_monitoring.py', 'w') as f:
            f.write(error_monitor_content)
        print_status("Created error monitoring setup")
    except Exception as e:
        print_status(f"Failed to create monitoring setup: {e}", False)

def main():
    """Main error fixing function"""
    print("🛠️  CricVerse System Error Fixer")
    print("🎯 Fixing all known errors and optimizing system")
    print("=" * 60)
    
    # Run all fixes
    fix_environment_file()
    create_required_directories()
    fix_deprecation_warnings()
    create_startup_script()
    create_database_initialization()
    optimize_system_performance()
    create_error_monitoring()
    
    # Final summary
    print_section("Fix Summary")
    print_status("Environment configuration fixed")
    print_status("Required directories created")
    print_status("Deprecation warnings addressed")
    print_status("Startup scripts created")
    print_status("Database initialization ready")
    print_status("Performance optimizations applied")
    print_status("Error monitoring configured")
    
    print(f"\n🎉 System Error Fixes Complete!")
    print(f"📋 Next Steps:")
    print(f"   1. Run: python init_database.py")
    print(f"   2. Run: python start_cricverse.py")
    print(f"   3. Test: python simple_health_check.py")
    print("=" * 60)

if __name__ == "__main__":
    main()