from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from core import db

# Models from app.py
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
    
    # Relationships
    events = db.relationship('Event', backref='stadium', lazy=True)
    seats = db.relationship('Seat', backref='stadium', lazy=True)
    concessions = db.relationship('Concession', backref='stadium', lazy=True)
    parkings = db.relationship('Parking', backref='stadium', lazy=True)
    photos = db.relationship('Photo', backref='stadium', lazy=True)

    @property
    def upcoming_matches(self):
        from datetime import datetime
        return Event.query.filter(
            Event.stadium_id == self.id,
            Event.event_date >= datetime.utcnow().date()
        ).order_by(Event.event_date).all()

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
    
    # Relationships
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
    
    # Relationships
    match = db.relationship('Match', backref='event', uselist=False)
    tickets = db.relationship('Ticket', backref='event', lazy=True)
    umpires = db.relationship('EventUmpire', backref='event', lazy=True)

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

class Seat(db.Model):
    __tablename__ = 'seat'
    
    id = db.Column(db.Integer, primary_key=True)
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'))
    section = db.Column(db.String(50), nullable=False)
    row_number = db.Column(db.String(10), nullable=False)
    seat_number = db.Column(db.String(10), nullable=False)
    seat_type = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Float, nullable=False)
    has_shade = db.Column(db.Boolean, default=False)
    
    # Relationships
    tickets = db.relationship('Ticket', backref='seat', lazy=True)

class Customer(db.Model, UserMixin):
    __tablename__ = 'customer'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(200))
    membership_level = db.Column(db.String(20), default='Basic')
    favorite_team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    role = db.Column(db.String(20), default='customer')  # 'customer', 'admin', or 'stadium_owner'
    
    # Relationships
    tickets = db.relationship('Ticket', backref='customer', lazy=True)
    orders = db.relationship('Order', backref='customer', lazy=True)
    parking_bookings = db.relationship('ParkingBooking', backref='customer', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def get_administered_stadiums(self):
        """Get list of stadium IDs this admin manages"""
        if not self.is_admin():
            return []
        admin_records = StadiumAdmin.query.filter_by(admin_id=self.id).all()
        return [record.stadium_id for record in admin_records]

class Booking(db.Model):
    """Represents a single transaction for booking one or more tickets."""
    __tablename__ = 'booking'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    
    # Relationships
    customer = db.relationship('Customer', backref='bookings')
    tickets = db.relationship('Ticket', backref='booking', lazy='dynamic')
    payment = db.relationship('Payment', backref='booking', uselist=False, cascade="all, delete-orphan")

class Ticket(db.Model):
    __tablename__ = 'ticket'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    seat_id = db.Column(db.Integer, db.ForeignKey('seat.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id')) # Can be deprecated in favor of booking.customer
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    ticket_status = db.Column(db.String(20), default='Booked')
    ticket_type = db.Column(db.String(20))
    access_gate = db.Column(db.String(10))

class Payment(db.Model):
    __tablename__ = 'payment'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), unique=True)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(20), nullable=False)
    transaction_id = db.Column(db.String(100), unique=True)

class Umpire(db.Model):
    __tablename__ = 'umpire'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    nationality = db.Column(db.String(50))
    umpire_level = db.Column(db.String(20))
    matches_officiated = db.Column(db.Integer, default=0)
    
    # Relationships
    events = db.relationship('EventUmpire', backref='umpire', lazy=True)

class EventUmpire(db.Model):
    __tablename__ = 'event_umpire'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    umpire_id = db.Column(db.Integer, db.ForeignKey('umpire.id'))
    umpire_role = db.Column(db.String(20))

class Concession(db.Model):
    __tablename__ = 'concession'
    
    id = db.Column(db.Integer, primary_key=True)
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'))
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    location_zone = db.Column(db.String(50))
    opening_hours = db.Column(db.String(100))
    description = db.Column(db.Text)

    # Relationships
    orders = db.relationship('Order', backref='concession', lazy=True)

class MenuItem(db.Model):
    __tablename__ = 'menu_item'

    id = db.Column(db.Integer, primary_key=True)
    concession_id = db.Column(db.Integer, db.ForeignKey('concession.id'))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50))  # e.g., "Main", "Side", "Drink"
    is_available = db.Column(db.Boolean, default=True)
    is_vegetarian = db.Column(db.Boolean, default=False) # New column for vegetarian option

    # Relationships
    concession = db.relationship('Concession', backref='menu_items')

