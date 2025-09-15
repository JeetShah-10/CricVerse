"""
Google Gemini AI Chatbot Integration for CricVerse
Intelligent booking assistant and customer support
"""

import os
import logging
import uuid
from datetime import datetime, date
import google.generativeai as genai
import json
from flask import request
from dotenv import load_dotenv

# Load environment variables first
if os.path.exists('cricverse.env'):
    load_dotenv('cricverse.env')
else:
    load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Gemini client with proper error handling
client = None
gemini_available = False

try:
    api_key = os.getenv('GEMINI_API_KEY')
    model_name = os.getenv('GEMINI_MODEL', 'gemini-pro')
    
    logger.info(f"🔧 Loading Gemini configuration: Model={model_name}")
    
    if api_key and api_key != 'your-gemini-api-key-here':
        genai.configure(api_key=api_key)
        client = genai.GenerativeModel(model_name)
        gemini_available = True
        logger.info(f"✅ Gemini client initialized successfully with model: {model_name}")
    else:
        logger.warning("⚠️ Gemini API key not configured. Chatbot will use fallback responses.")
        logger.warning("   Please set GEMINI_API_KEY in cricverse.env file")
        gemini_available = False
        
except ImportError:
    logger.warning("⚠️ Google Generative AI package not installed. Install with: pip install google-generativeai")
    gemini_available = False
except Exception as e:
    logger.error(f"❌ Error initializing Gemini client: {e}")
    gemini_available = False


