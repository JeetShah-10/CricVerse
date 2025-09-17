#!/usr/bin/env python3
"""
Comprehensive Chatbot Integration Test Suite
Tests all chatbot functionality including OpenAI integration, real-time features, and API endpoints
"""

import os
import sys
import json
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables first
if os.path.exists('cricverse.env'):
    load_dotenv('cricverse.env')
else:
    load_dotenv()

# Test configuration
BASE_URL = "http://localhost:5000"
TEST_API_KEY = os.getenv('OPENAI_API_KEY')

class ChatbotIntegrationTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.test_results = []
        
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
    
    def test_openai_api_key(self):
        """Test if OpenAI API key is configured"""
        try:
            if TEST_API_KEY and TEST_API_KEY.startswith('sk-'):
                self.log_test("OpenAI API Key", True, "API key is configured")
                return True
            else:
                self.log_test("OpenAI API Key", False, "API key not found or invalid")
                return False
        except Exception as e:
            self.log_test("OpenAI API Key", False, f"Error checking API key: {e}")
            return False
    
    def test_chatbot_import(self):
        """Test if chatbot module can be imported"""
        try:
            sys.path.append('.')
            import chatbot
            self.log_test("Chatbot Import", True, "Chatbot module imported successfully")
            return True
        except Exception as e:
            self.log_test("Chatbot Import", False, f"Failed to import chatbot: {e}")
            return False
    
    def test_realtime_import(self):
        """Test if realtime module can be imported"""
        try:
            import realtime
            self.log_test("Realtime Import", True, "Realtime module imported successfully")
            return True
        except Exception as e:
            self.log_test("Realtime Import", False, f"Failed to import realtime: {e}")
            return False
    
    def test_app_startup(self):
        """Test if Flask app can start"""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                self.log_test("App Startup", True, "Flask app is running")
                return True
            else:
                self.log_test("App Startup", False, f"App returned status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self.log_test("App Startup", False, "Cannot connect to Flask app - is it running?")
            return False
        except Exception as e:
            self.log_test("App Startup", False, f"Error connecting to app: {e}")
            return False
    
    def test_chat_endpoint(self):
        """Test the chat API endpoint"""
        try:
            # First get CSRF token
            csrf_response = self.session.get(f"{self.base_url}/api/csrf-token", timeout=10)
            csrf_token = None
            if csrf_response.status_code == 200:
                csrf_data = csrf_response.json()
                csrf_token = csrf_data.get('csrf_token')
            
            test_message = {
                "message": "Hello, can you help me book tickets?"
            }
            
            headers = {}
            if csrf_token:
                headers['X-CSRFToken'] = csrf_token
            
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json=test_message,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'response' in data:
                    self.log_test("Chat Endpoint", True, "Chat API working correctly")
                    return True
                else:
                    self.log_test("Chat Endpoint", False, "Response missing 'response' field", data)
                    return False
            else:
                self.log_test("Chat Endpoint", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Chat Endpoint", False, f"Error testing chat endpoint: {e}")
            return False
    
    def test_chat_suggestions(self):
        """Test chat suggestions endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/chat/suggestions", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'suggestions' in data and isinstance(data['suggestions'], list):
                    self.log_test("Chat Suggestions", True, f"Got {len(data['suggestions'])} suggestions")
                    return True
                else:
                    self.log_test("Chat Suggestions", False, "Invalid suggestions format", data)
                    return False
            else:
                self.log_test("Chat Suggestions", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Chat Suggestions", False, f"Error: {e}")
            return False
    
    def test_chat_interface(self):
        """Test chat interface page"""
        try:
            response = self.session.get(f"{self.base_url}/chat", timeout=10)
            
            if response.status_code == 200:
                if 'chat' in response.text.lower():
                    self.log_test("Chat Interface", True, "Chat page loads successfully")
                    return True
                else:
                    self.log_test("Chat Interface", False, "Chat page missing chat elements")
                    return False
            else:
                self.log_test("Chat Interface", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Chat Interface", False, f"Error: {e}")
            return False
    
    def test_realtime_stats(self):
        """Test real-time statistics endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/realtime/stats", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'stats' in data:
                    self.log_test("Realtime Stats", True, "Real-time stats working")
                    return True
                else:
                    self.log_test("Realtime Stats", False, "Missing stats in response", data)
                    return False
            else:
                self.log_test("Realtime Stats", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Realtime Stats", False, f"Error: {e}")
            return False
    
    def test_chatbot_functionality(self):
        """Test various chatbot conversation scenarios"""
        test_scenarios = [
            {
                "message": "What matches are coming up?",
                "expected_keywords": ["match", "event", "upcoming"]
            },
            {
                "message": "Help me book tickets",
                "expected_keywords": ["ticket", "book", "help"]
            },
            {
                "message": "What stadiums do you have?",
                "expected_keywords": ["stadium", "venue"]
            },
            {
                "message": "I need parking information",
                "expected_keywords": ["parking", "car"]
            }
        ]
        
        passed_scenarios = 0
        
        # Get CSRF token once for all scenarios
        csrf_response = self.session.get(f"{self.base_url}/api/csrf-token", timeout=10)
        csrf_token = None
        if csrf_response.status_code == 200:
            csrf_data = csrf_response.json()
            csrf_token = csrf_data.get('csrf_token')
        
        headers = {}
        if csrf_token:
            headers['X-CSRFToken'] = csrf_token
        
        for i, scenario in enumerate(test_scenarios):
            try:
                response = self.session.post(
                    f"{self.base_url}/api/chat",
                    json={"message": scenario["message"]},
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    response_text = data.get('response', '').lower()
                    
                    # Check if response contains expected keywords
                    keyword_found = any(keyword in response_text for keyword in scenario["expected_keywords"])
                    
                    if keyword_found:
                        passed_scenarios += 1
                        print(f"   [PASS] Scenario {i+1}: {scenario['message'][:30]}...")
                    else:
                        print(f"   [FAIL] Scenario {i+1}: {scenario['message'][:30]}... (no relevant keywords)")
                else:
                    print(f"   [FAIL] Scenario {i+1}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"   [FAIL] Scenario {i+1}: Error - {e}")
        
        success_rate = (passed_scenarios / len(test_scenarios)) * 100
        
        if success_rate >= 75:
            self.log_test("Chatbot Functionality", True, f"{passed_scenarios}/{len(test_scenarios)} scenarios passed ({success_rate:.1f}%)")
            return True
        else:
            self.log_test("Chatbot Functionality", False, f"Only {passed_scenarios}/{len(test_scenarios)} scenarios passed ({success_rate:.1f}%)")
            return False
    
    def run_all_tests(self):
        """Run all chatbot integration tests"""
        print("[START] Starting Chatbot Integration Tests...")
        print("=" * 60)
        
        # Core functionality tests
        tests = [
            self.test_openai_api_key,
            self.test_chatbot_import,
            self.test_realtime_import,
            self.test_app_startup,
            self.test_chat_interface,
            self.test_chat_endpoint,
            self.test_chat_suggestions,
            self.test_realtime_stats,
            self.test_chatbot_functionality
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"[FAIL] Test {test.__name__} failed with exception: {e}")
        
        print("\n" + "=" * 60)
        print(f"[STATS] TEST SUMMARY")
        print(f"Passed: {passed}/{total} ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            print("[SUCCESS] ALL TESTS PASSED! Chatbot integration is working correctly.")
            return True
        elif passed >= total * 0.8:
            print("[WARN]  Most tests passed. Minor issues may exist.")
            return True
        else:
            print("[FAIL] Multiple test failures. Chatbot integration needs attention.")
            return False
    
    def generate_report(self):
        """Generate detailed test report"""
        report = {
            "test_run": {
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(self.test_results),
                "passed": sum(1 for r in self.test_results if r['success']),
                "failed": sum(1 for r in self.test_results if not r['success'])
            },
            "results": self.test_results
        }
        
        with open('chatbot_test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n[REPORT] Detailed report saved to: chatbot_test_report.json")
        return report

def main():
    """Main test execution"""
    print("CricVerse Chatbot Integration Test Suite")
    print("========================================")
    
    tester = ChatbotIntegrationTester()
    
    # Run all tests
    success = tester.run_all_tests()
    
    # Generate report
    tester.generate_report()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
