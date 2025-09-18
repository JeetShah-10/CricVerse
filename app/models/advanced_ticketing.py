from app import db
from datetime import datetime, timezone
from sqlalchemy import Index
from sqlalchemy.schema import UniqueConstraint

class TicketTransfer(db.Model):
    __tablename__ = 'ticket_transfer'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True) # GENERATED ALWAYS AS IDENTITY
    ticket_id = db.Column(db.BigInteger, db.ForeignKey('ticket.id', ondelete='CASCADE'), nullable=False)
    from_customer_id = db.Column(db.BigInteger, db.ForeignKey('customer.id', ondelete='RESTRICT'), nullable=False)
    to_customer_id = db.Column(db.BigInteger, db.ForeignKey('customer.id', ondelete='SET NULL'), nullable=True)
    to_email = db.Column(db.Text)
    transfer_status = db.Column(db.Text, default='pending')
    transfer_code = db.Column(db.Text, nullable=False)
    transfer_fee = db.Column(db.Numeric(10, 2))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    completed_at = db.Column(db.DateTime(timezone=True))
    verification_code = db.Column(db.Text)
    is_verified = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    __table_args__ = (
        UniqueConstraint('transfer_code', name='uq_ticket_transfer_transfer_code'),
        Index('idx_ticket_transfer_ticket_id', 'ticket_id'),
        Index('idx_ticket_transfer_from_customer', 'from_customer_id'),
        Index('idx_ticket_transfer_to_customer', 'to_customer_id'),
        Index('idx_ticket_transfer_expires_at', 'expires_at'),
        Index('idx_ticket_transfer_status_created_at', 'transfer_status', db.desc('created_at')),
    )

    ticket = db.relationship('Ticket', backref='transfers')
    from_customer = db.relationship('Customer', foreign_keys=[from_customer_id])
    to_customer = db.relationship('Customer', foreign_keys=[to_customer_id])

class ResaleMarketplace(db.Model):
    __tablename__ = 'resale_marketplace'
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), unique=True, nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    original_price = db.Column(db.Float)
    listing_price = db.Column(db.Float, nullable=False)
    platform_fee = db.Column(db.Float)
    seller_fee = db.Column(db.Float)
    listing_status = db.Column(db.String(20), default='active')  # active, sold, expired, cancelled
    listing_description = db.Column(db.Text)
    is_negotiable = db.Column(db.Boolean, default=False)
    listed_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    sold_at = db.Column(db.DateTime)
    buyer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    ticket = db.relationship('Ticket', backref='resale_listing')
    seller = db.relationship('Customer', foreign_keys=[seller_id])
    buyer = db.relationship('Customer', foreign_keys=[buyer_id])

class SeasonTicket(db.Model):
    __tablename__ = 'season_ticket'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'), nullable=False)
    seat_id = db.Column(db.Integer, db.ForeignKey('seat.id'), nullable=False)
    season_name = db.Column(db.String(100), nullable=False)
    season_start_date = db.Column(db.Date)
    season_end_date = db.Column(db.Date)
    total_matches = db.Column(db.Integer)
    matches_used = db.Column(db.Integer, default=0)
    matches_transferred = db.Column(db.Integer, default=0)
    price_per_match = db.Column(db.Float)
    total_price = db.Column(db.Float)
    ticket_status = db.Column(db.String(20), default='active')  # active, expired, cancelled
    priority_booking = db.Column(db.Boolean, default=False)
    transfer_limit = db.Column(db.Integer, default=5)
    activated_at = db.Column(db.DateTime, default=datetime.utcnow)
    customer = db.relationship('Customer', backref='season_tickets')
    stadium = db.relationship('Stadium', backref='season_tickets')
    seat = db.relationship('Seat', backref='season_tickets')

class SeasonTicketMatch(db.Model):
    __tablename__ = 'season_ticket_match'
    id = db.Column(db.Integer, primary_key=True)
    season_ticket_id = db.Column(db.Integer, db.ForeignKey('season_ticket.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    used_at = db.Column(db.DateTime)
    is_transferred = db.Column(db.Boolean, default=False)
    transferred_at = db.Column(db.DateTime)
    transfer_price = db.Column(db.Float)
    season_ticket = db.relationship('SeasonTicket', backref='matches')
    event = db.relationship('Event', backref='season_ticket_matches')
