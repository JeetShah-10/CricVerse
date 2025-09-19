from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()

class Concession(db.Model):
    __tablename__ = 'concession'
    id = db.Column(db.Integer, primary_key=True)
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    category = db.Column(db.String(50), index=True)
    location_zone = db.Column(db.String(50))
    opening_hours = db.Column(db.String(100))
    description = db.Column(db.Text)
    menu_items = db.relationship('MenuItem', backref='concession', lazy=True)
    orders = db.relationship('Order', backref='concession', lazy=True)


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
    season_tickets = db.relationship('SeasonTicket', backref='stadium', lazy=True)
    analytics = db.relationship('BookingAnalytics', backref='stadium', lazy=True)


class Team(db.Model):
    __tablename__ = 'team'
    
    id = db.Column(db.Integer, primary_key=True)
    team_name = db.Column(db.String(100), nullable=False, index=True)
    tagline = db.Column(db.String(200))
    about = db.Column(db.Text)
    founding_year = db.Column(db.Integer)
    championships_won = db.Column(db.Integer, default=0)
    home_ground = db.Column(db.String(100))
    team_color = db.Column(db.String(50))
    color1 = db.Column(db.String(20))
    color2 = db.Column(db.String(20))
    coach_name = db.Column(db.String(100))
    manager = db.Column(db.String(100))
    owner_name = db.Column(db.String(100))
    fun_fact = db.Column(db.Text)
    team_logo = db.Column(db.String(200))
    home_city = db.Column(db.String(100), index=True)
    team_type = db.Column(db.String(50), index=True)
    
    players = db.relationship('Player', backref='team', lazy=True)
    home_events = db.relationship('Event', foreign_keys='Event.home_team_id', backref='home_team', lazy=True)
    away_events = db.relationship('Event', foreign_keys='Event.away_team_id', backref='away_team', lazy=True)

class Player(db.Model):
    __tablename__ = 'player'
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True, index=True)
    player_name = db.Column(db.String(100), nullable=False, index=True)
    age = db.Column(db.Integer)
    batting_style = db.Column(db.String(50))
    bowling_style = db.Column(db.String(50))
    player_role = db.Column(db.String(50), index=True)
    is_captain = db.Column(db.Boolean, default=False)
    is_wicket_keeper = db.Column(db.Boolean, default=False)
    nationality = db.Column(db.String(50), index=True)
    jersey_number = db.Column(db.Integer)
    market_value = db.Column(db.Float)
    photo_url = db.Column(db.String(200))

class Event(db.Model):
    __tablename__ = 'event'
    
    id = db.Column(db.Integer, primary_key=True)
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'), nullable=False, index=True)
    event_name = db.Column(db.String(100), nullable=False, index=True)
    event_type = db.Column(db.String(50), index=True)
    tournament_name = db.Column(db.String(100))
    event_date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time)
    home_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False, index=True)
    away_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False, index=True)
    match_status = db.Column(db.String(50), default='Scheduled', index=True)
    attendance = db.Column(db.Integer, default=0)
    
    match = db.relationship('Match', backref='event', uselist=False)
    tickets = db.relationship('Ticket', backref='event', lazy=True)
    umpires = db.relationship('EventUmpire', backref='event', lazy=True)
    analytics = db.relationship('BookingAnalytics', backref='event', lazy=True)


class Match(db.Model):
    __tablename__ = 'match'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), unique=True, nullable=False, index=True)
    home_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False, index=True)
    away_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False, index=True)
    toss_winner_id = db.Column(db.Integer, db.ForeignKey('team.id'), index=True)
    toss_decision = db.Column(db.String(10))
    home_score = db.Column(db.Integer, default=0)
    away_score = db.Column(db.Integer, default=0)
    home_wickets = db.Column(db.Integer, default=0)
    away_wickets = db.Column(db.Integer, default=0)
    home_overs = db.Column(db.Float, default=0.0)
    away_overs = db.Column(db.Float, default=0.0)
    result_type = db.Column(db.String(20))
    winning_margin = db.Column(db.String(20))
    updates = db.relationship('MatchUpdate', backref='match', lazy=True)


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
    season_tickets = db.relationship('SeasonTicket', backref='seat', lazy=True)