class Order(db.Model):
    __tablename__ = 'order'
    
    id = db.Column(db.Integer, primary_key=True)
    concession_id = db.Column(db.Integer, db.ForeignKey('concession.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String(20), default='Pending')

class Parking(db.Model):
    __tablename__ = 'parking'
    
    id = db.Column(db.Integer, primary_key=True)
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'))
    zone = db.Column(db.String(50), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    rate_per_hour = db.Column(db.Float, nullable=False)
    
    # Relationships
    bookings = db.relationship('ParkingBooking', backref='parking', lazy=True)

class ParkingBooking(db.Model):
    __tablename__ = 'parking_booking'
    
    id = db.Column(db.Integer, primary_key=True)
    parking_id = db.Column(db.Integer, db.ForeignKey('parking.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    vehicle_number = db.Column(db.String(20), nullable=False)
    arrival_time = db.Column(db.DateTime)
    departure_time = db.Column(db.DateTime)
    amount_paid = db.Column(db.Float, default=0.0)

class StadiumAdmin(db.Model):
    """Junction table for admin-stadium relationships"""
    __tablename__ = 'stadium_admin'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'), nullable=False)
    assigned_date = db.Column(db.DateTime, default=datetime.utcnow)

class StadiumOwner(db.Model):
    """Junction table for stadium_owner-stadium relationships"""
    __tablename__ = 'stadium_owner'
    
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'), nullable=False)
    assigned_date = db.Column(db.DateTime, default=datetime.utcnow)

class Photo(db.Model):
    __tablename__ = 'photo'
    id = db.Column(db.Integer, primary_key=True)
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'))
    url = db.Column(db.String(200), nullable=False)
    caption = db.Column(db.String(200))

# Models from enhanced_models.py
class CustomerProfile(db.Model):
    """Extended customer profile for enhanced features"""
    __tablename__ = 'customer_profile'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), unique=True, nullable=False)
    
    # Multi-factor Authentication
    mfa_enabled = db.Column(db.Boolean, default=False)
    mfa_secret = db.Column(db.String(32))  # TOTP secret
    backup_codes = db.Column(db.Text)  # JSON array of backup codes
    phone_verified = db.Column(db.Boolean, default=False)
    
    # Preferences
    notification_preferences = db.Column(db.Text)  # JSON: {"email": True, "sms": True, "push": False}
    preferred_language = db.Column(db.String(5), default='en')
    timezone = db.Column(db.String(50), default='UTC')
    
    # Analytics
    total_bookings = db.Column(db.Integer, default=0)
    total_spent = db.Column(db.Float, default=0.0)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    loyalty_points = db.Column(db.Integer, default=0)
    
    # Relationships
    customer = db.relationship('Customer', backref='profile', uselist=False)

class PaymentTransaction(db.Model):
    """Enhanced payment tracking with Stripe integration"""
    __tablename__ = 'payment_transaction'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'))
    parking_booking_id = db.Column(db.Integer, db.ForeignKey('parking_booking.id'))
    
    # Stripe integration
    stripe_payment_intent_id = db.Column(db.String(200), unique=True)
    stripe_charge_id = db.Column(db.String(200))
    stripe_customer_id = db.Column(db.String(200))
    
    # Payment details
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='AUD')
    payment_method = db.Column(db.String(50))  # card, bank_transfer, etc.
    payment_status = db.Column(db.String(20), default='pending')  # pending, succeeded, failed, canceled
    
    # Transaction metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    payment_date = db.Column(db.DateTime)
    
    # Additional info
    description = db.Column(db.String(500))
    receipt_url = db.Column(db.String(500))
    failure_reason = db.Column(db.String(500))
    
    # Relationships
    customer = db.relationship('Customer', backref='payment_transactions')

class QRCode(db.Model):
    """QR codes for tickets and parking passes"""
    __tablename__ = 'qr_code'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(200), unique=True, nullable=False)
    qr_type = db.Column(db.String(20), nullable=False)  # 'ticket', 'parking'
    
    # Reference IDs
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=True)
    parking_booking_id = db.Column(db.Integer, db.ForeignKey('parking_booking.id'), nullable=True)
    
    # QR Code details
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    is_used = db.Column(db.Boolean, default=False)
    used_at = db.Column(db.DateTime)
    
    # Security
    security_hash = db.Column(db.String(128))  # SHA-256 hash for verification
    scan_count = db.Column(db.Integer, default=0)
    max_scans = db.Column(db.Integer, default=1)
    
    # Relationships
    ticket = db.relationship('Ticket', backref='qr_codes')
    parking_booking = db.relationship('ParkingBooking', backref='qr_codes')

class Notification(db.Model):
    """Notification system for emails and SMS"""
    __tablename__ = 'notification'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    
    # Notification details
    notification_type = db.Column(db.String(50), nullable=False)  # 'email', 'sms', 'push'
    category = db.Column(db.String(50), nullable=False)  # 'booking_confirmation', 'reminder', 'update'
    
    # Content
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    template_id = db.Column(db.String(50))  # SendGrid template ID
    
    # Status tracking
    status = db.Column(db.String(20), default='pending')  # pending, sent, failed, delivered
    sent_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    opened_at = db.Column(db.DateTime)
    clicked_at = db.Column(db.DateTime)
    
    # External service IDs
    sendgrid_message_id = db.Column(db.String(100))
    twilio_message_sid = db.Column(db.String(100))
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    retry_count = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    
    # Relationships
    customer = db.relationship('Customer', backref='notifications')

