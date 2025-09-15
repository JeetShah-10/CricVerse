
"""
OpenAI GPT-4 Chatbot Integration for CricVerse
Intelligent booking assistant and customer support
"""

import os
import json
import logging
import openai
from datetime import datetime, timedelta
from flask import request, session
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
from openai import OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

class CricVerseChatbot:
    """AI-powered chatbot for CricVerse"""
    
    def __init__(self):
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4-1106-preview')
        self.max_tokens = 500
        self.temperature = 0.7
        
        # System prompt for CricVerse context
        self.system_prompt = """
You are CricVerse Assistant, an AI helper for a cricket stadium management and booking platform. Your role is to:

1. Help customers book tickets for cricket matches
2. Provide information about stadiums, events, and teams  
3. Assist with parking reservations
4. Answer questions about concessions and facilities
5. Handle booking modifications and cancellations
6. Provide cricket match information and updates

Key Guidelines:
- Be friendly, professional, and cricket-enthusiastic
- Always prioritize accurate booking information
- Suggest relevant matches and stadiums based on customer preferences  
- Help with payment issues and booking problems
- Provide real-time match updates when available
- Use cricket terminology naturally
- Be concise but informative

Current Context: You're helping customers with the CricVerse platform for cricket stadium bookings and match information.
"""

    def get_conversation_context(self, customer_id, session_id):
        """Get conversation history for context"""
        try:
            from app import db
            
            # Get recent conversation
            conversation = ChatConversation.query.filter_by(
                session_id=session_id
            ).first()
            
            if not conversation:
                return []
            
            # Get recent messages (last 10)
            messages = ChatMessage.query.filter_by(
                conversation_id=conversation.id
            ).order_by(ChatMessage.created_at.desc()).limit(10).all()
            
            # Format for OpenAI
            context = []
            for msg in reversed(messages):  # Reverse to get chronological order
                role = "user" if msg.sender_type == "user" else "assistant"
                context.append({
                    "role": role,
                    "content": msg.message
                })
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting conversation context: {e}")
            return []

    def get_booking_context(self, customer_id):
        """Get customer's booking context for personalized responses"""
        try:
            from app import Customer, Booking, Event, Stadium
            
            customer = Customer.query.get(customer_id)
            if not customer:
                return {}
            
            # Get recent bookings
            recent_bookings = Booking.query.filter_by(
                customer_id=customer_id
            ).order_by(Booking.booking_date.desc()).limit(5).all()
            
            # Get upcoming events
            upcoming_events = Event.query.filter(
                Event.event_date >= datetime.utcnow().date()
            ).order_by(Event.event_date).limit(5).all()
            
            context = {
                "customer_name": customer.name,
                "membership_level": customer.membership_level,
                "recent_bookings": len(recent_bookings),
                "upcoming_events_count": len(upcoming_events)
            }
            
            # Add favorite team if available
            if customer.favorite_team_id:
                from app import Team
                favorite_team = Team.query.get(customer.favorite_team_id)
                if favorite_team:
                    context["favorite_team"] = favorite_team.team_name
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting booking context: {e}")
            return {}

    def generate_response(self, user_message, customer_id=None, session_id=None):
        """Generate AI response using OpenAI GPT-4"""
        try:
            # Get conversation context
            conversation_history = []
            if session_id:
                conversation_history = self.get_conversation_context(customer_id, session_id)
            
            # Get booking context for personalization
            booking_context = {}
            if customer_id:
                booking_context = self.get_booking_context(customer_id)
            
            # Build enhanced system prompt with context
            enhanced_prompt = self.system_prompt
            
            if booking_context:
                enhanced_prompt += f"\n\nCustomer Context:\n"
                if booking_context.get('customer_name'):
                    enhanced_prompt += f"- Customer Name: {booking_context['customer_name']}\n"
                if booking_context.get('membership_level'):
                    enhanced_prompt += f"- Membership: {booking_context['membership_level']}\n"
                if booking_context.get('favorite_team'):
                    enhanced_prompt += f"- Favorite Team: {booking_context['favorite_team']}\n"
                if booking_context.get('recent_bookings'):
                    enhanced_prompt += f"- Recent Bookings: {booking_context['recent_bookings']}\n"
            
            # Prepare messages
            messages = [{"role": "system", "content": enhanced_prompt}]
            
            # Add conversation history
            messages.extend(conversation_history)
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Generate response
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Log the interaction
            self.log_interaction(user_message, ai_response, customer_id, session_id, response)
            
            return {
                'response': ai_response,
                'confidence': self.calculate_confidence(response),
                'tokens_used': response.usage.total_tokens,
                'model': self.model
            }
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return {
                'response': "I'm having trouble connecting to my AI services right now. Please try again in a moment, or contact our support team for immediate assistance.",
                'error': str(e),
                'confidence': 0.0
            }
        except Exception as e:
            logger.error(f"Chatbot error: {e}")
            return {
                'response': "I apologize, but I'm experiencing some technical difficulties. Please contact our support team for assistance with your booking needs.",
                'error': str(e),
                'confidence': 0.0
            }

    def calculate_confidence(self, openai_response):
        """Calculate confidence score based on response quality"""
        try:
            # Simple confidence calculation based on response length and structure
            response_text = openai_response.choices[0].message.content
            
            # Base confidence
            confidence = 0.8
            
            # Adjust based on response length
            if len(response_text) < 50:
                confidence -= 0.2
            elif len(response_text) > 200:
                confidence += 0.1
            
            # Check for helpful keywords
            helpful_keywords = ['book', 'stadium', 'match', 'ticket', 'help', 'available', 'schedule']
            keyword_count = sum(1 for keyword in helpful_keywords if keyword.lower() in response_text.lower())
            
            if keyword_count > 2:
                confidence += 0.1
            
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.5

    def log_interaction(self, user_message, ai_response, customer_id, session_id, openai_response):
        """Log chatbot interaction to database"""
        try:
            from enhanced_models import ChatConversation, ChatMessage
            from app import db
            
            # Get or create conversation
            conversation = ChatConversation.query.filter_by(
                session_id=session_id
            ).first()
            
            if not conversation:
                conversation = ChatConversation(
                    customer_id=customer_id,
                    session_id=session_id,
                    ip_address=request.environ.get('REMOTE_ADDR', 'unknown'),
                    user_agent=request.environ.get('HTTP_USER_AGENT', 'unknown')[:500]
                )
                db.session.add(conversation)
                db.session.flush()
            
            # Log user message
            user_msg = ChatMessage(
                conversation_id=conversation.id,
                sender_type='user',
                message=user_message[:1000]  # Truncate if too long
            )
            db.session.add(user_msg)
            
            # Log AI response
            ai_msg = ChatMessage(
                conversation_id=conversation.id,
                sender_type='bot',
                message=ai_response[:1000],  # Truncate if too long
                openai_response_id=openai_response.id if hasattr(openai_response, 'id') else None,
                tokens_used=openai_response.usage.total_tokens if hasattr(openai_response, 'usage') else 0
            )
            db.session.add(ai_msg)
            
            # Update conversation stats
            conversation.message_count = (conversation.message_count or 0) + 2
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error logging interaction: {e}")
            # Don't fail the response if logging fails
            pass

    def get_smart_suggestions(self, customer_id, query_type="general"):
        """Get smart suggestions based on customer history and current context"""
        try:
            suggestions = []
            
            if query_type == "booking":
                suggestions = [
                    "What matches are available this weekend?",
                    "Show me tickets for [Your Favorite Team]",
                    "Find stadiums near me",
                    "What are the best seats available?",
                    "Check parking availability"
                ]
            elif query_type == "match":
                suggestions = [
                    "What's the latest score?",
                    "When is the next match?",
                    "Which teams are playing today?",
                    "Show me match highlights"
                ]
            elif query_type == "support":
                suggestions = [
                    "Cancel my booking",
                    "Change my seat selection",
                    "Get a refund",
                    "Contact support",
                    "Check booking status"
                ]
            else:
                suggestions = [
                    "Help me book tickets",
                    "What matches are coming up?",
                    "Find parking near the stadium",
                    "What food is available?",
                    "How do I cancel a booking?"
                ]
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting suggestions: {e}")
            return []

    def detect_intent(self, message):
        """Detect user intent from message"""
        message_lower = message.lower()
        
        # Booking intents
        if any(word in message_lower for word in ['book', 'buy', 'ticket', 'reserve']):
            return 'booking'
        
        # Match information intents
        if any(word in message_lower for word in ['score', 'match', 'game', 'live', 'result']):
            return 'match_info'
        
        # Support intents  
        if any(word in message_lower for word in ['cancel', 'refund', 'problem', 'help', 'support']):
            return 'support'
        
        # Parking intents
        if any(word in message_lower for word in ['park', 'parking', 'car']):
            return 'parking'
        
        # Stadium/venue intents
        if any(word in message_lower for word in ['stadium', 'venue', 'location', 'address']):
            return 'venue_info'
        
        return 'general'

    def get_quick_actions(self, intent):
        """Get quick action buttons based on detected intent"""
        actions = []
        
        if intent == 'booking':
            actions = [
                {"text": "Browse Matches", "action": "browse_matches"},
                {"text": "Check Availability", "action": "check_availability"},
                {"text": "My Bookings", "action": "my_bookings"}
            ]
        elif intent == 'match_info':
            actions = [
                {"text": "Live Scores", "action": "live_scores"},
                {"text": "Upcoming Matches", "action": "upcoming_matches"},
                {"text": "Match Schedule", "action": "match_schedule"}
            ]
        elif intent == 'support':
            actions = [
                {"text": "Contact Support", "action": "contact_support"},
                {"text": "FAQ", "action": "faq"},
                {"text": "Booking Help", "action": "booking_help"}
            ]
        elif intent == 'parking':
            actions = [
                {"text": "Book Parking", "action": "book_parking"},
                {"text": "Parking Info", "action": "parking_info"},
                {"text": "My Parking", "action": "my_parking"}
            ]
        
        return actions