class Photo(db.Model):
    __tablename__ = 'photo'
    id = db.Column(db.Integer, primary_key=True)
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'), nullable=False, index=True)
    url = db.Column(db.String(200), nullable=False)
    caption = db.Column(db.String(200))


class MenuItem(db.Model):
    __tablename__ = 'menu_item'
    id = db.Column(db.Integer, primary_key=True)
    concession_id = db.Column(db.Integer, db.ForeignKey('concession.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), index=True)
    is_available = db.Column(db.Boolean, default=True, index=True)
    is_vegetarian = db.Column(db.Boolean, default=True, index=True)


class Parking(db.Model):
    __tablename__ = 'parking'
    id = db.Column(db.Integer, primary_key=True)
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'), nullable=False, index=True)
    zone = db.Column(db.String(50), nullable=False, index=True)
    capacity = db.Column(db.Integer, nullable=False)
    rate_per_hour = db.Column(db.Float, nullable=False)
    bookings = db.relationship('ParkingBooking', backref='parking', lazy=True)


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
    season_tickets = db.relationship('SeasonTicket', backref='customer', lazy=True)
    accessibility_needs = db.relationship('AccessibilityAccommodation', foreign_keys='AccessibilityAccommodation.customer_id', backref='customer', lazy=True)
    verified_by_user = db.relationship('AccessibilityAccommodation', foreign_keys='AccessibilityAccommodation.verified_by')
    verification_submissions = db.relationship('VerificationSubmission', backref='user', lazy=True)
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


class Booking(db.Model):
    __tablename__ = 'booking'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    total_amount = db.Column(db.Float, nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    tickets = db.relationship('Ticket', backref='booking', lazy=True)
    payments = db.relationship('Payment', backref='booking', lazy=True)


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


class Order(db.Model):
    __tablename__ = 'order'
    id = db.Column(db.Integer, primary_key=True)
    concession_id = db.Column(db.Integer, db.ForeignKey('concession.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    total_amount = db.Column(db.Float, nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_status = db.Column(db.String(20))


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


class StadiumAdmin(db.Model):
    __tablename__ = 'stadium_admin'
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'))


class EventUmpire(db.Model):
    __tablename__ = 'event_umpire'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    umpire_name = db.Column(db.String(100))


class Payment(db.Model):
    __tablename__ = 'payment'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'))
    amount = db.Column(db.Float)
    payment_method = db.Column(db.String(50))
    transaction_id = db.Column(db.String(100))
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)

# Models from enhanced_models.py
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

class QRCode(db.Model):
    __tablename__ = 'qr_code'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(200), unique=True, nullable=False)
    qr_type = db.Column(db.String(20), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=True)
    parking_booking_id = db.Column(db.Integer, db.ForeignKey('parking_booking.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    is_used = db.Column(db.Boolean, default=False)
    used_at = db.Column(db.DateTime)
    security_hash = db.Column(db.String(128))
    scan_count = db.Column(db.Integer, default=0)
    max_scans = db.Column(db.Integer, default=1)

class Notification(db.Model):
    __tablename__ = 'notification'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    template_id = db.Column(db.String(50))
    status = db.Column(db.String(20), default='pending')
    sent_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    opened_at = db.Column(db.DateTime)
    clicked_at = db.Column(db.DateTime)
    sendgrid_message_id = db.Column(db.String(100))
    twilio_message_sid = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    retry_count = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)

class MatchUpdate(db.Model):
    __tablename__ = 'match_update'
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=False)
    update_type = db.Column(db.String(20), nullable=False)
    update_data = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ball_number = db.Column(db.Float)
    is_broadcasted = db.Column(db.Boolean, default=False)
    broadcasted_at = db.Column(db.DateTime)

class BookingAnalytics(db.Model):
    __tablename__ = 'booking_analytics'
    id = db.Column(db.Integer, primary_key=True)
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=True)
    date = db.Column(db.Date, nullable=False)
    hour = db.Column(db.Integer)
    total_bookings = db.Column(db.Integer, default=0)
    total_revenue = db.Column(db.Float, default=0.0)
    unique_customers = db.Column(db.Integer, default=0)
    advance_booking_days = db.Column(db.Float)
    popular_sections = db.Column(db.Text)
    new_customers = db.Column(db.Integer, default=0)
    returning_customers = db.Column(db.Integer, default=0)
    conversion_rate = db.Column(db.Float, default=0.0)
    average_order_value = db.Column(db.Float, default=0.0)

class SystemLog(db.Model):
    __tablename__ = 'system_log'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    log_level = db.Column(db.String(10), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    request_url = db.Column(db.String(500))
    request_method = db.Column(db.String(10))
    extra_data = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class WebSocketConnection(db.Model):
    __tablename__ = 'websocket_connection'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False)
    socket_id = db.Column(db.String(100), unique=True, nullable=False)
    subscribed_matches = db.Column(db.Text)
    subscribed_stadiums = db.Column(db.Text)
    connected_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_ping = db.Column(db.DateTime, default=datetime.utcnow)
    disconnected_at = db.Column(db.DateTime)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))