class CricVerseChatbot:
    """AI-powered chatbot for CricVerse"""
    
    def __init__(self):
        self.model = os.getenv('GEMINI_MODEL', 'gemini-pro')
        self.max_tokens = 1000  # Increased for better responses
        self.temperature = 0.7
        self.api_key = os.getenv('GEMINI_API_KEY')
        
        # Conversation context tracking
        self.conversation_context = {}
        self.user_preferences = {}
        
    def get_database_context(self, user_message):
        """Get relevant database information for the user's query"""
        try:
            from app import app, db, Stadium, Concession, MenuItem, Event, Match, Team
            
            with app.app_context():
                context_data = {}
                message_lower = user_message.lower()
                
                # Get stadium information if location mentioned
                cities = ['melbourne', 'sydney', 'adelaide', 'brisbane', 'perth', 'hobart']
                venues = ['marvel', 'mcg', 'adelaide oval', 'scg', 'gabba']
                
                for city in cities:
                    if city in message_lower:
                        stadiums = Stadium.query.filter(Stadium.city.ilike(f'%{city}%')).all()
                        context_data['stadiums'] = [{'name': s.name, 'city': s.city, 'capacity': s.capacity} for s in stadiums]
                        break
                
                for venue in venues:
                    if venue in message_lower:
                        stadium = Stadium.query.filter(Stadium.name.ilike(f'%{venue}%')).first()
                        if stadium:
                            context_data['specific_stadium'] = {
                                'name': stadium.name,
                                'city': stadium.city,
                                'capacity': stadium.capacity
                            }
                        break
                
                # Get food information if food-related query
                if any(word in message_lower for word in ['food', 'eat', 'menu', 'dining', 'restaurant']):
                    if context_data.get('specific_stadium'):
                        stadium_id = Stadium.query.filter(Stadium.name.ilike(f'%{venue}%')).first().id
                        concessions = db.session.query(Concession, MenuItem).join(
                            MenuItem, Concession.id == MenuItem.concession_id
                        ).filter(
                            Concession.stadium_id == stadium_id,
                            MenuItem.is_available == True
                        ).limit(20).all()
                        
                        context_data['food_options'] = []
                        for concession, item in concessions:
                            context_data['food_options'].append({
                                'concession': concession.name,
                                'location': concession.location_zone,
                                'item': item.name,
                                'price': item.price,
                                'vegetarian': item.is_vegetarian
                            })
                
                # Get match information if matches mentioned
                if any(word in message_lower for word in ['match', 'game', 'fixture', 'ticket']):
                    upcoming_matches = self.get_upcoming_matches(5)
                    context_data['upcoming_matches'] = upcoming_matches
                
                return context_data
                
        except Exception as e:
            logger.error(f"Error getting database context: {e}")
            return {}

    def generate_response(self, user_message, customer_id=None, session_id=None):
        """Generate AI response using Google Gemini API with optimized prompting"""
        try:
            # Get conversation context (limit to last 3 exchanges to save tokens)
            conversation_context = self.get_conversation_context(customer_id, session_id)
            recent_context = conversation_context[-6:] if len(conversation_context) > 6 else conversation_context
            
            # Get relevant database context
            db_context = self.get_database_context(user_message)
            
            # Build optimized system prompt
            system_prompt = """You are CricVerse Assistant, a helpful AI for Big Bash League cricket fans. 

Key Guidelines:
- Be conversational and natural, like a knowledgeable cricket fan
- Use the provided database information to give specific, accurate answers
- Keep responses concise but informative (2-3 sentences max unless complex query)
- Reference specific stadiums, matches, prices when available
- If no relevant data is found, politely say so and offer general help

Available Information:"""
            
            if db_context:
                system_prompt += f"\n{json.dumps(db_context, indent=2)}"
            else:
                system_prompt += "\nNo specific database information available for this query."
            
            # Build conversation history (simplified format)
            messages = []
            if recent_context:
                for msg in recent_context:
                    role = "user" if msg["role"] == "user" else "model"
                    messages.append({"role": role, "parts": [msg["content"]]})
            
            # Add current user message
            messages.append({"role": "user", "parts": [user_message]})
            
            # Configure Gemini with optimized settings
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 200,  # Keep responses concise
            }
            
            # Initialize Gemini client
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(
                model_name=self.model,
                generation_config=generation_config
            )
            
            # Add system instruction as first message in history
            system_message = {"role": "user", "parts": [system_prompt]}
            system_response = {"role": "model", "parts": ["I understand. I'm CricVerse Assistant, ready to help with Big Bash League cricket information."]}
            
            # Build complete message history with system context
            full_history = [system_message, system_response]
            if recent_context:
                for msg in recent_context:
                    role = "user" if msg["role"] == "user" else "model"
                    full_history.append({"role": role, "parts": [msg["content"]]})
            
            # Generate response
            chat = model.start_chat(history=full_history)
            response = chat.send_message(user_message)
            ai_response = response.text.strip()
            
            # Calculate token usage estimate
            tokens_used = len(system_prompt.split()) + sum(len(msg["parts"][0].split()) for msg in messages) + len(ai_response.split())
            
            # Log interaction
            self.log_interaction(user_message, ai_response, customer_id, session_id, tokens_used)
            
            return {
                'response': ai_response,
                'confidence': 0.95,
                'tokens_used': tokens_used,
                'model': self.model
            }
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            # Simple fallback without complex logic
            return {
                'response': "I'm having trouble right now. Could you please rephrase your question or try again in a moment?",
                'confidence': 0.1,
                'tokens_used': 0,
                'model': 'fallback'
            }

    def get_conversation_context(self, customer_id, session_id):
        """Get conversation history for context"""
        try:
            from app import app, db
            
            # Use app context to fix SQLAlchemy instance error
            with app.app_context():
                # Get recent conversation
                from enhanced_models import ChatConversation
                conversation = ChatConversation.query.filter_by(
                    session_id=session_id
                ).first()
                
                if not conversation:
                    return []
                
                # Get recent messages (last 10)
                from enhanced_models import ChatMessage
                messages = ChatMessage.query.filter_by(
                    conversation_id=conversation.id
                ).order_by(ChatMessage.created_at.desc()).limit(10).all()
                
                # Format for Gemini
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

    def log_interaction(self, user_message, ai_response, customer_id, session_id, tokens_used):
        """Log the chat interaction to database"""
        try:
            from app import app, db
            
            # Use app context to fix SQLAlchemy instance error
            with app.app_context():
                # Try to import enhanced models, fallback to creating simple log
                try:
                    from enhanced_models import ChatConversation, ChatMessage
                    enhanced_models_available = True
                except ImportError:
                    logger.warning("Enhanced models not available, using simple logging")
                    enhanced_models_available = False
                
                if enhanced_models_available:
                    # Get or create conversation
                    conversation = ChatConversation.query.filter_by(
                        customer_id=customer_id,
                        session_id=session_id
                    ).first()
                    
                    if not conversation:
                        conversation = ChatConversation(
                            customer_id=customer_id,
                            session_id=session_id,
                            ip_address=request.environ.get('REMOTE_ADDR', 'unknown'),
                            user_agent=request.environ.get('HTTP_USER_AGENT', 'unknown')
                        )
                        db.session.add(conversation)
                        db.session.flush()  # Get the ID
                    
                    # Log user message
                    user_msg = ChatMessage(
                        conversation_id=conversation.id,
                        sender_type='user',
                        message=user_message
                    )
                    db.session.add(user_msg)
                    
                    # Log AI response
                    ai_msg = ChatMessage(
                        conversation_id=conversation.id,
                        sender_type='bot',
                        message=ai_response,
                        intent=None,
                        confidence_score=0.95,
                        tokens_used=tokens_used
                    )
                    db.session.add(ai_msg)
                    
                    # Update conversation message count
                    conversation.message_count = conversation.message_count + 2 if conversation.message_count else 2
                    
                    db.session.commit()
                else:
                    # Simple logging without enhanced models
                    logger.info(f"Chat interaction - User: {user_message[:100]}... | AI: {ai_response[:100]}...")
            
        except Exception as e:
            logger.warning(f"Could not log interaction (database tables may not exist): {e}")
            # Don't let logging errors break the chat functionality

    def get_upcoming_matches(self, limit=5):
        """Get upcoming matches from database"""
        try:
            from app import app, db, Event, Team, Stadium
            
            with app.app_context():
                # Query for upcoming events
                upcoming_events = Event.query.filter(
                    Event.event_date >= date.today()
                ).order_by(Event.event_date, Event.start_time).limit(limit).all()
                
                matches = []
                for event in upcoming_events:
                    home_team = Team.query.get(event.home_team_id)
                    away_team = Team.query.get(event.away_team_id)
                    stadium = Stadium.query.get(event.stadium_id)
                    
                    # Get minimum ticket price for this event
                    min_price = self.get_min_ticket_price(event.id)
                    
                    matches.append({
                        'event': event,
                        'home_team': home_team.team_name if home_team else 'TBD',
                        'away_team': away_team.team_name if away_team else 'TBD',
                        'stadium': stadium.stadium_name if stadium else 'TBD',
                        'min_price': min_price
                    })
                
                return matches
                
        except Exception as e:
            logger.error(f"Error getting upcoming matches: {e}")
            return []
    
    def get_min_ticket_price(self, event_id):
        """Get minimum ticket price for an event"""
        try:
            from app import app, db, Event, Seat
            
            with app.app_context():
                event = Event.query.get(event_id)
                if not event:
                    return 25  # Default price
                
                min_price = Seat.query.filter_by(
                    stadium_id=event.stadium_id
                ).with_entities(db.func.min(Seat.price)).scalar()
                
                return int(min_price) if min_price else 25
                
        except Exception as e:
            logger.error(f"Error getting min ticket price: {e}")
            return 25


