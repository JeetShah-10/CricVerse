from app import db
from datetime import datetime

class Stadium(db.Model):
    __tablename__ = 'stadium'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(200))
    contact_number = db.Column(db.String(20))
    opening_year = db.Column(db.Integer)
    pitch_type = db.Column(db.String(50))
    boundary_length = db.Column(db.Integer)
    floodlight_quality = db.Column(db.String(50))
    has_dressing_rooms = db.Column(db.Boolean, default=False)
    has_practice_nets = db.Column(db.Boolean, default=False)

class StadiumAdmin(db.Model):
    __tablename__ = 'stadium_admin'
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'), nullable=False)
    admin = db.relationship('Customer', backref='admin_stadiums')
    stadium = db.relationship('Stadium', backref='admins')

class Photo(db.Model):
    __tablename__ = 'photo'
    id = db.Column(db.Integer, primary_key=True)
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'), nullable=False)
    url = db.Column(db.String(200), nullable=False)
    caption = db.Column(db.String(200))

class Parking(db.Model):
    __tablename__ = 'parking'
    id = db.Column(db.Integer, primary_key=True)
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'), nullable=False)
    zone = db.Column(db.String(50), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    rate_per_hour = db.Column(db.Float, nullable=False)
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
    payment_status = db.Column(db.String(20), default='Pending')
    parking = db.relationship('Parking', backref='bookings')
    customer = db.relationship('Customer', backref='parking_bookings')

class Concession(db.Model):
    __tablename__ = 'concession'
    id = db.Column(db.Integer, primary_key=True)
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    location_zone = db.Column(db.String(50))
    opening_hours = db.Column(db.String(100))
    stadium = db.relationship('Stadium', backref='concessions')
    menu_items = db.relationship('MenuItem', backref='concession_menu', lazy=True)

class MenuItem(db.Model):
    __tablename__ = 'menu_item'
    id = db.Column(db.Integer, primary_key=True)
    concession_id = db.Column(db.Integer, db.ForeignKey('concession.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50))
    is_available = db.Column(db.Boolean, default=True)
    concession = db.relationship('Concession', backref='items')

class Order(db.Model):
    __tablename__ = 'order'
    id = db.Column(db.Integer, primary_key=True)
    concession_id = db.Column(db.Integer, db.ForeignKey('concession.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_status = db.Column(db.String(20), default='Pending')
    concession = db.relationship('Concession', backref='orders')
    customer = db.relationship('Customer', backref='orders')