class SeasonTicket(db.Model):
    __tablename__ = 'season_ticket'
    id = db.Column(db.BigInteger, primary_key=True)
    customer_id = db.Column(db.BigInteger, db.ForeignKey('customer.id'), nullable=False, index=True)
    stadium_id = db.Column(db.BigInteger, db.ForeignKey('stadium.id'), nullable=False, index=True)
    seat_id = db.Column(db.BigInteger, db.ForeignKey('seat.id'), nullable=False, index=True)
    season_name = db.Column(db.Text, nullable=False)
    season_start_date = db.Column(db.DateTime(timezone=True))
    season_end_date = db.Column(db.DateTime(timezone=True))
    total_matches = db.Column(db.Integer)
    matches_used = db.Column(db.Integer, default=0)
    matches_transferred = db.Column(db.Integer, default=0)
    price_per_match = db.Column(db.Numeric(12, 2))
    total_price = db.Column(db.Numeric(12, 2))
    ticket_status = db.Column(db.Text)
    priority_booking = db.Column(db.Boolean, default=False)
    transfer_limit = db.Column(db.Integer, default=0)
    activated_at = db.Column(db.DateTime(timezone=True))

    __table_args__ = (
        db.Index('idx_season_ticket_season_dates', 'season_start_date', 'season_end_date'),
        db.Index('idx_season_ticket_status_start', 'ticket_status', db.desc('season_start_date')),
    )

class AccessibilityAccommodation(db.Model):
    __tablename__ = 'accessibility_accommodation'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    accommodation_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    severity_level = db.Column(db.String(20))
    requires_wheelchair_access = db.Column(db.Boolean, default=False)
    requires_companion_seat = db.Column(db.Boolean, default=False)
    requires_aisle_access = db.Column(db.Boolean, default=False)
    requires_hearing_loop = db.Column(db.Boolean, default=False)
    requires_sign_language = db.Column(db.Boolean, default=False)
    requires_braille = db.Column(db.Boolean, default=False)
    mobility_equipment = db.Column(db.String(100))
    service_animal = db.Column(db.Boolean, default=False)
    service_animal_type = db.Column(db.String(50))
    preferred_communication = db.Column(db.String(50))
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(20))
    is_verified = db.Column(db.Boolean, default=False)
    verification_document = db.Column(db.String(200))
    verified_at = db.Column(db.DateTime)
    verified_by = db.Column(db.Integer, db.ForeignKey('customer.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class VerificationSubmission(db.Model):
    __tablename__ = 'verification_submission'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    document_urls = db.Column(db.Text)
    notes = db.Column(db.Text)
    submission_timestamp = db.Column(db.DateTime, default=datetime.utcnow)