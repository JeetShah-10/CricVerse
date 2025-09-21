"""
Real-time Notification Service for CricVerse
Handles live scoring, booking updates, system notifications, and real-time features
Big Bash League Cricket Platform
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
from threading import Thread
import time

from flask import current_app
from flask_socketio import emit, join_room, leave_room
from app import socketio, db
from app.models import Event, Match, Booking, Customer, Stadium

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationType(Enum):
    """Types of notifications"""
    BOOKING_CONFIRMATION = "booking_confirmation"
    BOOKING_UPDATE = "booking_update"
    LIVE_SCORE = "live_score"
    MATCH_START = "match_start"
    MATCH_END = "match_end"
    SYSTEM_ALERT = "system_alert"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    SEAT_AVAILABILITY = "seat_availability"
    WEATHER_UPDATE = "weather_update"
    TRAFFIC_ALERT = "traffic_alert"

@dataclass
class NotificationMessage:
    """Structure for notification messages"""
    id: str
    type: NotificationType
    title: str
    message: str
    data: Dict[str, Any]
    timestamp: datetime
    priority: str = "normal"  # low, normal, high, urgent
    expires_at: Optional[datetime] = None
    target_users: Optional[List[int]] = None
    target_rooms: Optional[List[str]] = None

@dataclass
class LiveScoreUpdate:
    """Structure for live score updates"""
    match_id: int
    team1_score: int
    team2_score: int
    team1_wickets: int
    team2_wickets: int
    current_over: str
    current_ball: int
    batting_team: str
    bowling_team: str
    last_ball: str
    commentary: str
    timestamp: datetime

@dataclass
class BookingNotification:
    """Structure for booking notifications"""
    booking_id: int
    customer_id: int
    event_id: int
    status: str
    message: str
    details: Dict[str, Any]
    timestamp: datetime

class RealtimeNotificationService:
    """Service for managing real-time notifications and live updates"""
    
    def __init__(self):
        self.active_matches = {}
        self.notification_queue = []
        self.user_subscriptions = {}
        self.room_subscriptions = {}
        self.score_updater_thread = None
        self.notification_processor_thread = None
        self._running = False
    
    def start_service(self):
        """Start the real-time service"""
        if not self._running:
            self._running = True
            self.score_updater_thread = Thread(target=self._score_updater_loop, daemon=True)
            self.notification_processor_thread = Thread(target=self._notification_processor_loop, daemon=True)
            
            self.score_updater_thread.start()
            self.notification_processor_thread.start()
            
            logger.info("Real-time notification service started")
    
    def stop_service(self):
        """Stop the real-time service"""
        self._running = False
        logger.info("Real-time notification service stopped")
    
    # Live Scoring Features
    def start_live_match(self, match_id: int, team1: str, team2: str):
        """Start live scoring for a match"""
        try:
            match_data = {
                'match_id': match_id,
                'team1': team1,
                'team2': team2,
                'team1_score': 0,
                'team2_score': 0,
                'team1_wickets': 0,
                'team2_wickets': 0,
                'current_over': '0.0',
                'current_ball': 0,
                'batting_team': team1,
                'bowling_team': team2,
                'status': 'live',
                'start_time': datetime.utcnow(),
                'last_update': datetime.utcnow(),
                'commentary': []
            }
            
            self.active_matches[match_id] = match_data
            
            # Notify match start
            notification = NotificationMessage(
                id=f"match_start_{match_id}",
                type=NotificationType.MATCH_START,
                title="Match Started!",
                message=f"{team1} vs {team2} - Live scoring has begun!",
                data={'match_id': match_id, 'teams': [team1, team2]},
                timestamp=datetime.utcnow(),
                priority="high",
                target_rooms=[f"match_{match_id}", "live_matches"]
            )
            
            self.queue_notification(notification)
            logger.info(f"Started live match {match_id}: {team1} vs {team2}")
            
        except Exception as e:
            logger.error(f"Error starting live match {match_id}: {str(e)}")
    
    def update_live_score(self, match_id: int, score_update: Dict[str, Any]):
        """Update live score for a match"""
        try:
            if match_id not in self.active_matches:
                logger.warning(f"Match {match_id} not found in active matches")
                return
            
            match_data = self.active_matches[match_id]
            
            # Update match data
            for key, value in score_update.items():
                if key in match_data:
                    match_data[key] = value
            
            match_data['last_update'] = datetime.utcnow()
            
            # Create live score update
            live_update = LiveScoreUpdate(
                match_id=match_id,
                team1_score=match_data['team1_score'],
                team2_score=match_data['team2_score'],
                team1_wickets=match_data['team1_wickets'],
                team2_wickets=match_data['team2_wickets'],
                current_over=match_data['current_over'],
                current_ball=match_data['current_ball'],
                batting_team=match_data['batting_team'],
                bowling_team=match_data['bowling_team'],
                last_ball=score_update.get('last_ball', ''),
                commentary=score_update.get('commentary', ''),
                timestamp=datetime.utcnow()
            )
            
            # Broadcast to subscribers
            self._broadcast_live_score(live_update)
            
            logger.info(f"Updated live score for match {match_id}")
            
        except Exception as e:
            logger.error(f"Error updating live score for match {match_id}: {str(e)}")
    
    def end_live_match(self, match_id: int, final_result: str):
        """End live scoring for a match"""
        try:
            if match_id not in self.active_matches:
                return
            
            match_data = self.active_matches[match_id]
            match_data['status'] = 'completed'
            match_data['final_result'] = final_result
            match_data['end_time'] = datetime.utcnow()
            
            # Notify match end
            notification = NotificationMessage(
                id=f"match_end_{match_id}",
                type=NotificationType.MATCH_END,
                title="Match Completed!",
                message=f"Final Result: {final_result}",
                data={
                    'match_id': match_id,
                    'final_result': final_result,
                    'match_data': match_data
                },
                timestamp=datetime.utcnow(),
                priority="high",
                target_rooms=[f"match_{match_id}", "live_matches"]
            )
            
            self.queue_notification(notification)
            
            # Remove from active matches after 1 hour
            def cleanup_match():
                time.sleep(3600)  # 1 hour
                if match_id in self.active_matches:
                    del self.active_matches[match_id]
            
            Thread(target=cleanup_match, daemon=True).start()
            
            logger.info(f"Ended live match {match_id}: {final_result}")
            
        except Exception as e:
            logger.error(f"Error ending live match {match_id}: {str(e)}")
    
    # Booking Notifications
    def send_booking_confirmation(self, booking_id: int):
        """Send booking confirmation notification"""
        try:
            booking = Booking.query.get(booking_id)
            if not booking:
                logger.warning(f"Booking {booking_id} not found")
                return
            
            customer = Customer.query.get(booking.customer_id)
            event = Event.query.get(booking.event_id) if hasattr(booking, 'event_id') else None
            
            notification_data = BookingNotification(
                booking_id=booking_id,
                customer_id=booking.customer_id,
                event_id=getattr(booking, 'event_id', None),
                status='confirmed',
                message=f"Your booking has been confirmed! Booking ID: {booking_id}",
                details={
                    'total_amount': float(booking.total_amount),
                    'booking_date': booking.booking_date.isoformat(),
                    'event_name': event.event_name if event else 'N/A',
                    'customer_name': customer.name if customer else 'N/A'
                },
                timestamp=datetime.utcnow()
            )
            
            notification = NotificationMessage(
                id=f"booking_confirm_{booking_id}",
                type=NotificationType.BOOKING_CONFIRMATION,
                title="Booking Confirmed! 🎉",
                message=notification_data.message,
                data=asdict(notification_data),
                timestamp=datetime.utcnow(),
                priority="high",
                target_users=[booking.customer_id]
            )
            
            self.queue_notification(notification)
            logger.info(f"Sent booking confirmation for booking {booking_id}")
            
        except Exception as e:
            logger.error(f"Error sending booking confirmation {booking_id}: {str(e)}")
    
    def send_booking_update(self, booking_id: int, status: str, message: str):
        """Send booking update notification"""
        try:
            booking = Booking.query.get(booking_id)
            if not booking:
                return
            
            notification_data = BookingNotification(
                booking_id=booking_id,
                customer_id=booking.customer_id,
                event_id=getattr(booking, 'event_id', None),
                status=status,
                message=message,
                details={'booking_id': booking_id, 'status': status},
                timestamp=datetime.utcnow()
            )
            
            notification = NotificationMessage(
                id=f"booking_update_{booking_id}_{int(time.time())}",
                type=NotificationType.BOOKING_UPDATE,
                title="Booking Update",
                message=message,
                data=asdict(notification_data),
                timestamp=datetime.utcnow(),
                priority="normal",
                target_users=[booking.customer_id]
            )
            
            self.queue_notification(notification)
            logger.info(f"Sent booking update for booking {booking_id}: {status}")
            
        except Exception as e:
            logger.error(f"Error sending booking update {booking_id}: {str(e)}")
    
    def send_payment_notification(self, booking_id: int, success: bool, message: str):
        """Send payment notification"""
        try:
            booking = Booking.query.get(booking_id)
            if not booking:
                return
            
            notification_type = NotificationType.PAYMENT_SUCCESS if success else NotificationType.PAYMENT_FAILED
            title = "Payment Successful! ✅" if success else "Payment Failed ❌"
            priority = "high" if not success else "normal"
            
            notification = NotificationMessage(
                id=f"payment_{booking_id}_{int(time.time())}",
                type=notification_type,
                title=title,
                message=message,
                data={
                    'booking_id': booking_id,
                    'success': success,
                    'amount': float(booking.total_amount)
                },
                timestamp=datetime.utcnow(),
                priority=priority,
                target_users=[booking.customer_id]
            )
            
            self.queue_notification(notification)
            logger.info(f"Sent payment notification for booking {booking_id}: {success}")
            
        except Exception as e:
            logger.error(f"Error sending payment notification {booking_id}: {str(e)}")
    
    # System Notifications
    def send_system_alert(self, title: str, message: str, priority: str = "normal", 
                         target_users: List[int] = None, target_rooms: List[str] = None):
        """Send system-wide alert"""
        try:
            notification = NotificationMessage(
                id=f"system_alert_{int(time.time())}",
                type=NotificationType.SYSTEM_ALERT,
                title=title,
                message=message,
                data={'alert_type': 'system'},
                timestamp=datetime.utcnow(),
                priority=priority,
                target_users=target_users,
                target_rooms=target_rooms or ["system_alerts"]
            )
            
            self.queue_notification(notification)
            logger.info(f"Sent system alert: {title}")
            
        except Exception as e:
            logger.error(f"Error sending system alert: {str(e)}")
    
    def send_seat_availability_update(self, event_id: int, available_seats: int):
        """Send seat availability update"""
        try:
            event = Event.query.get(event_id)
            if not event:
                return
            
            notification = NotificationMessage(
                id=f"seat_availability_{event_id}_{int(time.time())}",
                type=NotificationType.SEAT_AVAILABILITY,
                title="Seat Availability Update",
                message=f"{available_seats} seats available for {event.event_name}",
                data={
                    'event_id': event_id,
                    'available_seats': available_seats,
                    'event_name': event.event_name
                },
                timestamp=datetime.utcnow(),
                priority="low",
                target_rooms=[f"event_{event_id}", "seat_updates"]
            )
            
            self.queue_notification(notification)
            
        except Exception as e:
            logger.error(f"Error sending seat availability update {event_id}: {str(e)}")
    
    # Subscription Management
    def subscribe_user_to_match(self, user_id: int, match_id: int):
        """Subscribe user to match updates"""
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = set()
        
        self.user_subscriptions[user_id].add(f"match_{match_id}")
        logger.info(f"User {user_id} subscribed to match {match_id}")
    
    def unsubscribe_user_from_match(self, user_id: int, match_id: int):
        """Unsubscribe user from match updates"""
        if user_id in self.user_subscriptions:
            self.user_subscriptions[user_id].discard(f"match_{match_id}")
            logger.info(f"User {user_id} unsubscribed from match {match_id}")
    
    def subscribe_to_room(self, room_name: str):
        """Subscribe to a notification room"""
        if room_name not in self.room_subscriptions:
            self.room_subscriptions[room_name] = set()
        
        join_room(room_name)
        logger.info(f"Joined room: {room_name}")
    
    # Notification Processing
    def queue_notification(self, notification: NotificationMessage):
        """Queue a notification for processing"""
        self.notification_queue.append(notification)
    
    def _notification_processor_loop(self):
        """Process queued notifications"""
        while self._running:
            try:
                if self.notification_queue:
                    notification = self.notification_queue.pop(0)
                    self._process_notification(notification)
                else:
                    time.sleep(0.1)  # Short sleep when no notifications
                    
            except Exception as e:
                logger.error(f"Error in notification processor: {str(e)}")
                time.sleep(1)
    
    def _process_notification(self, notification: NotificationMessage):
        """Process a single notification"""
        try:
            notification_data = {
                'id': notification.id,
                'type': notification.type.value,
                'title': notification.title,
                'message': notification.message,
                'data': notification.data,
                'timestamp': notification.timestamp.isoformat(),
                'priority': notification.priority
            }
            
            # Send to specific users
            if notification.target_users:
                for user_id in notification.target_users:
                    socketio.emit('notification', notification_data, room=f"user_{user_id}")
            
            # Send to specific rooms
            if notification.target_rooms:
                for room in notification.target_rooms:
                    socketio.emit('notification', notification_data, room=room)
            
            # If no specific targets, broadcast to all
            if not notification.target_users and not notification.target_rooms:
                socketio.emit('notification', notification_data, broadcast=True)
            
            logger.debug(f"Processed notification: {notification.id}")
            
        except Exception as e:
            logger.error(f"Error processing notification {notification.id}: {str(e)}")
    
    def _broadcast_live_score(self, live_update: LiveScoreUpdate):
        """Broadcast live score update"""
        try:
            score_data = asdict(live_update)
            score_data['timestamp'] = live_update.timestamp.isoformat()
            
            # Broadcast to match-specific room
            socketio.emit('live_score_update', score_data, room=f"match_{live_update.match_id}")
            
            # Broadcast to general live matches room
            socketio.emit('live_score_update', score_data, room="live_matches")
            
            logger.debug(f"Broadcasted live score for match {live_update.match_id}")
            
        except Exception as e:
            logger.error(f"Error broadcasting live score: {str(e)}")
    
    def _score_updater_loop(self):
        """Simulate live score updates (for demo purposes)"""
        while self._running:
            try:
                # In a real implementation, this would fetch data from a cricket API
                # For now, we'll simulate updates for active matches
                for match_id, match_data in self.active_matches.items():
                    if match_data['status'] == 'live':
                        # Simulate random score updates
                        import random
                        if random.random() < 0.1:  # 10% chance of update every cycle
                            score_update = {
                                'team1_score': match_data['team1_score'] + random.randint(0, 6),
                                'last_ball': f"{random.randint(0, 6)} runs",
                                'commentary': f"Great shot! {random.randint(0, 6)} runs scored."
                            }
                            self.update_live_score(match_id, score_update)
                
                time.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in score updater loop: {str(e)}")
                time.sleep(5)
    
    # Utility Methods
    def get_active_matches(self) -> Dict[int, Dict]:
        """Get all active matches"""
        return self.active_matches.copy()
    
    def get_match_status(self, match_id: int) -> Optional[Dict]:
        """Get status of a specific match"""
        return self.active_matches.get(match_id)
    
    def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification service statistics"""
        return {
            'active_matches': len(self.active_matches),
            'queued_notifications': len(self.notification_queue),
            'user_subscriptions': len(self.user_subscriptions),
            'room_subscriptions': len(self.room_subscriptions),
            'service_running': self._running,
            'uptime': datetime.utcnow().isoformat()
        }

