from app import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Customer(db.Model, UserMixin):
    """Customer model for storing user information."""
    __tablename__ = 'customer'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    bookings = db.relationship('Booking', backref='customer', lazy=True)
    
    def __repr__(self):
        return f'<Customer {self.username}>'
    
    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password hash."""
        return check_password_hash(self.password_hash, password)

class Booking(db.Model):
    """Booking model for storing ticket bookings."""
    __tablename__ = 'booking'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_status = db.Column(db.String(20), default='Pending')
    
    # Relationships
    tickets = db.relationship('Ticket', backref='booking', lazy=True)
    
    def __repr__(self):
        return f'<Booking {self.id} for customer {self.customer_id}>'

class Ticket(db.Model):
    """Ticket model for storing individual tickets."""
    __tablename__ = 'ticket'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, nullable=False)
    seat_id = db.Column(db.Integer, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    ticket_type = db.Column(db.String(50))
    ticket_status = db.Column(db.String(20), default='Booked')
    access_gate = db.Column(db.String(50))
    qr_code = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Ticket {self.id} for event {self.event_id}>'

class Seat(db.Model):
    """Seat model for storing stadium seating information."""
    __tablename__ = 'seat'
    
    id = db.Column(db.Integer, primary_key=True)
    section = db.Column(db.String(10))
    row_number = db.Column(db.String(10))
    seat_number = db.Column(db.String(10))
    seat_type = db.Column(db.String(50))
    price = db.Column(db.Float)
    is_available = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Seat {self.section}-{self.row_number}-{self.seat_number}>'