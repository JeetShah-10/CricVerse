# Missing model definitions for CricVerse
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Assuming db is defined elsewhere in the app
# For now, we'll define a placeholder that will be replaced when imported
db = SQLAlchemy()

class Customer(db.Model, UserMixin):
    __tablename__ = 'customer'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='customer')  # customer, admin, stadium_owner
    membership_level = db.Column(db.String(20), default='Basic')  # Basic, Premium, VIP
    favorite_team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    verification_status = db.Column(db.String(20), default='unverified')  # unverified, pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    favorite_team = db.relationship('Team', backref='fans')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def get_administered_stadiums(self):
        # For admin users, return list of stadium IDs they manage
        if self.role == 'admin':
            # In a real implementation, this would query a join table
            # For now, return all stadiums as admins can manage all
            stadiums = Stadium.query.all()
            return [s.id for s in stadiums]
        return []

class Booking(db.Model):
    __tablename__ = 'booking'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_status = db.Column(db.String(20), default='Pending')  # Pending, Completed, Failed, Cancelled
    
    # Relationships
    customer = db.relationship('Customer', backref='bookings')
    tickets = db.relationship('Ticket', backref='booking', lazy=True)
    payments = db.relationship('Payment', backref='booking', lazy=True)

class Ticket(db.Model):
    __tablename__ = 'ticket'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    seat_id = db.Column(db.Integer, db.ForeignKey('seat.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    ticket_type = db.Column(db.String(50))  # Single Match, Season, Hospitality
    ticket_status = db.Column(db.String(20), default='Booked')  # Booked, Used, Cancelled, Transferred
    access_gate = db.Column(db.String(50))
    qr_code = db.Column(db.String(200))  # Path to QR code image
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    event = db.relationship('Event', backref='tickets')
    seat = db.relationship('Seat', backref='tickets')
    customer = db.relationship('Customer', backref='tickets')

class Payment(db.Model):
    __tablename__ = 'payment'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50))  # PayPal, Razorpay, Card, etc.
    transaction_id = db.Column(db.String(100), unique=True)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_status = db.Column(db.String(20), default='Completed')  # Pending, Completed, Failed, Refunded
    
    # Relationships
    booking = db.relationship('Booking', backref='payments')

class Concession(db.Model):
    __tablename__ = 'concession'
    
    id = db.Column(db.Integer, primary_key=True)
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))  # Food, Beverage, Merchandise
    location_zone = db.Column(db.String(50))  # North, South, East, West stands
    opening_hours = db.Column(db.String(100))
    
    # Relationships
    stadium = db.relationship('Stadium', backref='concessions')
    menu_items = db.relationship('MenuItem', backref='concession', lazy=True)

class MenuItem(db.Model):
    __tablename__ = 'menu_item'
    
    id = db.Column(db.Integer, primary_key=True)
    concession_id = db.Column(db.Integer, db.ForeignKey('concession.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50))  # Main Course, Snack, Drink, Dessert
    is_available = db.Column(db.Boolean, default=True)
    
    # Relationships
    concession = db.relationship('Concession', backref='items')

class Parking(db.Model):
    __tablename__ = 'parking'
    
    id = db.Column(db.Integer, primary_key=True)
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'), nullable=False)
    zone = db.Column(db.String(50), nullable=False)  # A, B, C, VIP, etc.
    capacity = db.Column(db.Integer, nullable=False)
    rate_per_hour = db.Column(db.Float, nullable=False)
    
    # Relationships
    stadium = db.relationship('Stadium', backref='parkings')

class ParkingBooking(db.Model):
    __tablename__ = 'parking_booking'
    
    id = db.Column(db.Integer, primary_key=True)
    parking_id = db.Column(db.Integer, db.ForeignKey('parking.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    vehicle_number = db.Column(db.String(20))
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    arrival_time = db.Column(db.DateTime)
    departure_time = db.Column(db.DateTime)
    amount_paid = db.Column(db.Float)
    payment_status = db.Column(db.String(20), default='Pending')  # Pending, Completed, Failed, Cancelled
    
    # Relationships
    parking = db.relationship('Parking', backref='bookings')
    customer = db.relationship('Customer', backref='parking_bookings')

class Order(db.Model):
    __tablename__ = 'order'
    
    id = db.Column(db.Integer, primary_key=True)
    concession_id = db.Column(db.Integer, db.ForeignKey('concession.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_status = db.Column(db.String(20), default='Pending')  # Pending, Completed, Failed, Cancelled
    
    # Relationships
    concession = db.relationship('Concession', backref='orders')
    customer = db.relationship('Customer', backref='orders')

class Photo(db.Model):
    __tablename__ = 'photo'
    
    id = db.Column(db.Integer, primary_key=True)
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'), nullable=False)
    url = db.Column(db.String(200), nullable=False)
    caption = db.Column(db.String(200))

class StadiumAdmin(db.Model):
    __tablename__ = 'stadium_admin'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'), nullable=False)
    
    # Relationships
    admin = db.relationship('Customer', backref='admin_stadiums')
    stadium = db.relationship('Stadium', backref='admins')