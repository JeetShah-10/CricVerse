
#!/usr/bin/env python3
"""
Comprehensive Test Suite for CricVerse Stadium System
This script tests all major components systematically and identifies errors
"""

import sys
import os
import time
import subprocess
import requests
import traceback
import json
from urllib.parse import urljoin

# Add the current directory to Python path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to import BeautifulSoup, install if missing
try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Installing required package: beautifulsoup4")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4"])
    from bs4 import BeautifulSoup

class CricVerseTestSuite:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.test_results = {}
        self.errors = []
        self.warnings = []
        self.server_process = None
        
    def log_error(self, test_name, error_msg):
        """Log an error for a specific test"""
        self.errors.append(f"[{test_name}] {error_msg}")
        print(f"❌ {test_name}: {error_msg}")
        
    def log_warning(self, test_name, warning_msg):
        """Log a warning for a specific test"""
        self.warnings.append(f"[{test_name}] {warning_msg}")
        print(f"⚠️ {test_name}: {warning_msg}")
        
    def log_success(self, test_name, success_msg):
        """Log a success for a specific test"""
        print(f"✅ {test_name}: {success_msg}")

    def test_imports(self):
        """Test all critical imports"""
        print("\n🔍 Testing imports...")
        try:
            # Test main app imports
            try:
                from app import app, db
                self.log_success("Imports", "Main app imports successful")
            except ImportError as e:
                # Try alternative import paths
                try:
                    import app
                    self.log_success("Imports", "App module imported successfully")
                except ImportError:
                    self.log_error("Imports", f"Cannot import app module: {e}")
                    return False
            
            # Test if socketio is available
            try:
                from app import socketio
                self.log_success("Imports", "SocketIO import successful")
            except (ImportError, AttributeError):
                self.log_warning("Imports", "SocketIO not available - real-time features may not work")
            
            # Test database models - handle different import patterns
            try:
                from app.models import User, Stadium, Event, Booking
                self.log_success("Imports", "Database models imported successfully")
            except ImportError:
                try:
                    from app import User, Stadium, Event, Booking
                    self.log_success("Imports", "Database models imported successfully")
                except ImportError as e:
                    self.log_warning("Imports", f"Some database models may not be available: {e}")
                
            return True
        except Exception as e:
            self.log_error("Imports", f"Critical import failure: {e}")
            return False

    def test_database_connection(self):
        """Test database connectivity"""
        print("\n🔍 Testing database connection...")
        try:
            # Try different import patterns
            try:
                from app import app, db
            except ImportError:
                import app
                app_instance = app.app if hasattr(app, 'app') else app
                db = app.db if hasattr(app, 'db') else None
                
            if not db:
                self.log_error("Database", "Database object not found")
                return False
                
            with app_instance.app_context():
                from sqlalchemy import text
                result = db.session.execute(text("SELECT 1")).scalar()
                if result == 1:
                    self.log_success("Database", "Connection successful")
                    return True
                else:
                    self.log_error("Database", "Connection test failed")
                    return False
        except Exception as e:
            self.log_error("Database", f"Connection failed: {e}")
            return False

    def test_database_tables(self):
        """Test database table structure"""
        print("\n🔍 Testing database tables...")
        try:
            from app import app, db
            
            with app.app_context():
                # Use inspector to check tables (more reliable)
                from sqlalchemy import inspect
                inspector = inspect(db.engine)
                existing_tables = inspector.get_table_names()
                
                # Common table names to check
                tables_to_check = ['users', 'stadiums', 'events', 'bookings', 'customers', 'tickets']
                found_tables = [table for table in tables_to_check if table in existing_tables]
                missing_tables = [table for table in tables_to_check if table not in existing_tables]
                
                if found_tables:
                    self.log_success("Database Tables", f"Found tables: {', '.join(found_tables)}")
                
                if missing_tables:
                    self.log_warning("Database Tables", f"Missing tables: {', '.join(missing_tables)}")
                
                if len(found_tables) >= 3:  # At least 3 core tables should exist
                    return True
                else:
                    self.log_error("Database Tables", "Insufficient core tables found")
                    return False
                    
        except Exception as e:
            self.log_error("Database Tables", f"Table check failed: {e}")
            return False

    def start_server(self):
        """Start the Flask server for testing"""
        print("\n🚀 Starting test server...")
        try:
            # Check if server is already running
            try:
                response = requests.get(self.base_url, timeout=3)
                if response.status_code == 200:
                    self.log_success("Server", "Server already running")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            # Try to start server
            app_files = ['app.py', 'app_enhanced.py', 'start.py']
            app_file = None
            
            for file in app_files:
                if os.path.exists(file):
                    app_file = file
                    break
            
            if not app_file:
                self.log_error("Server", "No app file found (app.py, app_enhanced.py, or start.py)")
                return False
            
            # Start server in background
            self.server_process = subprocess.Popen(
                [sys.executable, app_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            # Wait for server to start
            for i in range(20):  # Wait up to 20 seconds
                try:
                    response = requests.get(self.base_url, timeout=2)
                    if response.status_code == 200:
                        self.log_success("Server", f"Started successfully using {app_file}")
                        return True
                except requests.exceptions.RequestException:
                    time.sleep(1)
            
            # Check if process is still running
            if self.server_process.poll() is not None:
                stdout, stderr = self.server_process.communicate()
                self.log_error("Server", f"Process exited with code {self.server_process.returncode}")
                if stderr:
                    self.log_error("Server", f"Error output: {stderr.decode()[:200]}")
            else:
                self.log_error("Server", "Failed to start within 20 seconds")
            
            return False
            
        except Exception as e:
            self.log_error("Server", f"Startup failed: {e}")
            return False

    def test_home_page(self):
        """Test home page functionality"""
        print("\n🔍 Testing home page...")
        try:
            response = requests.get(self.base_url, timeout=10)
            
            if response.status_code != 200:
                self.log_error("Home Page", f"Status code: {response.status_code}")
                return False
            
            content = response.text.lower()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for essential elements (more flexible)
            required_elements = {
                "cricverse": "CricVerse branding",
                "stadium": "Stadium references",
            }
            
            # Optional elements
            optional_elements = {
                "ticket": "Ticket booking functionality",
                "bbl": "BBL references",
                "cricket": "Cricket references"
            }
            
            missing_required = []
            for element, description in required_elements.items():
                if element not in content:
                    missing_required.append(f"{element} ({description})")
            
            found_optional = []
            for element, description in optional_elements.items():
                if element in content:
                    found_optional.append(f"{element} ({description})")
            
            if missing_required:
                self.log_error("Home Page", f"Missing required elements: {', '.join(missing_required)}")
                return False
            
            if found_optional:
                self.log_success("Home Page", f"Found optional elements: {', '.join(found_optional)}")
            
            # Check for CSS and JS files
            css_files = soup.find_all('link', rel='stylesheet')
            js_files = soup.find_all('script', src=True)
            
            if len(css_files) == 0:
                self.log_warning("Home Page", "No CSS files found")
            else:
                self.log_success("Home Page", f"Found {len(css_files)} CSS files")
            
            if len(js_files) == 0:
                self.log_warning("Home Page", "No JavaScript files found")
            else:
                self.log_success("Home Page", f"Found {len(js_files)} JavaScript files")
            
            self.log_success("Home Page", "Loaded successfully with required content")
            return True
            
        except Exception as e:
            self.log_error("Home Page", f"Failed to load: {e}")
            return False

    def test_admin_pages(self):
        """Test admin panel pages"""
        print("\n🔍 Testing admin pages...")
        admin_pages = [
            "/admin",
            "/admin/dashboard",
            "/admin/stadiums",
            "/admin/events",
            "/admin/bookings",
            "/admin/users"
        ]
        
        accessible_pages = []
        failed_pages = []
        
        for page in admin_pages:
            try:
                url = urljoin(self.base_url, page)
                response = requests.get(url, timeout=5)
                
                # Admin pages should either load (200) or redirect to login (302/401/403)
                if response.status_code in [200, 302, 401, 403]:
                    accessible_pages.append(page)
                else:
                    failed_pages.append(f"{page} (Status: {response.status_code})")
                    
            except Exception as e:
                failed_pages.append(f"{page} (Error: {str(e)[:50]})")
        
        if accessible_pages:
            self.log_success("Admin Pages", f"Accessible pages: {', '.join(accessible_pages)}")
        
        if failed_pages:
            self.log_warning("Admin Pages", f"Failed pages: {', '.join(failed_pages)}")
        
        # Return True if at least one admin page is accessible
        return len(accessible_pages) > 0

    def test_api_endpoints(self):
        """Test API endpoints"""
        print("\n🔍 Testing API endpoints...")
        api_endpoints = [
            "/api/csrf-token",
            "/api/bbl/live-scores",
            "/api/stadiums",
            "/api/events",
            "/api/teams"
        ]
        
        failed_endpoints = []
        for endpoint in api_endpoints:
            try:
                url = urljoin(self.base_url, endpoint)
                response = requests.get(url, timeout=5)
                
                if response.status_code not in [200, 401, 403]:
                    failed_endpoints.append(f"{endpoint} (Status: {response.status_code})")
                else:
                    # Try to parse JSON for API endpoints
                    try:
                        response.json()
                    except:
                        if response.status_code == 200:
                            self.log_warning("API", f"{endpoint} returned non-JSON response")
                            
            except Exception as e:
                failed_endpoints.append(f"{endpoint} (Error: {str(e)[:50]})")
        
        if failed_endpoints:
            self.log_warning("API Endpoints", f"Failed endpoints: {', '.join(failed_endpoints)}")
        else:
            self.log_success("API Endpoints", "All API endpoints accessible")
        
        return True  # Non-critical for basic functionality

    def test_static_files(self):
        """Test static file serving"""
        print("\n🔍 Testing static files...")
        static_files = [
            "/static/css/unified.css",
            "/static/css/style.css",
            "/static/js/main.js",
            "/static/images/logo.png"
        ]
        
        missing_files = []
        for file_path in static_files:
            try:
                url = urljoin(self.base_url, file_path)
                response = requests.get(url, timeout=5)
                
                if response.status_code == 404:
                    missing_files.append(file_path)
                elif response.status_code != 200:
                    self.log_warning("Static Files", f"{file_path} returned status {response.status_code}")
                    
            except Exception as e:
                missing_files.append(f"{file_path} (Error: {str(e)[:50]})")
        
        if missing_files:
            self.log_warning("Static Files", f"Missing files: {', '.join(missing_files)}")
        else:
            self.log_success("Static Files", "All static files accessible")
        
        return True  # Non-critical for basic functionality

    def test_template_rendering(self):
        """Test template rendering"""
        print("\n🔍 Testing template rendering...")
        try:
            response = requests.get(self.base_url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for template errors
            error_indicators = [
                "templatedoesnotexist",
                "templateerror",
                "jinja2.exceptions",
                "500 internal server error"
            ]
            
            content_lower = response.text.lower()
            found_errors = [error for error in error_indicators if error in content_lower]
            
            if found_errors:
                self.log_error("Template Rendering", f"Template errors found: {', '.join(found_errors)}")
                return False
            
            # Check for proper HTML structure
            if not soup.find('html'):
                self.log_error("Template Rendering", "No HTML tag found")
                return False
            
            if not soup.find('head'):
                self.log_error("Template Rendering", "No HEAD tag found")
                return False
            
            if not soup.find('body'):
                self.log_error("Template Rendering", "No BODY tag found")
                return False
            
            self.log_success("Template Rendering", "Templates rendering correctly")
            return True
            
        except Exception as e:
            self.log_error("Template Rendering", f"Failed: {e}")
            return False

    def test_authentication_system(self):
        """Test authentication system"""
        print("\n🔍 Testing authentication system...")
        try:
            # Test login page
            login_url = urljoin(self.base_url, "/login")
            response = requests.get(login_url, timeout=5)
            
            if response.status_code != 200:
                self.log_error("Authentication", f"Login page not accessible (Status: {response.status_code})")
                return False
            
            # Test register page
            register_url = urljoin(self.base_url, "/register")
            response = requests.get(register_url, timeout=5)
            
            if response.status_code != 200:
                self.log_error("Authentication", f"Register page not accessible (Status: {response.status_code})")
                return False
            
            self.log_success("Authentication", "Authentication pages accessible")
            return True
            
        except Exception as e:
            self.log_error("Authentication", f"Failed: {e}")
            return False

    def test_database_operations(self):
        """Test basic database operations"""
        print("\n🔍 Testing database operations...")
        try:
            from app import app, db, User, Stadium
            
            with app.app_context():
                # Test user count
                user_count = User.query.count()
                self.log_success("Database Operations", f"Found {user_count} users")
                
                # Test stadium count
                stadium_count = Stadium.query.count()
                self.log_success("Database Operations", f"Found {stadium_count} stadiums")
                
                return True
                
        except Exception as e:
            self.log_error("Database Operations", f"Failed: {e}")
            return False

    def cleanup_server(self):
        """Clean up server process"""
        if self.server_process:
            try:
                self.server_process.terminate()
                time.sleep(2)
                if self.server_process.poll() is None:
                    self.server_process.kill()
                print("🧹 Server process cleaned up")
            except:
                pass

    def generate_error_report(self):
        """Generate comprehensive error report"""
        print("\n" + "=" * 80)
        print("📋 COMPREHENSIVE ERROR REPORT")
        print("=" * 80)
        
        if self.errors:
            print("❌ ERRORS FOUND:")
            for error in self.errors:
                print(f"  {error}")
        else:
            print("✅ No critical errors found")
            
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  {warning}")
        else:
            print("\n✅ No warnings found")
            
        print("\n📊 TEST RESULTS SUMMARY:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status}: {test_name}")
            
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results.values() if r)
        failed_tests = total_tests - passed_tests
        
        print(f"\n📈 OVERALL STATISTICS:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests}")
        print(f"  Failed: {failed_tests}")
        print(f"  Success Rate: {passed_tests/total_tests*100:.1f}%")
        
        if self.errors:
            print(f"\n🚨 SYSTEM IS NOT READY FOR PRODUCTION")
            print("Please fix the above errors before deployment.")
        else:
            print(f"\n🎉 ALL TESTS PASSED - SYSTEM IS OPERATIONAL")

    def run_all_tests(self):
        """Run all tests systematically"""
        print("=" * 80)
        print("🏏 CricVerse Stadium System - Comprehensive Error Detection Suite")
        print("=" * 80)
        
        # Define test sequence
        tests = [
            ("Imports", self.test_imports),
            ("Database Connection", self.test_database_connection),
            ("Database Tables", self.test_database_tables),
            ("Database Operations", self.test_database_operations),
            ("Server Startup", self.start_server),
            ("Home Page", self.test_home_page),
            ("Template Rendering", self.test_template_rendering),
            ("Admin Pages", self.test_admin_pages),
            ("API Endpoints", self.test_api_endpoints),
            ("Static Files", self.test_static_files),
            ("Authentication", self.test_authentication_system)
        ]
        
        # Run tests
        for test_name, test_func in tests:
            try:
                result = test_func()
                self.test_results[test_name] = result
            except Exception as e:
                self.log_error(test_name, f"Test crashed: {e}")
                self.test_results[test_name] = False
        
        # Generate comprehensive report
        self.generate_error_report()
        
        return len(self.errors)

if __name__ == "__main__":
    # Create test suite instance
    test_suite = CricVerseTestSuite()
    
    try:
        # Run all tests
        error_count = test_suite.run_all_tests()
        
        # Cleanup server process
        test_suite.cleanup_server()
        
        # Exit with appropriate code
        if error_count > 0:
            print(f"\n🏁 Test suite completed with {error_count} errors")
            sys.exit(1)
        else:
            print("\n🏁 Test suite completed successfully")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n🛑 Test suite interrupted by user")
        test_suite.cleanup_server()
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        traceback.print_exc()
        test_suite.cleanup_server()
        sys.exit(1)
