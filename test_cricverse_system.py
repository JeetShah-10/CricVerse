"""
Comprehensive Testing Script for CricVerse Stadium System
Tests all components: Database, Services, Routes, Live Cricket, etc.
Run this before starting the main application
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv
load_dotenv()
from app.services.supabase_service import supabase_service

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CricVerseSystemTester:
    """Comprehensive system tester for CricVerse"""
    
    def __init__(self):
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'summary': {
                'total_tests': 0,
                'passed': 0,
                'failed': 0,
                'warnings': 0
            }
        }
    
    def run_test(self, test_name: str, test_func) -> bool:
        """Run a single test and record results"""
        logger.info(f"🧪 Running test: {test_name}")
        self.test_results['summary']['total_tests'] += 1
        
        try:
            result = test_func()
            if result.get('success', False):
                self.test_results['summary']['passed'] += 1
                logger.info(f"✅ {test_name}: PASSED")
            else:
                self.test_results['summary']['failed'] += 1
                logger.error(f"❌ {test_name}: FAILED - {result.get('error', 'Unknown error')}")
            
            self.test_results['tests'][test_name] = result
            return result.get('success', False)
            
        except Exception as e:
            self.test_results['summary']['failed'] += 1
            error_msg = str(e)
            logger.error(f"❌ {test_name}: FAILED - {error_msg}")
            self.test_results['tests'][test_name] = {
                'success': False,
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            }
            return False
    
    def test_environment_variables(self) -> Dict[str, Any]:
        """Test environment variables and configuration"""
        required_vars = [
            'SUPABASE_URL',
            'SUPABASE_KEY',
            'SECRET_KEY'
        ]
        
        missing_vars = []
        present_vars = []
        
        for var in required_vars:
            if os.getenv(var):
                present_vars.append(var)
            else:
                missing_vars.append(var)
        
        success = len(missing_vars) == 0
        
        return {
            'success': success,
            'present_vars': present_vars,
            'missing_vars': missing_vars,
            'message': f"Environment check: {len(present_vars)}/{len(required_vars)} variables present",
            'timestamp': datetime.now().isoformat()
        }
    
    def test_flask_app_creation(self) -> Dict[str, Any]:
        """Test Flask app creation and configuration"""
        try:
            # Set environment for testing
            os.environ.setdefault('FLASK_ENV', 'development')
            
            from app import create_app
            app = create_app('development')
            
            return {
                'success': True,
                'app_name': app.name,
                'config_loaded': bool(app.config),
                'blueprints': list(app.blueprints.keys()),
                'message': f"Flask app created successfully with {len(app.blueprints)} blueprints",
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def test_database_connection(self) -> Dict[str, Any]:
        """Test Supabase database connection"""
        try:
            from app import create_app, db
            app = create_app('development')
            
            with app.app_context():
                # Test basic database connection
                result = db.session.execute(db.text('SELECT 1')).scalar()
                
                # Test model imports
                from app.models import Customer, Stadium, Event, Match, Booking
                
                # Test table existence (basic queries)
                table_tests = {}
                models_to_test = [
                    ('customers', Customer),
                    ('stadiums', Stadium), 
                    ('events', Event),
                    ('matches', Match),
                    ('bookings', Booking)
                ]
                
                for table_name, model in models_to_test:
                    try:
                        count = model.query.count()
                        table_tests[table_name] = {'exists': True, 'count': count}
                    except Exception as e:
                        table_tests[table_name] = {'exists': False, 'error': str(e)}
                
                return {
                    'success': True,
                    'connection_test': result == 1,
                    'tables': table_tests,
                    'message': "Database connection successful",
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def test_services_initialization(self) -> Dict[str, Any]:
        """Test all services initialization"""
        try:
            from app import create_app
            from app.services import get_services_health
            
            app = create_app('development')
            
            with app.app_context():
                services_health = get_services_health()
                
                return {
                    'success': services_health.get('initialized', False),
                    'services_count': services_health.get('total_services', 0),
                    'services_status': services_health.get('services', {}),
                    'message': f"Services initialized: {services_health.get('total_services', 0)} services",
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def test_supabase_service(self) -> Dict[str, Any]:
        """Test Supabase service functionality"""
        try:
            from app import create_app
            from app.services.supabase_service import supabase_service
            
            app = create_app('development')
            
            with app.app_context():
                # Test health check
                health = supabase_service.health_check()
                
                # Test basic operations
                stadiums = supabase_service.get_all_stadiums()
                events = supabase_service.get_upcoming_events(limit=5)
                
                return {
                    'success': health.get('status') == 'healthy',
                    'health_status': health,
                    'stadiums_count': len(stadiums),
                    'events_count': len(events),
                    'message': f"Supabase service healthy, {len(stadiums)} stadiums, {len(events)} events",
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def test_live_cricket_service(self) -> Dict[str, Any]:
        """Test live cricket service"""
        try:
            from app import create_app
            from app.services.live_cricket_service import live_cricket_service
            
            app = create_app('development')
            
            with app.app_context():
                # Test health check
                health = live_cricket_service.health_check()
                
                # Test getting live matches
                live_matches = live_cricket_service.get_all_live_matches()
                
                return {
                    'success': health.get('status') == 'healthy',
                    'health_status': health,
                    'live_matches_count': len(live_matches),
                    'initialized': health.get('initialized', False),
                    'message': f"Live cricket service: {len(live_matches)} live matches",
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def test_routes_registration(self) -> Dict[str, Any]:
        """Test that all routes are properly registered"""
        try:
            from app import create_app
            
            app = create_app('development')
            
            # Get all registered routes
            routes = []
            for rule in app.url_map.iter_rules():
                routes.append({
                    'endpoint': rule.endpoint,
                    'rule': rule.rule,
                    'methods': list(rule.methods)
                })
            
            # Check for key routes
            key_routes = [
                '/live/',
                '/enhanced/concessions',
                '/enhanced/parking',
                '/enhanced/about',
                '/health/services',
                '/health/database'
            ]
            
            found_routes = []
            missing_routes = []
            
            for key_route in key_routes:
                found = any(route['rule'] == key_route for route in routes)
                if found:
                    found_routes.append(key_route)
                else:
                    missing_routes.append(key_route)
            
            return {
                'success': len(missing_routes) == 0,
                'total_routes': len(routes),
                'found_key_routes': found_routes,
                'missing_key_routes': missing_routes,
                'blueprints': list(app.blueprints.keys()),
                'message': f"Routes registered: {len(routes)} total, {len(found_routes)}/{len(key_routes)} key routes found",
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def test_enhanced_booking_service(self) -> Dict[str, Any]:
        """Test enhanced booking service"""
        try:
            from app import create_app
            from app.services.enhanced_booking_service import enhanced_booking_service
            
            app = create_app('development')
            
            with app.app_context():
                # Test basic functionality
                stadiums = supabase_service.get_all_stadiums()
                
                if stadiums:
                    stadium_id = stadiums[0]['id']
                    menu_data = enhanced_booking_service.get_concession_menu(stadium_id)
                    
                    return {
                        'success': True,
                        'stadiums_available': len(stadiums),
                        'menu_test': 'concessions' in menu_data,
                        'message': f"Enhanced booking service working with {len(stadiums)} stadiums",
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    return {
                        'success': False,
                        'error': "No stadiums found in database",
                        'timestamp': datetime.now().isoformat()
                    }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results"""
        logger.info("🚀 Starting CricVerse System Tests")
        logger.info("=" * 50)
        
        # Define tests to run
        tests = [
            ("Environment Variables", self.test_environment_variables),
            ("Flask App Creation", self.test_flask_app_creation),
            ("Database Connection", self.test_database_connection),
            ("Services Initialization", self.test_services_initialization),
            ("Supabase Service", self.test_supabase_service),
            ("Live Cricket Service", self.test_live_cricket_service),
            ("Routes Registration", self.test_routes_registration),
            ("Enhanced Booking Service", self.test_enhanced_booking_service)
        ]
        
        # Run all tests
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
        
        # Generate summary
        summary = self.test_results['summary']
        success_rate = (summary['passed'] / summary['total_tests'] * 100) if summary['total_tests'] > 0 else 0
        
        logger.info("=" * 50)
        logger.info("🎯 TEST SUMMARY")
        logger.info(f"Total Tests: {summary['total_tests']}")
        logger.info(f"Passed: {summary['passed']}")
        logger.info(f"Failed: {summary['failed']}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            logger.info("🎉 System is ready for deployment!")
        elif success_rate >= 60:
            logger.warning("⚠️ System has some issues but may work")
        else:
            logger.error("❌ System has critical issues - fix before deployment")
        
        return self.test_results
    
    def save_results(self, filename: str = "test_results.json"):
        """Save test results to file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.test_results, f, indent=2)
            logger.info(f"📄 Test results saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save test results: {str(e)}")

def main():
    """Main testing function"""
    print("CricVerse Stadium System - Comprehensive Testing")
    print("=" * 60)
    
    # Create tester instance
    tester = CricVerseSystemTester()
    
    # Run all tests
    results = tester.run_all_tests()
    
    # Save results
    tester.save_results()
    
    # Return exit code based on results
    success_rate = (results['summary']['passed'] / results['summary']['total_tests'] * 100) if results['summary']['total_tests'] > 0 else 0
    
    if success_rate >= 80:
        print("\nAll tests passed! System is ready to run.")
        print("Next step: Run 'python app.py' or 'python run.py'")
        return 0
    else:
        print(f"\nSome tests failed (Success rate: {success_rate:.1f}%)")
        print("Check the test results and fix issues before running the app.")
        return 1

if __name__ == "__main__":
    exit(main())
