from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import re
from dotenv import load_dotenv
from functools import wraps
from flask_socketio import SocketIO
from chatbot import handle_chat_message

# Import our utility functions
from utils import (
    validate_email, validate_phone, validate_password_strength,
    sanitize_input, flash_errors, get_user_statistics, get_analytics_data,
    handle_form_errors, REGISTRATION_VALIDATION_RULES, STADIUM_VALIDATION_RULES,
    EVENT_VALIDATION_RULES, get_upcoming_events
)

# Load environment variables (prefer local cricverse.env, fallback to .env)
if os.path.exists('cricverse.env'):
    load_dotenv('cricverse.env')
else:
    load_dotenv()

app = Flask(__name__)

# Configuration with fallbacks
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'cricverse-secret-key-change-in-production')

# Database configuration with PostgreSQL fallback
database_url = os.getenv('DATABASE_URL')

# If no DATABASE_URL is set, try to construct PostgreSQL URL for stadium_db
if not database_url:
    # Try PostgreSQL first with stadium_db database name
    pg_user = os.getenv('POSTGRES_USER', 'postgres')
    pg_password = os.getenv('POSTGRES_PASSWORD', 'admin')
    pg_host = os.getenv('POSTGRES_HOST', 'localhost')
    pg_port = os.getenv('POSTGRES_PORT', '5432')
    pg_database = os.getenv('POSTGRES_DB', 'stadium_db')
    
    # Construct PostgreSQL URL
    database_url = f'postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}'
    print(f"No DATABASE_URL found. Attempting PostgreSQL connection to stadium_db...")
    
    # Test PostgreSQL connection
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=pg_host,
            port=pg_port,
            database=pg_database,
            user=pg_user,
            password=pg_password
        )
        conn.close()
        print(f"[SUCCESS] PostgreSQL connection successful: {pg_database}")
    except Exception as e:
        print(f"[WARNING] PostgreSQL connection failed: {e}")
        print(f"Falling back to SQLite...")
        database_url = 'sqlite:///cricverse.db'

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Database connection pool settings for PostgreSQL
if 'postgresql' in database_url:
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 0,
        'pool_size': 5,  # Reduced pool size for Supabase
        'echo': False  # Disable SQL logging for performance
    }

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Initialize SocketIO for real-time features
from realtime_simple import init_socketio
socketio = init_socketio(app)

# Database connection info
if 'postgresql' in database_url:
    # Mask password in PostgreSQL URL for display
    display_url = database_url
    if '@' in display_url:
        parts = display_url.split('@')
        if ':' in parts[0]:
            user_pass = parts[0].split('://', 1)[1]
            if ':' in user_pass:
                user, password = user_pass.split(':', 1)
                display_url = display_url.replace(f':{password}@', ':****@')
else:
    display_url = database_url
    
print(f"[DATABASE] Database configured: {display_url}")

# Models
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

# Authentication decorators
def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not current_user.is_admin():
            flash('Access denied. Admin privileges required.')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def customer_required(f):
    """Decorator to require customer role (non-admin)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if current_user.is_admin():
            flash('Access denied. This page is for customers only.')
            return redirect(url_for('admin_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def stadium_owner_required(f):
    """Decorator to require stadium owner role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if current_user.role != 'stadium_owner':
            flash('Access denied. Stadium owner privileges required.')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def stadium_admin_required(stadium_id_param='stadium_id'):
    """Decorator to require admin access to specific stadium"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if not current_user.is_admin():
                flash('Access denied. Admin privileges required.')
                return redirect(url_for('dashboard'))
            
            # Get stadium_id from URL parameters
            stadium_id = kwargs.get(stadium_id_param)
            if not stadium_id:
                flash('Stadium ID not provided.')
                return redirect(url_for('admin_dashboard'))
            
            # Check if admin manages this stadium
            administered_stadiums = current_user.get_administered_stadiums()
            if stadium_id not in administered_stadiums:
                flash('Access denied. You do not manage this stadium.')
                return redirect(url_for('admin_dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_static_fallback_data():
    """Provide static fallback data when database is unavailable"""
    from collections import namedtuple
    from datetime import datetime, timedelta
    
    # Create mock objects with the same structure as database models
    MockEvent = namedtuple('MockEvent', ['id', 'event_name', 'event_date', 'start_time', 'stadium_id', 'home_team_id', 'away_team_id'])
    MockStadium = namedtuple('MockStadium', ['id', 'name', 'location', 'capacity', 'image_url'])
    MockTeam = namedtuple('MockTeam', ['id', 'team_name', 'team_logo', 'home_city'])
    MockPlayer = namedtuple('MockPlayer', ['id', 'player_name', 'player_role'])
    MockTeamData = namedtuple('MockTeamData', ['team', 'star_player'])
    
    # Mock upcoming events
    tomorrow = datetime.now().date() + timedelta(days=1)
    next_week = datetime.now().date() + timedelta(days=7)
    next_month = datetime.now().date() + timedelta(days=30)
    
    upcoming_events = [
        MockEvent(
            id=1,
            event_name="Melbourne Stars vs Sydney Sixers",
            event_date=tomorrow,
            start_time=datetime.strptime('19:30', '%H:%M').time(),
            stadium_id=1,
            home_team_id=1,
            away_team_id=2
        ),
        MockEvent(
            id=2,
            event_name="Perth Scorchers vs Brisbane Heat",
            event_date=next_week,
            start_time=datetime.strptime('20:00', '%H:%M').time(),
            stadium_id=2,
            home_team_id=3,
            away_team_id=4
        ),
        MockEvent(
            id=3,
            event_name="Adelaide Strikers vs Hobart Hurricanes",
            event_date=next_month,
            start_time=datetime.strptime('19:45', '%H:%M').time(),
            stadium_id=3,
            home_team_id=5,
            away_team_id=6
        )
    ]
    
    # Mock featured stadiums
    featured_stadiums = [
        MockStadium(
            id=1,
            name="Melbourne Cricket Ground",
            location="Melbourne, VIC",
            capacity=100024,
            image_url="/static/img/stadiums/mcg.jpg"
        ),
        MockStadium(
            id=2,
            name="Sydney Cricket Ground",
            location="Sydney, NSW",
            capacity=48000,
            image_url="/static/img/stadiums/scg.jpg"
        ),
        MockStadium(
            id=3,
            name="Perth Stadium",
            location="Perth, WA",
            capacity=60000,
            image_url="/static/img/stadiums/perth.jpg"
        )
    ]
    
    # Mock featured teams with star players
    featured_teams_data = [
        MockTeamData(
            team=MockTeam(
                id=1,
                team_name="Melbourne Stars",
                team_logo="/static/img/teams/Melbourne_Stars_logo.png",
                home_city="Melbourne"
            ),
            star_player=MockPlayer(
                id=1,
                player_name="Marcus Stoinis",
                player_role="All-rounder"
            )
        ),
        MockTeamData(
            team=MockTeam(
                id=2,
                team_name="Sydney Sixers",
                team_logo="/static/img/teams/Sydney_Sixers_logo.svg.png",
                home_city="Sydney"
            ),
            star_player=MockPlayer(
                id=2,
                player_name="Moises Henriques",
                player_role="Captain"
            )
        ),
        MockTeamData(
            team=MockTeam(
                id=3,
                team_name="Perth Scorchers",
                team_logo="/static/img/teams/Perth Scorchers.png",
                home_city="Perth"
            ),
            star_player=MockPlayer(
                id=3,
                player_name="Mitchell Marsh",
                player_role="All-rounder"
            )
        )
    ]
    
    return upcoming_events, featured_stadiums, featured_teams_data


@login_manager.user_loader
def load_user(user_id):
    return Customer.query.get(int(user_id))

# Initialize database function
def init_db():
    """Initialize the database with tables only (no sample seeding)."""
    try:
        db.create_all()
        print("Database tables ensured.")
    except Exception as e:
        print(f"Error initializing database: {e}")

# Admin Routes
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard showing managed stadiums with statistics"""
    administered_stadiums = current_user.get_administered_stadiums()
    stadiums_data = []
    
    for stadium_id in administered_stadiums:
        stadium = Stadium.query.get(stadium_id)
        if stadium:
            events_count = Event.query.filter_by(stadium_id=stadium_id).count()
            concessions_count = Concession.query.filter_by(stadium_id=stadium_id).count()
            parking_count = Parking.query.filter_by(stadium_id=stadium_id).count()
            seats_count = Seat.query.filter_by(stadium_id=stadium_id).count()
            
            stadiums_data.append({
                'stadium': stadium,
                'events_count': events_count,
                'concessions_count': concessions_count,
                'parking_count': parking_count,
                'seats_count': seats_count
            })
    
    return render_template('admin_dashboard.html', stadiums_data=stadiums_data)

