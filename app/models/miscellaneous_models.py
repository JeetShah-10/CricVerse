from app import db
from datetime import datetime, timezone

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

class AccessibilityRequest(db.Model):
    __tablename__ = 'accessibility_request'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False, index=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False, index=True)
    request_type = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending', index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
