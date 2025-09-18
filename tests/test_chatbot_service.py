import unittest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestChatbotService(unittest.TestCase):
    """Test cases for the chatbot service."""

    def test_chatbot_import(self):
        """Test that the chatbot service can be imported."""
        try:
            # Test importing the simple chatbot service
            from app.services.chatbot_service_simple import ask_gemini
            self.assertTrue(True, "Chatbot service imported successfully")
            print("✅ Chatbot service imported successfully")
        except Exception as e:
            self.fail(f"Failed to import chatbot service: {e}")

    def test_basic_functionality(self):
        """Test basic chatbot functionality."""
        try:
            from app.services.chatbot_service_simple import ask_gemini
            
            # Test greeting
            result = ask_gemini("Hello")
            self.assertIsInstance(result, str)
            self.assertIn("Hello", result)
            
            # Test booking query
            result = ask_gemini("How can I book tickets?")
            self.assertIsInstance(result, str)
            self.assertIn("book", result.lower())
            
            # Test team query
            result = ask_gemini("Tell me about the teams")
            self.assertIsInstance(result, str)
            self.assertIn("team", result.lower())
            
            print("✅ Basic chatbot functionality test passed")
        except Exception as e:
            self.fail(f"Basic chatbot functionality test failed: {e}")

    def test_edge_cases(self):
        """Test edge cases for chatbot functionality."""
        try:
            from app.services.chatbot_service_simple import ask_gemini
            
            # Test empty message
            result = ask_gemini("")
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 0)
            
            # Test special characters
            result = ask_gemini("!@#$%^&*()")
            self.assertIsInstance(result, str)
            
            print("✅ Edge cases test passed")
        except Exception as e:
            self.fail(f"Edge cases test failed: {e}")

if __name__ == '__main__':
    unittest.main()