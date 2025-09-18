#!/usr/bin/env python3
"""
Comprehensive Test Script for New CricVerse Features
Tests the four new system features:
1. Ticket Transfer Functionality
2. Resale Marketplace Integration
3. Season Ticket Management
4. Accessibility Accommodations Tracking
"""

import requests
import json
import sys
from datetime import datetime, timedelta
import time

# Configuration
BASE_URL = "http://localhost:5001"
TEST_EMAIL = "test@cricverse.com"
TEST_PASSWORD = "TestPassword123!"
RECIPIENT_EMAIL = "recipient@cricverse.com"

class CricVerseTestSuite:
    def __init__(self):
        self.session = requests.Session()
        self.csrf_token = None
        self.user_id = None
        self.test_results = []
        
    def log_test(self, test_name, success, message="", response_data=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'data': response_data
        })
        
    def get_csrf_token(self):
        """Get CSRF token from the application"""
        try:
            response = self.session.get(f"{BASE_URL}/login")
            if response.status_code == 200:
                # Extract CSRF token from the response
                # In a real implementation, you'd parse the HTML to get the token
                # For now, we'll handle CSRF in headers
                return "test-csrf-token"
        except Exception as e:
            print(f"Warning: Could not get CSRF token: {e}")
            return None
            
    def login(self):
        """Login to get authenticated session"""
        try:
            # Get CSRF token first
            self.csrf_token = self.get_csrf_token()
            
            # Login
            login_data = {
                'email': TEST_EMAIL,
                'password': TEST_PASSWORD
            }
            
            response = self.session.post(f"{BASE_URL}/login", data=login_data)
            
            if response.status_code == 200 and 'dashboard' in response.url:
                self.log_test("User Login", True, f"Successfully logged in as {TEST_EMAIL}")
                return True
            else:
                self.log_test("User Login", False, f"Login failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("User Login", False, f"Login error: {e}")
            return False
            
    def test_ticket_transfer(self):
        """Test ticket transfer functionality"""
        print("\n🎫 Testing Ticket Transfer Functionality...")
        
        # Test 1: Initiate ticket transfer
        try:
            transfer_data = {
                'ticket_id': 1,  # Assuming ticket ID 1 exists
                'to_email': RECIPIENT_EMAIL,
                'transfer_fee': 5.0
            }
            
            headers = {
                'Content-Type': 'application/json',
                'X-CSRFToken': self.csrf_token
            } if self.csrf_token else {'Content-Type': 'application/json'}
            
            response = self.session.post(
                f"{BASE_URL}/api/ticket/transfer",
                json=transfer_data,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    transfer_code = data.get('transfer_code')
                    self.log_test("Initiate Ticket Transfer", True, 
                                f"Transfer initiated with code: {transfer_code[:8]}...", data)
                    
                    # Test 2: Accept ticket transfer
                    self.test_accept_transfer(transfer_code)
                else:
                    self.log_test("Initiate Ticket Transfer", False, 
                                f"Transfer failed: {data.get('error', 'Unknown error')}")
            else:
                try:
                    error_data = response.json()
                    self.log_test("Initiate Ticket Transfer", False, 
                                f"HTTP {response.status_code}: {error_data.get('error', 'Unknown error')}")
                except:
                    self.log_test("Initiate Ticket Transfer", False, 
                                f"HTTP {response.status_code}: {response.text[:100]}")
                    
        except Exception as e:
            self.log_test("Initiate Ticket Transfer", False, f"Exception: {e}")
            
    def test_accept_transfer(self, transfer_code):
        """Test accepting a ticket transfer"""
        try:
            accept_data = {
                'verification_code': '123456'  # Mock verification code
            }
            
            response = self.session.post(
                f"{BASE_URL}/api/ticket/transfer/{transfer_code}/accept",
                json=accept_data
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_test("Accept Ticket Transfer", True, 
                                f"Transfer accepted: {data.get('message')}", data)
                else:
                    self.log_test("Accept Ticket Transfer", False, 
                                f"Accept failed: {data.get('error')}")
            else:
                try:
                    error_data = response.json()
                    self.log_test("Accept Ticket Transfer", False, 
                                f"HTTP {response.status_code}: {error_data.get('error', 'Unknown error')}")
                except:
                    self.log_test("Accept Ticket Transfer", False, 
                                f"HTTP {response.status_code}: Not authenticated or invalid transfer")
                    
        except Exception as e:
            self.log_test("Accept Ticket Transfer", False, f"Exception: {e}")
            
    def test_marketplace(self):
        """Test resale marketplace functionality"""
        print("\n🏪 Testing Resale Marketplace...")
        
        # Test 1: List ticket for resale
        try:
            listing_data = {
                'ticket_id': 2,  # Assuming ticket ID 2 exists
                'listing_price': 120.0,
                'description': 'Great seats, can\'t attend anymore',
                'is_negotiable': True
            }
            
            headers = {
                'Content-Type': 'application/json',
                'X-CSRFToken': self.csrf_token
            } if self.csrf_token else {'Content-Type': 'application/json'}
            
            response = self.session.post(
                f"{BASE_URL}/api/marketplace/list-ticket",
                json=listing_data,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_test("List Ticket for Resale", True, 
                                f"Ticket listed successfully. Net amount: ${data.get('net_amount', 0):.2f}", data)
                else:
                    self.log_test("List Ticket for Resale", False, 
                                f"Listing failed: {data.get('error')}")
            else:
                try:
                    error_data = response.json()
                    self.log_test("List Ticket for Resale", False, 
                                f"HTTP {response.status_code}: {error_data.get('error', 'Unknown error')}")
                except:
                    self.log_test("List Ticket for Resale", False, 
                                f"HTTP {response.status_code}: {response.text[:100]}")
                    
        except Exception as e:
            self.log_test("List Ticket for Resale", False, f"Exception: {e}")
            
        # Test 2: Search marketplace
        self.test_marketplace_search()
        
    def test_marketplace_search(self):
        """Test marketplace search functionality"""
        try:
            # Search with various filters
            search_params = {
                'max_price': 150,
                'per_page': 5
            }
            
            response = self.session.get(
                f"{BASE_URL}/api/marketplace/search",
                params=search_params
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    listings = data.get('listings', [])
                    pagination = data.get('pagination', {})
                    self.log_test("Search Marketplace", True, 
                                f"Found {len(listings)} listings (Total: {pagination.get('total', 0)})", 
                                {'listing_count': len(listings), 'pagination': pagination})
                else:
                    self.log_test("Search Marketplace", False, f"Search failed: {data.get('error')}")
            else:
                try:
                    error_data = response.json()
                    self.log_test("Search Marketplace", False, 
                                f"HTTP {response.status_code}: {error_data.get('error', 'Unknown error')}")
                except:
                    self.log_test("Search Marketplace", False, 
                                f"HTTP {response.status_code}: {response.text[:100]}")
                    
        except Exception as e:
            self.log_test("Search Marketplace", False, f"Exception: {e}")
            
    def test_season_tickets(self):
        """Test season ticket functionality"""
        print("\n🎟️ Testing Season Ticket Management...")
        
        # Test 1: Purchase season ticket
        try:
            season_data = {
                'stadium_id': 1,  # Assuming stadium ID 1 exists
                'seat_id': 1,     # Assuming seat ID 1 exists
                'season_name': 'BBL 2024-25',
                'season_start_date': '2024-01-01',
                'season_end_date': '2024-12-31',
                'total_matches': 10,
                'transfer_limit': 5
            }
            
            headers = {
                'Content-Type': 'application/json',
                'X-CSRFToken': self.csrf_token
            } if self.csrf_token else {'Content-Type': 'application/json'}
            
            response = self.session.post(
                f"{BASE_URL}/api/season-ticket/purchase",
                json=season_data,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    season_ticket_id = data.get('season_ticket_id')
                    total_price = data.get('total_price', 0)
                    savings = data.get('savings', 0)
                    self.log_test("Purchase Season Ticket", True, 
                                f"Season ticket purchased (ID: {season_ticket_id}). Total: ${total_price:.2f}, Savings: ${savings:.2f}", data)
                    
                    # Test 2: Get season ticket matches
                    self.test_season_ticket_matches(season_ticket_id)
                else:
                    self.log_test("Purchase Season Ticket", False, 
                                f"Purchase failed: {data.get('error')}")
            else:
                try:
                    error_data = response.json()
                    self.log_test("Purchase Season Ticket", False, 
                                f"HTTP {response.status_code}: {error_data.get('error', 'Unknown error')}")
                except:
                    self.log_test("Purchase Season Ticket", False, 
                                f"HTTP {response.status_code}: {response.text[:100]}")
                    
        except Exception as e:
            self.log_test("Purchase Season Ticket", False, f"Exception: {e}")
            
    def test_season_ticket_matches(self, season_ticket_id):
        """Test getting season ticket matches"""
        try:
            response = self.session.get(
                f"{BASE_URL}/api/season-ticket/{season_ticket_id}/matches"
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    matches = data.get('matches', [])
                    season_info = data.get('season_ticket', {})
                    self.log_test("Get Season Ticket Matches", True, 
                                f"Retrieved {len(matches)} matches for season '{season_info.get('season_name')}'", 
                                {'match_count': len(matches), 'season_info': season_info})
                else:
                    self.log_test("Get Season Ticket Matches", False, 
                                f"Failed to get matches: {data.get('error')}")
            else:
                try:
                    error_data = response.json()
                    self.log_test("Get Season Ticket Matches", False, 
                                f"HTTP {response.status_code}: {error_data.get('error', 'Unknown error')}")
                except:
                    self.log_test("Get Season Ticket Matches", False, 
                                f"HTTP {response.status_code}: Access denied or invalid season ticket")
                    
        except Exception as e:
            self.log_test("Get Season Ticket Matches", False, f"Exception: {e}")
            
    def test_accessibility(self):
        """Test accessibility accommodations"""
        print("\n♿ Testing Accessibility Accommodations...")
        
        # Test 1: Register accessibility needs
        try:
            accessibility_data = {
                'accommodation_type': 'wheelchair',
                'description': 'Full-time wheelchair user requiring accessible seating',
                'severity_level': 'severe',
                'requires_wheelchair_access': True,
                'requires_companion_seat': True,
                'requires_aisle_access': True,
                'mobility_equipment': 'electric wheelchair',
                'service_animal': False,
                'preferred_communication': 'email',
                'emergency_contact_name': 'John Doe',
                'emergency_contact_phone': '+61400123456'
            }
            
            headers = {
                'Content-Type': 'application/json',
                'X-CSRFToken': self.csrf_token
            } if self.csrf_token else {'Content-Type': 'application/json'}
            
            response = self.session.post(
                f"{BASE_URL}/api/accessibility/register",
                json=accessibility_data,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    accommodation_id = data.get('accommodation_id')
                    verification_required = data.get('verification_required', False)
                    self.log_test("Register Accessibility Needs", True, 
                                f"Accessibility needs registered (ID: {accommodation_id}). Verification required: {verification_required}", data)
                    
                    # Test 2: Book with accessibility accommodations
                    self.test_accessibility_booking()
                else:
                    self.log_test("Register Accessibility Needs", False, 
                                f"Registration failed: {data.get('error')}")
            else:
                try:
                    error_data = response.json()
                    self.log_test("Register Accessibility Needs", False, 
                                f"HTTP {response.status_code}: {error_data.get('error', 'Unknown error')}")
                except:
                    self.log_test("Register Accessibility Needs", False, 
                                f"HTTP {response.status_code}: {response.text[:100]}")
                    
        except Exception as e:
            self.log_test("Register Accessibility Needs", False, f"Exception: {e}")
            
    def test_accessibility_booking(self):
        """Test booking with accessibility accommodations"""
        try:
            booking_data = {
                'event_id': 1,  # Assuming event ID 1 exists
                'seat_ids': [3, 4],  # Assuming seats 3,4 exist and are available
                'requested_accommodations': [
                    'wheelchair_accessible_seating',
                    'companion_seat',
                    'aisle_access'
                ],
                'special_instructions': 'Please ensure clear pathway to seats for electric wheelchair'
            }
            
            headers = {
                'Content-Type': 'application/json',
                'X-CSRFToken': self.csrf_token
            } if self.csrf_token else {'Content-Type': 'application/json'}
            
            response = self.session.post(
                f"{BASE_URL}/api/accessibility/book",
                json=booking_data,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    booking_id = data.get('booking_id')
                    accessibility_booking_id = data.get('accessibility_booking_id')
                    total_amount = data.get('total_amount', 0)
                    self.log_test("Book with Accessibility", True, 
                                f"Accessibility booking created (ID: {booking_id}, Accessibility ID: {accessibility_booking_id}). Amount: ${total_amount:.2f}", data)
                    
                    # Test 3: Check accessibility status
                    self.test_accessibility_status(booking_id)
                else:
                    self.log_test("Book with Accessibility", False, 
                                f"Booking failed: {data.get('error')}")
            else:
                try:
                    error_data = response.json()
                    self.log_test("Book with Accessibility", False, 
                                f"HTTP {response.status_code}: {error_data.get('error', 'Unknown error')}")
                except:
                    self.log_test("Book with Accessibility", False, 
                                f"HTTP {response.status_code}: {response.text[:100]}")
                    
        except Exception as e:
            self.log_test("Book with Accessibility", False, f"Exception: {e}")
            
    def test_accessibility_status(self, booking_id):
        """Test getting accessibility status"""
        try:
            response = self.session.get(
                f"{BASE_URL}/api/accessibility/status/{booking_id}"
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    status = data.get('accommodation_status')
                    requested = data.get('requested_accommodations', [])
                    provided = data.get('provided_accommodations', [])
                    self.log_test("Get Accessibility Status", True, 
                                f"Status: {status}. Requested: {len(requested)} accommodations, Provided: {len(provided)}", 
                                {'status': status, 'requested_count': len(requested), 'provided_count': len(provided)})
                else:
                    self.log_test("Get Accessibility Status", False, 
                                f"Failed to get status: {data.get('error')}")
            else:
                try:
                    error_data = response.json()
                    self.log_test("Get Accessibility Status", False, 
                                f"HTTP {response.status_code}: {error_data.get('error', 'Unknown error')}")
                except:
                    self.log_test("Get Accessibility Status", False, 
                                f"HTTP {response.status_code}: Access denied or not found")
                    
        except Exception as e:
            self.log_test("Get Accessibility Status", False, f"Exception: {e}")
            
    def generate_test_report(self):
        """Generate and display test report"""
        print("\n" + "="*60)
        print("🧪 CRICVERSE NEW FEATURES TEST REPORT")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for test in self.test_results if test['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for test in self.test_results:
                if not test['success']:
                    print(f"  • {test['test']}: {test['message']}")
                    
        print("\n📋 Feature Summary:")
        features = {
            'Ticket Transfer': ['Initiate Ticket Transfer', 'Accept Ticket Transfer'],
            'Resale Marketplace': ['List Ticket for Resale', 'Search Marketplace'],
            'Season Tickets': ['Purchase Season Ticket', 'Get Season Ticket Matches'],
            'Accessibility': ['Register Accessibility Needs', 'Book with Accessibility', 'Get Accessibility Status']
        }
        
        for feature, tests in features.items():
            feature_results = [test for test in self.test_results if test['test'] in tests]
            passed = sum(1 for test in feature_results if test['success'])
            total = len(feature_results)
            status = "✅" if passed == total else "⚠️" if passed > 0 else "❌"
            print(f"  {status} {feature}: {passed}/{total} tests passed")
            
        print("\n" + "="*60)
        
    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting CricVerse New Features Test Suite...")
        print(f"🔗 Target URL: {BASE_URL}")
        print(f"👤 Test User: {TEST_EMAIL}")
        
        # Check if server is running
        try:
            response = requests.get(BASE_URL, timeout=5)
            if response.status_code != 200:
                print(f"❌ Server not responding properly (Status: {response.status_code})")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot connect to server: {e}")
            print("💁 Please make sure the CricVerse application is running on http://localhost:5000")
            return False
            
        print("✅ Server is running")
        
        # Login (optional - some endpoints work without auth)
        print("\n🔐 Attempting to login...")
        login_success = self.login()
        if not login_success:
            print("⚠️ Login failed - continuing with unauthenticated tests...")
            
        # Run all test suites
        self.test_ticket_transfer()
        self.test_marketplace()
        self.test_season_tickets()
        self.test_accessibility()
        
        # Generate report
        self.generate_test_report()
        
        return True

def main():
    """Main function"""
    print("🏏 CricVerse New Features Test Suite")
    print("Testing: Ticket Transfers, Marketplace, Season Tickets, Accessibility")
    print("-" * 70)
    
    test_suite = CricVerseTestSuite()
    success = test_suite.run_all_tests()
    
    if not success:
        sys.exit(1)
        
    # Exit with appropriate code
    failed_tests = sum(1 for test in test_suite.test_results if not test['success'])
    sys.exit(1 if failed_tests > 0 else 0)

if __name__ == "__main__":
    main()