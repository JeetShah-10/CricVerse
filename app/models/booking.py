from app import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Customer(db.Model, UserMixin):
    """Customer model for storing user information."""
    __tablename__ = 'customer'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=True)
    first_name = db.Column(db.String(80), nullable=True)
    last_name = db.Column(db.String(80), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    role = db.Column(db.String(20), default='customer')  # customer, admin, stadium_owner
    
    # Relationships
    bookings = db.relationship('Booking', backref='customer', lazy=True)
    
    def __repr__(self):
        identifier = self.username or self.email
        return f'<Customer {identifier}>'
    
    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password hash."""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Check if user is admin."""
        return self.role == 'admin'
    
    def is_stadium_owner(self):
        """Check if user is stadium owner."""
        return self.role == 'stadium_owner'
    
    def is_customer(self):
        """Check if user is regular customer."""
        return self.role == 'customer'
    
    @property
    def name(self):
        """Get full name or username."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username or self.email

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

class CustomerProfile(db.Model):
    __tablename__ = 'customer_profile'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), unique=True, nullable=False)
    bio = db.Column(db.Text)
    profile_picture_url = db.Column(db.String(200))
    address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100))
    zip_code = db.Column(db.String(20))
    customer = db.relationship('Customer', backref=db.backref('profile', uselist=False))