# Global service instance
realtime_notification_service = RealtimeNotificationService()

# SocketIO Event Handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected")
    emit('connection_status', {'status': 'connected', 'timestamp': datetime.utcnow().isoformat()})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected")

@socketio.on('subscribe_to_match')
def handle_subscribe_to_match(data):
    """Handle match subscription"""
    try:
        match_id = data.get('match_id')
        user_id = data.get('user_id')
        
        if match_id and user_id:
            realtime_notification_service.subscribe_user_to_match(user_id, match_id)
            join_room(f"match_{match_id}")
            emit('subscription_status', {
                'status': 'subscribed',
                'match_id': match_id,
                'message': f'Subscribed to match {match_id} updates'
            })
        
    except Exception as e:
        logger.error(f"Error handling match subscription: {str(e)}")
        emit('error', {'message': 'Failed to subscribe to match'})

@socketio.on('unsubscribe_from_match')
def handle_unsubscribe_from_match(data):
    """Handle match unsubscription"""
    try:
        match_id = data.get('match_id')
        user_id = data.get('user_id')
        
        if match_id and user_id:
            realtime_notification_service.unsubscribe_user_from_match(user_id, match_id)
            leave_room(f"match_{match_id}")
            emit('subscription_status', {
                'status': 'unsubscribed',
                'match_id': match_id,
                'message': f'Unsubscribed from match {match_id} updates'
            })
        
    except Exception as e:
        logger.error(f"Error handling match unsubscription: {str(e)}")
        emit('error', {'message': 'Failed to unsubscribe from match'})

