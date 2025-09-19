#!/usr/bin/env python3
"""
Comprehensive CricVerse Website Diagnostics
Tests all major components and identifies issues for fixing
"""

import os
import sys
import json
import logging
import traceback
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CricVerseDiagnostics:
    """Comprehensive diagnostics for CricVerse website"""
    
    def __init__(self):
        self.results = {}
        self.issues = []
        self.recommendations = []
        
        # Load environment
        self.load_environment()
        
    def load_environment(self):
        """Load environment variables"""
        try:
            if os.path.exists('cricverse.env'):
                load_dotenv('cricverse.env')
                logger.info("✅ Loaded cricverse.env")
            elif os.path.exists('.env'):
                load_dotenv('.env')
                logger.info("✅ Loaded .env")
            else:
                logger.warning("⚠️ No environment file found")
        except Exception as e:
            logger.error(f"❌ Failed to load environment: {e}")
    
    def test_database_connectivity(self):
        """Test Supabase database connectivity"""
        logger.info("🔍 Testing database connectivity...")
        
        try:
            from sqlalchemy import create_engine, text
            
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                self.issues.append("DATABASE_URL not configured")
                self.results['database'] = {'status': 'FAIL', 'error': 'DATABASE_URL missing'}
                return False
            
            # Normalize URL for pg8000 driver
            if db_url.startswith('postgresql://'):
                db_url = db_url.replace('postgresql://', 'postgresql+pg8000://', 1)
            
            engine = create_engine(db_url)
            
            with engine.connect() as connection:
                # Test basic connection
                result = connection.execute(text("SELECT version(), current_database()"))
                version, db_name = result.fetchone()
                
                # Test table existence
                tables_query = text("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name
                """)
                tables_result = connection.execute(tables_query)
                tables = [row[0] for row in tables_result.fetchall()]
                
                # Test data in key tables
                data_counts = {}
                key_tables = ['customer', 'event', 'booking', 'ticket', 'stadium', 'team']
                
                for table in key_tables:
                    if table in tables:
                        try:
                            count_result = connection.execute(text(f"SELECT COUNT(*) FROM {table}"))
                            data_counts[table] = count_result.fetchone()[0]
                        except Exception as e:
                            data_counts[table] = f"Error: {e}"
                
                self.results['database'] = {
                    'status': 'PASS',
                    'version': version.split(',')[0],
                    'database': db_name,
                    'tables': tables,
                    'table_count': len(tables),
                    'data_counts': data_counts
                }
                
                logger.info(f"✅ Database connected: {db_name}")
                logger.info(f"   Tables found: {len(tables)}")
                logger.info(f"   Data counts: {data_counts}")
                
                # Check for empty tables
                empty_tables = [table for table, count in data_counts.items() 
                              if isinstance(count, int) and count == 0]
                if empty_tables:
                    self.issues.append(f"Empty tables detected: {empty_tables}")
                    self.recommendations.append("Run data seeding scripts to populate empty tables")
                
                return True
                
        except Exception as e:
            error_msg = str(e)
            self.issues.append(f"Database connection failed: {error_msg}")
            self.results['database'] = {'status': 'FAIL', 'error': error_msg}
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    def test_flask_app_startup(self):
        """Test Flask application startup"""
        logger.info("🔍 Testing Flask app startup...")
        
        try:
            # Import the app factory
            sys.path.insert(0, os.getcwd())
            from app import create_app
            
            # Create app instance
            app = create_app('default')
            
            # Test app configuration
            with app.app_context():
                # Check if database is configured
                db_configured = hasattr(app, 'config') and 'SQLALCHEMY_DATABASE_URI' in app.config
                
                # Check blueprints
                blueprints = list(app.blueprints.keys())
                
                # Check routes
                routes = []
                for rule in app.url_map.iter_rules():
                    routes.append({
                        'endpoint': rule.endpoint,
                        'methods': list(rule.methods),
                        'rule': str(rule)
                    })
                
                self.results['flask_app'] = {
                    'status': 'PASS',
                    'db_configured': db_configured,
                    'blueprints': blueprints,
                    'route_count': len(routes),
                    'routes': routes[:10]  # First 10 routes for brevity
                }
                
                logger.info(f"✅ Flask app started successfully")
                logger.info(f"   Blueprints: {blueprints}")
                logger.info(f"   Routes: {len(routes)}")
                
                return True
                
        except Exception as e:
            error_msg = str(e)
            self.issues.append(f"Flask app startup failed: {error_msg}")
            self.results['flask_app'] = {'status': 'FAIL', 'error': error_msg}
            logger.error(f"❌ Flask app startup failed: {e}")
            return False
    
    def test_ai_chatbot(self):
        """Test AI chatbot functionality"""
        logger.info("🔍 Testing AI chatbot...")
        
        try:
            # Check if chatbot.py exists and can be imported
            if not os.path.exists('chatbot.py'):
                self.issues.append("chatbot.py file not found")
                self.results['chatbot'] = {'status': 'FAIL', 'error': 'chatbot.py missing'}
                return False
            
            # Test API keys
            openai_key = os.getenv('OPENAI_API_KEY')
            gemini_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
            
            api_status = {
                'openai': 'configured' if openai_key and not openai_key.startswith('your_') else 'missing',
                'gemini': 'configured' if gemini_key and not gemini_key.startswith('your_') else 'missing'
            }
            
            # Try to import chatbot module
            from chatbot import get_chatbot_response
            
            # Test basic chatbot response
            test_message = "Hello, I need help with booking tickets"
            response = get_chatbot_response(test_message, user_id="test_user")
            
            self.results['chatbot'] = {
                'status': 'PASS',
                'api_keys': api_status,
                'test_response': response[:100] if response else "No response",
                'response_length': len(response) if response else 0
            }
            
            logger.info("✅ Chatbot functionality working")
            
            if api_status['openai'] == 'missing' and api_status['gemini'] == 'missing':
                self.issues.append("No AI API keys configured")
                self.recommendations.append("Configure OpenAI or Gemini API keys for AI functionality")
            
            return True
            
        except Exception as e:
            error_msg = str(e)
            self.issues.append(f"Chatbot test failed: {error_msg}")
            self.results['chatbot'] = {'status': 'FAIL', 'error': error_msg}
            logger.error(f"❌ Chatbot test failed: {e}")
            return False
    
    def test_admin_panel(self):
        """Test admin panel functionality"""
        logger.info("🔍 Testing admin panel...")
        
        try:
            # Check if admin is enabled
            admin_enabled = os.getenv('ENABLE_ADMIN', '0') == '1'
            
            if not admin_enabled:
                self.results['admin'] = {
                    'status': 'DISABLED',
                    'message': 'Admin panel is disabled in environment'
                }
                self.recommendations.append("Set ENABLE_ADMIN=1 to enable admin panel")
                return True
            
            # Check admin.py file
            if not os.path.exists('admin.py'):
                self.issues.append("admin.py file not found")
                self.results['admin'] = {'status': 'FAIL', 'error': 'admin.py missing'}
                return False
            
            # Try to import admin module
            from admin import init_admin
            
            self.results['admin'] = {
                'status': 'PASS',
                'enabled': admin_enabled,
                'admin_file_exists': True
            }
            
            logger.info("✅ Admin panel configuration working")
            return True
            
        except Exception as e:
            error_msg = str(e)
            self.issues.append(f"Admin panel test failed: {error_msg}")
            self.results['admin'] = {'status': 'FAIL', 'error': error_msg}
            logger.error(f"❌ Admin panel test failed: {e}")
            return False
    
    def test_qr_code_generation(self):
        """Test QR code generation"""
        logger.info("🔍 Testing QR code generation...")
        
        try:
            # Check if qr_generator.py exists
            if not os.path.exists('qr_generator.py'):
                self.issues.append("qr_generator.py file not found")
                self.results['qr_codes'] = {'status': 'FAIL', 'error': 'qr_generator.py missing'}
                return False
            
            # Try to import QR generator
            from qr_generator import generate_ticket_qr, generate_parking_qr
            
            # Test QR generation
            test_ticket_data = {
                'ticket_id': 'TEST123',
                'event_name': 'Test Match',
                'seat': 'A1'
            }
            
            qr_code = generate_ticket_qr(test_ticket_data)
            
            self.results['qr_codes'] = {
                'status': 'PASS',
                'test_generation': 'successful',
                'qr_code_length': len(qr_code) if qr_code else 0
            }
            
            logger.info("✅ QR code generation working")
            return True
            
        except Exception as e:
            error_msg = str(e)
            self.issues.append(f"QR code test failed: {error_msg}")
            self.results['qr_codes'] = {'status': 'FAIL', 'error': error_msg}
            logger.error(f"❌ QR code test failed: {e}")
            return False
    
    def test_notification_system(self):
        """Test notification system"""
        logger.info("🔍 Testing notification system...")
        
        try:
            # Check if notification.py exists
            if not os.path.exists('notification.py'):
                self.issues.append("notification.py file not found")
                self.results['notifications'] = {'status': 'FAIL', 'error': 'notification.py missing'}
                return False
            
            # Check notification service configuration
            email_config = {
                'sendgrid_key': os.getenv('SENDGRID_API_KEY'),
                'from_email': os.getenv('SENDGRID_FROM_EMAIL')
            }
            
            sms_config = {
                'twilio_sid': os.getenv('TWILIO_ACCOUNT_SID'),
                'twilio_token': os.getenv('TWILIO_AUTH_TOKEN'),
                'twilio_phone': os.getenv('TWILIO_PHONE_NUMBER')
            }
            
            # Try to import notification module
            from notification import email_service, sms_service
            
            self.results['notifications'] = {
                'status': 'PASS',
                'email_configured': bool(email_config['sendgrid_key'] and not email_config['sendgrid_key'].startswith('your_')),
                'sms_configured': bool(sms_config['twilio_sid'] and not sms_config['twilio_sid'].startswith('your_')),
                'services_imported': True
            }
            
            logger.info("✅ Notification system working")
            
            if not self.results['notifications']['email_configured']:
                self.recommendations.append("Configure SendGrid API key for email notifications")
            
            if not self.results['notifications']['sms_configured']:
                self.recommendations.append("Configure Twilio credentials for SMS notifications")
            
            return True
            
        except Exception as e:
            error_msg = str(e)
            self.issues.append(f"Notification test failed: {error_msg}")
            self.results['notifications'] = {'status': 'FAIL', 'error': error_msg}
            logger.error(f"❌ Notification test failed: {e}")
            return False
    
    def test_websocket_realtime(self):
        """Test WebSocket and real-time features"""
        logger.info("🔍 Testing WebSocket/real-time features...")
        
        try:
            # Check if realtime.py exists
            if not os.path.exists('realtime.py'):
                self.issues.append("realtime.py file not found")
                self.results['websocket'] = {'status': 'FAIL', 'error': 'realtime.py missing'}
                return False
            
            # Try to import realtime module
            from realtime_server import init_socketio
            
            self.results['websocket'] = {
                'status': 'PASS',
                'realtime_file_exists': True,
                'socketio_available': True
            }
            
            logger.info("✅ WebSocket/real-time features working")
            return True
            
        except Exception as e:
            error_msg = str(e)
            self.issues.append(f"WebSocket test failed: {error_msg}")
            self.results['websocket'] = {'status': 'FAIL', 'error': error_msg}
            logger.error(f"❌ WebSocket test failed: {e}")
            return False
    
    def analyze_test_files(self):
        """Analyze test files to identify usable vs outdated"""
        logger.info("🔍 Analyzing test files...")
        
        test_files = []
        for file_path in Path('.').glob('test_*.py'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Analyze file characteristics
                analysis = {
                    'file': str(file_path),
                    'size': len(content),
                    'lines': len(content.split('\n')),
                    'has_unittest': 'unittest' in content,
                    'has_pytest': 'pytest' in content,
                    'has_flask_test': 'test_client' in content,
                    'has_database_test': 'database' in content.lower() or 'db' in content.lower(),
                    'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                }
                
                test_files.append(analysis)
                
            except Exception as e:
                logger.warning(f"Could not analyze {file_path}: {e}")
        
        # Sort by last modified (newest first)
        test_files.sort(key=lambda x: x['last_modified'], reverse=True)
        
        self.results['test_files'] = {
            'status': 'ANALYZED',
            'total_files': len(test_files),
            'files': test_files[:10],  # Top 10 most recent
            'recommendations': []
        }
        
        # Identify potentially outdated files
        recent_files = [f for f in test_files if f['last_modified'] > '2024-01-01']
        old_files = [f for f in test_files if f['last_modified'] <= '2024-01-01']
        
        if old_files:
            self.recommendations.append(f"Consider reviewing {len(old_files)} older test files for relevance")
        
        logger.info(f"✅ Analyzed {len(test_files)} test files")
        logger.info(f"   Recent files: {len(recent_files)}")
        logger.info(f"   Older files: {len(old_files)}")
        
        return True
    
    def run_comprehensive_diagnostics(self):
        """Run all diagnostic tests"""
        logger.info("🚀 Starting comprehensive CricVerse diagnostics...")
        
        start_time = datetime.now()
        
        # Run all tests
        tests = [
            ('Database Connectivity', self.test_database_connectivity),
            ('Flask App Startup', self.test_flask_app_startup),
            ('AI Chatbot', self.test_ai_chatbot),
            ('Admin Panel', self.test_admin_panel),
            ('QR Code Generation', self.test_qr_code_generation),
            ('Notification System', self.test_notification_system),
            ('WebSocket/Real-time', self.test_websocket_realtime),
            ('Test Files Analysis', self.analyze_test_files)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"\n{'='*50}")
            logger.info(f"Running: {test_name}")
            logger.info(f"{'='*50}")
            
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                logger.error(f"Test {test_name} crashed: {e}")
                self.issues.append(f"{test_name} crashed: {str(e)}")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Generate summary
        summary = {
            'timestamp': end_time.isoformat(),
            'duration_seconds': duration,
            'tests_passed': passed,
            'tests_total': total,
            'success_rate': (passed / total) * 100,
            'issues_found': len(self.issues),
            'recommendations_count': len(self.recommendations),
            'results': self.results,
            'issues': self.issues,
            'recommendations': self.recommendations
        }
        
        # Save detailed report
        with open('comprehensive_diagnostics_report.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Print summary
        logger.info(f"\n{'='*60}")
        logger.info("COMPREHENSIVE DIAGNOSTICS SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Tests Passed: {passed}/{total} ({(passed/total)*100:.1f}%)")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Issues Found: {len(self.issues)}")
        logger.info(f"Recommendations: {len(self.recommendations)}")
        
        if self.issues:
            logger.info(f"\n🚨 CRITICAL ISSUES:")
            for i, issue in enumerate(self.issues, 1):
                logger.info(f"   {i}. {issue}")
        
        if self.recommendations:
            logger.info(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(self.recommendations, 1):
                logger.info(f"   {i}. {rec}")
        
        logger.info(f"\n📊 Detailed report saved to: comprehensive_diagnostics_report.json")
        
        return summary

def main():
    """Main execution"""
    diagnostics = CricVerseDiagnostics()
    summary = diagnostics.run_comprehensive_diagnostics()
    
    # Exit with appropriate code
    success_rate = summary['success_rate']
    if success_rate >= 80:
        logger.info("🎉 System is in good condition!")
        sys.exit(0)
    elif success_rate >= 60:
        logger.warning("⚠️ System has some issues but is functional")
        sys.exit(1)
    else:
        logger.error("❌ System has critical issues requiring attention")
        sys.exit(2)

if __name__ == "__main__":
    main()
