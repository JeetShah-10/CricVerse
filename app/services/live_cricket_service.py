"""
Live Cricket Scoring Service for CricVerse
Simple live cricket scoring system like Cricbuzz
Real-time updates for scores, overs, runs, and wickets
Big Bash League Cricket Platform
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from flask import current_app
from flask_socketio import SocketIO, emit, join_room, leave_room
from sqlalchemy import func
from app import db
from app.models import Match, Team, Event, Stadium
from app.services.supabase_service import supabase_service

# Configure logging
logger = logging.getLogger(__name__)

class LiveCricketService:
    """Service for live cricket scoring and real-time updates"""
    
    def __init__(self):
        self.socketio = None
        self.active_matches = {}
        self.initialized = False
    
    def init_app(self, app, socketio_instance):
        """Initialize with Flask app and SocketIO"""
        self.socketio = socketio_instance
        self.initialized = True
        logger.info("✅ Live cricket service initialized")
        
        # Register SocketIO event handlers
        self.register_socketio_handlers()
    
    def register_socketio_handlers(self):
        """Register SocketIO event handlers for live cricket"""
        if not self.socketio:
            return
        
        @self.socketio.on('join_match')
        def handle_join_match(data):
            """Handle client joining a match room"""
            try:
                match_id = data.get('match_id')
                if match_id:
                    join_room(f'match_{match_id}')
                    # Send current match status
                    match_status = self.get_live_match_status(match_id)
                    emit('match_status', match_status)
                    logger.info(f"Client joined match room: match_{match_id}")
            except Exception as e:
                logger.error(f"Error joining match room: {str(e)}")
        
        @self.socketio.on('leave_match')
        def handle_leave_match(data):
            """Handle client leaving a match room"""
            try:
                match_id = data.get('match_id')
                if match_id:
                    leave_room(f'match_{match_id}')
                    logger.info(f"Client left match room: match_{match_id}")
            except Exception as e:
                logger.error(f"Error leaving match room: {str(e)}")
        
        @self.socketio.on('get_live_matches')
        def handle_get_live_matches():
            """Handle request for all live matches"""
            try:
                live_matches = self.get_all_live_matches()
                emit('live_matches_update', live_matches)
            except Exception as e:
                logger.error(f"Error getting live matches: {str(e)}")
    
    def get_live_match_status(self, match_id: int) -> Dict[str, Any]:
        """Get current status of a live match"""
        try:
            match = Match.query.get(match_id)
            if not match:
                return {'error': 'Match not found'}
            
            # Get team information
            team1 = match.team1
            team2 = match.team2
            
            # Get basic match info
            match_status = {
                'match_id': match.id,
                'status': match.event.match_status,
                'team1': {
                    'id': match.event.home_team.id if match.event.home_team else None,
                    'name': match.event.home_team.team_name if match.event.home_team else 'Team 1',
                    'score': getattr(match, 'home_score', 0),
                    'wickets': getattr(match, 'wickets_home', 0),
                    'overs': getattr(match, 'overs_home', '0.0')
                },
                'team2': {
                    'id': match.event.away_team.id if match.event.away_team else None,
                    'name': match.event.away_team.team_name if match.event.away_team else 'Team 2',
                    'score': getattr(match, 'away_score', 0),
                    'wickets': getattr(match, 'wickets_away', 0),
                    'overs': getattr(match, 'overs_away', '0.0')
                },
                'current_over': getattr(match, 'current_over', '0.0'),
                'current_innings': getattr(match, 'current_innings', 1),
                'batting_team': getattr(match, 'current_innings', 1),
                'venue': match.event.stadium.name if match.event and match.event.stadium else 'Unknown',
                'match_type': getattr(match.event, 'event_type', 'T20'),
                'last_updated': datetime.utcnow().isoformat()
            }
            
            # Add match summary
            if match.is_live == True:
                batting_team_name = match_status['team1']['name'] if match_status['batting_team'] == 1 else match_status['team2']['name']
                batting_score = match_status['team1']['score'] if match_status['batting_team'] == 1 else match_status['team2']['score']
                batting_wickets = match_status['team1']['wickets'] if match_status['batting_team'] == 1 else match_status['team2']['wickets']
                batting_overs = match_status['team1']['overs'] if match_status['batting_team'] == 1 else match_status['team2']['overs']
                
                match_status['summary'] = f"{batting_team_name} {batting_score}/{batting_wickets} ({batting_overs} overs)"
            elif match.is_live == False and match.event.match_status == 'Completed':
                # Determine winner
                team1_total = match_status['team1']['score']
                team2_total = match_status['team2']['score']
                if team1_total > team2_total:
                    match_status['summary'] = f"{match_status['team1']['name']} won by {team1_total - team2_total} runs"
                elif team2_total > team1_total:
                    match_status['summary'] = f"{match_status['team2']['name']} won by {team2_total - team1_total} runs"
                else:
                    match_status['summary'] = "Match tied"
            else:
                match_status['summary'] = f"Match {match.event.match_status}"
            
            return match_status
            
        except Exception as e:
            logger.error(f"Error getting match status for {match_id}: {str(e)}")
            return {'error': str(e)}
    
    def get_all_live_matches(self) -> List[Dict[str, Any]]:
        """Get all currently live matches"""
        try:
            live_matches = Match.query.filter_by(is_live=True).all()
            
            matches_data = []
            for match in live_matches:
                match_status = self.get_live_match_status(match.id)
                if 'error' not in match_status:
                    matches_data.append(match_status)
            
            return matches_data
            
        except Exception as e:
            logger.error(f"Error getting all live matches: {str(e)}")
            return []
    
    def update_match_score(self, match_id: int, update_data: Dict[str, Any]) -> bool:
        """Update match score and broadcast to clients"""
        try:
            match = Match.query.get(match_id)
            if not match:
                return False
            
            # Update match data
            if 'team1_score' in update_data:
                match.home_score = update_data['team1_score']
            if 'team1_wickets' in update_data:
                match.wickets_home = update_data['team1_wickets']
            if 'team1_overs' in update_data:
                match.overs_home = update_data['team1_overs']
            if 'team2_score' in update_data:
                match.away_score = update_data['team2_score']
            if 'team2_wickets' in update_data:
                match.wickets_away = update_data['team2_wickets']
            if 'team2_overs' in update_data:
                match.overs_away = update_data['team2_overs']
            if 'current_over' in update_data:
                match.current_over = update_data['current_over']
            if 'current_innings' in update_data:
                match.current_innings = update_data['current_innings']
            if 'batting_team' in update_data:
                match.batting_team = update_data['batting_team']
            if 'is_live' in update_data:
                match.is_live = update_data['is_live']
            if 'match_status' in update_data:
                match.event.match_status = update_data['match_status']
            
            db.session.commit()
            
            # Broadcast update to all clients in match room
            if self.socketio:
                match_status = self.get_live_match_status(match_id)
                self.socketio.emit('match_update', match_status, room=f'match_{match_id}')
                
                # Also broadcast to general live matches room
                live_matches = self.get_all_live_matches()
                self.socketio.emit('live_matches_update', live_matches, room='live_matches')
            
            logger.info(f"Match {match_id} updated and broadcasted")
            return True
            
        except Exception as e:
            logger.error(f"Error updating match {match_id}: {str(e)}")
            db.session.rollback()
            return False
    
    def start_match(self, match_id: int) -> bool:
        """Start a match and set it to live status"""
        try:
            match = Match.query.get(match_id)
            if not match:
                return False
            
            match.is_live = True
            match.event.match_status = 'Live'
            match.current_innings = 1
            match.batting_team = 1  # Team 1 bats first by default
            match.current_over = '0.0'
            
            # Initialize scores if not set
            if not hasattr(match, 'home_score') or match.home_score is None:
                match.home_score = 0
                match.wickets_home = 0
                match.overs_home = '0.0'
                match.away_score = 0
                match.wickets_away = 0
                match.overs_away = '0.0'
            
            db.session.commit()
            
            # Broadcast match start
            if self.socketio:
                match_status = self.get_live_match_status(match_id)
                self.socketio.emit('match_started', match_status, room=f'match_{match_id}')
                
                # Update live matches list
                live_matches = self.get_all_live_matches()
                self.socketio.emit('live_matches_update', live_matches, room='live_matches')
            
            logger.info(f"Match {match_id} started")
            return True
            
        except Exception as e:
            logger.error(f"Error starting match {match_id}: {str(e)}")
            db.session.rollback()
            return False
    
    def end_match(self, match_id: int) -> bool:
        """End a match and set it to completed status"""
        try:
            match = Match.query.get(match_id)
            if not match:
                return False
            
            match.is_live = False
            match.event.match_status = 'Completed'
            db.session.commit()
            
            # Broadcast match end
            if self.socketio:
                match_status = self.get_live_match_status(match_id)
                self.socketio.emit('match_ended', match_status, room=f'match_{match_id}')
                
                # Update live matches list
                live_matches = self.get_all_live_matches()
                self.socketio.emit('live_matches_update', live_matches, room='live_matches')
            
            logger.info(f"Match {match_id} ended")
            return True
            
        except Exception as e:
            logger.error(f"Error ending match {match_id}: {str(e)}")
            db.session.rollback()
            return False
    
    def get_match_summary(self, match_id: int) -> Dict[str, Any]:
        """Get comprehensive match summary"""
        try:
            match_status = self.get_live_match_status(match_id)
            if 'error' in match_status:
                return match_status
            
            # Add additional summary information
            match_status['match_info'] = {
                'format': match_status.get('match_type', 'T20'),
                'total_overs': 20 if match_status.get('match_type', 'T20') == 'T20' else 50,
                'venue': match_status['venue'],
                'status': match_status['status']
            }
            
            return match_status
            
        except Exception as e:
            logger.error(f"Error getting match summary for {match_id}: {str(e)}")
            return {'error': str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for live cricket service"""
        try:
            live_matches_count = Match.query.filter_by(is_live=True).count()
            total_matches = Match.query.count()
            
            return {
                'status': 'healthy',
                'initialized': self.initialized,
                'socketio_connected': self.socketio is not None,
                'live_matches': live_matches_count,
                'total_matches': total_matches,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Live cricket service health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

# Global service instance
live_cricket_service = LiveCricketService()
