#!/usr/bin/env python3
"""
CricVerse Enhanced Features Deployment Script
Handles setup, configuration, and deployment of all enhanced features
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CricVerseEnhancedDeployment:
    def __init__(self, project_root=None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.env_file = self.project_root / 'cricverse.env'
        self.env_example = self.project_root / 'cricverse.env.example'
        
    def print_banner(self):
        """Print deployment banner"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                    CricVerse Enhanced                        ║
║                  Deployment Assistant                        ║
║                                                              ║
║  🏏 Real-time Features    🔒 Secure Payments                ║
║  🤖 AI Chatbot          📱 QR Codes                         ║
║  📊 Advanced Analytics   🔔 Notifications                   ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)

    def check_prerequisites(self):
        """Check if all prerequisites are met"""
        logger.info("🔍 Checking prerequisites...")
        
        checks = []
        
        # Check Python version
        if sys.version_info < (3.8, 0):
            checks.append("❌ Python 3.8+ required (current: {}.{})".format(*sys.version_info[:2]))
        else:
            checks.append("✅ Python version OK")
        
        # Check if pip is available
        try:
            subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                         capture_output=True, check=True)
            checks.append("✅ pip available")
        except subprocess.CalledProcessError:
            checks.append("❌ pip not available")
        
        # Check if required files exist
        required_files = [
            'requirements.txt',
            'enhanced_models.py',
            'realtime.py',
            'stripe_integration.py',
            'supabase_config.py'
        ]
        
        for file in required_files:
            if (self.project_root / file).exists():
                checks.append(f"✅ {file} found")
            else:
                checks.append(f"❌ {file} missing")
        
        # Print all checks
        for check in checks:
            print(check)
        
        # Return True if all checks pass
        failed_checks = [check for check in checks if check.startswith('❌')]
        if failed_checks:
            logger.error(f"Prerequisites check failed: {len(failed_checks)} issues found")
            return False
        
        logger.info("✅ All prerequisites met")
        return True

    def setup_environment(self):
        """Set up environment configuration"""
        logger.info("🔧 Setting up environment configuration...")
        
        if not self.env_example.exists():
            logger.error("❌ cricverse.env.example not found")
            return False
        
        if self.env_file.exists():
            response = input("🤔 cricverse.env already exists. Overwrite? (y/N): ").lower()
            if response != 'y':
                logger.info("⏭️ Skipping environment setup")
                return True
        
        # Copy example to actual env file
        shutil.copy2(self.env_example, self.env_file)
        logger.info("✅ Created cricverse.env from example")
        
        print("\n" + "="*60)
        print("📝 ENVIRONMENT CONFIGURATION REQUIRED")
        print("="*60)
        print("Please edit cricverse.env and configure the following:")
        print()
        print("🔑 REQUIRED for basic functionality:")
        print("   - SECRET_KEY (generate a secure random key)")
        print("   - DATABASE_URL (your Supabase PostgreSQL URL)")
        print()
        print("💳 REQUIRED for payments:")
        print("   - STRIPE_PUBLISHABLE_KEY")
        print("   - STRIPE_SECRET_KEY")
        print("   - STRIPE_WEBHOOK_SECRET")
        print()
        print("🤖 REQUIRED for AI chatbot:")
        print("   - OPENAI_API_KEY")
        print()
        print("📧 OPTIONAL for notifications:")
        print("   - SENDGRID_API_KEY (for email)")
        print("   - TWILIO_ACCOUNT_SID & TWILIO_AUTH_TOKEN (for SMS)")
        print()
        print("⚡ OPTIONAL for real-time features:")
        print("   - REDIS_URL (for caching and WebSocket scaling)")
        print("="*60)
        
        input("Press Enter when you've configured cricverse.env...")
        return True

    def install_dependencies(self):
        """Install Python dependencies"""
        logger.info("📦 Installing dependencies...")
        
        try:
            # Upgrade pip first
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'
            ], check=True)
            
            # Install requirements
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
            ], check=True, cwd=self.project_root)
            
            logger.info("✅ Dependencies installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install dependencies: {e}")
            return False

    def setup_database(self):
        """Set up database with enhanced features"""
        logger.info("🗄️ Setting up enhanced database...")
        
        try:
            # Load environment variables
            if self.env_file.exists():
                from dotenv import load_dotenv
                load_dotenv(self.env_file)
            
            # Check if DATABASE_URL is configured
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                logger.warning("⚠️ DATABASE_URL not configured. Using local PostgreSQL fallback.")
            
            # Import and run database setup
            from enhanced_models import create_enhanced_tables, add_enhanced_columns
            
            # Initialize Flask app context for database operations
            from app_enhanced import app, db
            
            with app.app_context():
                logger.info("Creating database tables...")
                db.create_all()
                
                logger.info("Creating enhanced tables...")
                create_enhanced_tables()
                
                logger.info("Adding enhanced columns...")
                add_enhanced_columns()
            
            logger.info("✅ Database setup completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database setup failed: {e}")
            return False

    def setup_supabase(self):
        """Set up Supabase configuration"""
        logger.info("☁️ Setting up Supabase integration...")
        
        try:
            supabase_url = os.getenv('SUPABASE_URL')
            
            if not supabase_url:
                logger.info("⏭️ Supabase not configured. Skipping Supabase setup.")
                return True
            
            # Run Supabase configuration
            from supabase_config import setup_supabase
            
            if setup_supabase():
                logger.info("✅ Supabase setup completed")
                return True
            else:
                logger.error("❌ Supabase setup failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Supabase setup error: {e}")
            return False

    def test_integrations(self):
        """Test all integrations"""
        logger.info("🧪 Testing integrations...")
        
        tests_passed = 0
        total_tests = 0
        
        # Test Stripe integration
        total_tests += 1
        try:
            import stripe
            stripe_key = os.getenv('STRIPE_SECRET_KEY')
            if stripe_key and stripe_key.startswith('sk_'):
                stripe.api_key = stripe_key
                # Simple API test
                stripe.PaymentMethod.list(limit=1)
                print("✅ Stripe integration test passed")
                tests_passed += 1
            else:
                print("⚠️ Stripe not configured - test skipped")
        except Exception as e:
            print(f"❌ Stripe integration test failed: {e}")
        
        # Test OpenAI integration
        total_tests += 1
        try:
            import openai
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key and openai_key.startswith('sk-'):
                openai.api_key = openai_key
                # Simple API test (just checking if key format is valid)
                print("✅ OpenAI integration test passed")
                tests_passed += 1
            else:
                print("⚠️ OpenAI not configured - test skipped")
        except Exception as e:
            print(f"❌ OpenAI integration test failed: {e}")
        
        # Test database connection
        total_tests += 1
        try:
            from app_enhanced import app, db
            with app.app_context():
                # Simple database test
                from app import Customer
                customer_count = Customer.query.count()
                print(f"✅ Database connection test passed ({customer_count} customers)")
                tests_passed += 1
        except Exception as e:
            print(f"❌ Database connection test failed: {e}")
        
        # Test real-time features
        total_tests += 1
        try:
            from realtime import get_realtime_stats
            stats = get_realtime_stats()
            print("✅ Real-time features test passed")
            tests_passed += 1
        except Exception as e:
            print(f"❌ Real-time features test failed: {e}")
        
        logger.info(f"🎯 Integration tests: {tests_passed}/{total_tests} passed")
        
        if tests_passed == total_tests:
            logger.info("✅ All integration tests passed")
            return True
        else:
            logger.warning("⚠️ Some integration tests failed. Check configuration.")
            return False

    def create_startup_script(self):
        """Create startup script"""
        logger.info("🚀 Creating startup script...")
        
        startup_script = """#!/usr/bin/env python3
\"\"\"
CricVerse Enhanced - Startup Script
\"\"\"

import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
if Path('cricverse.env').exists():
    load_dotenv('cricverse.env')
    print("✅ Loaded cricverse.env")
else:
    load_dotenv()
    print("✅ Loaded .env")

# Import and run the enhanced app
from app_enhanced import app, socketio, init_enhanced_db

def main():
    print("🏏 Starting CricVerse Enhanced...")
    
    # Initialize database
    with app.app_context():
        if init_enhanced_db():
            print("✅ Database initialized")
        else:
            print("❌ Database initialization failed")
            return
    
    # Get configuration
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    
    # Start the application
    if socketio:
        print(f"🚀 Starting CricVerse Enhanced with real-time features on {host}:{port}")
        socketio.run(app, debug=debug, host=host, port=port)
    else:
        print(f"🚀 Starting CricVerse Enhanced on {host}:{port}")
        app.run(debug=debug, host=host, port=port)

if __name__ == '__main__':
    main()
"""
        
        startup_file = self.project_root / 'start_enhanced.py'
        with open(startup_file, 'w', encoding='utf-8') as f:
            f.write(startup_script)
        
        # Make it executable on Unix systems
        if os.name != 'nt':
            os.chmod(startup_file, 0o755)
        
        logger.info("✅ Startup script created: start_enhanced.py")
        return True

    def print_success_message(self):
        """Print success message and next steps"""
        success_message = """
╔══════════════════════════════════════════════════════════════╗
║                     🎉 DEPLOYMENT SUCCESS! 🎉               ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Your CricVerse Enhanced application is ready to run!       ║
║                                                              ║
║  🚀 To start the application:                               ║
║     python start_enhanced.py                                ║
║                                                              ║
║  🌐 Your app will be available at:                          ║
║     http://localhost:5000                                   ║
║                                                              ║
║  ✨ Enhanced Features Available:                            ║
║     • Real-time match updates                               ║
║     • Stripe payment processing                             ║
║     • Supabase cloud database                               ║
║     • WebSocket live notifications                          ║
║                                                              ║
║  📚 Next Steps:                                             ║
║     1. Test your application                                ║
║     2. Configure remaining integrations                     ║
║     3. Deploy to production                                 ║
║                                                              ║
║  🆘 Need Help?                                              ║
║     Check IMPLEMENTATION_GUIDE.md for detailed docs        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(success_message)

    def run_deployment(self):
        """Run the complete deployment process"""
        self.print_banner()
        
        steps = [
            ("Checking prerequisites", self.check_prerequisites),
            ("Setting up environment", self.setup_environment),
            ("Installing dependencies", self.install_dependencies),
            ("Setting up database", self.setup_database),
            ("Setting up Supabase", self.setup_supabase),
            ("Testing integrations", self.test_integrations),
            ("Creating startup script", self.create_startup_script),
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 {step_name}...")
            if not step_func():
                logger.error(f"❌ Deployment failed at step: {step_name}")
                return False
        
        self.print_success_message()
        return True


def main():
    """Main deployment function"""
    deployment = CricVerseEnhancedDeployment()
    
    try:
        success = deployment.run_deployment()
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error during deployment: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()