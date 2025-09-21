"""
Simple Chatbot Service for CricVerse
Lightweight version for testing and fallback scenarios
"""

import os
import logging
from typing import Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

def ask_gemini(message: str, customer_id: int = None) -> str:
    """
    Simple chatbot function that provides fallback responses.
    This is used when the full Gemini AI service is not available.
    
    Args:
        message (str): User's message
        customer_id (int, optional): Customer ID for personalization
    
    Returns:
        str: Response message
    """
    if not message:
        return "Hello! How can I help you with your cricket experience today?"
    
    message_lower = message.lower()
    
    # Greeting responses
    if any(word in message_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']):
        return "Hello! Welcome to CricVerse! I'm here to help you with cricket match bookings, stadium information, and everything BBL. How can I assist you today?"
    
    # Booking related queries
    if any(word in message_lower for word in ['book', 'ticket', 'buy', 'purchase', 'reserve']):
        return "I can help you book tickets for upcoming BBL matches! We have various seating options available including General Admission, Premium, and VIP experiences. Would you like to see available matches or learn about our pricing options?"
    
    # Stadium/venue queries
    if any(word in message_lower for word in ['stadium', 'venue', 'ground', 'location', 'where']):
        return "We have matches at premier cricket venues across Australia including the MCG, SCG, Adelaide Oval, Gabba, Perth Stadium, and Marvel Stadium. Each venue offers unique facilities, food options, and experiences. Which stadium would you like to know more about?"
    
    # Team related queries
    if any(word in message_lower for word in ['team', 'teams', 'player', 'squad']):
        return "The BBL features 8 exciting teams: Melbourne Stars, Melbourne Renegades, Sydney Sixers, Sydney Thunder, Brisbane Heat, Perth Scorchers, Adelaide Strikers, and Hobart Hurricanes. Each team has amazing players and passionate fan bases. Which team interests you?"
    
    # Food and dining queries
    if any(word in message_lower for word in ['food', 'eat', 'drink', 'menu', 'hungry', 'thirsty']):
        return "Our stadiums offer fantastic food options! From classic cricket snacks like meat pies and hot dogs to gourmet dining experiences, craft beers, and healthy options. Many venues also cater to dietary requirements including vegetarian, vegan, and gluten-free options."
    
    # Parking and transport
    if any(word in message_lower for word in ['park', 'parking', 'transport', 'car', 'train', 'bus']):
        return "All our venues offer convenient parking options and excellent public transport connections. Most stadiums have on-site parking (booking recommended), and are well-connected by train, bus, and tram services. I can provide specific transport details for any venue."
    
    # Pricing queries
    if any(word in message_lower for word in ['price', 'cost', 'cheap', 'expensive', 'discount', 'offer']):
        return "We offer great value tickets starting from around $25 for General Admission, with Premium seating from $45 and VIP experiences from $85. We also have family packages, group discounts, and special offers for students and seniors. Early bird bookings save up to 20%!"
    
    # Match/fixture queries
    if any(word in message_lower for word in ['match', 'game', 'fixture', 'when', 'schedule']):
        return "The BBL season runs from December to February with matches almost every day! Each team plays 14 regular season games followed by finals. Matches are typically in the evening (7:15pm start) with some afternoon games on weekends. Would you like to see upcoming fixtures?"
    
    # Weather queries
    if any(word in message_lower for word in ['weather', 'rain', 'hot', 'cold', 'temperature']):
        return "Australian summer cricket weather is generally fantastic! Most matches are played in warm, pleasant conditions. All our major venues have covered seating areas and weather protection. We monitor weather conditions and will notify you of any match delays or changes."
    
    # Accessibility queries
    if any(word in message_lower for word in ['accessibility', 'wheelchair', 'disabled', 'special needs']):
        return "All our venues are fully accessible with wheelchair seating, accessible toilets, lifts, and assistance services. We offer companion card recognition and can arrange special assistance. Please let us know your requirements when booking so we can ensure the best experience."
    
    # General help
    if any(word in message_lower for word in ['help', 'support', 'assistance', 'problem']):
        return "I'm here to help with all your cricket needs! I can assist with ticket bookings, venue information, match schedules, food options, parking, team details, and much more. What specific information would you like?"
    
    # Thank you responses
    if any(word in message_lower for word in ['thank', 'thanks', 'cheers']):
        return "You're very welcome! Enjoy the cricket and have an amazing time at the match! Feel free to ask if you need any more help. Go cricket! 🏏"
    
    # Default response
    return "That's a great question! I can help you with cricket match bookings, stadium information, team details, food options, parking, and much more about the BBL experience. Could you tell me more specifically what you'd like to know?"

def get_chatbot_response(message: str, customer_id: int = None) -> Dict[str, Any]:
    """
    Get chatbot response in structured format.
    
    Args:
        message (str): User's message
        customer_id (int, optional): Customer ID for personalization
    
    Returns:
        Dict[str, Any]: Structured response with message and metadata
    """
    try:
        response_text = ask_gemini(message, customer_id)
        
        return {
            'success': True,
            'message': response_text,
            'timestamp': '2024-01-01T00:00:00Z',  # Placeholder timestamp
            'source': 'simple_chatbot',
            'customer_id': customer_id
        }
    except Exception as e:
        logger.error(f"Error in chatbot response: {e}")
        return {
            'success': False,
            'message': "I'm sorry, I'm having trouble right now. Please try again or contact our support team for assistance.",
            'error': str(e),
            'source': 'simple_chatbot',
            'customer_id': customer_id
        }

# Backward compatibility aliases
def simple_chatbot_response(message: str) -> str:
    """Simple alias for ask_gemini function."""
    return ask_gemini(message)

def process_message(message: str, user_id: int = None) -> str:
    """Process message alias for compatibility."""
    return ask_gemini(message, user_id)
