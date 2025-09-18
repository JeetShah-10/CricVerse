import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestAppInitialization(unittest.TestCase):
    """Test cases for application initialization."""

    def test_app_factory_import(self):
        """Test that the application factory can be imported."""
        try:
            from app import create_app
            self.assertTrue(True)  # Import successful
        except Exception as e:
            self.fail(f"Failed to import application factory: {e}")

    def test_config_import(self):
        """Test that the configuration can be imported."""
        try:
            from config import Config
            self.assertTrue(True)  # Import successful
        except Exception as e:
            self.fail(f"Failed to import configuration: {e}")

if __name__ == '__main__':
    unittest.main()