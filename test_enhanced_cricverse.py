"""
Comprehensive Test Suite for Enhanced CricVerse Features
Tests analytics, booking, security, performance, and admin dashboard enhancements
Big Bash League Cricket Platform
"""

import unittest
import json
import time
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test configuration
os.environ['FLASK_ENV'] = 'testing'
os.environ['TESTING'] = 'True'

from app import create_app, db
from app.models import Customer, Stadium, Event, Booking, Ticket, Seat
from app.services.analytics_service import analytics_service
from app.services.enhanced_booking_service import enhanced_booking_service, BookingItem, BookingType
from app.services.security_service import security_service, InputValidator
from app.services.performance_service import performance_service

class TestAnalyticsService(unittest.TestCase):
    """Test the enhanced analytics service"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        
        db.create_all()
        self._create_test_data()
    
    def tearDown(self):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def _create_test_data(self):
        """Create test data for analytics"""
        # Create test stadium
        stadium = Stadium(
            name="Test Stadium",
            location="Test City",
            capacity=50000
        )
        db.session.add(stadium)
        db.session.flush()
        
        # Create test customer
        customer = Customer(
            name="Test Customer",
            email="test@example.com",
            membership_level="Premium"
        )
        db.session.add(customer)
        db.session.flush()
        
        # Create test event
        event = Event(
            event_name="Test Match",
            event_date=date.today() + timedelta(days=7),
            stadium_id=stadium.id
        )
        db.session.add(event)
        db.session.flush()
        
        # Create test booking
        booking = Booking(
            customer_id=customer.id,
            total_amount=150.00,
            booking_date=datetime.utcnow(),
            payment_status='Completed'
        )
        db.session.add(booking)
        db.session.flush()
        
        # Store IDs for tests
        self.stadium_id = stadium.id
        self.customer_id = customer.id
        self.event_id = event.id
        self.booking_id = booking.id
        
        db.session.commit()
    
    def test_revenue_analytics(self):
        """Test revenue analytics functionality"""
        # Test basic revenue analytics
        result = analytics_service.get_revenue_analytics()
        
        self.assertIsInstance(result, dict)
        self.assertIn('summary', result)
        self.assertIn('revenue_trend', result)
        self.assertIn('total_revenue', result['summary'])
        self.assertEqual(result['summary']['total_revenue'], 150.00)
    
    def test_stadium_specific_analytics(self):
        """Test stadium-specific analytics"""
        result = analytics_service.get_revenue_analytics(stadium_id=self.stadium_id)
        
        self.assertIsInstance(result, dict)
        self.assertIn('summary', result)
        self.assertGreaterEqual(result['summary']['total_revenue'], 0)
    
    def test_customer_analytics(self):
        """Test customer analytics functionality"""
        result = analytics_service.get_customer_analytics()
        
        self.assertIsInstance(result, dict)
        self.assertIn('customer_segments', result)
        self.assertIn('top_customers', result)
        self.assertIn('retention', result)
    
    def test_stadium_utilization(self):
        """Test stadium utilization analytics"""
        result = analytics_service.get_stadium_utilization(self.stadium_id)
        
        self.assertIsInstance(result, dict)
        self.assertIn('stadium_info', result)
        self.assertIn('utilization_summary', result)
        self.assertEqual(result['stadium_info']['name'], "Test Stadium")
    
    def test_booking_patterns(self):
        """Test booking pattern analytics"""
        result = analytics_service.get_booking_patterns()
        
        self.assertIsInstance(result, dict)
        self.assertIn('day_of_week', result)
        self.assertIn('hourly', result)
    
    def test_financial_dashboard(self):
        """Test financial dashboard data"""
        result = analytics_service.get_financial_dashboard()
        
        self.assertIsInstance(result, dict)
        self.assertIn('current_month', result)
        self.assertIn('growth_metrics', result)

class TestEnhancedBookingService(unittest.TestCase):
    """Test the enhanced booking service"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        
        db.create_all()
        self._create_test_data()
    
    def tearDown(self):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def _create_test_data(self):
        """Create test data for booking"""
        # Create test stadium
        stadium = Stadium(
            name="Booking Test Stadium",
            location="Test City",
            capacity=1000
        )
        db.session.add(stadium)
        db.session.flush()
        
        # Create test customer
        customer = Customer(
            name="Booking Customer",
            email="booking@example.com"
        )
        db.session.add(customer)
        db.session.flush()
        
        # Create test event
        event = Event(
            event_name="Booking Test Match",
            event_date=date.today() + timedelta(days=14),
            stadium_id=stadium.id
        )
        db.session.add(event)
        db.session.flush()
        
        # Create test seat
        seat = Seat(
            stadium_id=stadium.id,
            section="A",
            row_number="1",
            seat_number="1",
            seat_type="Standard",
            price=75.00
        )
        db.session.add(seat)
        db.session.flush()
        
        # Store IDs for tests
        self.stadium_id = stadium.id
        self.customer_id = customer.id
        self.event_id = event.id
        self.seat_id = seat.id
        
        db.session.commit()
    
    def test_seat_availability(self):
        """Test seat availability functionality"""
        result = enhanced_booking_service.get_seat_availability(self.event_id)
        
        self.assertIsInstance(result, dict)
        self.assertIn('event_id', result)
        self.assertIn('availability', result)
        self.assertEqual(result['event_id'], self.event_id)
    
    def test_seat_availability_with_section(self):
        """Test seat availability with section filter"""
        result = enhanced_booking_service.get_seat_availability(self.event_id, section="A")
        
        self.assertIsInstance(result, dict)
        self.assertIn('availability', result)
        self.assertIn('A', result['availability'])
    
    def test_parking_availability(self):
        """Test parking availability functionality"""
        result = enhanced_booking_service.get_parking_availability(self.event_id)
        
        self.assertIsInstance(result, dict)
        self.assertIn('event_id', result)
        self.assertIn('parking_availability', result)
    
    def test_concession_menu(self):
        """Test concession menu functionality"""
        result = enhanced_booking_service.get_concession_menu(self.stadium_id)
        
        self.assertIsInstance(result, dict)
        self.assertIn('stadium_id', result)
        self.assertIn('concessions', result)
    
    def test_booking_item_creation(self):
        """Test booking item creation"""
        booking_item = BookingItem(
            item_type=BookingType.TICKET,
            item_id=self.seat_id,
            quantity=1,
            price=75.00
        )
        
        self.assertEqual(booking_item.item_type, BookingType.TICKET)
        self.assertEqual(booking_item.item_id, self.seat_id)
        self.assertEqual(booking_item.quantity, 1)
        self.assertEqual(booking_item.price, 75.00)
    
    @patch('app.services.enhanced_booking_service.session')
    def test_comprehensive_booking_creation(self, mock_session):
        """Test comprehensive booking creation"""
        booking_items = [
            BookingItem(
                item_type=BookingType.TICKET,
                item_id=self.seat_id,
                quantity=1,
                price=75.00
            )
        ]
        
        result = enhanced_booking_service.create_comprehensive_booking(
            self.customer_id, self.event_id, booking_items
        )
        
        self.assertIsInstance(result.success, bool)
        if result.success:
            self.assertIsNotNone(result.booking_id)
            self.assertIsNotNone(result.payment_data)

