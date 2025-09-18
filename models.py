from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()

class Concession(db.Model):
    __tablename__ = 'concession'
    id = db.Column(db.Integer, primary_key=True)
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'))
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    location_zone = db.Column(db.String(50))
    opening_hours = db.Column(db.String(100))
    menu_items = db.relationship('MenuItem', backref='concession', lazy=True)
    orders = db.relationship('Order', backref='concession', lazy=True)


class Stadium(db.Model):
    __tablename__ = 'stadium'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    contact_number = db.Column(db.String(20))
    opening_year = db.Column(db.Integer)
    pitch_type = db.Column(db.String(50))
    boundary_length = db.Column(db.Integer)
    floodlight_quality = db.Column(db.String(20))
    has_dressing_rooms = db.Column(db.Boolean, default=True)
    has_practice_nets = db.Column(db.Boolean, default=True)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(200), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
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
    team_name = db.Column(db.String(100), nullable=False)
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
    home_city = db.Column(db.String(100))
    team_type = db.Column(db.String(50))
    
    players = db.relationship('Player', backref='team', lazy=True)
    home_events = db.relationship('Event', foreign_keys='Event.home_team_id', backref='home_team', lazy=True)
    away_events = db.relationship('Event', foreign_keys='Event.away_team_id', backref='away_team', lazy=True)

class Player(db.Model):
    __tablename__ = 'player'
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)
    player_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    batting_style = db.Column(db.String(50))
    bowling_style = db.Column(db.String(50))
    player_role = db.Column(db.String(50))
    is_captain = db.Column(db.Boolean, default=False)
    is_wicket_keeper = db.Column(db.Boolean, default=False)
    nationality = db.Column(db.String(50))
    jersey_number = db.Column(db.Integer)
    market_value = db.Column(db.Float)
    photo_url = db.Column(db.String(200))

class Event(db.Model):
    __tablename__ = 'event'
    
    id = db.Column(db.Integer, primary_key=True)
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'))
    event_name = db.Column(db.String(100), nullable=False)
    event_type = db.Column(db.String(50))
    tournament_name = db.Column(db.String(100))
    event_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time)
    home_team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    away_team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    match_status = db.Column(db.String(50), default='Scheduled')
    attendance = db.Column(db.Integer, default=0)
    
    match = db.relationship('Match', backref='event', uselist=False)
    tickets = db.relationship('Ticket', backref='event', lazy=True)
    umpires = db.relationship('EventUmpire', backref='event', lazy=True)
    season_ticket_matches = db.relationship('SeasonTicketMatch', backref='event', lazy=True)
    analytics = db.relationship('BookingAnalytics', backref='event', lazy=True)


class Match(db.Model):
    __tablename__ = 'match'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), unique=True)
    home_team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    away_team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    toss_winner_id = db.Column(db.Integer, db.ForeignKey('team.id'))
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
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'))
    seat_number = db.Column(db.String(20), nullable=False)
    section = db.Column(db.String(50))
    row_number = db.Column(db.String(10))
    seat_type = db.Column(db.String(50))
    price = db.Column(db.Float)
    has_shade = db.Column(db.Boolean, default=False)
    is_available = db.Column(db.Boolean, default=True)
    season_tickets = db.relationship('SeasonTicket', backref='seat', lazy=True)


class Photo(db.Model):
    __tablename__ = 'photo'
    id = db.Column(db.Integer, primary_key=True)
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'))
    url = db.Column(db.String(200), nullable=False)
    caption = db.Column(db.String(200))


class MenuItem(db.Model):
    __tablename__ = 'menu_item'
    id = db.Column(db.Integer, primary_key=True)
    concession_id = db.Column(db.Integer, db.ForeignKey('concession.id'))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50))
    is_available = db.Column(db.Boolean, default=True)


class Parking(db.Model):
    __tablename__ = 'parking'
    id = db.Column(db.Integer, primary_key=True)
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'))
    zone = db.Column(db.String(50), nullable=False)
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
    sent_transfers = db.relationship('TicketTransfer', foreign_keys='TicketTransfer.from_customer_id', backref='from_customer', lazy=True)
    received_transfers = db.relationship('TicketTransfer', foreign_keys='TicketTransfer.to_customer_id', backref='to_customer', lazy=True)
    selling_tickets = db.relationship('ResaleMarketplace', foreign_keys='ResaleMarketplace.seller_id', backref='seller', lazy=True)
    bought_tickets = db.relationship('ResaleMarketplace', foreign_keys='ResaleMarketplace.buyer_id', backref='buyer', lazy=True)
    season_tickets = db.relationship('SeasonTicket', backref='customer', lazy=True)
    received_season_matches = db.relationship('SeasonTicketMatch', backref='transferred_to', lazy=True)
    accessibility_needs = db.relationship('AccessibilityAccommodation', foreign_keys='AccessibilityAccommodation.customer_id', backref='customer', lazy=True)
    verified_by_user = db.relationship('AccessibilityAccommodation', foreign_keys='AccessibilityAccommodation.verified_by')
    assigned_accessibility_tasks = db.relationship('AccessibilityBooking', backref='assigned_staff', lazy=True)
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
    accessibility_bookings = db.relationship('AccessibilityBooking', backref='booking', lazy=True)


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
    
    transfers = db.relationship('TicketTransfer', backref='ticket', lazy=True)
    marketplace_listings = db.relationship('ResaleMarketplace', backref='ticket', lazy=True)
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