# Initialize global chatbot instance
cricverse_chatbot = CricVerseChatbot()


def get_chatbot_response(message, customer_id=None, session_id=None):
    """Main function to get chatbot response"""
    if not session_id:
        session_id = str(uuid.uuid4())
    
    return cricverse_chatbot.generate_response(message, customer_id, session_id)


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
        
        # Get AI response
        response_data = get_chatbot_response(message, customer_id, session_id)
        
        return jsonify({
            'response': response_data['response'],
            'confidence': response_data.get('confidence', 0.8),
            'session_id': session_id,
            'tokens_used': response_data.get('tokens_used', 0)
        })
        
    except Exception as e:
        logger.error(f"Error handling chat message: {e}")
        return jsonify({
            'error': 'Failed to process message',
            'response': "I'm sorry, I'm having trouble right now. Please try again or contact support."
        }), 500


def get_chat_suggestions(customer_id=None, query_type="general"):
    """Get smart suggestions for chat"""
    suggestions = []
    
    if query_type == "booking":
        suggestions = [
            "What matches are available this weekend?",
            "Show me tickets for my favorite team",
            "Find stadiums near me"
        ]
    elif query_type == "match":
        suggestions = [
            "What's the latest score?",
            "When is the next match?",
            "Which teams are playing today?"
        ]
    elif query_type == "support":
        suggestions = [
            "Cancel my booking",
            "Change my seat selection",
            "Get a refund"
        ]
    else:
        suggestions = [
            "Help me book tickets",
            "What matches are coming up?",
            "Find parking near the stadium"
        ]
    
    return suggestions


def detect_user_intent(message):
    """Detect user intent from message"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['book', 'buy', 'ticket', 'reserve']):
        return 'booking'
    elif any(word in message_lower for word in ['match', 'game', 'score']):
        return 'match_info'
    elif any(word in message_lower for word in ['park', 'parking']):
        return 'parking'
    elif any(word in message_lower for word in ['food', 'eat', 'menu']):
        return 'food'
    elif any(word in message_lower for word in ['help', 'support', 'problem']):
        return 'support'
    else:
        return 'general'


def get_intent_actions(intent):
    """Get quick actions for intent"""
    actions = []
    
    if intent == 'booking':
        actions = [
            {"text": "Browse Matches", "action": "browse_matches"},
            {"text": "Check Availability", "action": "check_availability"}
        ]
    elif intent == 'parking':
        actions = [
            {"text": "Book Parking", "action": "book_parking"},
            {"text": "Parking Info", "action": "parking_info"}
        ]
    elif intent == 'food':
        actions = [
            {"text": "View Menu", "action": "view_menu"},
            {"text": "Dietary Options", "action": "dietary_options"}
        ]
    
    return actions