@app.route('/admin/stadium/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_stadium():
    """Add a new stadium and assign current admin to it"""
    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        capacity = int(request.form['capacity'])
        contact_number = request.form.get('contact_number')
        opening_year = int(request.form['opening_year']) if request.form.get('opening_year') else None
        pitch_type = request.form.get('pitch_type')
        boundary_length = int(request.form['boundary_length']) if request.form.get('boundary_length') else None
        floodlight_quality = request.form.get('floodlight_quality')
        has_dressing_rooms = 'has_dressing_rooms' in request.form
        has_practice_nets = 'has_practice_nets' in request.form
        
        new_stadium = Stadium(
            name=name,
            location=location,
            capacity=capacity,
            contact_number=contact_number,
            opening_year=opening_year,
            pitch_type=pitch_type,
            boundary_length=boundary_length,
            floodlight_quality=floodlight_quality,
            has_dressing_rooms=has_dressing_rooms,
            has_practice_nets=has_practice_nets
        )
        
        db.session.add(new_stadium)
        db.session.flush()  # Get the stadium ID
        
        # Assign current admin to this stadium
        admin_assignment = StadiumAdmin(admin_id=current_user.id, stadium_id=new_stadium.id)
        db.session.add(admin_assignment)
        db.session.commit()
        
        flash(f'Stadium "{name}" created successfully and assigned to you.')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_add_stadium.html')

@app.route('/admin/stadium/<int:stadium_id>/edit', methods=['GET', 'POST'])
@login_required
@stadium_admin_required('stadium_id')
def edit_stadium(stadium_id):
    """Edit stadium details"""
    stadium = Stadium.query.get_or_404(stadium_id)
    
    if request.method == 'POST':
        stadium.name = request.form['name']
        stadium.location = request.form['location']
        stadium.capacity = int(request.form['capacity'])
        stadium.contact_number = request.form.get('contact_number')
        stadium.opening_year = int(request.form['opening_year']) if request.form.get('opening_year') else None
        stadium.pitch_type = request.form.get('pitch_type')
        stadium.boundary_length = int(request.form['boundary_length']) if request.form.get('boundary_length') else None
        stadium.floodlight_quality = request.form.get('floodlight_quality')
        stadium.has_dressing_rooms = 'has_dressing_rooms' in request.form
        stadium.has_practice_nets = 'has_practice_nets' in request.form
        
        db.session.commit()
        flash(f'Stadium "{stadium.name}" updated successfully.')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_edit_stadium.html', stadium=stadium)

@app.route('/admin/stadium/<int:stadium_id>/manage')
@login_required
@stadium_admin_required('stadium_id')
def manage_stadium(stadium_id):
    """Stadium management page showing events, concessions, parking, seats"""
    stadium = Stadium.query.get_or_404(stadium_id)
    events = Event.query.filter_by(stadium_id=stadium_id).all()
    concessions = Concession.query.filter_by(stadium_id=stadium_id).all()
    parking_zones = Parking.query.filter_by(stadium_id=stadium_id).all()
    seats = Seat.query.filter_by(stadium_id=stadium_id).all()
    
    # Group seats by section for display
    sections = {}
    for seat in seats:
        if seat.section not in sections:
            sections[seat.section] = []
        sections[seat.section].append(seat)
    
    return render_template('admin_manage_stadium.html', 
                         stadium=stadium, events=events, 
                         concessions=concessions, parking_zones=parking_zones, 
                         seats=seats, sections=sections)

@app.route('/admin/stadium/<int:stadium_id>/event/add', methods=['GET', 'POST'])
@login_required
@stadium_admin_required('stadium_id')
def add_event(stadium_id):
    """Add a new event to the stadium"""
    stadium = Stadium.query.get_or_404(stadium_id)
    teams = Team.query.all()
    
    if request.method == 'POST':
        event_name = request.form['event_name']
        event_type = request.form['event_type']
        tournament_name = request.form.get('tournament_name')
        event_date = datetime.strptime(request.form['event_date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(request.form['start_time'], '%H:%M').time()
        end_time = datetime.strptime(request.form['end_time'], '%H:%M').time() if request.form.get('end_time') else None
        home_team_id = int(request.form['home_team_id']) if request.form.get('home_team_id') else None
        away_team_id = int(request.form['away_team_id']) if request.form.get('away_team_id') else None
        match_status = request.form.get('match_status', 'Scheduled')
        
        new_event = Event(
            event_name=event_name,
            event_type=event_type,
            tournament_name=tournament_name,
            event_date=event_date,
            start_time=start_time,
            end_time=end_time,
            stadium_id=stadium_id,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            match_status=match_status
        )
        
        db.session.add(new_event)
        db.session.commit()
        
        flash(f'Event "{event_name}" added successfully.')
        return redirect(url_for('manage_stadium', stadium_id=stadium_id))
    
    return render_template('admin_add_event.html', stadium=stadium, teams=teams)

@app.route('/admin/stadium/<int:stadium_id>/concession/add', methods=['GET', 'POST'])
@login_required
@stadium_admin_required('stadium_id')
def add_concession(stadium_id):
    """Add a new concession to the stadium"""
    stadium = Stadium.query.get_or_404(stadium_id)
    
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        location_zone = request.form['location_zone']
        opening_hours = request.form['opening_hours']
        
        new_concession = Concession(
            name=name,
            category=category,
            location_zone=location_zone,
            opening_hours=opening_hours,
            stadium_id=stadium_id
        )
        
        db.session.add(new_concession)
        db.session.commit()
        
        flash(f'Concession "{name}" added successfully.')
        return redirect(url_for('manage_stadium', stadium_id=stadium_id))
    
    return render_template('admin_add_concession.html', stadium=stadium)

@app.route('/admin/concession/<int:concession_id>/menu/add', methods=['GET', 'POST'])
@login_required
def add_menu_item(concession_id):
    """Add a menu item to a concession"""
    concession = Concession.query.get_or_404(concession_id)
    
    # Check if admin manages this stadium
    if concession.stadium_id not in current_user.get_administered_stadiums():
        flash('Access denied.')
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description')
        price = float(request.form['price'])
        category = request.form['category']
        is_available = 'is_available' in request.form
        
        new_item = MenuItem(
            name=name,
            description=description,
            price=price,
            category=category,
            is_available=is_available,
            concession_id=concession_id
        )
        
        db.session.add(new_item)
        db.session.commit()
        
        flash(f'Menu item "{name}" added successfully.')
        return redirect(url_for('manage_stadium', stadium_id=concession.stadium_id))
    
    return render_template('admin_add_menu_item.html', concession=concession)

@app.route('/admin/stadium/<int:stadium_id>/parking/add', methods=['GET', 'POST'])
@login_required
@stadium_admin_required('stadium_id')
def add_parking(stadium_id):
    """Add a parking zone to the stadium"""
    stadium = Stadium.query.get_or_404(stadium_id)
    
    if request.method == 'POST':
        zone = request.form['zone_name']
        capacity = int(request.form['capacity'])
        rate_per_hour = float(request.form['hourly_rate'])
        
        new_parking = Parking(
            zone=zone,
            capacity=capacity,
            rate_per_hour=rate_per_hour,
            stadium_id=stadium_id
        )
        
        db.session.add(new_parking)
        db.session.commit()
        
        flash(f'Parking zone "{zone}" added successfully.')
        return redirect(url_for('manage_stadium', stadium_id=stadium_id))
    
    return render_template('admin_add_parking.html', stadium=stadium)

@app.route('/admin/stadium/<int:stadium_id>/seats/add', methods=['GET', 'POST'])
@login_required
@stadium_admin_required('stadium_id')
def add_seats(stadium_id):
    """Bulk add seats to the stadium"""
    stadium = Stadium.query.get_or_404(stadium_id)
    
    if request.method == 'POST':
        section = request.form['section']
        row_start = request.form['row_start']
        row_end = request.form['row_end']
        seat_start = int(request.form['seat_start'])
        seat_end = int(request.form['seat_end'])
        seat_type = request.form['seat_type']
        price = float(request.form['price'])
        has_shade = 'has_shade' in request.form
        
        seats_created = 0
        
        # Generate row range (A-Z or numbers)
        if row_start.isalpha() and row_end.isalpha():
            rows = [chr(i) for i in range(ord(row_start.upper()), ord(row_end.upper()) + 1)]
        else:
            rows = [str(i) for i in range(int(row_start), int(row_end) + 1)]
        
        for row in rows:
            for seat_num in range(seat_start, seat_end + 1):
                seat_number = f"{section}-{row}-{seat_num}"
                
                # Check if seat already exists
                existing_seat = Seat.query.filter_by(
                    stadium_id=stadium_id, 
                    seat_number=seat_number
                ).first()
                
                if not existing_seat:
                    new_seat = Seat(
                        seat_number=seat_number,
                        section=section,
                        row_number=row,
                        seat_type=seat_type,
                        price=price,
                        has_shade=has_shade,
                        stadium_id=stadium_id
                    )
                    db.session.add(new_seat)
                    seats_created += 1
        
        db.session.commit()
        flash(f'{seats_created} seats added successfully.')
        return redirect(url_for('manage_stadium', stadium_id=stadium_id))
    
    return render_template('admin_add_seats.html', stadium=stadium)

# Admin Statistics and Overview Routes
@app.route('/admin/stadiums')
@login_required
@admin_required
def admin_stadiums_overview():
    """Admin stadiums overview page"""
    administered_stadiums = current_user.get_administered_stadiums()
    stadiums_data = []
    
    for stadium_id in administered_stadiums:
        stadium = Stadium.query.get(stadium_id)
        if stadium:
            events_count = Event.query.filter_by(stadium_id=stadium_id).count()
            concessions_count = Concession.query.filter_by(stadium_id=stadium_id).count()
            parking_count = Parking.query.filter_by(stadium_id=stadium_id).count()
            seats_count = Seat.query.filter_by(stadium_id=stadium_id).count()
            
            stadiums_data.append({
                'stadium': stadium,
                'events_count': events_count,
                'concessions_count': concessions_count,
                'parking_count': parking_count,
                'seats_count': seats_count
            })
    
    return render_template('admin_stadiums_overview.html', stadiums_data=stadiums_data)

@app.route('/admin/events')
@login_required
@admin_required
def admin_events_overview():
    """Admin events overview with statistics"""
    administered_stadiums = current_user.get_administered_stadiums()
    events_data = []
    
    for stadium_id in administered_stadiums:
        stadium = Stadium.query.get(stadium_id)
        if stadium:
            events = Event.query.filter_by(stadium_id=stadium_id).all()
            for event in events:
                # Calculate ticket sales statistics
                tickets_sold = Ticket.query.filter_by(event_id=event.id).count()
                # Correctly calculate revenue from distinct bookings for this event
                total_revenue = db.session.query(db.func.sum(Booking.total_amount)).filter(
                    Booking.id.in_(
                        db.session.query(Ticket.booking_id).filter_by(event_id=event.id).distinct()
                    )
                ).scalar() or 0

                events_data.append({
                    'event': event,
                    'stadium': stadium,
                    'tickets_sold': tickets_sold,
                    'total_revenue': total_revenue,
                    'capacity_percentage': round((tickets_sold / stadium.capacity) * 100, 1) if stadium.capacity > 0 else 0
                })
    
    return render_template('admin_events_overview.html', events_data=events_data)

@app.route('/admin/bookings')
@login_required
@admin_required
def admin_bookings_overview():
    """Admin ticket bookings overview"""
    administered_stadiums = current_user.get_administered_stadiums()
    booking_stats = []
    
    for stadium_id in administered_stadiums:
        stadium = Stadium.query.get(stadium_id)
        if stadium:
            # Get all events for this stadium
            events = Event.query.filter_by(stadium_id=stadium_id).all()
            
            for event in events:
                tickets = Ticket.query.filter_by(event_id=event.id).all()
                total_tickets = len(tickets)
                # Correctly calculate revenue from distinct bookings for this event
                total_revenue = db.session.query(db.func.sum(Booking.total_amount)).filter(
                    Booking.id.in_(
                        db.session.query(Ticket.booking_id).filter_by(event_id=event.id).distinct()
                    )
                ).scalar() or 0

                booking_stats.append({
                    'stadium': stadium,
                    'event': event,
                    'total_tickets': total_tickets,
                    'total_revenue': total_revenue,
                    'tickets': tickets
                })
    
    return render_template('admin_bookings_overview.html', booking_stats=booking_stats)

@app.route('/admin/parking')
@login_required
@admin_required
def admin_parking_overview():
    """Admin parking management with statistics"""
    administered_stadiums = current_user.get_administered_stadiums()
    parking_stats = []
    
    for stadium_id in administered_stadiums:
        stadium = Stadium.query.get(stadium_id)
        if stadium:
            parking_zones = Parking.query.filter_by(stadium_id=stadium_id).all()
            
            for parking in parking_zones:
                bookings = ParkingBooking.query.filter_by(parking_id=parking.id).all()
                total_bookings = len(bookings)
                total_revenue = sum(booking.amount_paid for booking in bookings if hasattr(booking, 'amount_paid'))
                occupancy_rate = round((total_bookings / parking.capacity) * 100, 1) if parking.capacity > 0 else 0
                
                parking_stats.append({
                    'stadium': stadium,
                    'parking': parking,
                    'total_bookings': total_bookings,
                    'total_revenue': total_revenue,
                    'occupancy_rate': occupancy_rate,
                    'available_spots': parking.capacity - total_bookings
                })
    
    return render_template('admin_parking_overview.html', parking_stats=parking_stats)

@app.route('/admin/concessions')
@login_required
@admin_required
def admin_concessions_overview():
    """Admin concessions overview with sales statistics"""
    administered_stadiums = current_user.get_administered_stadiums()
    concession_stats = []
    
    for stadium_id in administered_stadiums:
        stadium = Stadium.query.get(stadium_id)
        if stadium:
            concessions = Concession.query.filter_by(stadium_id=stadium_id).all()
            
            for concession in concessions:
                orders = Order.query.filter_by(concession_id=concession.id).all()
                total_orders = len(orders)
                total_revenue = sum(order.total_amount for order in orders)
                menu_items_count = MenuItem.query.filter_by(concession_id=concession.id).count()
                
                concession_stats.append({
                    'stadium': stadium,
                    'concession': concession,
                    'total_orders': total_orders,
                    'total_revenue': total_revenue,
                    'menu_items_count': menu_items_count,
                    'recent_orders': orders[-5:] if orders else []
                })
    
    return render_template('admin_concessions_overview.html', concession_stats=concession_stats)

@app.route('/admin/users')
@login_required
@admin_required
def admin_user_management():
    """Admin user management page with comprehensive user data and statistics"""
    
    # Get all users
    users = Customer.query.order_by(Customer.name).all()
    
    # Get user statistics using utility function
    user_stats = get_user_statistics(db, Customer)
    
    return render_template('admin_user_management.html', 
                           users=users, 
                           **user_stats)

@app.route('/admin/analytics')
@login_required
@admin_required
def admin_analytics():
    # Get comprehensive analytics data using utility function
    analytics_data = get_analytics_data(db, Stadium, Event, Ticket, Order, ParkingBooking)
    
    return render_template('admin_analytics.html', analytics_data=analytics_data)

@app.route('/admin/stadium/<int:stadium_id>/analytics')
@login_required
@stadium_admin_required('stadium_id')
def admin_stadium_analytics(stadium_id):
    """Detailed analytics for a specific stadium"""
    stadium = Stadium.query.get_or_404(stadium_id)
    
    # Calculate detailed stadium metrics
    events = Event.query.filter_by(stadium_id=stadium_id).all()
    total_tickets_sold = db.session.query(db.func.count(Ticket.id)).join(Event).filter(Event.stadium_id == stadium_id).scalar() or 0
    
    # Correctly calculate ticket revenue from distinct bookings for this stadium
    total_ticket_revenue = db.session.query(db.func.sum(Booking.total_amount)).filter(
        Booking.id.in_(
            db.session.query(Ticket.booking_id).join(Event).filter(Event.stadium_id == stadium_id).distinct()
        )
    ).scalar() or 0
    total_concession_revenue = db.session.query(db.func.sum(Order.total_amount)).join(Concession).filter(Concession.stadium_id == stadium_id).scalar() or 0
    
    analytics = {
        'stadium': stadium,
        'total_events': len(events),
        'total_tickets_sold': total_tickets_sold,
        'total_revenue': total_ticket_revenue + total_concession_revenue,
        'average_attendance': round(total_tickets_sold / len(events), 1) if events else 0,
        'capacity_utilization': round((total_tickets_sold / (stadium.capacity * len(events))) * 100, 1) if events and stadium.capacity > 0 else 0,
        'events': events
    }
    
    return render_template('admin_stadium_analytics.html', analytics=analytics)

@app.route('/admin/profile')
@login_required
@admin_required
def admin_profile():
    stadium_ids = current_user.get_administered_stadiums()  # returns list of IDs
    administered_stadiums = Stadium.query.filter(Stadium.id.in_(stadium_ids)).all()
    return render_template('admin_profile.html', administered_stadiums=administered_stadiums)

# Routes

@app.route('/')
def index():
    """Home page with enhanced error handling and database fallbacks"""
    try:
        # Initialize data with empty fallbacks
        upcoming_events = []
        featured_stadiums = []
        featured_teams_data = []
        next_match_countdown = None
        
        # Try to fetch data from database with timeout protection
        try:
            # Fetch upcoming events using utility function with error handling
            upcoming_events = get_upcoming_events(Event, limit=3)
        except Exception as e:
            print(f"Warning: Could not fetch upcoming events: {e}")
            upcoming_events = []
        
        try:
            # Fetch featured stadiums (top 3 by capacity)
            featured_stadiums = Stadium.query.order_by(Stadium.capacity.desc()).limit(3).all()
        except Exception as e:
            print(f"Warning: Could not fetch featured stadiums: {e}")
            featured_stadiums = []
        
        try:
            # Fetch teams and star players
            teams = Team.query.limit(3).all()
            for team in teams:
                try:
                    star_player = Player.query.filter_by(team_id=team.id).first()
                    featured_teams_data.append({
                        'team': team,
                        'star_player': star_player
                    })
                except Exception as e:
                    print(f"Warning: Could not fetch star player for team {team.id}: {e}")
                    # Add team without star player
                    featured_teams_data.append({
                        'team': team,
                        'star_player': None
                    })
        except Exception as e:
            print(f"Warning: Could not fetch teams: {e}")
            featured_teams_data = []
        
        # Calculate countdown to next event if available
        try:
            if upcoming_events:
                next_event = upcoming_events[0]
                next_event_datetime = datetime.combine(next_event.event_date, next_event.start_time)
                time_difference = next_event_datetime - datetime.utcnow()
                if time_difference.total_seconds() > 0:
                    days = time_difference.days
                    hours = time_difference.seconds // 3600
                    minutes = (time_difference.seconds % 3600) // 60
                    next_match_countdown = {'days': days, 'hours': hours, 'minutes': minutes}
        except Exception as e:
            print(f"Warning: Could not calculate countdown: {e}")
            next_match_countdown = None
        
        # Log successful data retrieval
        print(f"✅ Home page loaded: {len(upcoming_events)} events, {len(featured_stadiums)} stadiums, {len(featured_teams_data)} teams")
        
        # If no data was loaded from database, provide static fallback
        if not upcoming_events and not featured_stadiums and not featured_teams_data:
            print("🔄 Using static fallback data due to database issues")
            upcoming_events, featured_stadiums, featured_teams_data = get_static_fallback_data()
        
        return render_template('index.html',
                               upcoming_events=upcoming_events,
                               featured_stadiums=featured_stadiums,
                               featured_teams_data=featured_teams_data,
                               next_match_countdown=next_match_countdown)
        
    except Exception as e:
        print(f"❌ Critical error in index route: {e}")
        # Return template with empty data to prevent complete failure
        return render_template('index.html',
                               upcoming_events=[],
                               featured_stadiums=[],
                               featured_teams_data=[],
                               next_match_countdown=None,
                               error_message="Some content may not be available due to connectivity issues.")


@app.route('/stadiums')
def stadiums():
    stadiums = Stadium.query.all()
    return render_template('stadiums.html', stadiums=stadiums)

@app.route('/stadium/<int:stadium_id>')
def stadium_detail(stadium_id):
    stadium = Stadium.query.get_or_404(stadium_id)
    current_time = datetime.now()
    return render_template('stadium_detail.html', stadium=stadium, current_time=current_time)

@app.route('/events')
def events():
    events = Event.query.order_by(Event.event_date.desc()).all()
    return render_template('events.html', events=events)

@app.route('/event/<int:event_id>')
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)
    return render_template('event_detail.html', event=event)

@app.route('/teams')
def teams():
    teams = Team.query.all()
    return render_template('teams.html', teams=teams)

@app.route('/team/<int:team_id>')
def team_detail(team_id):
    team = Team.query.get_or_404(team_id)
    # Find the stadium for the team's home ground
    stadium = None
    if hasattr(team, 'home_ground') and team.home_ground:
        stadium = Stadium.query.filter_by(name=team.home_ground).first()
    return render_template('team_detail.html', team=team, stadium=stadium)

@app.route('/players')
def players():
    players = Player.query.all()
    return render_template('players.html', players=players)

@app.route('/player/<int:player_id>')
def player_detail(player_id):
    player = Player.query.get_or_404(player_id)
    return render_template('player_detail.html', player=player)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Sanitize form data
        form_data = {
            'name': sanitize_input(request.form.get('name', ''), 100),
            'email': sanitize_input(request.form.get('email', ''), 100).lower(),
            'phone': sanitize_input(request.form.get('phone', ''), 20),
            'password': request.form.get('password', ''),
            'role': request.form.get('role', 'customer')
        }
        
        # Validate form data
        errors = handle_form_errors(form_data, REGISTRATION_VALIDATION_RULES)
        
        # Additional validations
        if form_data['email']:
            existing_customer = Customer.query.filter_by(email=form_data['email']).first()
            if existing_customer:
                errors.append('An account with this email already exists. Please try logging in instead.')
        
        # Password strength validation
        password_errors = validate_password_strength(form_data['password'])
        errors.extend(password_errors)
        
        # Role validation
        valid_roles = ['customer', 'admin', 'stadium_owner']
        if form_data['role'] not in valid_roles:
            form_data['role'] = 'customer'  # Default fallback
        
        # If there are validation errors, return to form with errors
        if errors:
            flash_errors(errors)
            return render_template('register.html')
        
        try:
            # Create new customer account
            new_customer = Customer(
                name=form_data['name'], 
                email=form_data['email'], 
                phone=form_data['phone'], 
                role=form_data['role'],
                membership_level='Basic'
            )
            new_customer.set_password(form_data['password'])
            db.session.add(new_customer)
            db.session.commit()
            
            # Role-specific success messages
            role_messages = {
                'admin': f'Administrator account created successfully! Welcome {form_data["name"]}. You now have full system access.',
                'stadium_owner': f'Stadium Owner account created successfully! Welcome {form_data["name"]}. You can now manage stadium operations.',
                'customer': f'Account created successfully! Welcome to CricVerse, {form_data["name`"]}',
            }
            
            flash(role_messages.get(form_data['role'], role_messages['customer']), 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
            print(f"Registration error: {e}")
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Sanitize form data
        email = sanitize_input(request.form.get('email', ''), 100).lower()
        password = request.form.get('password', '')
        remember_me = request.form.get('remember_me') == 'on'
        
        # Basic input validation
        if not email or not password:
            flash('Please enter both email and password.', 'danger')
            return render_template('login.html')
        
        # Email format validation
        if not validate_email(email):
            flash('Please enter a valid email address.', 'danger')
            return render_template('login.html')
        
        # Find user by email
        customer = Customer.query.filter_by(email=email).first()
        
        if customer and customer.check_password(password):
            # Successful login
            login_user(customer, remember=remember_me)
            
            # Role-specific welcome messages and redirection
            role_redirects = {
                'admin': {
                    'message': f'Welcome back, Administrator {customer.name}! You have full system access.',
                    'redirect': 'admin_dashboard'
                },
                'stadium_owner': {
                    'message': f'Welcome back, {customer.name}! Ready to manage your stadiums.',
                    'redirect': 'stadium_owner_dashboard'
                },
                'customer': {
                    'message': f'Welcome back, {customer.name}! Enjoy your CricVerse experience.',
                    'redirect': 'dashboard'
                }
            }
            
            role_config = role_redirects.get(customer.role, role_redirects['customer'])
            flash(role_config['message'], 'success')
            
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for(role_config['redirect']))
                
        else:
            # Login failed
            if customer:
                flash('Incorrect password. Please try again or reset your password.', 'danger')
            else:
                flash('No account found with this email address. Please check your email or register for a new account.', 'danger')
    
    return render_template('login.html')

@app.route('/stadium_owner/dashboard')
@login_required
@stadium_owner_required
def stadium_owner_dashboard():
    return render_template('stadium_owner_dashboard.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
@customer_required
def dashboard():
    # Get user's data with ordering for a better display
    tickets = Ticket.query.filter_by(customer_id=current_user.id).join(Event).order_by(Event.event_date.desc()).all()
    orders = Order.query.filter_by(customer_id=current_user.id).order_by(Order.order_date.desc()).all()
    parking_bookings = ParkingBooking.query.filter_by(customer_id=current_user.id).order_by(ParkingBooking.booking_date.desc()).all()

    # --- Calculate stats for the summary cards ---
    total_tickets = len(tickets)
    
    # Calculate total spent from all sources
    ticket_spend = db.session.query(db.func.sum(Booking.total_amount)).filter(
        Booking.customer_id == current_user.id
    ).scalar() or 0
    order_spend = db.session.query(db.func.sum(Order.total_amount)).filter_by(customer_id=current_user.id).scalar() or 0
    parking_spend = db.session.query(db.func.sum(ParkingBooking.amount_paid)).filter_by(customer_id=current_user.id).scalar() or 0
    
    total_spent = ticket_spend + order_spend + parking_spend
    
    # Find upcoming events from the user's tickets
    upcoming_events_count = db.session.query(Ticket).join(Event).filter(
        Ticket.customer_id == current_user.id,
        Event.event_date >= datetime.utcnow().date()
    ).count()

    stats = {
        'total_tickets': total_tickets,
        'total_spent': total_spent,
        'upcoming_events': upcoming_events_count,
        'total_orders': len(orders)
    }

    return render_template('dashboard.html', 
                           tickets=tickets, 
                           orders=orders, 
                           parking_bookings=parking_bookings,
                           stats=stats)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
@customer_required
def profile():
    teams = Team.query.all()
    if request.method == 'POST':
        current_user.name = request.form['name']
        current_user.phone = request.form['phone']
        favorite_team_id = request.form.get('favorite_team_id')
        current_user.favorite_team_id = int(favorite_team_id) if favorite_team_id else None
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {e}', 'danger')
        return redirect(url_for('profile'))
    return render_template('profile.html', teams=teams)

@app.route('/change_password', methods=['POST'])
@login_required
@customer_required
def change_password():
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']

    if not current_user.check_password(current_password):
        flash('Incorrect current password.', 'danger')
    elif new_password != confirm_password:
        flash('New password and confirm password do not match.', 'danger')
    else:
        current_user.set_password(new_password)
        try:
            db.session.commit()
            flash('Password changed successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error changing password: {e}', 'danger')
    return redirect(url_for('profile'))

@app.route('/book_ticket/<int:event_id>', methods=['POST'])
@login_required
@customer_required
def book_ticket(event_id):
    event = Event.query.get_or_404(event_id)
    
    selected_seat_ids = request.form.get('selected_seats', '').split(',')
    ticket_type = request.form.get('ticket_type')
    payment_method = request.form.get('payment_method')
    
    if not selected_seat_ids or selected_seat_ids == ['']:
        flash('Please select at least one seat.', 'warning')
        return redirect(url_for('select_seats', event_id=event_id))

    selected_seat_ids = [int(sid) for sid in selected_seat_ids if sid]

    # Check if seats are still available
    seats = Seat.query.filter(Seat.id.in_(selected_seat_ids)).all()
    
    if len(seats) != len(selected_seat_ids):
        flash('One or more selected seats could not be found or are invalid.', 'danger')
        return redirect(url_for('select_seats', event_id=event_id))

    booked_seats = Ticket.query.filter(
        Ticket.seat_id.in_(selected_seat_ids),
        Ticket.event_id == event_id,
        Ticket.ticket_status.in_(['Booked', 'Used'])
    ).all()
    
    if booked_seats:
        flash('Some selected seats are no longer available. Please choose again.', 'warning')
        return redirect(url_for('select_seats', event_id=event_id))
    
    total_amount = sum(seat.price for seat in seats)

    new_booking = Booking(customer_id=current_user.id, total_amount=total_amount)
    db.session.add(new_booking)

    for seat in seats:
        ticket = Ticket(
            event_id=event_id,
            seat_id=seat.id,
            customer_id=current_user.id,
            ticket_type=ticket_type,
            access_gate=f"Gate {seat.section[0]}",
            booking=new_booking
        )
        db.session.add(ticket)
    
    payment = Payment(
        amount=total_amount,
        payment_method=payment_method,
        transaction_id=f"TXN{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        booking=new_booking
    )
    db.session.add(payment)
    
    try:
        db.session.commit()
        flash(f'Successfully booked {len(seats)} ticket(s) for {event.event_name}!', 'success')
        return redirect(url_for('dashboard'))
    except Exception as e:
        db.session.rollback()
        print(f"Error during booking: {e}")
        flash('An error occurred while processing your booking. Please try again.', 'danger')
        return redirect(url_for('select_seats', event_id=event_id))

@app.route('/select_seats/<int:event_id>')
@login_required
@customer_required
def select_seats(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Get all seats for the stadium
    all_seats = Seat.query.filter_by(stadium_id=event.stadium_id).all()
    
    # Get booked seats for this event
    booked_seat_ids = db.session.query(Ticket.seat_id).filter(
        Ticket.event_id == event_id,
        Ticket.ticket_status.in_(['Booked', 'Used'])
    ).all()
    booked_seat_ids = [seat_id[0] for seat_id in booked_seat_ids]
    
    # Mark seats as available/unavailable
    for seat in all_seats:
        seat.is_available = seat.id not in booked_seat_ids
    
    # Group seats by section -> rows with enhanced data structure
    sections: dict = {}
    total_available = 0
    
    for seat in all_seats:
        section_name = seat.section
        row_name = seat.row_number
        
        if section_name not in sections:
            sections[section_name] = {
                'name': section_name,
                'rows': {},
                'total_seats': 0,
                'available_seats': 0,
                'price_range': {'min': float('inf'), 'max': 0},
                'seat_types': set(),
                'class': 'standard'  # CSS class for styling
            }
        
        if row_name not in sections[section_name]['rows']:
            sections[section_name]['rows'][row_name] = {
                'name': row_name,
                'seats': []
            }
        
        sections[section_name]['rows'][row_name]['seats'].append(seat)
        sections[section_name]['total_seats'] += 1
        sections[section_name]['seat_types'].add(seat.seat_type)
        
        # Update price range
        if seat.price < sections[section_name]['price_range']['min']:
            sections[section_name]['price_range']['min'] = seat.price
        if seat.price > sections[section_name]['price_range']['max']:
            sections[section_name]['price_range']['max'] = seat.price
        
        if seat.is_available:
            sections[section_name]['available_seats'] += 1
            total_available += 1
    
    # Determine section styling class based on seat types
    for section_data in sections.values():
        seat_types = section_data['seat_types']
        if 'VIP' in seat_types:
            section_data['class'] = 'vip'
        elif 'Corporate' in seat_types:
            section_data['class'] = 'corporate'
        elif 'Premium' in seat_types:
            section_data['class'] = 'premium'
        else:
            section_data['class'] = 'standard'
        
        # Format price range
        min_price = section_data['price_range']['min']
        max_price = section_data['price_range']['max']
        if min_price == max_price:
            section_data['price_range'] = f"₹{min_price:.0f}"
        else:
            section_data['price_range'] = f"₹{min_price:.0f} - ₹{max_price:.0f}"
    
    # Sort seats within rows by numeric seat_number when possible
    def _to_int_or_str(value: str):
        try:
            return int(value)
        except Exception:
            return value
    
    for section_data in sections.values():
        # Order rows by natural name
        ordered_rows = []
        for row_name, row_data in section_data['rows'].items():
            row_data['seats'].sort(key=lambda s: _to_int_or_str(s.seat_number))
            ordered_rows.append(row_data)
        # Sort rows by their name with numeric fallback
        ordered_rows.sort(key=lambda r: _to_int_or_str(r['name']))
        section_data['rows'] = ordered_rows
    
    # Convert to list for template, sorted by section importance
    def section_priority(section):
        # Priority order: VIP -> Corporate -> Premium -> Standard -> General
        if 'VIP' in section['seat_types']:
            return 0
        elif 'Corporate' in section['seat_types']:
            return 1
        elif 'Premium' in section['seat_types']:
            return 2
        elif 'Standard' in section['seat_types']:
            return 3
        else:
            return 4
    
    sections_list = sorted(sections.values(), key=section_priority)
    
    # Use enhanced template if it exists, fallback to original
    try:
        return render_template('enhanced_seat_selection.html', 
                             event=event, 
                             sections=sections_list,
                             selected_seats=[],
                             total_available=total_available)
    except Exception:
        # Fallback to original template
        return render_template('seat_selection.html', 
                             event=event, 
                             sections=sections_list,
                             selected_seats=[],
                             total_available=total_available)

@app.route('/parking')
def parking():
    stadiums = Stadium.query.all()
    parking_zones = Parking.query.all()
    return render_template('parking.html', stadiums=stadiums, parking_zones=parking_zones)

@app.route('/concessions')
def concessions():
    # Optional filters via query params: stadium_id, category
    stadium_id = request.args.get('stadium_id', type=int)
    category = request.args.get('category', type=str)

    query = Concession.query
    if stadium_id:
        query = query.filter_by(stadium_id=stadium_id)
    if category:
        query = query.filter_by(category=category)

    concessions_list = query.order_by(Concession.name.asc()).all()

    # For filter dropdowns
    stadiums = Stadium.query.order_by(Stadium.name.asc()).all()
    categories = [row[0] for row in db.session.query(Concession.category).distinct().order_by(Concession.category.asc()).all()]

    return render_template(
        'concessions.html',
        concessions=concessions_list,
        stadiums=stadiums,
        categories=categories,
        selected_stadium_id=stadium_id,
        selected_category=category,
    )

@app.route('/concession/<int:concession_id>/menu')
@login_required
@customer_required
def concession_menu(concession_id):
    concession = Concession.query.get_or_404(concession_id)
    
    # Get menu items from database for this concession
    menu_items = MenuItem.query.filter_by(
        concession_id=concession_id, 
        is_available=True
    ).order_by(MenuItem.category, MenuItem.name).all()
    
    return render_template('concession_menu.html', 
                         concession=concession, 
                         menu_items=menu_items)

@app.route('/place_order', methods=['POST'])
@login_required
@customer_required
def place_order():
    concession_id = request.form['concession_id']
    selected_items = request.form.getlist('selected_items')
    quantities = request.form.getlist('quantities')
    total_amount = float(request.form['total_amount'])
    
    # Create order details
    order_details = []
    for i, item in enumerate(selected_items):
        if quantities[i] and int(quantities[i]) > 0:
            order_details.append(f"{quantities[i]}x {item}")
    
    order_items = ", ".join(order_details)
    
    order = Order(
        concession_id=concession_id,
        customer_id=current_user.id,
        total_amount=total_amount,
        payment_status='Completed'
    )
    
    db.session.add(order)
    db.session.commit()
    
    flash(f'Order placed successfully! Total: ${total_amount:.2f}')
    return redirect(url_for('dashboard'))

@app.route('/book_parking/<int:stadium_id>', methods=['GET', 'POST'])
@login_required
@customer_required
def book_parking(stadium_id):
    stadium = Stadium.query.get_or_404(stadium_id)
    parking_zones = Parking.query.filter_by(stadium_id=stadium_id).all()
    
    if request.method == 'POST':
        parking_id = request.form['parking_id']
        vehicle_number = request.form['vehicle_number']
        arrival_time = datetime.strptime(request.form['arrival_time'], '%Y-%m-%dT%H:%M')
        departure_time = datetime.strptime(request.form['departure_time'], '%Y-%m-%dT%H:%M')
        
        parking = Parking.query.get(parking_id)
        hours = (departure_time - arrival_time).total_seconds() / 3600
        amount = parking.rate_per_hour * hours
        
        booking = ParkingBooking(
            parking_id=parking_id,
            customer_id=current_user.id,
            vehicle_number=vehicle_number,
            arrival_time=arrival_time,
            departure_time=departure_time,
            amount_paid=amount
        )
        
        db.session.add(booking)
        db.session.commit()
        
        flash('Parking booked successfully')
        return redirect(url_for('dashboard'))
    
    return render_template('book_parking.html', stadium=stadium, parking_zones=parking_zones)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/chat')
def chat_interface():
    """Render the enhanced AI chatbot interface"""
    return render_template('chat.html')

@app.route('/ai-assistant')
def ai_assistant():
    """Render the new 3D AI Assistant Command Center"""
    return render_template('ai_assistant.html')

@app.route('/ai-options')
def ai_options():
    """AI Assistant options page"""
    return render_template('ai_options.html')

@app.route('/api/chat', methods=['POST'])
def enhanced_chat_api():
    """Enhanced AI chatbot API endpoint using Gemini AI"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({
                'success': False,
                'error': 'Message cannot be empty'
            }), 400
        
        # Get user context
        from flask import session
        customer_id = current_user.id if current_user.is_authenticated else None
        session_id = session.get('chat_session_id')
        
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
            session['chat_session_id'] = session_id
        
        # Import and use the chatbot with proper error handling
        from chatbot import get_chatbot_response, detect_user_intent, get_intent_actions
        
        try:
            # Get AI response with timeout protection
            import signal
            import threading
            import queue
            
            result_queue = queue.Queue()
            exception_queue = queue.Queue()
            
            def get_response_worker():
                try:
                    result = get_chatbot_response(message, customer_id, session_id)
                    result_queue.put(result)
                except Exception as e:
                    print(f"Chatbot response error: {e}")
                    exception_queue.put(e)
                    # Put a fallback response
                    fallback_response = {
                        'response': f"I understand you're asking about '{message}'. While I'm having some technical difficulties with my advanced features, I can tell you that CricVerse offers comprehensive BBL ticket booking, stadium information, and customer support. Please try asking something specific like 'Tell me about MCG' or 'Book tickets'.",
                        'confidence': 0.7,
                        'tokens_used': 0,
                        'model': 'fallback-error'
                    }
                    result_queue.put(fallback_response)
            
            # Run with timeout
            worker_thread = threading.Thread(target=get_response_worker)
            worker_thread.daemon = True
            worker_thread.start()
            worker_thread.join(timeout=15)  # 15 second timeout
            
            if worker_thread.is_alive():
                # Timeout occurred
                print("Chatbot response timed out")
                ai_response = {
                    'response': f"Thanks for your message about '{message}'. I'm processing your request but it's taking longer than expected. CricVerse offers comprehensive BBL ticket booking, stadium information, and customer support. Please try a more specific question.",
                    'confidence': 0.7,
                    'tokens_used': 0,
                    'model': 'fallback-timeout'
                }
            else:
                try:
                    ai_response = result_queue.get_nowait()
                except queue.Empty:
                    ai_response = {
                        'response': f"I apologize, but I encountered an issue processing your request about '{message}'. CricVerse is your destination for BBL cricket experiences. Please try asking about specific topics like stadiums, tickets, or match information.",
                        'confidence': 0.7,
                        'tokens_used': 0,
                        'model': 'fallback-empty'
                    }
            
        except ImportError as e:
            print(f"Chatbot import error: {e}")
            # Fallback if chatbot module has issues
            ai_response = {
                'response': f"Hello! I'm experiencing some technical difficulties with my advanced AI features, but I can still help you with CricVerse services. You asked about '{message}' - please try asking specific questions about BBL ticket booking, stadium information, or match schedules.",
                'confidence': 0.6,
                'tokens_used': 0,
                'model': 'fallback-import-error'
            }
        
        # Detect intent and get quick actions with error handling
        try:
            intent = detect_user_intent(message)
            quick_actions = get_intent_actions(intent)
        except Exception as e:
            print(f"Intent detection error: {e}")
            # Simple fallback intent detection
            message_lower = message.lower()
            if any(word in message_lower for word in ['book', 'buy', 'ticket', 'reserve']):
                intent = 'booking'
                quick_actions = [{"text": "Browse Matches", "action": "browse_matches"}]
            elif any(word in message_lower for word in ['stadium', 'venue', 'ground']):
                intent = 'venue_info'
                quick_actions = [{"text": "Stadium Guide", "action": "stadium_guide"}]
            else:
                intent = 'general'
                quick_actions = [{"text": "Help me book tickets", "action": "booking_help"}]
        
        return jsonify({
            'success': True,
            'response': ai_response.get('response', 'I apologize, but I\'m having trouble processing your request.'),
            'confidence': ai_response.get('confidence', 0.5),
            'intent': intent,
            'quick_actions': quick_actions,
            'tokens_used': ai_response.get('tokens_used', 0),
            'model': ai_response.get('model', 'gemini-1.5-flash'),
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Enhanced chatbot error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'Sorry, I\'m experiencing technical difficulties. Please try again or contact support.',
            'fallback_response': True
        }), 500

@app.route('/api/chat/suggestions')
def chat_suggestions():
    """Get smart chat suggestions based on user context"""
    try:
        customer_id = current_user.id if current_user.is_authenticated else None
        query_type = request.args.get('type', 'general')
        
        from chatbot import get_chat_suggestions
        suggestions = get_chat_suggestions(customer_id, query_type)
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
        
    except Exception as e:
        print(f"Error getting chat suggestions: {e}")
        return jsonify({
            'success': False,
            'suggestions': [
                "Help me book tickets",
                "What matches are coming up?",
                "Show me stadium information",
                "How do I cancel a booking?"
            ]
        })

@app.route('/api/chat/history')
@login_required
def chat_history():
    """Get user's chat history"""
    try:
        from enhanced_models import ChatConversation, ChatMessage
        
        conversations = ChatConversation.query.filter_by(
            customer_id=current_user.id
        ).order_by(ChatConversation.created_at.desc()).limit(5).all()
        
        history = []
        for conv in conversations:
            messages = ChatMessage.query.filter_by(
                conversation_id=conv.id
            ).order_by(ChatMessage.created_at).limit(20).all()
            
            history.append({
                'conversation_id': conv.id,
                'session_id': conv.session_id,
                'created_at': conv.created_at.isoformat(),
                'message_count': conv.message_count,
                'messages': [{
                    'sender': msg.sender_type,
                    'message': msg.message,
                    'timestamp': msg.created_at.isoformat()
                } for msg in messages]
            })
        
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        print(f"Error getting chat history: {e}")
        return jsonify({
            'success': False,
            'error': 'Could not retrieve chat history'
        })

# ============================================================================ 
# REAL-TIME WEBSOCKET ROUTES
# ============================================================================ 

@app.route('/realtime')
def realtime_demo():
    """Real-time features demo page"""
    return render_template('realtime.html')

@app.route('/api/realtime/stats')
def realtime_stats():
    """Get real-time connection statistics"""
    try:
        from realtime_simple import get_realtime_stats
        stats = get_realtime_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/realtime/broadcast', methods=['POST'])
@admin_required
def broadcast_message():
    """Admin endpoint to broadcast messages to all users"""
    try:
        data = request.get_json()
        message = data.get('message')
        message_type = data.get('type', 'info')
        
        if not message:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400
        
        from realtime_simple import broadcast_general_announcement
        broadcast_general_announcement(message, message_type)
        
        return jsonify({
            'success': True,
            'message': 'Broadcast sent successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/match/<int:match_id>/update', methods=['POST'])
@admin_required  
def update_match_live(match_id):
    """Update live match data and broadcast to subscribers"""
    try:
        data = request.get_json()
        
        # Update match in database
        event = Event.query.get_or_404(match_id)
        match = event.match
        
        if not match:
            return jsonify({
                'success': False,
                'error': 'Match record not found'
            }), 404
        
        # Update match data
        if 'score_home' in data:
            match.score_home = data['score_home']
        if 'score_away' in data:
            match.score_away = data['score_away']
        if 'overs_home' in data:
            match.overs_home = data['overs_home']
        if 'overs_away' in data:
            match.overs_away = data['overs_away']
        if 'current_innings' in data:
            match.current_innings = data['current_innings']
        if 'is_live' in data:
            match.is_live = data['is_live']
        
        db.session.commit()
        
        # Broadcast update to subscribers
        from realtime_simple import broadcast_match_update
        update_data = {
            'type': data.get('update_type', 'score_update'),
            'score_home': match.score_home,
            'score_away': match.score_away,
            'overs_home': match.overs_home,
            'overs_away': match.overs_away,
            'current_innings': match.current_innings,
            'is_live': match.is_live,
            'timestamp': datetime.now().isoformat()
        }
        
        broadcast_match_update(match_id, update_data)
        
        return jsonify({
            'success': True,
            'message': 'Match updated and broadcast sent'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    
# ============================================================================ 
# QR CODE GENERATION ROUTES
# ============================================================================ 

@app.route('/qr-demo')
def qr_demo():
    """QR code generation demo page"""
    return render_template('qr_demo.html')

@app.route('/api/qr/generate/ticket', methods=['POST'])
@login_required
def generate_ticket_qr():
    """Generate QR code for ticket"""
    try:
        data = request.get_json()
        
        # Add customer ID from current user
        data['customer_id'] = current_user.id
        
        from qr_generator import qr_generator
        qr_result = qr_generator.generate_ticket_qr(data)
        
        if qr_result:
            return jsonify({
                'success': True,
                'qr_code': qr_result['qr_code_base64'],
                'verification_code': qr_result['verification_code'],
                'ticket_info': qr_result['ticket_info']
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to generate QR code'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/qr/generate/parking', methods=['POST'])
@login_required
def generate_parking_qr():
    """Generate QR code for parking pass"""
    try:
        data = request.get_json()
        
        from qr_generator import qr_generator
        qr_result = qr_generator.generate_parking_qr(data)
        
        if qr_result:
            return jsonify({
                'success': True,
                'qr_code': qr_result['qr_code_base64'],
                'verification_code': qr_result['verification_code'],
                'parking_info': qr_result['parking_info']
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to generate parking QR code'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/qr/generate/entry', methods=['POST'])
@login_required
def generate_entry_qr():
    """Generate QR code for event entry"""
    try:
        data = request.get_json()
        data['customer_id'] = current_user.id
        data['customer_name'] = current_user.name
        
        from qr_generator import qr_generator
        qr_result = qr_generator.generate_event_entry_qr(data)
        
        if qr_result:
            return jsonify({
                'success': True,
                'qr_code': qr_result['qr_code_base64'],
                'verification_code': qr_result['verification_code'],
                'entry_info': qr_result['entry_info']
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to generate entry QR code'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/qr/generate/pass', methods=['POST'])
@login_required
def generate_digital_pass():
    """Generate digital pass with QR code"""
    try:
        data = request.get_json()
        pass_type = data.get('type', 'general')
        
        # Add customer info
        data['customer_name'] = current_user.name
        
        from qr_generator import qr_generator
        pass_result = qr_generator.generate_digital_pass(data, pass_type)
        
        if pass_result:
            return jsonify({
                'success': True,
                'qr_code': pass_result['qr_code_base64'],
                'pass_image': pass_result['pass_image_base64'],
                'verification_code': pass_result['verification_code'],
                'pass_info': pass_result['pass_info']
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to generate digital pass'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/verify/ticket/<verification_code>')
def verify_ticket_qr(verification_code):
    """Verify ticket QR code"""
    try:
        from qr_generator import qr_generator
        result = qr_generator.verify_qr_code(verification_code)
        
        if result['valid']:
            ticket_data = result['data']
            return render_template('qr_verification.html', 
                                 verification_result=result,
                                 data_type='ticket',
                                 ticket_data=ticket_data)
        else:
            return render_template('qr_verification.html',
                                 verification_result=result,
                                 data_type='ticket')
            
    except Exception as e:
        return render_template('qr_verification.html',
                             verification_result={'valid': False, 'error': str(e)},
                             data_type='ticket')

@app.route('/verify/parking/<verification_code>')
def verify_parking_qr(verification_code):
    """Verify parking QR code"""
    try:
        from qr_generator import qr_generator
        result = qr_generator.verify_qr_code(verification_code)
        
        if result['valid']:
            parking_data = result['data']
            return render_template('qr_verification.html',
                                 verification_result=result,
                                 data_type='parking',
                                 parking_data=parking_data)
        else:
            return render_template('qr_verification.html',
                                 verification_result=result,
                                 data_type='parking')
            
    except Exception as e:
        return render_template('qr_verification.html',
                             verification_result={'valid': False, 'error': str(e)},
                             data_type='parking')

@app.route('/verify/entry/<verification_code>')
def verify_entry_qr(verification_code):
    """Verify event entry QR code"""
    try:
        from qr_generator import qr_generator
        result = qr_generator.verify_qr_code(verification_code)
        
        if result['valid']:
            entry_data = result['data']
            return render_template('qr_verification.html',
                                 verification_result=result,
                                 data_type='entry',
                                 entry_data=entry_data)
        else:
            return render_template('qr_verification.html',
                                 verification_result=result,
                                 data_type='entry')
            
    except Exception as e:
        return render_template('qr_verification.html',
                             verification_result={'valid': False, 'error': str(e)},
                             data_type='entry')

@app.route('/verify/pass/<verification_code>')
def verify_pass_qr(verification_code):
    """Verify digital pass QR code"""
    try:
        from qr_generator import qr_generator
        result = qr_generator.verify_qr_code(verification_code)
        
        if result['valid']:
            pass_data = result['data']
            return render_template('qr_verification.html',
                                 verification_result=result,
                                 data_type='pass',
                                 pass_data=pass_data)
        else:
            return render_template('qr_verification.html',
                                 verification_result=result,
                                 data_type='pass')
            
    except Exception as e:
        return render_template('qr_verification.html',
                             verification_result={'valid': False, 'error': str(e)},
                             data_type='pass')

if __name__ == '__main__':
    with app.app_context():
        try:
            # Create all basic tables
            db.create_all()
            print("✅ Basic database tables created")
            
            # Create enhanced tables with better error handling
            # Temporarily disabled to avoid circular import issues
            print("⚠️ Enhanced tables creation temporarily disabled")
            print("📝 Application will continue with basic functionality")
            # try:
            #     # Import enhanced models only within app context to avoid circular imports
            #     import sys
            #     if 'enhanced_models' not in sys.modules:
            #         import enhanced_models
            #         # Pass db instance to avoid circular import
            #         enhanced_models.db = db
            #     
            #     success = enhanced_models._create_tables_internal(db)
            #     if success:
            #         print("✅ Enhanced database tables created")
            #     else:
            #         print("⚠️ Enhanced tables creation skipped (likely already exist)")
            # except Exception as e:
            #     print(f"⚠️ Could not create enhanced tables: {e}")
            #     print("📝 Application will continue with basic functionality")
                
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            print("📝 Check your database connection and try again")
    
    # Start the application with optimized settings
    print("🚀 Starting CricVerse Stadium System...")
    print(f"🌐 Server will be available at: http://localhost:5000")
    
    # Use production-like settings even in development for better performance
    socketio.run(app, 
                debug=False,  # Disable debug mode to prevent restarts
                host='0.0.0.0', 
                port=5000,
                use_reloader=False,  # Disable auto-reloader
                log_output=False)  # Reduce logging for performance
