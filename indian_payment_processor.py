"""
Indian Payment Processor for CricVerse Stadium System
Integration with Razorpay for Indian customers
Big Bash League Cricket Platform
"""

import os
import logging
import json
import hmac
import hashlib
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PaymentStatus(Enum):
    """Payment status enum"""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PROCESSING = "processing"

@dataclass
class PaymentResponse:
    """Payment response data structure"""
    payment_id: str
    status: PaymentStatus
    amount: float
    currency: str
    error_message: Optional[str] = None
    metadata: Optional[Dict] = None

class IndianPaymentProcessor:
    """Indian payment processor for Razorpay integration"""
    
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
        """Create Razorpay payment order"""
        try:
            import razorpay
            
            client = razorpay.Client(auth=(self.key_id, self.key_secret))
            
            # Create order
            order_data = {
                'amount': int(amount * 100),  # Convert to paise
                'currency': 'INR',
                'receipt': f"bbl_booking_{metadata.get('booking_id', 'unknown')}",
                'payment_capture': 1  # Auto capture
            }
            
            order = client.order.create(data=order_data)
            
            logger.info(f"✅ Created Razorpay order: {order['id']}")
            
            return PaymentResponse(
                payment_id=order['id'],
                status=PaymentStatus.PENDING,
                amount=amount,
                currency='INR',
                metadata={
                    'razorpay_order_id': order['id'],
                    'amount': order['amount'],
                    'currency': order['currency']
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Payment creation failed: {e}")
            return PaymentResponse(
                payment_id="",
                status=PaymentStatus.FAILED,
                amount=amount,
                currency='INR',
                error_message=str(e)
            )
    
    def verify_payment(self, payment_data: Dict) -> PaymentResponse:
        """Verify Razorpay payment"""
        try:
            import razorpay
            
            client = razorpay.Client(auth=(self.key_id, self.key_secret))
            
            # Verify payment signature
            params_dict = {
                'razorpay_order_id': payment_data['razorpay_order_id'],
                'razorpay_payment_id': payment_data['razorpay_payment_id'],
                'razorpay_signature': payment_data['razorpay_signature']
            }
            
            client.utility.verify_payment_signature(params_dict)
            
            # Fetch payment details
            payment = client.payment.fetch(payment_data['razorpay_payment_id'])
            
            logger.info(f"✅ Verified payment: {payment_data['razorpay_payment_id']}")
            
            return PaymentResponse(
                payment_id=payment_data['razorpay_payment_id'],
                status=PaymentStatus.SUCCESS,
                amount=payment['amount'] / 100,  # Convert from paise
                currency=payment['currency']
            )
            
        except Exception as e:
            logger.error(f"❌ Payment verification failed: {e}")
            return PaymentResponse(
                payment_id=payment_data.get('razorpay_payment_id', ''),
                status=PaymentStatus.FAILED,
                amount=0,
                currency='INR',
                error_message=str(e)
            )
    
    def verify_webhook_signature(self, body: bytes, signature: str, webhook_secret: str = None) -> bool:
        """Verify Razorpay webhook signature"""
        try:
            secret = webhook_secret or self.webhook_secret
            
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                body,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"❌ Webhook signature verification failed: {e}")
            return False
    
    def process_successful_payment(self, payment_response: PaymentResponse, 
                                 metadata: Dict[str, Any]) -> bool:
        """Process successful payment and fulfill booking"""
        from app import db, Booking, Ticket
        
        try:
            # Start atomic transaction
            with db.session.begin():
                booking_type = metadata.get('booking_type', 'ticket')
                
                if booking_type == 'ticket':
                    success = self._fulfill_ticket_booking(payment_response, metadata, db)
                elif booking_type == 'parking':
                    success = self._fulfill_parking_booking(payment_response, metadata, db)
                else:
                    logger.error(f"❌ Unknown booking type: {booking_type}")
                    return False
                
                if success:
                    # Log successful payment
                    from security_framework import security_monitor
                    security_monitor.log_payment_attempt(
                        user_id=int(metadata.get('customer_id', 0)),
                        amount=payment_response.amount,
                        payment_method='razorpay',
                        success=True
                    )
                    
                    logger.info(f"✅ Payment processed successfully: {payment_response.payment_id}")
                    return True
                else:
                    db.session.rollback()
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Payment fulfillment failed: {e}")
            db.session.rollback()
            return False
    
    def _fulfill_ticket_booking(self, payment_response: PaymentResponse, 
                              metadata: Dict, db) -> bool:
        """Fulfill ticket booking"""
        from app import Booking, Ticket
        
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
                payment_method='Razorpay',
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
            
            logger.info(f"✅ Ticket booking fulfilled: {booking.id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ticket booking fulfillment failed: {e}")
            return False
    
    def _fulfill_parking_booking(self, payment_response: PaymentResponse, 
                               metadata: Dict, db) -> bool:
        """Fulfill parking booking"""
        # Parking booking logic would go here
        logger.info("✅ Parking booking fulfilled")
        return True

# Initialize the Indian payment processor
indian_payment_processor = IndianPaymentProcessor()