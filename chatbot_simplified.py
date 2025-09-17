"""
Simplified Google Gemini AI Chatbot for CricVerse
Focused on reliability and error handling
"""

import os
import logging
import uuid
from datetime import datetime
from dotenv import load_dotenv
import json

# Load environment variables
if os.path.exists('cricverse.env'):
    load_dotenv('cricverse.env')
else:
    load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import Gemini
try:
    import google.generativeai as genai
    gemini_available = True
    logger.info("✅ Google Generative AI imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Google Generative AI not available: {e}")
    gemini_available = False

# Initialize Gemini client
client = None
if gemini_available:
    try:
        api_key = os.getenv('GEMINI_API_KEY')
        model_name = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
        
        if api_key and api_key.startswith('AIza'):
            genai.configure(api_key=api_key)
            client = genai.GenerativeModel(model_name)
            logger.info(f"✅ Gemini client initialized with model: {model_name}")
        else:
            logger.warning("⚠️ Invalid or missing Gemini API key")
            gemini_available = False
    except Exception as e:
        logger.error(f"❌ Error initializing Gemini: {e}")
        gemini_available = False

class SimpleCricVerseChatbot:
    """Simplified chatbot with robust fallback system"""
    
    def __init__(self):
        self.system_prompt = """You are CricVerse Assistant, an AI specialized in Big Bash League (BBL) cricket.

Help users with:
- Stadium information and locations
- Match schedules and ticket booking
- Food and concessions
- Parking information
- Team and player details

Always be friendly, enthusiastic about cricket, and provide specific, helpful information.
If you don't have specific information, provide general guidance and suggest contacting support.
"""

    def get_simple_database_context(self, user_message):
        """Get basic database context without complex imports"""
        try:
            # Import Flask components carefully
            from flask import current_app
            if current_app:
                with current_app.app_context():
                    from app import Stadium, Event, Match
                    
                    context = {}
                    message_lower = user_message.lower()
                    
                    # Get stadium info for venue queries
                    if any(word in message_lower for word in ['stadium', 'venue', 'location']):
                        stadiums = Stadium.query.limit(5).all()
                        context['stadiums'] = []
                        for stadium in stadiums:
                            context['stadiums'].append({
                                'name': stadium.name,
                                'location': stadium.location,
                                'capacity': stadium.capacity,
                                'facilities': getattr(stadium, 'facilities', 'Modern facilities available')
                            })
                    
                    # Get match info for booking queries
                    if any(word in message_lower for word in ['match', 'ticket', 'book']):
                        matches = Match.query.filter(Match.match_date >= datetime.now()).limit(3).all()
                        context['matches'] = []
                        for match in matches:
                            context['matches'].append({
                                'home_team': match.home_team,
                                'away_team': match.away_team,
                                'match_date': match.match_date.strftime('%Y-%m-%d') if match.match_date else 'TBD',
                                'venue': match.venue,
                                'ticket_price': float(match.ticket_price) if match.ticket_price else None
                            })
                    
                    return context
        except Exception as e:
            logger.warning(f"Could not get database context: {e}")
            return {}

    def get_fallback_response(self, user_message):
        """Comprehensive fallback responses"""
        message_lower = user_message.lower()
        
        # Stadium information
        if any(word in message_lower for word in ['stadium', 'venue', 'location', 'where']):
            return {
                'response': """🏟️ **BBL Stadiums Information**

**Major BBL Venues:**
• **Melbourne Cricket Ground (MCG)** - Melbourne Stars
• **Marvel Stadium** - Melbourne Renegades
• **Sydney Cricket Ground (SCG)** - Sydney Sixers
• **Adelaide Oval** - Adelaide Strikers
• **The Gabba** - Brisbane Heat
• **Perth Stadium** - Perth Scorchers

**Features:**
✅ Modern facilities and amenities
✅ Food courts and premium dining
✅ Accessible seating and parking
✅ Public transport connections

Need specific information about a stadium? Ask me about any venue!""",
                'confidence': 0.9,
                'tokens_used': 0,
                'model': 'fallback'
            }
        
        # Ticket booking
        elif any(word in message_lower for word in ['ticket', 'book', 'buy', 'match', 'game']):
            return {
                'response': """🎫 **BBL Ticket Booking**

**Ticket Categories:**
• **General Admission** - ₹2,000-2,800
• **Premium Seating** - ₹3,600-5,200
• **VIP Experience** - ₹6,800-9,600
• **Family Packages** - ₹6,400-8,000

**How to Book:**
1. Choose your match from upcoming fixtures
2. Select your preferred seating category
3. Add extras like parking and food
4. Complete secure payment

**Special Offers:**
🎉 Early Bird - 20% off (2+ weeks ahead)
👥 Group Discounts - 15% off (10+ people)
🎂 Birthday Special - Free cake!

Ready to book? Tell me your preferred team or date!""",
                'confidence': 0.9,
                'tokens_used': 0,
                'model': 'fallback'
            }
        
        # Food and concessions
        elif any(word in message_lower for word in ['food', 'eat', 'drink', 'menu', 'hungry']):
            return {
                'response': """🍔 **Stadium Food & Beverages**

**Popular Options:**
• **Gourmet Burgers** - ₹400-600
• **Wood-fired Pizza** - ₹500-800
• **Fish & Chips** - ₹450
• **Chicken Wings** - ₹450
• **Loaded Nachos** - ₹400

**Beverages:**
🍺 **Beer** - ₹250-400
🥤 **Soft Drinks** - ₹150-250
☕ **Coffee** - ₹150-250

**Dietary Options:**
🌱 Vegetarian/Vegan available
🚫 Gluten-free options marked
🥗 Healthy choices available

**Ordering:**
📱 Mobile app for skip-the-queue ordering
🏪 Traditional concession stands
🎫 In-seat service for premium tickets

What type of food are you craving?""",
                'confidence': 0.9,
                'tokens_used': 0,
                'model': 'fallback'
            }
        
        # Parking
        elif any(word in message_lower for word in ['park', 'parking', 'car']):
            return {
                'response': """🚗 **Stadium Parking**

**Parking Options:**
• **Premium Parking** - ₹500 (closest to entrance)
• **General Parking** - ₹300 (short walk)
• **Economy Parking** - ₹200 (shuttle service)
• **VIP Parking** - ₹800 (valet service)

**Tips:**
🎯 Pre-book online and save 30%
🕐 Arrive early - lots fill quickly
♿ Accessible parking available

**Alternatives:**
🚊 Public transport recommended
🚕 Ride-share drop-off zones
🚲 Bike parking facilities

Book parking: cricverse.com/parking
Phone: 1800-CRICKET""",
                'confidence': 0.9,
                'tokens_used': 0,
                'model': 'fallback'
            }
        
        # Help and support
        elif any(word in message_lower for word in ['help', 'support', 'problem']):
            return {
                'response': """🎧 **CricVerse Support**

**I can help you with:**
✅ Booking BBL match tickets
✅ Stadium information and directions
✅ Parking reservations
✅ Food options and pre-ordering
✅ Match schedules and teams
✅ Group bookings

**Need more help?**
📞 Phone: 1800-CRICKET (24/7)
💬 Live Chat: Available here!
📧 Email: support@cricverse.com

**Quick Actions:**
• "Book tickets for Melbourne Stars"
• "Show me stadium parking options"
• "What food is available at MCG?"

How can I assist you today?""",
                'confidence': 0.8,
                'tokens_used': 0,
                'model': 'fallback'
            }
        
        # Default response
        else:
            return {
                'response': f"""👋 **Hello! I'm your CricVerse Assistant**

I noticed you asked about "{user_message[:50]}..." 

**I can help you with:**
🎫 **Ticket Booking** - Find and book BBL match tickets
🏟️ **Stadium Info** - Locations, facilities, directions
🚗 **Parking** - Reserve parking spots
🍔 **Food & Drinks** - Stadium dining options
📞 **Support** - Customer service and help

**Try asking:**
• "Book tickets for the next Melbourne match"
• "Where is Adelaide Oval located?"
• "What food is available at the stadium?"
• "How do I reserve parking?"

What would you like to know about BBL cricket?""",
                'confidence': 0.7,
                'tokens_used': 0,
                'model': 'fallback'
            }

    def generate_response(self, user_message, customer_id=None, session_id=None):
        """Generate AI response with proper error handling"""
        try:
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # Get database context if available
            db_context = self.get_simple_database_context(user_message)
            
            # Try Gemini first if available
            if gemini_available and client:
                try:
                    # Build prompt
                    prompt_parts = [self.system_prompt]
                    
                    if db_context:
                        prompt_parts.append(f"Database context: {json.dumps(db_context, indent=2)}")
                    
                    prompt_parts.append(f"User: {user_message}")
                    prompt_parts.append("Assistant:")
                    
                    prompt_text = "\n".join(prompt_parts)
                    
                    # Generate response with timeout
                    response = client.generate_content(prompt_text)
                    ai_response = response.text.strip()
                    
                    return {
                        'response': ai_response,
                        'confidence': 0.9,
                        'tokens_used': len(prompt_text.split()) + len(ai_response.split()),
                        'model': os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
                    }
                    
                except Exception as e:
                    logger.error(f"Gemini API error: {e}")
                    # Fall back to hardcoded responses
                    return self.get_fallback_response(user_message)
            else:
                # Use fallback responses
                return self.get_fallback_response(user_message)
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                'response': "I apologize, but I'm experiencing technical difficulties. Please try again or contact support at 1800-CRICKET.",
                'confidence': 0.5,
                'tokens_used': 0,
                'model': 'error-fallback'
            }

