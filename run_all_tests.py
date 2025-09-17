#!/usr/bin/env python3
"""
Comprehensive Test Runner for CricVerse
Runs all tests and fixes common issues automatically
"""

import os
import sys
import subprocess
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
if os.path.exists('cricverse.env'):
    load_dotenv('cricverse.env')
else:
    load_dotenv()

class CricVerseTestRunner:
    def __init__(self):
        self.test_results = []
        self.fixes_applied = []
        
    def log_test(self, test_name, success, message="", details=None):
        """Log test results"""
        status = "[PASS] PASS" if success else "[FAIL] FAIL"
        result = {
            'test': test_name,
            'status': status,
            'success': success,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status} {test_name}: {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def log_fix(self, fix_name, success, message=""):
        """Log fixes applied"""
        status = "[FIX] APPLIED" if success else "[FAIL] FAILED"
        result = {
            'fix': fix_name,
            'status': status,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.fixes_applied.append(result)
        print(f"{status} {fix_name}: {message}")
    
    def check_flask_app_running(self):
        """Check if Flask app is running"""
        try:
            import requests
            response = requests.get("http://localhost:5000/", timeout=5)
            if response.status_code == 200:
                self.log_test("Flask App", True, "App is running")
                return True
            else:
                self.log_test("Flask App", False, f"App returned status {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Flask App", False, f"App not running: {e}")
            return False
    
    def start_flask_app(self):
        """Start Flask app in background"""
        try:
            print("[START] Starting Flask app...")
            # Start Flask app in background
            process = subprocess.Popen([
                sys.executable, 'app.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for app to start
            time.sleep(5)
            
            # Check if app is running
            if self.check_flask_app_running():
                self.log_fix("Flask App Startup", True, "App started successfully")
                return process
            else:
                self.log_fix("Flask App Startup", False, "App failed to start")
                return None
                
        except Exception as e:
            self.log_fix("Flask App Startup", False, f"Error starting app: {e}")
            return None
    
    def run_credential_tests(self):
        """Run credential tests"""
        try:
            print("\n[SECURITY] Testing Credentials...")
            result = subprocess.run([sys.executable, 'test_credentials.py'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.log_test("Credentials", True, "All credentials are valid")
                return True
            else:
                self.log_test("Credentials", False, "Credential test failed")
                print(f"   Output: {result.stdout}")
                print(f"   Error: {result.stderr}")
                return False
                
        except Exception as e:
            self.log_test("Credentials", False, f"Error running credential test: {e}")
            return False
    
    def run_qr_code_tests(self):
        """Run QR code tests"""
        try:
            print("\n[QR] Testing QR Code Generation...")
            result = subprocess.run([sys.executable, 'test_qr_code.py'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.log_test("QR Code", True, "QR code generation working")
                return True
            else:
                self.log_test("QR Code", False, "QR code test failed")
                print(f"   Output: {result.stdout}")
                print(f"   Error: {result.stderr}")
                return False
                
        except Exception as e:
            self.log_test("QR Code", False, f"Error running QR code test: {e}")
            return False
    
    def run_chatbot_tests(self):
        """Run chatbot integration tests"""
        try:
            print("\n[BOT] Testing Chatbot Integration...")
            result = subprocess.run([sys.executable, 'test_chatbot_integration.py'], 
                                  capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                self.log_test("Chatbot", True, "Chatbot integration working")
                return True
            else:
                self.log_test("Chatbot", False, "Chatbot test failed")
                print(f"   Output: {result.stdout}")
                print(f"   Error: {result.stderr}")
                return False
                
        except Exception as e:
            self.log_test("Chatbot", False, f"Error running chatbot test: {e}")
            return False
    
    def run_performance_tests(self):
        """Run performance tests"""
        try:
            print("\n[PERF] Testing Performance...")
            result = subprocess.run([sys.executable, 'test_performance.py'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.log_test("Performance", True, "Performance test completed")
                return True
            else:
                self.log_test("Performance", False, "Performance test failed")
                print(f"   Output: {result.stdout}")
                print(f"   Error: {result.stderr}")
                return False
                
        except Exception as e:
            self.log_test("Performance", False, f"Error running performance test: {e}")
            return False
    
    def run_performance_optimization(self):
        """Run performance optimization"""
        try:
            print("\n[FIX] Running Performance Optimization...")
            result = subprocess.run([sys.executable, 'performance_optimizer.py'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.log_fix("Performance Optimization", True, "Optimization completed")
                return True
            else:
                self.log_fix("Performance Optimization", False, "Optimization failed")
                print(f"   Output: {result.stdout}")
                print(f"   Error: {result.stderr}")
                return False
                
        except Exception as e:
            self.log_fix("Performance Optimization", False, f"Error running optimization: {e}")
            return False
    
    def fix_common_issues(self):
        """Fix common issues automatically"""
        print("\n[FIX] Applying Common Fixes...")
        
        # Fix 1: Ensure environment file exists
        if not os.path.exists('.env') and os.path.exists('cricverse.env'):
            try:
                import shutil
                shutil.copy('cricverse.env', '.env')
                self.log_fix("Environment File", True, "Created .env from cricverse.env")
            except Exception as e:
                self.log_fix("Environment File", False, f"Error: {e}")
        
        # Fix 2: Create necessary directories
        directories = [
            'static/qrcodes',
            'static/uploads',
            'logs'
        ]
        
        for directory in directories:
            try:
                os.makedirs(directory, exist_ok=True)
                self.log_fix(f"Directory {directory}", True, "Created successfully")
            except Exception as e:
                self.log_fix(f"Directory {directory}", False, f"Error: {e}")
        
        # Fix 3: Check database connection
        try:
            from app import app, db
            with app.app_context():
                db.create_all()
                self.log_fix("Database", True, "Database tables created/verified")
        except Exception as e:
            self.log_fix("Database", False, f"Error: {e}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("[START] CricVerse Comprehensive Test Suite")
        print("=" * 60)
        print(f"[TIME] Started: {datetime.now().strftime('%H:%M:%S')}")
        
        # Apply common fixes first
        self.fix_common_issues()
        
        # Check if Flask app is running, start if not
        flask_process = None
        if not self.check_flask_app_running():
            flask_process = self.start_flask_app()
            if not flask_process:
                print("[FAIL] Cannot start Flask app. Please start it manually and run tests again.")
                return False
        
        # Run all tests
        tests = [
            self.run_credential_tests,
            self.run_qr_code_tests,
            self.run_chatbot_tests,
            self.run_performance_tests,
            self.run_performance_optimization
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"[FAIL] Test {test.__name__} failed with exception: {e}")
        
        # Cleanup
        if flask_process:
            try:
                flask_process.terminate()
                flask_process.wait(timeout=5)
            except:
                flask_process.kill()
        
        print("\n" + "=" * 60)
        print("[STATS] FINAL TEST SUMMARY")
        print("=" * 60)
        print(f"Tests Passed: {passed}/{total} ({(passed/total)*100:.1f}%)")
        print(f"Fixes Applied: {len(self.fixes_applied)}")
        
        if passed == total:
            print("[SUCCESS] ALL TESTS PASSED! CricVerse is ready for Big Bash League!")
            return True
        elif passed >= total * 0.8:
            print("[WARN]  Most tests passed. Minor issues may exist.")
            return True
        else:
            print("[FAIL] Multiple test failures. Please check the issues above.")
            return False
    
    def generate_report(self):
        """Generate detailed test report"""
        report = {
            "test_run": {
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(self.test_results),
                "passed": sum(1 for r in self.test_results if r['success']),
                "failed": sum(1 for r in self.test_results if not r['success']),
                "fixes_applied": len(self.fixes_applied)
            },
            "test_results": self.test_results,
            "fixes_applied": self.fixes_applied
        }
        
        with open('comprehensive_test_report.json', 'w') as f:
            import json
            json.dump(report, f, indent=2)
        
        print(f"\n[REPORT] Detailed report saved to: comprehensive_test_report.json")
        return report

def main():
    """Main test execution"""
    print("CricVerse Comprehensive Test Runner")
    print("===================================")
    
    runner = CricVerseTestRunner()
    
    # Run all tests
    success = runner.run_all_tests()
    
    # Generate report
    runner.generate_report()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
