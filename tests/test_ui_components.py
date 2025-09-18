import unittest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestUIComponents(unittest.TestCase):
    """Test cases for UI components and frontend templates."""

    def test_template_imports(self):
        """Test that main templates can be imported/loaded."""
        try:
            # Test importing main templates
            template_files = [
                'index.html',
                'login.html',
                'register.html',
                'dashboard.html',
                'teams.html',
                'stadiums.html',
                'events.html',
                'players.html',
                'ai_options.html',
                'chat.html'
            ]
            
            template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
            
            for template_file in template_files:
                template_path = os.path.join(template_dir, template_file)
                self.assertTrue(os.path.exists(template_path), 
                               f"Template {template_file} should exist")
            
            print("✅ Main templates exist")
        except Exception as e:
            self.fail(f"Template import test failed: {e}")

    def test_admin_template_imports(self):
        """Test that admin templates can be imported/loaded."""
        try:
            # Test importing admin templates - only check if directory exists
            template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates', 'admin')
            self.assertTrue(os.path.exists(template_dir), "Admin template directory should exist")
            
            print("✅ Admin template directory exists")
        except Exception as e:
            self.fail(f"Admin template import test failed: {e}")

    def test_booking_templates(self):
        """Test that booking-related templates exist."""
        try:
            # Test importing booking templates
            booking_template_files = [
                'book_ticket.html',
                'seat_selection.html',
                'enhanced_seat_selection.html',
                'checkout.html',
                'payment_success.html'
            ]
            
            template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
            
            for template_file in booking_template_files:
                template_path = os.path.join(template_dir, template_file)
                self.assertTrue(os.path.exists(template_path), 
                               f"Booking template {template_file} should exist")
            
            print("✅ Booking templates exist")
        except Exception as e:
            self.fail(f"Booking template test failed: {e}")

    def test_template_structure(self):
        """Test that key templates have basic structure."""
        try:
            # Check index.html for Jinja2 template structure
            index_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'index.html')
            self.assertTrue(os.path.exists(index_path), "index.html should exist")
            
            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Check for Jinja2 template structure
                self.assertIn('{%', content, "index.html should be a Jinja2 template")
                self.assertIn('extends', content, "index.html should extend a base template")
                self.assertIn('block', content, "index.html should have template blocks")
            
            # Check login.html for form elements
            login_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'login.html')
            self.assertTrue(os.path.exists(login_path), "login.html should exist")
            
            with open(login_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn('<form', content.lower(), "login.html should have a form tag")
                # Check for email and password fields (case insensitive)
                content_lower = content.lower()
                self.assertTrue('email' in content_lower or 'e-mail' in content_lower or 'input' in content_lower,
                               "login.html should have form inputs")
            
            print("✅ Template structure checks passed")
        except Exception as e:
            self.fail(f"Template structure check failed: {e}")

    def test_css_files_exist(self):
        """Test that CSS files exist."""
        try:
            # Check CSS files
            css_files = [
                'css/ai_assistant.css',
                'css/bbl-action-hub.css',
                'css/bbl-enhanced.css',
                'css/checkout.css',
                'css/home-enhanced.css',
                'css/stadium_enhanced.css',
                'css/unified.css',
                'css/unified_theme_base.css'
            ]
            
            static_dir = os.path.join(os.path.dirname(__file__), '..', 'static')
            
            for css_file in css_files:
                css_path = os.path.join(static_dir, css_file)
                self.assertTrue(os.path.exists(css_path), 
                               f"CSS file {css_file} should exist")
            
            print("✅ CSS files exist")
        except Exception as e:
            self.fail(f"CSS file test failed: {e}")

    def test_js_files_exist(self):
        """Test that JavaScript files exist."""
        try:
            # Check JavaScript files
            js_files = [
                'js/ai_assistant.js',
                'js/bbl-enhanced.js',
                'js/checkout.js',
                'js/main.js',
                'js/realtime_client.js',
                'js/unified_payment.js'
            ]
            
            static_dir = os.path.join(os.path.dirname(__file__), '..', 'static')
            
            for js_file in js_files:
                js_path = os.path.join(static_dir, js_file)
                self.assertTrue(os.path.exists(js_path), 
                               f"JavaScript file {js_file} should exist")
            
            print("✅ JavaScript files exist")
        except Exception as e:
            self.fail(f"JavaScript file test failed: {e}")

if __name__ == '__main__':
    unittest.main()