# Global instance
simplified_chatbot = SimpleCricVerseChatbot()

def get_chatbot_response(message, customer_id=None, session_id=None):
    """Main function for getting chatbot responses"""
    return simplified_chatbot.generate_response(message, customer_id, session_id)

def detect_user_intent(message):
    """Simple intent detection"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['book', 'buy', 'ticket', 'reserve']):
        return 'booking'
    elif any(word in message_lower for word in ['stadium', 'venue', 'location']):
        return 'venue_info'
    elif any(word in message_lower for word in ['food', 'eat', 'menu']):
        return 'food'
    elif any(word in message_lower for word in ['park', 'parking']):
        return 'parking'
    elif any(word in message_lower for word in ['help', 'support']):
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
    elif intent == 'venue_info':
        actions = [
            {"text": "Stadium Guide", "action": "stadium_guide"},
            {"text": "Directions", "action": "directions"}
        ]
    elif intent == 'parking':
        actions = [
            {"text": "Book Parking", "action": "book_parking"},
            {"text": "Parking Rates", "action": "parking_rates"}
        ]
    elif intent == 'food':
        actions = [
            {"text": "View Menu", "action": "view_menu"},
            {"text": "Pre-Order", "action": "pre_order"}
        ]
    
    return actions

def get_chat_suggestions(customer_id=None, query_type="general"):
    """Get chat suggestions"""
    suggestions = []
    
    if query_type == "booking":
        suggestions = [
            "Show me upcoming Melbourne matches",
            "Book premium tickets for the next game",
            "What's available for this weekend?"
        ]
    elif query_type == "venue":
        suggestions = [
            "Where is the MCG located?",
            "What facilities are at Adelaide Oval?",
            "How do I get to Perth Stadium?"
        ]
    else:
        suggestions = [
            "Help me book tickets",
            "Show stadium information",
            "What food options are available?",
            "How do I reserve parking?"
        ]
    
    return suggestions