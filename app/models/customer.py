from app import db
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class Customer(db.Model, UserMixin):
    __tablename__ = 'customer'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(200))
    role = db.Column(db.String(20), default='customer')
    membership_level = db.Column(db.String(50))
    verification_status = db.Column(db.String(20), default='not_verified')
    favorite_team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    bookings = db.relationship('Booking', backref='customer', lazy=True)
    orders = db.relationship('Order', backref='customer', lazy=True)
    parking_bookings = db.relationship('ParkingBooking', backref='customer', lazy=True)
    accessibility_requests = db.relationship('AccessibilityRequest', backref='customer', lazy=True)
    system_logs = db.relationship('SystemLog', backref='customer', lazy=True)
    websocket_connections = db.relationship('WebSocketConnection', backref='customer', lazy=True)
    payment_transactions = db.relationship('PaymentTransaction', backref='customer', lazy=True)
    profile = db.relationship('CustomerProfile', backref='customer', uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def get_administered_stadiums(self):
        if self.is_admin():
            return [sa.stadium_id for sa in StadiumAdmin.query.filter_by(admin_id=self.id).all()]
        return []

class CustomerProfile(db.Model):
    __tablename__ = 'customer_profile'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), unique=True, nullable=False)
    mfa_enabled = db.Column(db.Boolean, default=False)
    mfa_secret = db.Column(db.String(32))
    backup_codes = db.Column(db.Text)
    phone_verified = db.Column(db.Boolean, default=False)
    notification_preferences = db.Column(db.Text)
    preferred_language = db.Column(db.String(5), default='en')
    timezone = db.Column(db.String(50), default='UTC')
    total_bookings = db.Column(db.Integer, default=0)
    total_spent = db.Column(db.Float, default=0.0)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    loyalty_points = db.Column(db.Integer, default=0)
    
    # Fields from app/models/booking.py CustomerProfile
    bio = db.Column(db.Text)
    profile_picture_url = db.Column(db.String(200))
    address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100))
    zip_code = db.Column(db.String(20))
