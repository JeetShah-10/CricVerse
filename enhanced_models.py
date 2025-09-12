"""
Enhanced Database Models for CricVerse Advanced Features
These models extend the existing database schema with new functionality.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json

# Import the existing db instance
from app import db


# Enhanced Customer model with additional fields for new features
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


# Enhanced Payment model with Stripe integration
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


# QR Code model for tickets and parking passes
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


# Notification system
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


# Real-time match updates
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


# AI Chatbot conversation history
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


# Enhanced analytics
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


# WebSocket connection tracking
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


def create_enhanced_tables():
    """Create all enhanced tables"""
    try:
        db.create_all()
        print("✅ Enhanced database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to create enhanced tables: {e}")
        return False


def add_enhanced_columns():
    """Add new columns to existing tables"""
    try:
        # Add columns to existing Customer table
        # Note: These would be migration commands in a real application
        migration_commands = [
            # Customer table enhancements
            "ALTER TABLE customer ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;",
            "ALTER TABLE customer ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;",
            "ALTER TABLE customer ADD COLUMN IF NOT EXISTS last_login TIMESTAMP;",
            "ALTER TABLE customer ADD COLUMN IF NOT EXISTS is_email_verified BOOLEAN DEFAULT FALSE;",
            "ALTER TABLE customer ADD COLUMN IF NOT EXISTS email_verification_token VARCHAR(100);",
            
            # Payment table enhancements
            "ALTER TABLE payment ADD COLUMN IF NOT EXISTS stripe_payment_intent_id VARCHAR(200);",
            "ALTER TABLE payment ADD COLUMN IF NOT EXISTS currency VARCHAR(3) DEFAULT 'AUD';",
            "ALTER TABLE payment ADD COLUMN IF NOT EXISTS payment_status VARCHAR(20) DEFAULT 'completed';",
            
            # Ticket table enhancements
            "ALTER TABLE ticket ADD COLUMN IF NOT EXISTS qr_code VARCHAR(200);",
            "ALTER TABLE ticket ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;",
            "ALTER TABLE ticket ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;",
            
            # Parking booking enhancements
            "ALTER TABLE parking_booking ADD COLUMN IF NOT EXISTS qr_code VARCHAR(200);",
            "ALTER TABLE parking_booking ADD COLUMN IF NOT EXISTS payment_status VARCHAR(20) DEFAULT 'pending';",
            "ALTER TABLE parking_booking ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;",
            
            # Event table enhancements for real-time updates
            "ALTER TABLE event ADD COLUMN IF NOT EXISTS is_live BOOLEAN DEFAULT FALSE;",
            "ALTER TABLE event ADD COLUMN IF NOT EXISTS live_score_home INTEGER DEFAULT 0;",
            "ALTER TABLE event ADD COLUMN IF NOT EXISTS live_score_away INTEGER DEFAULT 0;",
            "ALTER TABLE event ADD COLUMN IF NOT EXISTS current_over FLOAT DEFAULT 0.0;",
        ]
        
        print("📝 Enhanced column migration commands ready:")
        for cmd in migration_commands:
            print(f"   {cmd}")
        
        print("\n⚠️ Note: These migrations should be run manually in your database.")
        print("   For PostgreSQL, connect to your database and run the ALTER TABLE commands.")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to prepare enhanced columns: {e}")
        return False