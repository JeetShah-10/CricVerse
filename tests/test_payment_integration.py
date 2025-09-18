import unittest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestPaymentIntegration(unittest.TestCase):
    """Test cases for payment processing integration."""

    def test_payment_model_import(self):
        """Test Payment model import."""
        try:
            from app.models.payment import Payment, PaymentTransaction
            self.assertTrue(Payment is not None)
            self.assertTrue(PaymentTransaction is not None)
            print("✅ Payment models imported successfully")
        except Exception as e:
            self.fail(f"Payment model import failed: {e}")

    def test_payment_creation(self):
        """Test Payment model creation."""
        try:
            from app.models.payment import Payment
            
            # Create a mock payment
            payment = Payment(
                booking_id=1,
                amount=150.0,
                payment_method="MockPayPal",
                transaction_id="MOCK_TXN_12345"
            )
            
            # Test that payment object is created
            self.assertEqual(payment.booking_id, 1)
            self.assertEqual(payment.amount, 150.0)
            self.assertEqual(payment.payment_method, "MockPayPal")
            self.assertEqual(payment.transaction_id, "MOCK_TXN_12345")
            
            print("✅ Payment model creation test passed")
        except Exception as e:
            self.fail(f"Payment model creation test failed: {e}")

    def test_payment_transaction_creation(self):
        """Test PaymentTransaction model creation."""
        try:
            from app.models.payment import PaymentTransaction
            
            # Create a mock payment transaction
            transaction = PaymentTransaction(
                payment_id=1,
                gateway="MockPayPal",
                gateway_transaction_id="MOCK_GATEWAY_TXN_12345",
                amount=150.0,
                currency="USD"
            )
            
            # Test that transaction object is created
            self.assertEqual(transaction.payment_id, 1)
            self.assertEqual(transaction.gateway, "MockPayPal")
            self.assertEqual(transaction.gateway_transaction_id, "MOCK_GATEWAY_TXN_12345")
            self.assertEqual(transaction.amount, 150.0)
            self.assertEqual(transaction.currency, "USD")
            
            print("✅ PaymentTransaction model creation test passed")
        except Exception as e:
            self.fail(f"PaymentTransaction model creation test failed: {e}")

    def test_capture_payment_function_import(self):
        """Test that capture payment function can be imported."""
        try:
            from app.services.booking_service import capture_payment_and_create_booking
            self.assertTrue(capture_payment_and_create_booking is not None)
            print("✅ Capture payment function imported successfully")
        except Exception as e:
            self.fail(f"Capture payment function import failed: {e}")

if __name__ == '__main__':
    unittest.main()