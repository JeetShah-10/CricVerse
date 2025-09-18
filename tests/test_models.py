import unittest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestModels(unittest.TestCase):
    """Test cases for the database models."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        pass

    def tearDown(self):
        """Tear down test fixtures after each test method."""
        pass

    def test_customer_model_import(self):
        """Test Customer model import."""
        try:
            from app.models import Customer
            self.assertTrue(Customer is not None)
            print("✅ Customer model imported successfully")
        except Exception as e:
            self.fail(f"Customer model import failed: {e}")

    def test_seat_model_import(self):
        """Test Seat model import."""
        try:
            from app.models.booking import Seat
            self.assertTrue(Seat is not None)
            print("✅ Seat model imported successfully")
        except Exception as e:
            self.fail(f"Seat model import failed: {e}")

    def test_booking_model_import(self):
        """Test Booking model import."""
        try:
            from app.models.booking import Booking
            self.assertTrue(Booking is not None)
            print("✅ Booking model imported successfully")
        except Exception as e:
            self.fail(f"Booking model import failed: {e}")

    def test_ticket_model_import(self):
        """Test Ticket model import."""
        try:
            from app.models.booking import Ticket
            self.assertTrue(Ticket is not None)
            print("✅ Ticket model imported successfully")
        except Exception as e:
            self.fail(f"Ticket model import failed: {e}")

    def test_stadium_model_import(self):
        """Test Stadium model import."""
        try:
            from app.models.stadium import Stadium
            self.assertTrue(Stadium is not None)
            print("✅ Stadium model imported successfully")
        except Exception as e:
            self.fail(f"Stadium model import failed: {e}")

    def test_team_model_import(self):
        """Test Team model import."""
        try:
            from app.models.match import Team
            self.assertTrue(Team is not None)
            print("✅ Team model imported successfully")
        except Exception as e:
            self.fail(f"Team model import failed: {e}")

    def test_event_model_import(self):
        """Test Event model import."""
        try:
            from app.models.match import Event
            self.assertTrue(Event is not None)
            print("✅ Event model imported successfully")
        except Exception as e:
            self.fail(f"Event model import failed: {e}")

if __name__ == '__main__':
    unittest.main()