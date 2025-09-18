import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestSimple(unittest.TestCase):
    """Simple test cases."""

    def test_import_booking_service(self):
        """Test that the booking service can be imported."""
        try:
            from app.services.booking_service import book_seat
            self.assertTrue(True)  # Import successful
        except Exception as e:
            self.fail(f"Failed to import booking service: {e}")

    def test_import_chatbot_service(self):
        """Test that the chatbot service can be imported."""
        try:
            from app.services.chatbot_service import ask_gemini
            self.assertTrue(True)  # Import successful
        except Exception as e:
            self.fail(f"Failed to import chatbot service: {e}")

if __name__ == '__main__':
    unittest.main()