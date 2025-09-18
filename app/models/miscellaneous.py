from app import db
from datetime import datetime

class AccessibilityAccommodation(db.Model):
    __tablename__ = 'accessibility_accommodation'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), unique=True, nullable=False)
    accommodation_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    severity_level = db.Column(db.String(50))
    is_verified = db.Column(db.Boolean, default=False)
    verified_by = db.Column(db.String(100))
    verified_at = db.Column(db.DateTime)
    requires_wheelchair_access = db.Column(db.Boolean, default=False)
    requires_companion_seat = db.Column(db.Boolean, default=False)
    requires_aisle_access = db.Column(db.Boolean, default=False)
    requires_hearing_loop = db.Column(db.Boolean, default=False)
    requires_sign_language = db.Column(db.Boolean, default=False)
    requires_braille = db.Column(db.Boolean, default=False)
    mobility_equipment = db.Column(db.String(100))
    service_animal = db.Column(db.Boolean, default=False)
    service_animal_type = db.Column(db.String(100))
    preferred_communication = db.Column(db.String(50))
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    customer = db.relationship('Customer', backref='accessibility_accommodation')

class AccessibilityBooking(db.Model):
    __tablename__ = 'accessibility_booking'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    accommodation_id = db.Column(db.Integer, db.ForeignKey('accessibility_accommodation.id'), nullable=False)
    requested_accommodations = db.Column(db.Text)
    provided_accommodations = db.Column(db.Text)
    special_instructions = db.Column(db.Text)
    accommodation_status = db.Column(db.String(20), default='requested') # requested, confirmed, denied
    staff_notes = db.Column(db.Text)
    fulfilled_at = db.Column(db.DateTime)
    booking = db.relationship('Booking', backref='accessibility_booking')
    accommodation = db.relationship('AccessibilityAccommodation', backref='bookings')

class VerificationSubmission(db.Model):
    __tablename__ = 'verification_submission'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    document_urls = db.Column(db.Text)
    notes = db.Column(db.Text)
    submission_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    review_status = db.Column(db.String(20), default='pending') # pending, approved, rejected
    reviewed_by = db.Column(db.String(100))
    reviewed_at = db.Column(db.DateTime)
    user = db.relationship('Customer', backref='verification_submissions')

class QRCode(db.Model):
    __tablename__ = 'qr_code'
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    qr_code_data = db.Column(db.String(255), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    ticket = db.relationship('Ticket', backref='qr_codes')

class Notification(db.Model):
    __tablename__ = 'notification'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    notification_type = db.Column(db.String(50)) # booking_confirmation, event_reminder, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    customer = db.relationship('Customer', backref='notifications')

class MatchUpdate(db.Model):
    __tablename__ = 'match_update'
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=False)
    update_type = db.Column(db.String(50)) # score, wicket, etc.
    update_data = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    match = db.relationship('Match', backref='updates')

class ChatConversation(db.Model):
    __tablename__ = 'chat_conversation'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    session_id = db.Column(db.String(100), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    message_count = db.Column(db.Integer, default=0)
    customer = db.relationship('Customer', backref='chat_conversations')

class ChatMessage(db.Model):
    __tablename__ = 'chat_message'
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('chat_conversation.id'), nullable=False)
    sender_type = db.Column(db.String(20)) # user, bot
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    conversation = db.relationship('ChatConversation', backref='messages')

class BookingAnalytics(db.Model):
    __tablename__ = 'booking_analytics'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'))
    booking_date = db.Column(db.Date)
    total_bookings = db.Column(db.Integer)
    total_revenue = db.Column(db.Float)
    event = db.relationship('Event', backref='analytics')
    stadium = db.relationship('Stadium', backref='analytics')

class SystemLog(db.Model):
    __tablename__ = 'system_log'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    log_level = db.Column(db.String(20)) # INFO, WARNING, ERROR, CRITICAL
    category = db.Column(db.String(50)) # auth, payment, security, etc.
    action = db.Column(db.String(100))
    message = db.Column(db.Text)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    request_url = db.Column(db.String(255))
    request_method = db.Column(db.String(10))
    extra_data = db.Column(db.Text)
    customer = db.relationship('Customer', backref='logs')

class WebSocketConnection(db.Model):
    __tablename__ = 'websocket_connection'
    id = db.Column(db.Integer, primary_key=True)
    sid = db.Column(db.String(100), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    connected_at = db.Column(db.DateTime, default=datetime.utcnow)
    disconnected_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    customer = db.relationship('Customer', backref='websocket_connections')
