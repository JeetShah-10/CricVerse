#!/usr/bin/env python3
"""
Test Enhanced Booking Endpoints - CricVerse
Tests for rate limiting, enhanced validation, concurrency handling, and transaction management
"""

import requests
import json
import time
import concurrent.futures
from datetime import datetime, timedelta
import random

class BookingEndpointTester:
    def __init__(self, base_url="http://127.0.0.1:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name, success, details=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            'test': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        print(f"{status} - {test_name}: {details}")
    
    def login_test_user(self):
        """Login with test user credentials"""
        try:
            login_data = {
                'email': 'test@cricverse.com',
                'password': 'TestPass123!'
            }
            
            response = self.session.post(f"{self.base_url}/login", data=login_data)
            if response.status_code == 200 or 'dashboard' in response.url:
                self.log_test("User Login", True, "Successfully logged in test user")
                return True
            else:
                self.log_test("User Login", False, f"Login failed: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("User Login", False, f"Login error: {e}")
            return False
    
    def test_rate_limiting(self):
        """Test rate limiting on booking endpoints"""
        print("\n🔥 Testing Rate Limiting...")
        
        # Test data for booking creation
        booking_data = {
            "event_id": 1,
            "seat_ids": [1, 2],
            "ticket_type": "Single Match",
            "total_amount": 100.0
        }
        
        # Make rapid requests to trigger rate limiting
        success_count = 0
        rate_limited_count = 0
        
        for i in range(8):  # Try 8 requests (limit is 5 per minute)
            try:
                response = self.session.post(
                    f"{self.base_url}/booking/create-order",
                    json=booking_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    success_count += 1
                elif response.status_code == 429:  # Too Many Requests
                    rate_limited_count += 1
                    
                time.sleep(0.1)  # Small delay between requests
                
            except Exception as e:
                self.log_test(f"Rate Limit Request {i+1}", False, f"Error: {e}")
        
        # Check if rate limiting is working
        if rate_limited_count > 0 and success_count <= 5:
            self.log_test("Rate Limiting", True, f"Blocked {rate_limited_count} requests after {success_count} successful")
        else:
            self.log_test("Rate Limiting", False, f"Rate limiting not working properly: {success_count} success, {rate_limited_count} blocked")
    
    def test_enhanced_validation(self):
        """Test enhanced input validation"""
        print("\n🔍 Testing Enhanced Validation...")
        
        # Test cases with invalid data
        test_cases = [
            {
                "name": "Missing Event ID",
                "data": {"seat_ids": [1, 2], "total_amount": 100.0},
                "should_fail": True
            },
            {
                "name": "Invalid Seat IDs (empty)",
                "data": {"event_id": 1, "seat_ids": [], "total_amount": 100.0},
                "should_fail": True
            },
            {
                "name": "Invalid Amount (negative)",
                "data": {"event_id": 1, "seat_ids": [1], "total_amount": -50.0},
                "should_fail": True
            },
            {
                "name": "Invalid Ticket Type",
                "data": {"event_id": 1, "seat_ids": [1], "ticket_type": "Invalid Type", "total_amount": 100.0},
                "should_fail": True
            },
            {
                "name": "Valid Booking Data",
                "data": {"event_id": 1, "seat_ids": [10, 11], "ticket_type": "Single Match", "total_amount": 150.0},
                "should_fail": False
            }
        ]
        
        for test_case in test_cases:
            try:
                response = self.session.post(
                    f"{self.base_url}/api/booking/create",
                    json=test_case["data"],
                    headers={'Content-Type': 'application/json'}
                )
                
                is_error = response.status_code >= 400
                test_passed = (test_case["should_fail"] and is_error) or (not test_case["should_fail"] and not is_error)
                
                details = f"Status: {response.status_code}"
                if is_error:
                    try:
                        error_data = response.json()
                        details += f" - {error_data.get('error', 'Unknown error')}"
                    except:
                        pass
                
                self.log_test(f"Validation - {test_case['name']}", test_passed, details)
                
            except Exception as e:
                self.log_test(f"Validation - {test_case['name']}", False, f"Error: {e}")
    
    def test_concurrency_handling(self):
        """Test concurrency handling for seat availability"""
        print("\n⚡ Testing Concurrency Handling...")
        
        # Simulate multiple users trying to book the same seats
        def attempt_booking(user_id):
            """Simulate a booking attempt"""
            booking_data = {
                "event_id": 1,
                "seat_ids": [50, 51],  # Same seats for all users
                "ticket_type": "Single Match", 
                "total_amount": 120.0
            }
            
            try:
                response = self.session.post(
                    f"{self.base_url}/booking/create-order",
                    json=booking_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                return {
                    'user_id': user_id,
                    'status_code': response.status_code,
                    'success': response.status_code == 200,
                    'response': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                }
            except Exception as e:
                return {
                    'user_id': user_id,
                    'status_code': 500,
                    'success': False,
                    'error': str(e)
                }
        
        # Use ThreadPoolExecutor to simulate concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(attempt_booking, i) for i in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Analyze results
        successful_bookings = [r for r in results if r['success']]
        failed_bookings = [r for r in results if not r['success']]
        conflict_responses = [r for r in results if r.get('response', {}).get('error_code') == 'SEATS_UNAVAILABLE']
        
        # Should have only 1 successful booking and rest should fail due to conflicts
        if len(successful_bookings) <= 1 and len(conflict_responses) >= 3:
            self.log_test("Concurrency Handling", True, f"1 success, {len(conflict_responses)} conflicts detected")
        else:
            self.log_test("Concurrency Handling", False, f"{len(successful_bookings)} successes, {len(conflict_responses)} conflicts")
    
    def test_transaction_atomicity(self):
        """Test transaction management for booking atomicity"""
        print("\n🔒 Testing Transaction Atomicity...")
        
        # Test booking with invalid parking to trigger rollback
        booking_data = {
            "event_id": 1,
            "seat_ids": [100, 101],
            "ticket_type": "Single Match",
            "total_amount": 150.0,
            "parking_id": 99999,  # Invalid parking ID
            "parking_hours": 3
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/booking/create-order",
                json=booking_data,
                headers={'Content-Type': 'application/json'}
            )
            
            # Should fail due to invalid parking
            if response.status_code >= 400:
                # Verify seats are still available after failed transaction
                verification_data = {
                    "event_id": 1,
                    "seat_ids": [100, 101],
                    "ticket_type": "Single Match",
                    "total_amount": 120.0
                }
                
                verify_response = self.session.post(
                    f"{self.base_url}/booking/create-order",
                    json=verification_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                if verify_response.status_code == 200:
                    self.log_test("Transaction Atomicity", True, "Seats remained available after failed booking")
                else:
                    self.log_test("Transaction Atomicity", False, "Seats locked after failed transaction")
            else:
                self.log_test("Transaction Atomicity", False, "Booking should have failed with invalid parking")
                
        except Exception as e:
            self.log_test("Transaction Atomicity", False, f"Error: {e}")
    
    def test_booking_data_validation(self):
        """Test comprehensive booking data validation"""
        print("\n📋 Testing Booking Data Validation...")
        
        # Test amount calculation validation
        booking_data = {
            "event_id": 1,
            "seat_ids": [200, 201],
            "ticket_type": "Single Match",
            "total_amount": 50.0  # Intentionally low amount to trigger mismatch
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/booking/create-order",
                json=booking_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code >= 400:
                response_data = response.json()
                if 'amount' in response_data.get('error', '').lower() or response_data.get('error_code') == 'AMOUNT_MISMATCH':
                    self.log_test("Amount Validation", True, "Amount mismatch detected correctly")
                else:
                    self.log_test("Amount Validation", False, f"Wrong error: {response_data.get('error')}")
            else:
                self.log_test("Amount Validation", False, "Should have failed with amount mismatch")
                
        except Exception as e:
            self.log_test("Amount Validation", False, f"Error: {e}")
    
    def test_session_security(self):
        """Test session-based security features"""
        print("\n🛡️ Testing Session Security...")
        
        # Test booking expiration
        booking_data = {
            "event_id": 1,
            "seat_ids": [300],
            "ticket_type": "Single Match",
            "total_amount": 75.0
        }
        
        try:
            # Create a booking order
            response = self.session.post(
                f"{self.base_url}/booking/create-order",
                json=booking_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                order_data = response.json()
                
                # Test immediate capture (should work)
                capture_data = {
                    "orderID": order_data.get("orderID"),
                    "payerID": "TEST_PAYER"
                }
                
                capture_response = self.session.post(
                    f"{self.base_url}/booking/capture-order",
                    json=capture_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                if capture_response.status_code == 200:
                    self.log_test("Session Security", True, "Booking capture works with valid session")
                else:
                    self.log_test("Session Security", False, "Booking capture failed with valid session")
            else:
                self.log_test("Session Security", False, "Could not create test booking")
                
        except Exception as e:
            self.log_test("Session Security", False, f"Error: {e}")
    
    def run_all_tests(self):
        """Run all booking endpoint tests"""
        print("🏏 CricVerse Enhanced Booking Endpoints Test Suite")
        print("=" * 60)
        
        # Login first
        if not self.login_test_user():
            print("❌ Cannot proceed without login")
            return
        
        # Run all tests
        self.test_rate_limiting()
        time.sleep(2)  # Wait for rate limit reset
        
        self.test_enhanced_validation() 
        self.test_concurrency_handling()
        self.test_transaction_atomicity()
        self.test_booking_data_validation()
        self.test_session_security()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = len([r for r in self.test_results if "✅" in r['status']])
        failed = len([r for r in self.test_results if "❌" in r['status']])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if "❌" in result['status']:
                    print(f"  - {result['test']}: {result['details']}")

if __name__ == "__main__":
    tester = BookingEndpointTester()
    tester.run_all_tests()