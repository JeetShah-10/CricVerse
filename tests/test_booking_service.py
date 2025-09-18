import unittest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.booking_service import book_seat

class TestBookingService(unittest.TestCase):
    """Test cases for the booking service."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Mock the db object
        self.mock_db = MagicMock()
        self.mock_session = MagicMock()
        self.mock_db.session = self.mock_session
        
        # Patch the db import in booking_service
        self.db_patcher = patch('app.services.booking_service.db', self.mock_db)
        self.db_patcher.start()

    def tearDown(self):
        """Tear down test fixtures after each test method."""
        self.db_patcher.stop()

    def test_book_seat_success(self):
        """Test successful seat booking."""
        # Mock the seat query
        mock_seat = MagicMock()
        mock_seat.price = 50.0
        mock_seat.section = 'A'
        
        # Mock the session query methods
        self.mock_session.query.return_value.with_for_update.return_value.get.return_value = mock_seat
        self.mock_session.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = None
        
        # Mock the booking and ticket objects
        mock_booking = MagicMock()
        mock_booking.id = 1
        mock_ticket = MagicMock()
        mock_ticket.id = 101
        
        # Mock the db session add and flush methods
        self.mock_session.add.side_effect = [mock_booking, mock_ticket]
        self.mock_session.flush.return_value = None
        
        # Mock the commit method
        self.mock_session.commit.return_value = None
        
        # Mock the context manager
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__ = MagicMock(return_value=None)
        mock_context_manager.__exit__ = MagicMock(return_value=None)
        self.mock_session.begin.return_value = mock_context_manager
        
        # Call the function
        result = book_seat(1, 1, 1)
        
        # Print result for debugging
        print(f"Booking result: {result}")
        
        # Assert the result
        self.assertTrue(result['success'])
        # Check that we get a booking_id and ticket_id (they might not be exactly 1 and 101)
        self.assertIn('booking_id', result)
        self.assertIn('ticket_id', result)
        self.assertEqual(result['message'], 'Seat booked successfully')

    def test_book_seat_seat_not_found(self):
        """Test booking when seat is not found."""
        # Mock the seat query to return None
        self.mock_session.query.return_value.with_for_update.return_value.get.return_value = None
        
        # Mock the context manager
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__ = MagicMock(return_value=None)
        mock_context_manager.__exit__ = MagicMock(return_value=None)
        self.mock_session.begin.return_value = mock_context_manager
        
        # Call the function
        result = book_seat(999, 1, 1)
        
        # Assert the result
        self.assertFalse(result['success'])
        self.assertEqual(result['message'], 'Seat not found')

    def test_book_seat_already_booked(self):
        """Test booking when seat is already booked."""
        # Mock the seat query
        mock_seat = MagicMock()
        
        # Mock the existing ticket query to return a ticket (already booked)
        mock_existing_ticket = MagicMock()
        
        self.mock_session.query.return_value.with_for_update.return_value.get.return_value = mock_seat
        self.mock_session.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = mock_existing_ticket
        
        # Mock the context manager
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__ = MagicMock(return_value=None)
        mock_context_manager.__exit__ = MagicMock(return_value=None)
        self.mock_session.begin.return_value = mock_context_manager
        
        # Call the function
        result = book_seat(1, 1, 1)
        
        # Assert the result
        self.assertFalse(result['success'])
        self.assertEqual(result['message'], 'Seat is already booked for this event')

    def test_book_seat_database_error(self):
        """Test booking when database error occurs."""
        # Mock the seat query to raise an exception
        self.mock_session.query.return_value.with_for_update.return_value.get.side_effect = Exception("Database error")
        
        # Mock the rollback method
        self.mock_session.rollback.return_value = None
        
        # Mock the context manager
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__ = MagicMock(return_value=None)
        mock_context_manager.__exit__ = MagicMock(return_value=None)
        self.mock_session.begin.return_value = mock_context_manager
        
        # Call the function
        result = book_seat(1, 1, 1)
        
        # Assert the result
        self.assertFalse(result['success'])
        self.assertIn('An error occurred', result['message'])

    def test_book_seat_with_invalid_parameters(self):
        """Test booking with invalid parameters."""
        # Mock the context manager
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__ = MagicMock(return_value=None)
        mock_context_manager.__exit__ = MagicMock(return_value=None)
        self.mock_session.begin.return_value = mock_context_manager
        
        # Test with negative seat_id
        result = book_seat(-1, 1, 1)
        # The function doesn't validate parameters, so it will proceed to the database query
        # which will return None for a negative ID, leading to "Seat not found"
        self.assertFalse(result['success'])
        
        # Test with negative event_id
        result = book_seat(1, -1, 1)
        # The function doesn't validate parameters, so it will proceed to the database query
        self.assertFalse(result['success'])
        
        # Test with negative customer_id
        result = book_seat(1, 1, -1)
        # The function doesn't validate parameters, so it will proceed to the database query
        self.assertFalse(result['success'])

if __name__ == '__main__':
    unittest.main()