class MatchUpdate(db.Model):
    """Real-time match updates for WebSocket broadcasting"""
    __tablename__ = 'match_update'
    
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=False)
    
    # Update details
    update_type = db.Column(db.String(20), nullable=False)  # 'score', 'wicket', 'over', 'status'
    update_data = db.Column(db.Text, nullable=False)  # JSON data
    
    # Timing
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ball_number = db.Column(db.Float)  # Over.Ball format (e.g., 15.3 for 15th over, 3rd ball)
    
    # Broadcasting
    is_broadcasted = db.Column(db.Boolean, default=False)
    broadcasted_at = db.Column(db.DateTime)
    
    # Relationships
    match = db.relationship('Match', backref='updates')

class ChatConversation(db.Model):
    """AI chatbot conversation history"""
    __tablename__ = 'chat_conversation'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    session_id = db.Column(db.String(100), nullable=False)
    
    # Conversation details
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    
    # Metadata
    user_agent = db.Column(db.String(500))
    ip_address = db.Column(db.String(45))
    language = db.Column(db.String(5), default='en')
    
    # Analytics
    message_count = db.Column(db.Integer, default=0)
    satisfaction_rating = db.Column(db.Integer)  # 1-5 rating
    
    # Relationships
    customer = db.relationship('Customer', backref='chat_conversations')
    messages = db.relationship('ChatMessage', backref='conversation', lazy='dynamic')

class ChatMessage(db.Model):
    """Individual chat messages"""
    __tablename__ = 'chat_message'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('chat_conversation.id'), nullable=False)
    
    # Message details
    sender_type = db.Column(db.String(10), nullable=False)  # 'user', 'bot'
    message = db.Column(db.Text, nullable=False)
    
    # AI metadata
    intent = db.Column(db.String(100))  # Detected intent
    confidence_score = db.Column(db.Float)
    openai_response_id = db.Column(db.String(100))
    
    # Timing
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Processing
    tokens_used = db.Column(db.Integer)
    response_time_ms = db.Column(db.Integer)

class BookingAnalytics(db.Model):
    """Enhanced booking analytics"""
    __tablename__ = 'booking_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=True)
    
    # Time dimension
    date = db.Column(db.Date, nullable=False)
    hour = db.Column(db.Integer)  # 0-23 for hourly analytics
    
    # Metrics
    total_bookings = db.Column(db.Integer, default=0)
    total_revenue = db.Column(db.Float, default=0.0)
    unique_customers = db.Column(db.Integer, default=0)
    
    # Booking patterns
    advance_booking_days = db.Column(db.Float)  # Average days in advance
    popular_sections = db.Column(db.Text)  # JSON array of popular sections
    
    # Customer demographics
    new_customers = db.Column(db.Integer, default=0)
    returning_customers = db.Column(db.Integer, default=0)
    
    # Performance metrics
    conversion_rate = db.Column(db.Float, default=0.0)  # Page visits to bookings
    average_order_value = db.Column(db.Float, default=0.0)
    
    # Relationships
    stadium = db.relationship('Stadium', backref='analytics')
    event = db.relationship('Event', backref='analytics')

class SystemLog(db.Model):
    """System logs for security and auditing"""
    __tablename__ = 'system_log'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    
    # Log details
    log_level = db.Column(db.String(10), nullable=False)  # INFO, WARNING, ERROR, CRITICAL
    category = db.Column(db.String(50), nullable=False)  # auth, payment, booking, system
    action = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    # Context
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    request_url = db.Column(db.String(500))
    request_method = db.Column(db.String(10))
    
    # Additional data
    metadata = db.Column(db.Text)  # JSON additional data
    
    # Timing
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    customer = db.relationship('Customer', backref='system_logs')

class WebSocketConnection(db.Model):
    """Track active WebSocket connections for real-time features"""
    __tablename__ = 'websocket_connection'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    
    # Connection details
    session_id = db.Column(db.String(100), unique=True, nullable=False)
    socket_id = db.Column(db.String(100), unique=True, nullable=False)
    
    # Subscriptions
    subscribed_matches = db.Column(db.Text)  # JSON array of match IDs
    subscribed_stadiums = db.Column(db.Text)  # JSON array of stadium IDs
    
    # Connection status
    connected_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_ping = db.Column(db.DateTime, default=datetime.utcnow)
    disconnected_at = db.Column(db.DateTime)
    
    # Client info
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    
    # Relationships
    customer = db.relationship('Customer', backref='websocket_connections')