@socketio.on('join_user_room')
def handle_join_user_room(data):
    """Handle user joining their personal notification room"""
    try:
        user_id = data.get('user_id')
        if user_id:
            join_room(f"user_{user_id}")
            emit('room_status', {
                'status': 'joined',
                'room': f"user_{user_id}",
                'message': 'Joined personal notification room'
            })
        
    except Exception as e:
        logger.error(f"Error joining user room: {str(e)}")
        emit('error', {'message': 'Failed to join user room'})

@socketio.on('get_live_matches')
def handle_get_live_matches():
    """Handle request for live matches"""
    try:
        active_matches = realtime_notification_service.get_active_matches()
        emit('live_matches', {'matches': active_matches})
        
    except Exception as e:
        logger.error(f"Error getting live matches: {str(e)}")
        emit('error', {'message': 'Failed to get live matches'})

@socketio.on('get_match_status')
def handle_get_match_status(data):
    """Handle request for specific match status"""
    try:
        match_id = data.get('match_id')
        if match_id:
            match_status = realtime_notification_service.get_match_status(match_id)
            emit('match_status', {
                'match_id': match_id,
                'status': match_status
            })
        
    except Exception as e:
        logger.error(f"Error getting match status: {str(e)}")
        emit('error', {'message': 'Failed to get match status'})
