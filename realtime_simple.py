"""
Simple Real-time WebSocket Features for CricVerse
Handles live match updates, booking notifications, and stadium occupancy tracking
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import request, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import current_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global SocketIO instance
socketio = None

def init_socketio(app):
    """Initialize SocketIO with the Flask app"""
    global socketio
    
    try:
        # Initialize SocketIO
        socketio = SocketIO(app, 
                          cors_allowed_origins="*",
                          async_mode='threading')
        
        # Register event handlers
        register_handlers()
        
        logger.info("✅ SocketIO initialized successfully")
        return socketio
        
    except Exception as e:
        logger.error(f"❌ SocketIO initialization failed: {e}")
        return None

def register_handlers():
    """Register all SocketIO event handlers"""
    global socketio
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        try:
            client_id = request.sid
            ip_address = request.environ.get('REMOTE_ADDR', 'unknown')
            
            logger.info(f"🔌 Client connected: {client_id} from {ip_address}")
            
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
            
            logger.info(f"👥 Client {client_id} joined match {match_id}")
            
            # Send confirmation
            emit('subscription_status', {
                'type': 'match',
                'id': match_id,
                'status': 'subscribed',
                'message': f'You are now receiving updates for match {match_id}'
            })
            
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

    @socketio.on('join_room')
    def handle_join_room(data):
        """Join a general room"""
        try:
            room_name = data.get('room')
            client_id = request.sid
            
            if not room_name:
                emit('error', {'message': 'Room name is required'})
                return
            
            join_room(room_name)
            
            logger.info(f"👥 Client {client_id} joined room {room_name}")
            
            emit('room_joined', {
                'room': room_name,
                'message': f'Joined {room_name}',
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Join room error: {e}")
            emit('error', {'message': 'Failed to join room'})

    @socketio.on('send_message')
    def handle_send_message(data):
        """Handle real-time chat messages"""
        try:
            if not current_user.is_authenticated:
                emit('error', {'message': 'Authentication required'})
                return
            
            message = data.get('message', '').strip()
            room = data.get('room', 'general')
            
            if not message:
                emit('error', {'message': 'Message cannot be empty'})
                return
            
            # Prepare message data
            message_data = {
                'user_id': current_user.id,
                'username': current_user.name,
                'message': message[:500],  # Limit message length
                'room': room,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Broadcast to room
            socketio.emit('new_message', message_data, room=room)
            
            logger.info(f"Message from {current_user.name} in {room}: {message[:50]}")
            
        except Exception as e:
            logger.error(f"❌ Send message error: {e}")
            emit('error', {'message': 'Failed to send message'})

def broadcast_match_update(match_id, update_data):
    """Broadcast live match updates to subscribers"""
    if not socketio:
        return
    
    try:
        room_name = f'match_{match_id}'
        
        update_payload = {
            'match_id': match_id,
            'update_type': update_data.get('type', 'score_update'),
            'data': update_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        socketio.emit('match_update', update_payload, room=room_name)
        
        logger.info(f"Broadcast match update for {match_id}: {update_data.get('type')}")
        
    except Exception as e:
        logger.error(f"❌ Broadcast match update error: {e}")

def broadcast_general_announcement(message, announcement_type='info'):
    """Broadcast general announcements to all connected users"""
    if not socketio:
        return
    
    try:
        announcement_payload = {
            'id': str(datetime.utcnow().timestamp()),
            'type': announcement_type,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        socketio.emit('announcement', announcement_payload, room='general')
        
        logger.info(f"Broadcast announcement: {message[:50]}")
        
    except Exception as e:
        logger.error(f"❌ Broadcast announcement error: {e}")

def get_realtime_stats():
    """Get real-time statistics about connected users"""
    try:
        # Simple stats since we don't have Redis tracking
        stats = {
            'total_connections': 0,  # Would need to track this properly
            'active_rooms': 0,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Get realtime stats error: {e}")
        return {'error': 'Failed to get statistics'}