# Initialize global chatbot instance
cricverse_chatbot = CricVerseChatbot()


def get_chatbot_response(message, customer_id=None, session_id=None):
    """Main function to get chatbot response"""
    if not session_id:
        session_id = str(uuid.uuid4())
    
    return cricverse_chatbot.generate_response(message, customer_id, session_id)


def get_chat_suggestions(customer_id=None, query_type="general"):
    """Get smart suggestions for chat"""
    return cricverse_chatbot.get_smart_suggestions(customer_id, query_type)


def detect_user_intent(message):
    """Detect user intent from message"""
    return cricverse_chatbot.detect_intent(message)


def get_intent_actions(intent):
    """Get quick actions for intent"""
    return cricverse_chatbot.get_quick_actions(intent)


# Flask route handlers
def handle_chat_message():
    """Handle incoming chat messages"""
    try:
        from flask import request, jsonify
        from flask_login import current_user
        
        data = request.get_json()
        message = data.get('message', '').strip()
        session_id = data.get('session_id') or str(uuid.uuid4())
        
        if not message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Get customer ID if authenticated
        customer_id = current_user.id if current_user.is_authenticated else None
        
        # Detect intent
        intent = detect_user_intent(message)
        
        # Get AI response
        response_data = get_chatbot_response(message, customer_id, session_id)
        
        # Get quick actions
        quick_actions = get_intent_actions(intent)
        
        # Get suggestions
        suggestions = get_chat_suggestions(customer_id, intent)
        
        return jsonify({
            'response': response_data['response'],
            'confidence': response_data.get('confidence', 0.8),
            'intent': intent,
            'quick_actions': quick_actions,
            'suggestions': suggestions[:3],  # Limit to 3 suggestions
            'session_id': session_id,
            'tokens_used': response_data.get('tokens_used', 0)
        })
        
    except Exception as e:
        logger.error(f"Error handling chat message: {e}")
        return jsonify({
            'error': 'Failed to process message',
            'response': "I'm sorry, I'm having trouble right now. Please try again or contact support."
        }), 500


def get_chat_history():
    """Get chat history for authenticated user"""
    try:
        from flask import request, jsonify
        from flask_login import current_user, login_required
        from enhanced_models import ChatConversation, ChatMessage
        
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        session_id = request.args.get('session_id')
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        # Get conversation
        conversation = ChatConversation.query.filter_by(
            customer_id=current_user.id,
            session_id=session_id
        ).first()
        
        if not conversation:
            return jsonify({'messages': []})
        
        # Get messages
        messages = ChatMessage.query.filter_by(
            conversation_id=conversation.id
        ).order_by(ChatMessage.created_at).all()
        
        # Format messages
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                'sender': msg.sender_type,
                'message': msg.message,
                'timestamp': msg.created_at.isoformat(),
                'confidence': msg.confidence_score
            })
        
        return jsonify({
            'messages': formatted_messages,
            'conversation_id': conversation.id,
            'message_count': len(formatted_messages)
        })
        
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        return jsonify({'error': 'Failed to get chat history'}), 500