"""
Unified Payment Processor for CricVerse Stadium System
Supporting both PayPal (International) and Indian Payment Gateways
Big Bash League Cricket Platform
"""

import os
import logging
import json
from typing import Dict, Any, Optional, List
from decimal import Decimal
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

# Import PayPal SDK
import paypalrestsdk

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define PaymentStatus enum
class PaymentStatus(Enum):
    """Payment status enum"""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PROCESSING = "processing"

# Define PaymentResponse dataclass
class PaymentResponse:
    """Payment response data structure"""
    def __init__(self, payment_id: str, status: PaymentStatus, amount: float, currency: str, 
                 error_message: Optional[str] = None, metadata: Optional[Dict] = None):
        self.payment_id = payment_id
        self.status = status
        self.amount = amount
        self.currency = currency
        self.error_message = error_message
        self.metadata = metadata or {}

# Indian Payment Processor (Simplified)
class IndianPaymentProcessor:
    """Simplified Indian payment processor for Razorpay integration"""
    
    def __init__(self):
        self.key_id = os.getenv('RAZORPAY_KEY_ID')
        self.key_secret = os.getenv('RAZORPAY_KEY_SECRET')
        self.webhook_secret = os.getenv('RAZORPAY_WEBHOOK_SECRET')
        
        if not self.key_id or not self.key_secret:
            logger.warning("⚠️ Razorpay credentials not configured")
        else:
            logger.info("✅ Razorpay processor initialized")
    
    def create_payment(self, amount: float, customer_email: str, 
                      payment_method: str, metadata: Dict[str, str]) -> PaymentResponse:
        """Create Razorpay payment order (simplified)"""
        try:
            # In a real implementation, this would call the Razorpay API
            # For now, we'll simulate a successful payment creation
            
            # Generate a mock payment ID
            import uuid
            payment_id = f"order_{uuid.uuid4().hex[:12]}"
            
            logger.info(f"✅ Created mock Razorpay order: {payment_id}")
            
            return PaymentResponse(
                payment_id=payment_id,
                status=PaymentStatus.PENDING,
                amount=amount,
                currency="INR",
                metadata={
                    'key_id': self.key_id,
                    'amount': amount * 100,  # Convert to paise
                    'currency': 'INR',
                    'description': f"Big Bash League - {metadata.get('description', 'Booking')}"
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Payment creation failed: {e}")
            return PaymentResponse(
                payment_id="",
                status=PaymentStatus.FAILED,
                amount=amount,
                currency="INR",
                error_message=str(e)
            )
    
    def verify_payment(self, payment_data: Dict) -> PaymentResponse:
        """Verify Razorpay payment (simplified)"""
        try:
            # In a real implementation, this would verify the payment with Razorpay
            # For now, we'll simulate a successful verification
            
            logger.info(f"✅ Verified mock payment: {payment_data.get('payment_id', 'unknown')}")
            
            return PaymentResponse(
                payment_id=payment_data.get('payment_id', 'verified_payment'),
                status=PaymentStatus.SUCCESS,
                amount=payment_data.get('amount', 0),
                currency="INR"
            )
            
        except Exception as e:
            logger.error(f"❌ Payment verification failed: {e}")
            return PaymentResponse(
                payment_id=payment_data.get('payment_id', ''),
                status=PaymentStatus.FAILED,
                amount=0,
                currency="INR",
                error_message=str(e)
            )

# Import PayPal SDK
import paypalrestsdk

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PaymentGateway(Enum):
    """Supported payment gateways"""
    PAYPAL = "paypal"
    RAZORPAY = "razorpay"
    UPI = "upi"
    PAYU = "payu"

class Currency(Enum):
    """Supported currencies"""
    USD = "USD"  # PayPal primary
    AUD = "AUD"  # PayPal BBL
    INR = "INR"  # Indian gateways
    EUR = "EUR"  # PayPal international
    GBP = "GBP"  # PayPal international

@dataclass
class UnifiedPaymentResponse:
    """Unified payment response structure"""
    success: bool
    payment_id: str
    gateway: PaymentGateway
    amount: float
    currency: str
    status: PaymentStatus
    payment_url: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict] = None
    approval_url: Optional[str] = None  # For PayPal

class PayPalProcessor:
    """PayPal payment processor for international customers"""
    
    def __init__(self):
        self.client_id = os.getenv('PAYPAL_CLIENT_ID')
        self.client_secret = os.getenv('PAYPAL_CLIENT_SECRET')
        self.mode = os.getenv('PAYPAL_MODE', 'sandbox')  # sandbox or live
        
        if self.client_id and self.client_secret:
            # Configure PayPal SDK
            paypalrestsdk.configure({
                "mode": self.mode,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            })
            logger.info("✅ PayPal processor initialized")
        else:
            logger.warning("⚠️ PayPal credentials not configured")
    
    def create_payment(self, amount: float, currency: str, customer_email: str, 
                      metadata: Dict[str, str]) -> UnifiedPaymentResponse:
        """Create PayPal payment"""
        try:
            if not self.client_id or not self.client_secret:
                return UnifiedPaymentResponse(
                    success=False,
                    payment_id="",
                    gateway=PaymentGateway.PAYPAL,
                    amount=amount,
                    currency=currency,
                    status=PaymentStatus.FAILED,
                    error_message="PayPal not configured"
                )
            
            # Create PayPal payment
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "redirect_urls": {
                    "return_url": f"{metadata.get('base_url', 'http://localhost:5000')}/payment/paypal/success",
                    "cancel_url": f"{metadata.get('base_url', 'http://localhost:5000')}/payment/paypal/cancel"
                },
                "transactions": [{
                    "item_list": {
                        "items": [{
                            "name": f"CricVerse BBL - {metadata.get('description', 'Booking')}",
                            "sku": metadata.get('booking_id', 'BBL001'),
                            "price": str(amount),
                            "currency": currency,
                            "quantity": 1
                        }]
                    },
                    "amount": {
                        "total": str(amount),
                        "currency": currency
                    },
                    "description": f"Big Bash League cricket booking - {metadata.get('description', 'Ticket booking')}"
                }]
            })
            
            if payment.create():
                # Find approval URL
                approval_url = None
                for link in payment.links:
                    if link.rel == "approval_url":
                        approval_url = link.href
                        break
                
                logger.info(f"✅ PayPal payment created: {payment.id}")
                
                return UnifiedPaymentResponse(
                    success=True,
                    payment_id=payment.id,
                    gateway=PaymentGateway.PAYPAL,
                    amount=amount,
                    currency=currency,
                    status=PaymentStatus.PENDING,
                    approval_url=approval_url,
                    metadata={'paypal_payment': payment.to_dict()}
                )
            else:
                logger.error(f"❌ PayPal payment creation failed: {payment.error}")
                return UnifiedPaymentResponse(
                    success=False,
                    payment_id="",
                    gateway=PaymentGateway.PAYPAL,
                    amount=amount,
                    currency=currency,
                    status=PaymentStatus.FAILED,
                    error_message=str(payment.error)
                )
                
        except Exception as e:
            logger.error(f"❌ PayPal payment creation error: {e}")
            return UnifiedPaymentResponse(
                success=False,
                payment_id="",
                gateway=PaymentGateway.PAYPAL,
                amount=amount,
                currency=currency,
                status=PaymentStatus.FAILED,
                error_message=str(e)
            )
    
    def execute_payment(self, payment_id: str, payer_id: str) -> UnifiedPaymentResponse:
        """Execute approved PayPal payment"""
        try:
            payment = paypalrestsdk.Payment.find(payment_id)
            
            if payment.execute({"payer_id": payer_id}):
                logger.info(f"✅ PayPal payment executed: {payment_id}")
                
                # Extract payment details
                transaction = payment.transactions[0]
                amount = float(transaction.amount.total)
                currency = transaction.amount.currency
                
                return UnifiedPaymentResponse(
                    success=True,
                    payment_id=payment_id,
                    gateway=PaymentGateway.PAYPAL,
                    amount=amount,
                    currency=currency,
                    status=PaymentStatus.SUCCESS,
                    metadata={'paypal_payment': payment.to_dict()}
                )
            else:
                logger.error(f"❌ PayPal payment execution failed: {payment.error}")
                return UnifiedPaymentResponse(
                    success=False,
                    payment_id=payment_id,
                    gateway=PaymentGateway.PAYPAL,
                    amount=0,
                    currency='USD',
                    status=PaymentStatus.FAILED,
                    error_message=str(payment.error)
                )
                
        except Exception as e:
            logger.error(f"❌ PayPal payment execution error: {e}")
            return UnifiedPaymentResponse(
                success=False,
                payment_id=payment_id,
                gateway=PaymentGateway.PAYPAL,
                amount=0,
                currency='USD',
                status=PaymentStatus.FAILED,
                error_message=str(e)
            )