class ChatConversation(db.Model):
    __tablename__ = 'chat_conversation'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    session_id = db.Column(db.String(100), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    user_agent = db.Column(db.String(500))
    ip_address = db.Column(db.String(45))
    language = db.Column(db.String(5), default='en')
    message_count = db.Column(db.Integer, default=0)
    satisfaction_rating = db.Column(db.Integer)
    messages = db.relationship('ChatMessage', backref='conversation', lazy='dynamic')

class ChatMessage(db.Model):
    __tablename__ = 'chat_message'
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('chat_conversation.id'), nullable=False)
    sender_type = db.Column(db.String(10), nullable=False)
    message = db.Column(db.Text, nullable=False)
    intent = db.Column(db.String(100))
    confidence_score = db.Column(db.Float)
    openai_response_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tokens_used = db.Column(db.Integer)
    response_time_ms = db.Column(db.Integer)

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

class TicketTransfer(db.Model):
    __tablename__ = 'ticket_transfer'
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    from_customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    to_customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    to_email = db.Column(db.String(100))
    transfer_status = db.Column(db.String(20), default='pending')
    transfer_code = db.Column(db.String(32), unique=True, nullable=False)
    transfer_fee = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    completed_at = db.Column(db.DateTime)
    verification_code = db.Column(db.String(6))
    is_verified = db.Column(db.Boolean, default=False)

class ResaleMarketplace(db.Model):
    __tablename__ = 'resale_marketplace'
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    original_price = db.Column(db.Float, nullable=False)
    listing_price = db.Column(db.Float, nullable=False)
    final_price = db.Column(db.Float)
    platform_fee = db.Column(db.Float, default=0.0)
    seller_fee = db.Column(db.Float, default=0.0)
    listing_status = db.Column(db.String(20), default='active')
    listing_description = db.Column(db.Text)
    is_negotiable = db.Column(db.Boolean, default=False)
    listed_at = db.Column(db.DateTime, default=datetime.utcnow)
    sold_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    is_verified = db.Column(db.Boolean, default=False)
    verification_status = db.Column(db.String(20), default='pending')

class SeasonTicket(db.Model):
    __tablename__ = 'season_ticket'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'), nullable=False)
    seat_id = db.Column(db.Integer, db.ForeignKey('seat.id'), nullable=False)
    season_name = db.Column(db.String(100), nullable=False)
    season_start_date = db.Column(db.Date, nullable=False)
    season_end_date = db.Column(db.Date, nullable=False)
    total_matches = db.Column(db.Integer, nullable=False)
    matches_used = db.Column(db.Integer, default=0)
    matches_transferred = db.Column(db.Integer, default=0)
    total_price = db.Column(db.Float, nullable=False)
    price_per_match = db.Column(db.Float, nullable=False)
    ticket_status = db.Column(db.String(20), default='active')
    priority_booking = db.Column(db.Boolean, default=True)
    transfer_limit = db.Column(db.Integer, default=5)
    purchased_at = db.Column(db.DateTime, default=datetime.utcnow)
    activated_at = db.Column(db.DateTime)
    matches = db.relationship('SeasonTicketMatch', backref='season_ticket', lazy='dynamic')

class SeasonTicketMatch(db.Model):
    __tablename__ = 'season_ticket_match'
    id = db.Column(db.Integer, primary_key=True)
    season_ticket_id = db.Column(db.Integer, db.ForeignKey('season_ticket.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    used_at = db.Column(db.DateTime)
    is_transferred = db.Column(db.Boolean, default=False)
    transferred_to_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    transferred_at = db.Column(db.DateTime)
    transfer_price = db.Column(db.Float, default=0.0)

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
    bookings = db.relationship('AccessibilityBooking', backref='accommodation', lazy='dynamic')

class AccessibilityBooking(db.Model):
    __tablename__ = 'accessibility_booking'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    accommodation_id = db.Column(db.Integer, db.ForeignKey('accessibility_accommodation.id'), nullable=False)
    requested_accommodations = db.Column(db.Text)
    provided_accommodations = db.Column(db.Text)
    staff_notes = db.Column(db.Text)
    special_instructions = db.Column(db.Text)
    accommodation_status = db.Column(db.String(20), default='requested')
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    fulfillment_notes = db.Column(db.Text)
    fulfilled_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class VerificationSubmission(db.Model):
    __tablename__ = 'verification_submission'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    document_urls = db.Column(db.Text)
    notes = db.Column(db.Text)
    submission_timestamp = db.Column(db.DateTime, default=datetime.utcnow)