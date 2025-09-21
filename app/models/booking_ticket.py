from app import db
from datetime import datetime

class Booking(db.Model):
    __tablename__ = 'booking'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    total_amount = db.Column(db.Float, nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_status = db.Column(db.String(20), default='Pending') # Merged from app/models/booking.py
    
    tickets = db.relationship('Ticket', backref='booking', lazy=True)
    accessibility_requests = db.relationship('AccessibilityRequest', backref='booking', lazy=True)


class Ticket(db.Model):
    __tablename__ = 'ticket'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    seat_id = db.Column(db.Integer, db.ForeignKey('seat.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'))
    ticket_type = db.Column(db.String(50))
    access_gate = db.Column(db.String(20))
    ticket_status = db.Column(db.String(20), default='Booked')
    qr_code = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    qr_codes = db.relationship('QRCode', backref='ticket', lazy=True)


class Seat(db.Model):
    __tablename__ = 'seat'
    
    id = db.Column(db.Integer, primary_key=True)
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'), nullable=False, index=True)
    seat_number = db.Column(db.String(20), nullable=False, index=True)
    section = db.Column(db.String(50), index=True)
    row_number = db.Column(db.String(10))
    seat_type = db.Column(db.String(50), index=True)
    price = db.Column(db.Float)
    has_shade = db.Column(db.Boolean, default=False)
    is_available = db.Column(db.Boolean, default=True, index=True)
