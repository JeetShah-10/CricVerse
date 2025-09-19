from app import db
from datetime import datetime

class Event(db.Model):
    __tablename__ = 'event'
    id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String(100), nullable=False)
    event_type = db.Column(db.String(50))
    tournament_name = db.Column(db.String(100))
    event_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time)
    stadium_id = db.Column(db.Integer, db.ForeignKey('stadium.id'), nullable=False)
    home_team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    away_team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    match_status = db.Column(db.String(20), default='Scheduled')
    stadium = db.relationship('Stadium', backref='events')
    home_team = db.relationship('Team', foreign_keys=[home_team_id])
    away_team = db.relationship('Team', foreign_keys=[away_team_id])

class Match(db.Model):
    __tablename__ = 'match'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    score_home = db.Column(db.String(20))
    score_away = db.Column(db.String(20))
    overs_home = db.Column(db.Float)
    overs_away = db.Column(db.Float)
    current_innings = db.Column(db.String(20))
    is_live = db.Column(db.Boolean, default=False)
    event = db.relationship('Event', backref='match')

class Team(db.Model):
    __tablename__ = 'team'
    id = db.Column(db.Integer, primary_key=True)
    team_name = db.Column(db.String(100), nullable=False)
    team_logo = db.Column(db.String(200))
    # Removed non-existent columns (coach, captain, home_city, home_ground) to match Supabase
    players = db.relationship('Player', backref='team', lazy=True)

class Player(db.Model):
    __tablename__ = 'player'
    id = db.Column(db.Integer, primary_key=True)
    player_name = db.Column(db.String(100), nullable=False)
    player_role = db.Column(db.String(50))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    nationality = db.Column(db.String(50))
    batting_style = db.Column(db.String(50))
    bowling_style = db.Column(db.String(50))
    # Align with actual database column name 'photo_url' but expose as image_url attribute
    image_url = db.Column('photo_url', db.String(200))

class EventUmpire(db.Model):
    __tablename__ = 'event_umpire'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    umpire_name = db.Column(db.String(100), nullable=False)
    umpire_role = db.Column(db.String(50)) # On-field, Third Umpire, etc.
    event = db.relationship('Event', backref='umpires')
