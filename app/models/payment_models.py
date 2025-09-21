from app import db
from datetime import datetime

class Payment(db.Model):
    __tablename__ = 'payment'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50))
    transaction_id = db.Column(db.String(100), unique=True)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_status = db.Column(db.String(20), default='Completed')
    booking = db.relationship('Booking', backref='payments')

class PaymentTransaction(db.Model):
    __tablename__ = 'payment_transaction'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'))
    parking_booking_id = db.Column(db.Integer, db.ForeignKey('parking_booking.id'))
    stripe_payment_intent_id = db.Column(db.String(200), unique=True)
    stripe_charge_id = db.Column(db.String(200))
    stripe_customer_id = db.Column(db.String(200))
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='AUD')
    payment_method = db.Column(db.String(50))
    payment_status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    payment_date = db.Column(db.DateTime)
    description = db.Column(db.String(500))
    receipt_url = db.Column(db.String(500))
    failure_reason = db.Column(db.String(500))
