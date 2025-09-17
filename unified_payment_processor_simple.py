"""
Simplified Payment Processor for Testing CricVerse New Features
This is a minimal implementation to allow testing of the new features
without complex payment processing dependencies.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class PaymentGateway(Enum):
    PAYPAL = "paypal"
    RAZORPAY = "razorpay"
    UPI = "upi"
    CARD = "card"

class Currency(Enum):
    USD = "USD"
    INR = "INR"
    AUD = "AUD"
    EUR = "EUR"

@dataclass
class UnifiedPaymentResponse:
    success: bool
    payment_id: Optional[str] = None
    gateway: Optional[PaymentGateway] = None
    amount: Optional[float] = None
    currency: Optional[Currency] = None
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    approval_url: Optional[str] = None

class UnifiedPaymentProcessor:
    """Simplified payment processor for testing"""
    
    def __init__(self):
        logger.info("💳 Simplified payment processor initialized for testing")
    
    def create_payment(self, amount: float, currency: str, payment_method: str, 
                      customer_email: str, metadata: Dict[str, Any]) -> UnifiedPaymentResponse:
        """Create a mock payment for testing"""
        try:
            # Generate mock payment ID
            import secrets
            payment_id = f"test_payment_{secrets.token_urlsafe(8)}"
            
            logger.info(f"💳 Mock payment created: {payment_id} for ${amount:.2f} {currency}")
            
            return UnifiedPaymentResponse(
                success=True,
                payment_id=payment_id,
                gateway=PaymentGateway.PAYPAL if payment_method == 'paypal' else PaymentGateway.RAZORPAY,
                amount=amount,
                currency=Currency(currency),
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"❌ Mock payment creation failed: {e}")
            return UnifiedPaymentResponse(
                success=False,
                error_message=str(e)
            )
    
    def verify_payment(self, payment_data: Dict[str, Any]) -> UnifiedPaymentResponse:
        """Verify a mock payment for testing"""
        try:
            payment_id = payment_data.get('payment_id') or payment_data.get('razorpay_payment_id')
            
            if payment_id and payment_id.startswith('test_payment_'):
                logger.info(f"✅ Mock payment verified: {payment_id}")
                return UnifiedPaymentResponse(
                    success=True,
                    payment_id=payment_id,
                    gateway=PaymentGateway.PAYPAL if 'paypal' in payment_data.get('gateway', '') else PaymentGateway.RAZORPAY
                )
            else:
                return UnifiedPaymentResponse(
                    success=False,
                    error_message="Invalid payment ID for testing"
                )
                
        except Exception as e:
            logger.error(f"❌ Mock payment verification failed: {e}")
            return UnifiedPaymentResponse(
                success=False,
                error_message=str(e)
            )
    
    def get_supported_methods(self, currency: str) -> list:
        """Get supported payment methods for currency"""
        if currency == 'INR':
            return ['razorpay', 'upi', 'card', 'netbanking']
        else:
            return ['paypal', 'card']
    
    def get_currency_for_country(self, country: str) -> str:
        """Get default currency for country"""
        currency_map = {
            'IN': 'INR',
            'US': 'USD',
            'AU': 'AUD',
            'GB': 'GBP'
        }
        return currency_map.get(country, 'USD')
    
    def process_successful_payment(self, payment_response: UnifiedPaymentResponse, metadata: Dict[str, Any]) -> bool:
        """Process a successful payment (mock implementation)"""
        logger.info(f"✅ Mock payment processing completed for {payment_response.payment_id}")
        return True

# Create global instance
unified_payment_processor = UnifiedPaymentProcessor()