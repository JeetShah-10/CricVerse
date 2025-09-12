"""
Stripe Payment Processing Integration for CricVerse
Handles ticket bookings, parking reservations, and concession purchases
"""

import os
import logging
import stripe
from datetime import datetime, timedelta
from flask import request, session, jsonify, redirect, url_for, flash
from decimal import Decimal
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

class StripePaymentProcessor:
    """Handles all Stripe payment operations"""
    
    def __init__(self):
        self.webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        self.publishable_key = os.getenv('STRIPE_PUBLISHABLE_KEY')
        
        if not stripe.api_key:
            logger.warning("⚠️ Stripe secret key not configured")
        if not self.publishable_key:
            logger.warning("⚠️ Stripe publishable key not configured")
            
        logger.info("✅ Stripe Payment Processor initialized")
    
    def create_customer(self, customer_data):
        """Create a Stripe customer"""
        try:
            stripe_customer = stripe.Customer.create(
                name=customer_data.get('name'),
                email=customer_data.get('email'),
                phone=customer_data.get('phone'),
                metadata={
                    'cricverse_customer_id': customer_data.get('customer_id'),
                    'source': 'CricVerse'
                }
            )
            
            logger.info(f"✅ Created Stripe customer: {stripe_customer.id}")
            return stripe_customer
            
        except stripe.error.StripeError as e:
            logger.error(f"❌ Failed to create Stripe customer: {e}")
            return None
    
    def create_payment_intent(self, amount, currency, customer_id, metadata=None):
        """Create a payment intent for booking"""
        try:
            # Convert amount to cents (Stripe uses smallest currency unit)
            amount_cents = int(amount * 100)
            
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency.lower(),
                customer=customer_id,
                metadata=metadata or {},
                automatic_payment_methods={
                    'enabled': True,
                },
                # Enable receipt emails
                receipt_email=metadata.get('customer_email') if metadata else None,
                description=metadata.get('description', 'CricVerse Booking') if metadata else 'CricVerse Booking'
            )
            
            logger.info(f"✅ Created payment intent: {payment_intent.id} for ${amount}")
            return payment_intent
            
        except stripe.error.StripeError as e:
            logger.error(f"❌ Failed to create payment intent: {e}")
            return None
    
    def confirm_payment_intent(self, payment_intent_id, payment_method_id=None):
        """Confirm a payment intent"""
        try:
            if payment_method_id:
                payment_intent = stripe.PaymentIntent.confirm(
                    payment_intent_id,
                    payment_method=payment_method_id
                )
            else:
                payment_intent = stripe.PaymentIntent.confirm(payment_intent_id)
            
            logger.info(f"✅ Confirmed payment intent: {payment_intent_id}")
            return payment_intent
            
        except stripe.error.StripeError as e:
            logger.error(f"❌ Failed to confirm payment intent: {e}")
            return None
    
    def get_payment_intent(self, payment_intent_id):
        """Retrieve a payment intent"""
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return payment_intent
            
        except stripe.error.StripeError as e:
            logger.error(f"❌ Failed to retrieve payment intent: {e}")
            return None
    
    def create_refund(self, payment_intent_id, amount=None, reason=None):
        """Create a refund for a payment"""
        try:
            refund_data = {
                'payment_intent': payment_intent_id,
                'reason': reason or 'requested_by_customer'
            }
            
            if amount:
                refund_data['amount'] = int(amount * 100)  # Convert to cents
            
            refund = stripe.Refund.create(**refund_data)
            
            logger.info(f"✅ Created refund: {refund.id}")
            return refund
            
        except stripe.error.StripeError as e:
            logger.error(f"❌ Failed to create refund: {e}")
            return None
    
    def handle_webhook(self, payload, sig_header):
        """Handle Stripe webhook events"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            
            logger.info(f"📡 Received Stripe webhook: {event['type']}")
            
            # Handle different event types
            if event['type'] == 'payment_intent.succeeded':
                return self._handle_payment_succeeded(event['data']['object'])
            elif event['type'] == 'payment_intent.payment_failed':
                return self._handle_payment_failed(event['data']['object'])
            elif event['type'] == 'payment_intent.canceled':
                return self._handle_payment_canceled(event['data']['object'])
            elif event['type'] == 'charge.dispute.created':
                return self._handle_dispute_created(event['data']['object'])
            
            return True
            
        except ValueError as e:
            logger.error(f"❌ Invalid webhook payload: {e}")
            return False
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"❌ Invalid webhook signature: {e}")
            return False
    
    def _handle_payment_succeeded(self, payment_intent):
        """Handle successful payment"""
        try:
            from app import db
            from enhanced_models import PaymentTransaction
            
            # Update payment transaction status
            transaction = PaymentTransaction.query.filter_by(
                stripe_payment_intent_id=payment_intent['id']
            ).first()
            
            if transaction:
                transaction.payment_status = 'succeeded'
                transaction.payment_date = datetime.utcnow()
                transaction.stripe_charge_id = payment_intent.get('latest_charge')
                transaction.receipt_url = payment_intent.get('charges', {}).get('data', [{}])[0].get('receipt_url')
                db.session.commit()
                
                # Send confirmation notification
                self._send_payment_confirmation(transaction)
                
                logger.info(f"✅ Payment succeeded for transaction: {transaction.id}")
            else:
                logger.warning(f"⚠️ Transaction not found for payment intent: {payment_intent['id']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error handling payment success: {e}")
            return False
    
    def _handle_payment_failed(self, payment_intent):
        """Handle failed payment"""
        try:
            from app import db
            from enhanced_models import PaymentTransaction
            
            # Update payment transaction status
            transaction = PaymentTransaction.query.filter_by(
                stripe_payment_intent_id=payment_intent['id']
            ).first()
            
            if transaction:
                transaction.payment_status = 'failed'
                transaction.failure_reason = payment_intent.get('last_payment_error', {}).get('message', 'Unknown error')
                db.session.commit()
                
                logger.info(f"❌ Payment failed for transaction: {transaction.id}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error handling payment failure: {e}")
            return False
    
    def _handle_payment_canceled(self, payment_intent):
        """Handle canceled payment"""
        try:
            from app import db
            from enhanced_models import PaymentTransaction
            
            # Update payment transaction status
            transaction = PaymentTransaction.query.filter_by(
                stripe_payment_intent_id=payment_intent['id']
            ).first()
            
            if transaction:
                transaction.payment_status = 'canceled'
                db.session.commit()
                
                logger.info(f"🚫 Payment canceled for transaction: {transaction.id}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error handling payment cancellation: {e}")
            return False
    
    def _handle_dispute_created(self, dispute):
        """Handle dispute creation"""
        try:
            # Log dispute for manual review
            logger.warning(f"⚠️ Dispute created: {dispute['id']} for charge: {dispute['charge']}")
            
            # Here you could implement automatic dispute handling
            # For now, just log it for manual review
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error handling dispute: {e}")
            return False
    
    def _send_payment_confirmation(self, transaction):
        """Send payment confirmation notification"""
        try:
            # Import notification system
            from notifications import send_booking_confirmation
            
            # Get booking details
            booking = transaction.booking if hasattr(transaction, 'booking') else None
            if booking:
                customer = booking.customer
                event = booking.tickets[0].event if booking.tickets else None
                
                # Send confirmation email
                send_booking_confirmation(
                    customer=customer,
                    booking=booking,
                    event=event,
                    payment_amount=transaction.amount,
                    receipt_url=transaction.receipt_url
                )
            
        except Exception as e:
            logger.error(f"❌ Error sending payment confirmation: {e}")


# Initialize global payment processor
payment_processor = StripePaymentProcessor()


# Flask route handlers
def create_booking_payment_intent(booking_data):
    """Create payment intent for a booking"""
    try:
        from app import Customer
        
        # Get customer
        customer = Customer.query.get(booking_data['customer_id'])
        if not customer:
            return {'error': 'Customer not found'}, 400
        
        # Create or get Stripe customer
        if not hasattr(customer, 'stripe_customer_id') or not customer.stripe_customer_id:
            stripe_customer = payment_processor.create_customer({
                'name': customer.name,
                'email': customer.email,
                'phone': customer.phone,
                'customer_id': customer.id
            })
            
            if not stripe_customer:
                return {'error': 'Failed to create payment customer'}, 500
            
            # Store Stripe customer ID (you'll need to add this field to Customer model)
            # customer.stripe_customer_id = stripe_customer.id
            # db.session.commit()
        
        # Prepare payment metadata
        metadata = {
            'cricverse_booking_id': booking_data.get('booking_id'),
            'customer_id': str(customer.id),
            'customer_email': customer.email,
            'event_id': str(booking_data.get('event_id', '')),
            'seat_count': str(booking_data.get('seat_count', 0)),
            'description': f"CricVerse Booking - {booking_data.get('event_name', 'Event')}"
        }
        
        # Create payment intent
        payment_intent = payment_processor.create_payment_intent(
            amount=booking_data['total_amount'],
            currency='AUD',  # Or get from config
            customer_id=stripe_customer.id if 'stripe_customer' in locals() else None,
            metadata=metadata
        )
        
        if not payment_intent:
            return {'error': 'Failed to create payment intent'}, 500
        
        # Store payment transaction record
        from app import db
        from enhanced_models import PaymentTransaction
        
        transaction = PaymentTransaction(
            customer_id=customer.id,
            booking_id=booking_data.get('booking_id'),
            stripe_payment_intent_id=payment_intent.id,
            amount=booking_data['total_amount'],
            currency='AUD',
            payment_status='pending',
            description=metadata['description']
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return {
            'client_secret': payment_intent.client_secret,
            'payment_intent_id': payment_intent.id,
            'publishable_key': payment_processor.publishable_key
        }
        
    except Exception as e:
        logger.error(f"❌ Error creating booking payment intent: {e}")
        return {'error': 'Payment setup failed'}, 500


def create_parking_payment_intent(parking_data):
    """Create payment intent for parking booking"""
    try:
        from app import Customer
        
        # Similar to booking payment but for parking
        customer = Customer.query.get(parking_data['customer_id'])
        if not customer:
            return {'error': 'Customer not found'}, 400
        
        metadata = {
            'cricverse_parking_id': parking_data.get('parking_booking_id'),
            'customer_id': str(customer.id),
            'customer_email': customer.email,
            'stadium_id': str(parking_data.get('stadium_id', '')),
            'vehicle_number': parking_data.get('vehicle_number', ''),
            'description': f"CricVerse Parking - {parking_data.get('stadium_name', 'Stadium')}"
        }
        
        # Create payment intent
        payment_intent = payment_processor.create_payment_intent(
            amount=parking_data['amount'],
            currency='AUD',
            customer_id=None,  # You can implement customer creation similar to above
            metadata=metadata
        )
        
        if not payment_intent:
            return {'error': 'Failed to create payment intent'}, 500
        
        # Store payment transaction record
        from app import db
        from enhanced_models import PaymentTransaction
        
        transaction = PaymentTransaction(
            customer_id=customer.id,
            parking_booking_id=parking_data.get('parking_booking_id'),
            stripe_payment_intent_id=payment_intent.id,
            amount=parking_data['amount'],
            currency='AUD',
            payment_status='pending',
            description=metadata['description']
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return {
            'client_secret': payment_intent.client_secret,
            'payment_intent_id': payment_intent.id,
            'publishable_key': payment_processor.publishable_key
        }
        
    except Exception as e:
        logger.error(f"❌ Error creating parking payment intent: {e}")
        return {'error': 'Payment setup failed'}, 500


def handle_stripe_webhook():
    """Handle Stripe webhook endpoint"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    if not sig_header:
        logger.error("❌ Missing Stripe signature header")
        return {'error': 'Missing signature'}, 400
    
    success = payment_processor.handle_webhook(payload, sig_header)
    
    if success:
        return {'status': 'success'}, 200
    else:
        return {'error': 'Webhook processing failed'}, 400


