from app import db
from datetime import datetime

class Stadium(db.Model):
    __tablename__ = 'stadium'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    location = db.Column(db.String(100), nullable=False, index=True)
    capacity = db.Column(db.Integer, nullable=False, index=True)
    contact_number = db.Column(db.String(20))
    opening_year = db.Column(db.Integer)
    pitch_type = db.Column(db.String(50))
    boundary_length = db.Column(db.Integer)
    floodlight_quality = db.Column(db.String(20))
    has_dressing_rooms = db.Column(db.Boolean, default=True)
    has_practice_nets = db.Column(db.Boolean, default=True)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(200), nullable=True)
    latitude = db.Column(db.Float, nullable=True, index=True)
    longitude = db.Column(db.Float, nullable=True, index=True)
    open_hour = db.Column(db.Time, nullable=True)
    close_hour = db.Column(db.Time, nullable=True)
    
    events = db.relationship('Event', backref='stadium', lazy=True)
    seats = db.relationship('Seat', backref='stadium', lazy=True)
    concessions = db.relationship('Concession', backref='stadium', lazy=True)
    parkings = db.relationship('Parking', backref='stadium', lazy=True)
    photos = db.relationship('Photo', backref='stadium', lazy=True)
    analytics = db.relationship('BookingAnalytics', backref='stadium', lazy=True)


class StadiumAdmin(db.Model):
    __tablename__ = 'stadium_admin'
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'))


class Photo(db.Model):
    __tablename__ = 'photo'
    id = db.Column(db.Integer, primary_key=True)
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'), nullable=False, index=True)
    url = db.Column(db.String(200), nullable=False)
    caption = db.Column(db.String(200))


class Parking(db.Model):
    __tablename__ = 'parking'
    id = db.Column(db.Integer, primary_key=True)
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'), nullable=False, index=True)
    zone = db.Column(db.String(50), nullable=False, index=True)
    capacity = db.Column(db.Integer, nullable=False)
    rate_per_hour = db.Column(db.Float, nullable=False)
    bookings = db.relationship('ParkingBooking', backref='parking', lazy=True)


class ParkingBooking(db.Model):
    __tablename__ = 'parking_booking'
    id = db.Column(db.Integer, primary_key=True)
    parking_id = db.Column(db.Integer, db.ForeignKey('parking.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    vehicle_number = db.Column(db.String(20))
    arrival_time = db.Column(db.DateTime)
    departure_time = db.Column(db.DateTime)
    amount_paid = db.Column(db.Float)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    qr_codes = db.relationship('QRCode', backref='parking_booking', lazy=True)
    payment_status = db.Column(db.String(20), default='Pending') # Merged from app/models/stadium.py


class Concession(db.Model):
    __tablename__ = 'concession'
    id = db.Column(db.Integer, primary_key=True)
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    category = db.Column(db.String(50), index=True)
    location_zone = db.Column(db.String(50))
    opening_hours = db.Column(db.String(100))
    description = db.Column(db.Text) # Merged from root models.py
    menu_items = db.relationship('MenuItem', back_populates='concession', lazy=True, overlaps="concession")
    orders = db.relationship('Order', backref='concession', lazy=True)


class MenuItem(db.Model):
    __tablename__ = 'menu_item'
    id = db.Column(db.Integer, primary_key=True)
    concession_id = db.Column(db.Integer, db.ForeignKey('concession.id'), nullable=False, index=True)
    concession = db.relationship('Concession', back_populates='menu_items', overlaps="menu_items")
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), index=True)
    is_available = db.Column(db.Boolean, default=True, index=True)
    is_vegetarian = db.Column(db.Boolean, default=True, index=True) # Merged from root models.py


class Order(db.Model):
    __tablename__ = 'order'
    id = db.Column(db.Integer, primary_key=True)
    concession_id = db.Column(db.Integer, db.ForeignKey('concession.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    total_amount = db.Column(db.Float, nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_status = db.Column(db.String(20))