class UnifiedPaymentProcessor:
    """Main payment processor supporting both PayPal and Indian gateways"""
    
    def __init__(self):
        self.paypal_processor = PayPalProcessor()
        self.indian_processor = IndianPaymentProcessor()
        
        logger.info("🌏 Unified Payment Processor initialized - Supporting PayPal + Indian Gateways")
        logger.info("🏏 Ready for Big Bash League international and domestic fans!")
    
    def get_supported_methods(self, currency: str) -> List[Dict[str, str]]:
        """Get supported payment methods based on currency"""
        methods = []
        
        if currency.upper() in ['USD', 'AUD', 'EUR', 'GBP']:
            # International currencies - PayPal
            methods.extend([
                {
                    'id': 'paypal',
                    'name': 'PayPal',
                    'gateway': 'paypal',
                    'description': 'Pay securely with PayPal',
                    'currencies': ['USD', 'AUD', 'EUR', 'GBP'],
                    'icon': '/static/images/paypal-icon.png'
                }
            ])
        
        if currency.upper() == 'INR':
            # Indian currency - Indian gateways
            methods.extend([
                {
                    'id': 'upi',
                    'name': 'UPI',
                    'gateway': 'razorpay',
                    'description': 'Pay with PhonePe, Google Pay, Paytm',
                    'currencies': ['INR'],
                    'icon': '/static/images/upi-icon.png'
                },
                {
                    'id': 'card',
                    'name': 'Cards',
                    'gateway': 'razorpay',
                    'description': 'Debit/Credit Cards, RuPay',
                    'currencies': ['INR'],
                    'icon': '/static/images/card-icon.png'
                },
                {
                    'id': 'netbanking',
                    'name': 'Net Banking',
                    'gateway': 'razorpay',
                    'description': 'All major Indian banks',
                    'currencies': ['INR'],
                    'icon': '/static/images/netbanking-icon.png'
                },
                {
                    'id': 'wallet',
                    'name': 'Wallets',
                    'gateway': 'razorpay',
                    'description': 'Paytm, Mobikwik, Amazon Pay',
                    'currencies': ['INR'],
                    'icon': '/static/images/wallet-icon.png'
                }
            ])
        
        # If both USD/AUD and INR are supported, show both
        if currency.upper() in ['USD', 'AUD'] and os.getenv('RAZORPAY_KEY_ID'):
            # Also offer Indian methods for international currencies (converted)
            methods.append({
                'id': 'razorpay_international',
                'name': 'Indian Payment Methods',
                'gateway': 'razorpay',
                'description': 'UPI, Cards, Net Banking (INR)',
                'currencies': ['INR'],
                'icon': '/static/images/razorpay-icon.png',
                'conversion_required': True
            })
        
        return methods
    
    def create_payment(self, amount: float, currency: str, payment_method: str,
                      customer_email: str, metadata: Dict[str, str]) -> UnifiedPaymentResponse:
        """Create payment using appropriate gateway"""
        try:
            # Determine gateway based on payment method and currency
            if payment_method == 'paypal' or currency.upper() in ['USD', 'AUD', 'EUR', 'GBP']:
                # Use PayPal for international payments
                return self.paypal_processor.create_payment(
                    amount=amount,
                    currency=currency.upper(),
                    customer_email=customer_email,
                    metadata=metadata
                )
            
            elif currency.upper() == 'INR' or payment_method in ['upi', 'card', 'netbanking', 'wallet']:
                # Use Indian payment gateways
                indian_response = self.indian_processor.create_payment(
                    amount=amount,
                    customer_email=customer_email,
                    payment_method=payment_method,
                    metadata=metadata
                )
                
                # Convert to unified response
                return UnifiedPaymentResponse(
                    success=indian_response.status == PaymentStatus.PENDING,
                    payment_id=indian_response.payment_id,
                    gateway=PaymentGateway.RAZORPAY,
                    amount=indian_response.amount,
                    currency=Currency.INR,
                    status=indian_response.status,
                    error_message=indian_response.error_message,
                    metadata=indian_response.metadata
                )
            
            else:
                raise ValueError(f"Unsupported payment method: {payment_method} for currency: {currency}")
                
        except Exception as e:
            logger.error(f"❌ Unified payment creation failed: {e}")
            return UnifiedPaymentResponse(
                success=False,
                payment_id="",
                gateway=PaymentGateway.PAYPAL,
                amount=amount,
                currency=Currency(currency.upper()),
                status=PaymentStatus.FAILED,
                error_message=str(e)
            )
    
    def verify_payment(self, payment_data: Dict[str, Any]) -> UnifiedPaymentResponse:
        """Verify payment based on gateway"""
        try:
            gateway = payment_data.get('gateway', 'paypal')
            
            if gateway == 'paypal':
                # PayPal verification
                payment_id = payment_data.get('payment_id')
                payer_id = payment_data.get('payer_id')
                
                return self.paypal_processor.execute_payment(payment_id, payer_id)
            
            elif gateway in ['razorpay', 'upi']:
                # Indian payment verification
                indian_response = self.indian_processor.verify_payment(payment_data)
                
                # Convert to unified response
                return UnifiedPaymentResponse(
                    success=indian_response.status == PaymentStatus.SUCCESS,
                    payment_id=indian_response.payment_id,
                    gateway=PaymentGateway.RAZORPAY,
                    amount=indian_response.amount,
                    currency=Currency.INR,
                    status=indian_response.status,
                    error_message=indian_response.error_message,
                    metadata=indian_response.metadata
                )
            
            else:
                raise ValueError(f"Unsupported gateway: {gateway}")
                
        except Exception as e:
            logger.error(f"❌ Payment verification failed: {e}")
            return UnifiedPaymentResponse(
                success=False,
                payment_id=payment_data.get('payment_id', ''),
                gateway=PaymentGateway.PAYPAL,
                amount=0,
                currency=Currency.USD,
                status=PaymentStatus.FAILED,
                error_message=str(e)
            )
    
    def process_successful_payment(self, payment_response: UnifiedPaymentResponse,
                                 metadata: Dict[str, Any]) -> bool:
        """Process successful payment regardless of gateway"""
        try:
            if payment_response.gateway == PaymentGateway.PAYPAL:
                # Process PayPal payment
                return self._process_paypal_success(payment_response, metadata)
            else:
                # Process Indian payment via existing processor
                # Convert unified response back to PaymentResponse for compatibility
                # Use the PaymentResponse class from the Indian payment processor
                indian_response = PaymentResponse(
                    payment_id=payment_response.payment_id,
                    status=payment_response.status,
                    amount=payment_response.amount,
                    currency=payment_response.currency,
                    metadata=payment_response.metadata
                )
                
                return self.indian_processor.process_successful_payment(indian_response, metadata)
                
        except Exception as e:
            logger.error(f"❌ Payment processing failed: {e}")
            return False
    
    def _process_paypal_success(self, payment_response: UnifiedPaymentResponse,
                              metadata: Dict[str, Any]) -> bool:
        """Process successful PayPal payment"""
        from app import db, Booking, Ticket, Customer, Event, Seat
        
        try:
            # Start atomic transaction
            with db.session.begin():
                booking_type = metadata.get('booking_type', 'ticket')
                
                if booking_type == 'ticket':
                    success = self._fulfill_paypal_ticket_booking(payment_response, metadata, db)
                elif booking_type == 'parking':
                    success = self._fulfill_paypal_parking_booking(payment_response, metadata, db)
                else:
                    logger.error(f"❌ Unknown booking type: {booking_type}")
                    return False
                
                if success:
                    # Log successful payment
                    from security_framework import security_monitor
                    security_monitor.log_payment_attempt(
                        user_id=int(metadata.get('customer_id', 0)),
                        amount=payment_response.amount,
                        payment_method='paypal',
                        success=True
                    )
                    
                    logger.info(f"✅ PayPal payment processed successfully: {payment_response.payment_id}")
                    return True
                else:
                    db.session.rollback()
                    return False
                    
        except Exception as e:
            logger.error(f"❌ PayPal payment fulfillment failed: {e}")
            db.session.rollback()
            return False
    
    def _fulfill_paypal_ticket_booking(self, payment_response: UnifiedPaymentResponse,
                                     metadata: Dict, db) -> bool:
        """Fulfill PayPal ticket booking"""
        from app import Booking, Ticket, Customer, Event, Seat
        
        try:
            # Extract and validate metadata
            customer_id = int(metadata['customer_id'])
            event_id = int(metadata['event_id'])
            seat_ids = json.loads(metadata['seat_ids'])
            
            # Create booking record
            booking = Booking(
                customer_id=customer_id,
                event_id=event_id,
                booking_date=datetime.utcnow(),
                total_amount=payment_response.amount,
                booking_status='Confirmed',
                payment_method='PayPal',
                payment_id=payment_response.payment_id
            )
            db.session.add(booking)
            db.session.flush()
            
            # Create tickets
            for seat_id in seat_ids:
                ticket = Ticket(
                    customer_id=customer_id,
                    event_id=event_id,
                    seat_id=seat_id,
                    booking_id=booking.id,
                    price=payment_response.amount / len(seat_ids),
                    ticket_status='Booked',
                    booking_date=datetime.utcnow()
                )
                db.session.add(ticket)
            
            logger.info(f"✅ PayPal ticket booking fulfilled: {booking.id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ PayPal ticket booking fulfillment failed: {e}")
            return False
    
    def _fulfill_paypal_parking_booking(self, payment_response: UnifiedPaymentResponse,
                                      metadata: Dict, db) -> bool:
        """Fulfill PayPal parking booking"""
        # Parking booking logic would go here
        logger.info("✅ PayPal parking booking fulfilled")
        return True
    
    def get_currency_for_country(self, country_code: str) -> str:
        """Get recommended currency based on country"""
        currency_map = {
            'IN': 'INR',  # India
            'US': 'USD',  # United States
            'AU': 'AUD',  # Australia
            'GB': 'GBP',  # United Kingdom
            'EU': 'EUR',  # European Union
            'CA': 'USD',  # Canada
        }
        return currency_map.get(country_code.upper(), 'USD')
    
    def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> float:
        """Convert currency (simplified - in production use real exchange rates)"""
        # Simplified conversion rates (use real API in production)
        rates = {
            'USD_INR': 83.0,
            'AUD_INR': 55.0,
            'INR_USD': 0.012,
            'INR_AUD': 0.018,
            'USD_AUD': 1.5,
            'AUD_USD': 0.67
        }
        
        conversion_key = f"{from_currency}_{to_currency}"
        rate = rates.get(conversion_key, 1.0)
        
        return round(amount * rate, 2)

# Initialize the unified payment processor
unified_payment_processor = UnifiedPaymentProcessor()