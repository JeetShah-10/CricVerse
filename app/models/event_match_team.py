from app import db
from datetime import datetime

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
    image_url = db.Column(db.String(200)) # Using image_url as per app/models/match.py

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
    home_score = db.Column(db.Integer, default=0) # Using Integer as per root models.py
    away_score = db.Column(db.Integer, default=0) # Using Integer as per root models.py
    home_wickets = db.Column(db.Integer, default=0)
    away_wickets = db.Column(db.Integer, default=0)
    home_overs = db.Column(db.Float, default=0.0)
    away_overs = db.Column(db.Float, default=0.0)
    result_type = db.Column(db.String(20))
    winning_margin = db.Column(db.String(20))
    updates = db.relationship('MatchUpdate', backref='match', lazy=True)


class EventUmpire(db.Model):
    __tablename__ = 'event_umpire'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    umpire_name = db.Column(db.String(100))
    umpire_role = db.Column(db.String(50)) # Merged from app/models/match.py