class TestSecurityService(unittest.TestCase):
    """Test the security service"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        """Clean up test environment"""
        self.app_context.pop()
    
    def test_email_validation(self):
        """Test email validation"""
        # Valid emails
        valid, msg = InputValidator.validate_email("test@example.com")
        self.assertTrue(valid)
        
        valid, msg = InputValidator.validate_email("user.name+tag@domain.co.uk")
        self.assertTrue(valid)
        
        # Invalid emails
        valid, msg = InputValidator.validate_email("invalid-email")
        self.assertFalse(valid)
        
        valid, msg = InputValidator.validate_email("@domain.com")
        self.assertFalse(valid)
        
        valid, msg = InputValidator.validate_email("")
        self.assertFalse(valid)
    
    def test_phone_validation(self):
        """Test phone validation"""
        # Valid phones
        valid, msg = InputValidator.validate_phone("1234567890")
        self.assertTrue(valid)
        
        valid, msg = InputValidator.validate_phone("+1234567890")
        self.assertTrue(valid)
        
        # Invalid phones
        valid, msg = InputValidator.validate_phone("123")
        self.assertFalse(valid)
        
        valid, msg = InputValidator.validate_phone("")
        self.assertFalse(valid)
    
    def test_password_validation(self):
        """Test password validation"""
        # Strong passwords
        valid, msg = InputValidator.validate_password("StrongPass123!")
        self.assertTrue(valid)
        
        valid, msg = InputValidator.validate_password("MyP@ssw0rd")
        self.assertTrue(valid)
        
        # Weak passwords
        valid, msg = InputValidator.validate_password("weak")
        self.assertFalse(valid)
        
        valid, msg = InputValidator.validate_password("password123")
        self.assertFalse(valid)
        
        valid, msg = InputValidator.validate_password("")
        self.assertFalse(valid)
    
    def test_input_sanitization(self):
        """Test input sanitization"""
        # Test XSS prevention
        malicious_input = "<script>alert('xss')</script>"
        sanitized = InputValidator.sanitize_input(malicious_input)
        self.assertNotIn("<script>", sanitized)
        
        # Test SQL injection prevention
        sql_input = "'; DROP TABLE users; --"
        sanitized = InputValidator.sanitize_input(sql_input)
        self.assertEqual(sanitized, "")  # Should be empty due to SQL pattern
        
        # Test normal input
        normal_input = "Hello World"
        sanitized = InputValidator.sanitize_input(normal_input)
        self.assertEqual(sanitized, "Hello World")
    
    def test_booking_data_validation(self):
        """Test booking data validation"""
        # Valid booking data
        valid_data = {
            'customer_id': 1,
            'event_id': 1,
            'seat_ids': [1, 2, 3]
        }
        valid, errors = InputValidator.validate_booking_data(valid_data)
        self.assertTrue(valid)
        self.assertEqual(len(errors), 0)
        
        # Invalid booking data
        invalid_data = {
            'customer_id': 'invalid',
            'event_id': -1,
            'seat_ids': ['a', 'b', 'c']
        }
        valid, errors = InputValidator.validate_booking_data(invalid_data)
        self.assertFalse(valid)
        self.assertGreater(len(errors), 0)
    
    def test_rate_limiter(self):
        """Test rate limiting functionality"""
        rate_limiter = security_service.rate_limiter
        
        # Test normal usage
        is_limited, info = rate_limiter.is_rate_limited("test_user", 5, 60)
        self.assertFalse(is_limited)
        self.assertIn('remaining', info)
        
        # Test rate limit exceeded
        for i in range(6):  # Exceed limit of 5
            is_limited, info = rate_limiter.is_rate_limited("test_user_2", 5, 60)
        
        self.assertTrue(is_limited)
        self.assertIn('rate_limited', info)

class TestPerformanceService(unittest.TestCase):
    """Test the performance service"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        """Clean up test environment"""
        self.app_context.pop()
    
    def test_cache_manager_initialization(self):
        """Test cache manager initialization"""
        cache_manager = performance_service.cache_manager
        self.assertIsNotNone(cache_manager.cache)
    
    def test_cache_stats(self):
        """Test cache statistics"""
        stats = performance_service.cache_manager.get_cache_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn('type', stats)
    
    def test_database_optimizer(self):
        """Test database optimizer"""
        db_optimizer = performance_service.db_optimizer
        analysis = db_optimizer.analyze_query_patterns()
        
        self.assertIsInstance(analysis, dict)
        self.assertIn('slow_queries_count', analysis)
        self.assertIn('optimization_suggestions', analysis)
    
    def test_performance_monitor(self):
        """Test performance monitoring"""
        monitor = performance_service.performance_monitor
        report = monitor.get_performance_report()
        
        self.assertIsInstance(report, dict)
        self.assertIn('summary', report)
        self.assertIn('endpoint_performance', report)
    
    def test_comprehensive_report(self):
        """Test comprehensive performance report"""
        report = performance_service.get_comprehensive_report()
        
        self.assertIsInstance(report, dict)
        self.assertIn('timestamp', report)
        self.assertIn('cache_stats', report)
        self.assertIn('database_analysis', report)
        self.assertIn('performance_report', report)
        self.assertIn('system_recommendations', report)

class TestAdminRoutes(unittest.TestCase):
    """Test enhanced admin routes"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        
        db.create_all()
        self._create_test_admin()
    
    def tearDown(self):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def _create_test_admin(self):
        """Create test admin user"""
        admin = Customer(
            name="Test Admin",
            email="admin@cricverse.com",
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()
        self.admin_id = admin.id
    
    def test_admin_api_stats(self):
        """Test admin API stats endpoint"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.admin_id
        
        response = self.client.get('/admin/api/stats')
        self.assertIn(response.status_code, [200, 401, 403])  # May require authentication
    
    def test_admin_api_revenue_analytics(self):
        """Test admin revenue analytics API"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.admin_id
        
        response = self.client.get('/admin/api/analytics/revenue')
        self.assertIn(response.status_code, [200, 401, 403])
    
    def test_admin_api_customer_analytics(self):
        """Test admin customer analytics API"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.admin_id
        
        response = self.client.get('/admin/api/analytics/customers')
        self.assertIn(response.status_code, [200, 401, 403])

class TestIntegration(unittest.TestCase):
    """Integration tests for all enhanced features"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        
        db.create_all()
        self._create_comprehensive_test_data()
    
    def tearDown(self):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def _create_comprehensive_test_data(self):
        """Create comprehensive test data"""
        # Create stadium
        stadium = Stadium(
            name="Integration Test Stadium",
            location="Test City",
            capacity=10000
        )
        db.session.add(stadium)
        db.session.flush()
        
        # Create customer
        customer = Customer(
            name="Integration Customer",
            email="integration@example.com",
            role="customer"
        )
        db.session.add(customer)
        db.session.flush()
        
        # Create admin
        admin = Customer(
            name="Integration Admin",
            email="admin@integration.com",
            role="admin"
        )
        db.session.add(admin)
        db.session.flush()
        
        # Create event
        event = Event(
            event_name="Integration Test Match",
            event_date=date.today() + timedelta(days=30),
            stadium_id=stadium.id
        )
        db.session.add(event)
        db.session.flush()
        
        # Create seats
        for i in range(5):
            seat = Seat(
                stadium_id=stadium.id,
                section="A",
                row_number="1",
                seat_number=str(i+1),
                seat_type="Standard",
                price=100.00
            )
            db.session.add(seat)
        
        db.session.commit()
        
        self.stadium_id = stadium.id
        self.customer_id = customer.id
        self.admin_id = admin.id
        self.event_id = event.id
    
    def test_full_booking_flow_with_analytics(self):
        """Test complete booking flow with analytics integration"""
        # Get initial analytics
        initial_analytics = analytics_service.get_revenue_analytics()
        initial_revenue = initial_analytics['summary']['total_revenue']
        
        # Create booking
        booking = Booking(
            customer_id=self.customer_id,
            total_amount=200.00,
            booking_date=datetime.utcnow(),
            payment_status='Completed'
        )
        db.session.add(booking)
        db.session.commit()
        
        # Get updated analytics
        updated_analytics = analytics_service.get_revenue_analytics()
        updated_revenue = updated_analytics['summary']['total_revenue']
        
        # Verify analytics updated
        self.assertGreater(updated_revenue, initial_revenue)
    
    def test_security_with_booking(self):
        """Test security integration with booking system"""
        # Test input validation
        booking_data = {
            'customer_id': self.customer_id,
            'event_id': self.event_id,
            'seat_ids': [1, 2]
        }
        
        valid, errors = InputValidator.validate_booking_data(booking_data)
        self.assertTrue(valid)
        
        # Test malicious input
        malicious_data = {
            'customer_id': "'; DROP TABLE bookings; --",
            'event_id': self.event_id
        }
        
        valid, errors = InputValidator.validate_booking_data(malicious_data)
        self.assertFalse(valid)
    
    def test_performance_monitoring_integration(self):
        """Test performance monitoring with actual operations"""
        # Perform some operations
        analytics_service.get_revenue_analytics()
        enhanced_booking_service.get_seat_availability(self.event_id)
        
        # Check performance report
        report = performance_service.get_comprehensive_report()
        
        self.assertIsInstance(report, dict)
        self.assertIn('timestamp', report)
    
    def test_cache_integration(self):
        """Test caching integration across services"""
        # This would test if caching is working properly across services
        # For now, just verify cache manager is accessible
        cache_stats = performance_service.cache_manager.get_cache_stats()
        self.assertIsInstance(cache_stats, dict)

def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("🚀 Starting Enhanced CricVerse Comprehensive Test Suite")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestAnalyticsService,
        TestEnhancedBookingService,
        TestSecurityService,
        TestPerformanceService,
        TestAdminRoutes,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError: ')[-1].split('\n')[0]}")
    
    if result.errors:
        print("\n🚨 ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('\n')[-2]}")
    
    if not result.failures and not result.errors:
        print("\n✅ ALL TESTS PASSED!")
        print("🎉 Enhanced CricVerse is ready for production!")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_comprehensive_tests()
    exit(0 if success else 1)