def get_payment_status(payment_intent_id):
    """Get payment status"""
    try:
        payment_intent = payment_processor.get_payment_intent(payment_intent_id)
        
        if not payment_intent:
            return {'error': 'Payment not found'}, 404
        
        return {
            'status': payment_intent.status,
            'amount': payment_intent.amount / 100,  # Convert from cents
            'currency': payment_intent.currency,
            'created': payment_intent.created
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting payment status: {e}")
        return {'error': 'Failed to get payment status'}, 500


def process_refund(payment_intent_id, refund_amount=None, reason=None):
    """Process a refund"""
    try:
        refund = payment_processor.create_refund(
            payment_intent_id=payment_intent_id,
            amount=refund_amount,
            reason=reason
        )
        
        if not refund:
            return {'error': 'Refund failed'}, 500
        
        # Update transaction record
        from app import db
        from enhanced_models import PaymentTransaction
        
        transaction = PaymentTransaction.query.filter_by(
            stripe_payment_intent_id=payment_intent_id
        ).first()
        
        if transaction:
            transaction.payment_status = 'refunded'
            db.session.commit()
        
        return {
            'refund_id': refund.id,
            'amount': refund.amount / 100,
            'status': refund.status
        }
        
    except Exception as e:
        logger.error(f"❌ Error processing refund: {e}")
        return {'error': 'Refund processing failed'}, 500


# Utility functions for payment calculations
def calculate_booking_total(seats, event, concessions=None):
    """Calculate total booking amount including fees"""
    try:
        subtotal = sum(seat.price for seat in seats)
        
        # Add concession costs if any
        if concessions:
            concession_total = sum(item['price'] * item['quantity'] for item in concessions)
            subtotal += concession_total
        
        # Calculate fees (you can customize this)
        service_fee = subtotal * 0.05  # 5% service fee
        processing_fee = 2.50  # Fixed processing fee
        
        total = subtotal + service_fee + processing_fee
        
        return {
            'subtotal': round(subtotal, 2),
            'service_fee': round(service_fee, 2),
            'processing_fee': round(processing_fee, 2),
            'total': round(total, 2)
        }
        
    except Exception as e:
        logger.error(f"❌ Error calculating booking total: {e}")
        return None


def calculate_parking_fee(parking_zone, hours):
    """Calculate parking fee based on zone and duration"""
    try:
        hourly_rate = parking_zone.rate_per_hour
        base_fee = hourly_rate * hours
        
        # Add any applicable taxes
        tax_rate = 0.10  # 10% tax
        tax = base_fee * tax_rate
        
        total = base_fee + tax
        
        return {
            'base_fee': round(base_fee, 2),
            'tax': round(tax, 2),
            'total': round(total, 2)
        }
        
    except Exception as e:
        logger.error(f"❌ Error calculating parking fee: {e}")
        return None