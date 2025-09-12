"""
Real-time WebSocket Features for CricVerse
Handles live match updates, booking notifications, and stadium occupancy tracking
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import request, session
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask_login import current_user
import redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize SocketIO
socketio = None
redis_client = None

def init_socketio(app):
    """Initialize SocketIO with the Flask app"""
    global socketio, redis_client
    
    # Initialize Redis for message passing between server instances
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    try:
        redis_client = redis.from_url(redis_url, decode_responses=True)
        redis_client.ping()
        logger.info(f"✅ Redis connected: {redis_url}")
    except Exception as e:
        logger.warning(f"⚠️ Redis connection failed: {e}")
        redis_client = None
    
    # Initialize SocketIO with Redis adapter if available
    if redis_client:
        socketio = SocketIO(app, 
                          cors_allowed_origins="*",
                          message_queue=redis_url,
                          async_mode='threading')
    else:
        socketio = SocketIO(app, 
                          cors_allowed_origins="*",
                          async_mode='threading')
    
    logger.info("✅ SocketIO initialized successfully")
    return socketio


# WebSocket Event Handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    try:
        # Log connection
        client_id = request.sid
        ip_address = request.environ.get('REMOTE_ADDR', 'unknown')
        user_agent = request.environ.get('HTTP_USER_AGENT', 'unknown')
        
        logger.info(f"🔌 Client connected: {client_id} from {ip_address}")
        
        # Store connection info in Redis if available
        if redis_client:
            connection_data = {
                'connected_at': datetime.utcnow().isoformat(),
                'ip_address': ip_address,
                'user_agent': user_agent[:500],  # Truncate long user agents
                'customer_id': current_user.id if current_user.is_authenticated else None
            }
            redis_client.hset(f'ws_connection:{client_id}', mapping=connection_data)
            redis_client.expire(f'ws_connection:{client_id}', 3600)  # Expire after 1 hour
        
        # Send welcome message
        emit('connection_status', {
            'status': 'connected',
            'message': 'Welcome to CricVerse live updates!',
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Connection error: {e}")


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    try:
        client_id = request.sid
        logger.info(f"🔌 Client disconnected: {client_id}")
        
        # Clean up Redis data
        if redis_client:
            redis_client.delete(f'ws_connection:{client_id}')
        
    except Exception as e:
        logger.error(f"❌ Disconnection error: {e}")


@socketio.on('join_match')
def handle_join_match(data):
    """Subscribe to match updates"""
    try:
        match_id = data.get('match_id')
        client_id = request.sid
        
        if not match_id:
            emit('error', {'message': 'Match ID is required'})
            return
        
        # Join the match room
        room = f'match_{match_id}'
        join_room(room)
        
        # Store subscription in Redis
        if redis_client:
            redis_client.sadd(f'match_subscribers:{match_id}', client_id)
            redis_client.expire(f'match_subscribers:{match_id}', 7200)  # 2 hours
        
        logger.info(f"👥 Client {client_id} joined match {match_id}")
        
        # Send confirmation
        emit('subscription_status', {
            'type': 'match',
            'id': match_id,
            'status': 'subscribed',
            'message': f'You are now receiving updates for match {match_id}'
        })
        
        # Send current match status if available
        send_current_match_status(match_id)
        
    except Exception as e:
        logger.error(f"❌ Join match error: {e}")
        emit('error', {'message': 'Failed to join match updates'})


@socketio.on('leave_match')
def handle_leave_match(data):
    """Unsubscribe from match updates"""
    try:
        match_id = data.get('match_id')
        client_id = request.sid
        
        if not match_id:
            emit('error', {'message': 'Match ID is required'})
            return
        
        # Leave the match room
        room = f'match_{match_id}'
        leave_room(room)
        
        # Remove subscription from Redis
        if redis_client:
            redis_client.srem(f'match_subscribers:{match_id}', client_id)
        
        logger.info(f"👥 Client {client_id} left match {match_id}")
        
        # Send confirmation
        emit('subscription_status', {
            'type': 'match',
            'id': match_id,
            'status': 'unsubscribed',
            'message': f'You are no longer receiving updates for match {match_id}'
        })
        
    except Exception as e:
        logger.error(f"❌ Leave match error: {e}")
        emit('error', {'message': 'Failed to leave match updates'})


@socketio.on('join_stadium')
def handle_join_stadium(data):
    """Subscribe to stadium updates (booking notifications, occupancy)"""
    try:
        stadium_id = data.get('stadium_id')
        client_id = request.sid
        
        if not stadium_id:
            emit('error', {'message': 'Stadium ID is required'})
            return
        
        # Join the stadium room
        room = f'stadium_{stadium_id}'
        join_room(room)
        
        # Store subscription in Redis
        if redis_client:
            redis_client.sadd(f'stadium_subscribers:{stadium_id}', client_id)
            redis_client.expire(f'stadium_subscribers:{stadium_id}', 7200)  # 2 hours
        
        logger.info(f"🏟️ Client {client_id} joined stadium {stadium_id}")
        
        # Send confirmation
        emit('subscription_status', {
            'type': 'stadium',
            'id': stadium_id,
            'status': 'subscribed',
            'message': f'You are now receiving updates for stadium {stadium_id}'
        })
        
        # Send current stadium occupancy
        send_stadium_occupancy(stadium_id)
        
    except Exception as e:
        logger.error(f"❌ Join stadium error: {e}")
        emit('error', {'message': 'Failed to join stadium updates'})


# Broadcasting Functions
def broadcast_match_update(match_id, update_type, update_data):
    """Broadcast match update to all subscribers"""
    try:
        if not socketio:
            logger.warning("SocketIO not initialized")
            return
        
        room = f'match_{match_id}'
        
        update_message = {
            'match_id': match_id,
            'type': update_type,
            'data': update_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Broadcast to room
        socketio.emit('match_update', update_message, room=room)
        
        # Store in Redis for persistence
        if redis_client:
            redis_client.lpush(f'match_updates:{match_id}', json.dumps(update_message))
            redis_client.ltrim(f'match_updates:{match_id}', 0, 99)  # Keep last 100 updates
            redis_client.expire(f'match_updates:{match_id}', 86400)  # 24 hours
        
        logger.info(f"📡 Broadcasted match update for match {match_id}: {update_type}")
        
    except Exception as e:
        logger.error(f"❌ Broadcast match update error: {e}")


def broadcast_booking_notification(stadium_id, booking_data):
    """Broadcast booking notification to stadium subscribers"""
    try:
        if not socketio:
            logger.warning("SocketIO not initialized")
            return
        
        room = f'stadium_{stadium_id}'
        
        notification_message = {
            'stadium_id': stadium_id,
            'type': 'booking_notification',
            'data': booking_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Broadcast to room
        socketio.emit('booking_notification', notification_message, room=room)
        
        logger.info(f"📡 Broadcasted booking notification for stadium {stadium_id}")
        
    except Exception as e:
        logger.error(f"❌ Broadcast booking notification error: {e}")


def broadcast_stadium_occupancy(stadium_id, occupancy_data):
    """Broadcast stadium occupancy update"""
    try:
        if not socketio:
            logger.warning("SocketIO not initialized")
            return
        
        room = f'stadium_{stadium_id}'
        
        occupancy_message = {
            'stadium_id': stadium_id,
            'type': 'occupancy_update',
            'data': occupancy_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Broadcast to room
        socketio.emit('occupancy_update', occupancy_message, room=room)
        
        # Store in Redis
        if redis_client:
            redis_client.set(f'stadium_occupancy:{stadium_id}', json.dumps(occupancy_data), ex=300)  # 5 minutes
        
        logger.info(f"📡 Broadcasted occupancy update for stadium {stadium_id}")
        
    except Exception as e:
        logger.error(f"❌ Broadcast occupancy error: {e}")


# Helper Functions
def send_current_match_status(match_id):
    """Send current match status to client"""
    try:
        from app import Match, Event
        
        # Get match from database
        match = Match.query.filter_by(event_id=match_id).first()
        if not match:
            emit('error', {'message': f'Match {match_id} not found'})
            return
        
        # Get event details
        event = Event.query.get(match_id)
        if not event:
            emit('error', {'message': f'Event {match_id} not found'})
            return
        
        # Prepare match status
        match_status = {
            'match_id': match_id,
            'event_name': event.event_name,
            'status': event.match_status,
            'home_team': event.home_team.team_name if event.home_team else 'TBD',
            'away_team': event.away_team.team_name if event.away_team else 'TBD',
            'home_score': match.home_score,
            'away_score': match.away_score,
            'home_wickets': match.home_wickets,
            'away_wickets': match.away_wickets,
            'home_overs': match.home_overs,
            'away_overs': match.away_overs,
            'current_time': datetime.utcnow().isoformat()
        }
        
        emit('current_match_status', match_status)
        
    except Exception as e:
        logger.error(f"❌ Send current match status error: {e}")
        emit('error', {'message': 'Failed to get current match status'})


def send_stadium_occupancy(stadium_id):
    """Send current stadium occupancy to client"""
    try:
        # Get occupancy from Redis first
        if redis_client:
            occupancy_data = redis_client.get(f'stadium_occupancy:{stadium_id}')
            if occupancy_data:
                emit('current_occupancy', json.loads(occupancy_data))
                return
        
        # Calculate occupancy from database
        from app import Stadium, Seat, Ticket, Event
        from datetime import date
        
        stadium = Stadium.query.get(stadium_id)
        if not stadium:
            emit('error', {'message': f'Stadium {stadium_id} not found'})
            return
        
        # Get today's events
        today_events = Event.query.filter(
            Event.stadium_id == stadium_id,
            Event.event_date == date.today()
        ).all()
        
        total_seats = Seat.query.filter_by(stadium_id=stadium_id).count()
        booked_seats = 0
        
        for event in today_events:
            booked_seats += Ticket.query.join(Seat).filter(
                Ticket.event_id == event.id,
                Seat.stadium_id == stadium_id,
                Ticket.ticket_status == 'Booked'
            ).count()
        
        occupancy_percentage = (booked_seats / total_seats * 100) if total_seats > 0 else 0
        
        occupancy_data = {
            'stadium_id': stadium_id,
            'total_seats': total_seats,
            'booked_seats': booked_seats,
            'available_seats': total_seats - booked_seats,
            'occupancy_percentage': round(occupancy_percentage, 2),
            'events_today': len(today_events),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        emit('current_occupancy', occupancy_data)
        
    except Exception as e:
        logger.error(f"❌ Send stadium occupancy error: {e}")
        emit('error', {'message': 'Failed to get stadium occupancy'})


def get_active_connections():
    """Get count of active WebSocket connections"""
    try:
        if not redis_client:
            return 0
        
        # Get all connection keys
        connection_keys = redis_client.keys('ws_connection:*')
        return len(connection_keys)
        
    except Exception as e:
        logger.error(f"❌ Get active connections error: {e}")
        return 0


# Match Update Functions (to be called from other parts of the app)
def update_match_score(match_id, home_score, away_score, home_wickets=None, away_wickets=None, current_over=None):
    """Update match score and broadcast to subscribers"""
    update_data = {
        'home_score': home_score,
        'away_score': away_score,
    }
    
    if home_wickets is not None:
        update_data['home_wickets'] = home_wickets
    if away_wickets is not None:
        update_data['away_wickets'] = away_wickets
    if current_over is not None:
        update_data['current_over'] = current_over
    
    broadcast_match_update(match_id, 'score_update', update_data)


def update_match_wicket(match_id, team, batsman_name, bowler_name, wicket_type, current_score, current_over):
    """Update match wicket and broadcast to subscribers"""
    update_data = {
        'team': team,
        'batsman': batsman_name,
        'bowler': bowler_name,
        'wicket_type': wicket_type,
        'current_score': current_score,
        'current_over': current_over
    }
    
    broadcast_match_update(match_id, 'wicket', update_data)


def update_match_status(match_id, status, winner=None):
    """Update match status and broadcast to subscribers"""
    update_data = {
        'status': status,
        'winner': winner
    }
    
    broadcast_match_update(match_id, 'status_change', update_data)


# Booking notification functions
def notify_new_booking(stadium_id, booking_info):
    """Notify about new booking"""
    booking_data = {
        'type': 'new_booking',
        'customer_name': booking_info.get('customer_name', 'Anonymous'),
        'event_name': booking_info.get('event_name', 'Unknown Event'),
        'seats_booked': booking_info.get('seats_count', 0),
        'total_amount': booking_info.get('total_amount', 0)
    }
    
    broadcast_booking_notification(stadium_id, booking_data)


# Background tasks for cleanup and monitoring
def cleanup_expired_connections():
    """Clean up expired WebSocket connections (run periodically)"""
    try:
        if not redis_client:
            return
        
        # This would be called by a background task (e.g., Celery)
        connection_keys = redis_client.keys('ws_connection:*')
        current_time = datetime.utcnow()
        
        for key in connection_keys:
            connection_data = redis_client.hgetall(key)
            if connection_data:
                connected_at = datetime.fromisoformat(connection_data.get('connected_at', ''))
                if current_time - connected_at > timedelta(hours=2):
                    redis_client.delete(key)
                    logger.info(f"🧹 Cleaned up expired connection: {key}")
    
    except Exception as e:
        logger.error(f"❌ Cleanup connections error: {e}")


# Statistics and monitoring
def get_realtime_stats():
    """Get real-time statistics"""
    try:
        stats = {
            'active_connections': get_active_connections(),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if redis_client:
            # Get active matches
            match_keys = redis_client.keys('match_subscribers:*')
            stats['active_matches'] = len(match_keys)
            
            # Get active stadiums
            stadium_keys = redis_client.keys('stadium_subscribers:*')
            stats['active_stadiums'] = len(stadium_keys)
        else:
            stats['active_matches'] = 0
            stats['active_stadiums'] = 0
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Get realtime stats error: {e}")
        return {
            'active_connections': 0,
            'active_matches': 0,
            'active_stadiums': 0,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }