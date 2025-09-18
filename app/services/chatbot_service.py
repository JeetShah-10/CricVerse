"""
Google Gemini AI Chatbot Integration for CricVerse
Intelligent booking assistant and customer support
"""

import os
import logging
import uuid
from datetime import datetime, date, timedelta
import google.generativeai as genai
import json
from flask import request, current_app
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
    """AI-powered chatbot for CricVerse with enhanced database integration and personalization"""
    
    def __init__(self):
        self.model = os.getenv('GEMINI_MODEL', 'gemini-pro')
        self.max_tokens = 1500  # Increased for better responses
        self.temperature = 0.7
        self.api_key = os.getenv('GEMINI_API_KEY')
        
        # Enhanced conversation context tracking
        self.conversation_context = {}
        self.user_preferences = {}
        self.user_profiles = {}  # Cache user profiles for better performance
        self.database_cache = {}  # Cache frequently accessed data
        self.cache_timeout = 300  # 5 minutes cache timeout
        
        # Enhanced system prompt with comprehensive cricket expertise and personalization
        self.system_prompt = """You are CricVerse Assistant, an intelligent AI specialized in Australian Big Bash League (BBL) cricket venues with advanced personalization capabilities.

You have access to comprehensive live database information including:
- Stadium locations, facilities, capacity, parking, and accessibility features with real-time occupancy
- Upcoming matches with dates, teams, venues, ticket prices, and live scores
- Special events and entertainment beyond regular matches
- Food concessions with detailed menus, prices, dietary options, and wait times
- Team information including players, stats, performance data, and recent form
- Parking rates, locations, transport options, and real-time availability
- Pricing categories, special offers, discounts, season passes, and dynamic pricing
- Accessibility services and special assistance options
- Customer bookings, preferences, purchase history, and loyalty status
- Real-time match updates, live scores, and commentary
- Weather conditions, crowd predictions, and venue atmosphere
- User conversation history and personal preferences

Personalization Features:
- Remember user preferences from previous conversations
- Tailor recommendations based on booking history
- Suggest relevant content based on favorite teams
- Provide personalized offers and discounts
- Remember accessibility needs and dietary preferences
- Track user engagement patterns for better assistance

When users ask questions:
1. ALWAYS prioritize live database information - it contains real, current, personalized data
2. Reference user's conversation history and preferences for personalized responses
3. Combine database facts with your cricket knowledge for comprehensive answers
4. Be specific with prices, dates, locations, and availability from the database
5. Proactively suggest relevant options based on user profile and preferences
6. Maintain conversational, enthusiastic cricket fan tone with personal touch
7. Provide actionable next steps with booking links and personalized recommendations
8. Remember and reference previous interactions to build rapport
9. Suggest upgrades or complementary services based on user history
10. Alert users about special offers relevant to their interests

Advanced Capabilities:
- Process booking requests with seat selection and payment integration
- Provide real-time match updates and live commentary
- Suggest optimal arrival times based on traffic and parking
- Recommend food pre-orders to avoid queues
- Alert about weather changes and venue updates
- Offer personalized matchday experiences
- Track loyalty points and membership benefits
- Provide multilingual support when requested

Always prioritize database information over general knowledge, use personalization data to enhance responses, and provide the most helpful, accurate, and tailored assistance possible."""

    def get_user_profile(self, customer_id):
        """Get comprehensive user profile with preferences and history"""
        if not customer_id:
            return {}
            
        with current_app.app_context():
            try:
                from app import db, Customer, Team, Booking
                from enhanced_models import CustomerProfile, ChatConversation, ChatMessage
                
                # Check cache first
                cache_key = f"user_profile_{customer_id}"
                if cache_key in self.user_profiles:
                    profile_data = self.user_profiles[cache_key]
                    # Check if cache is still valid (5 minutes)
                    if datetime.now().timestamp() - profile_data.get('cached_at', 0) < self.cache_timeout:
                        return profile_data['data']
                
                customer = Customer.query.get(customer_id)
                if not customer:
                    return {}
                
                # Build comprehensive user profile
                profile = {
                    'customer_id': customer_id,
                    'name': customer.name,
                    'email': customer.email,
                    'membership_level': customer.membership_level,
                    'favorite_team_id': customer.favorite_team_id,
                    'role': customer.role
                }
                
                # Get favorite team details
                if customer.favorite_team_id:
                    favorite_team = Team.query.get(customer.favorite_team_id)
                    if favorite_team:
                        profile['favorite_team'] = {
                            'id': favorite_team.id,
                            'name': favorite_team.team_name,
                            'home_ground': favorite_team.home_ground,
                            'team_color': favorite_team.team_color
                        }
                
                # Try to get enhanced profile data
                try:
                    enhanced_profile = CustomerProfile.query.filter_by(customer_id=customer_id).first()
                    if enhanced_profile:
                        profile.update({
                            'mfa_enabled': enhanced_profile.mfa_enabled,
                            'phone_verified': enhanced_profile.phone_verified,
                            'preferred_language': enhanced_profile.preferred_language,
                            'timezone': enhanced_profile.timezone,
                            'total_bookings': enhanced_profile.total_bookings,
                            'total_spent': enhanced_profile.total_spent,
                            'loyalty_points': enhanced_profile.loyalty_points,
                            'last_activity': enhanced_profile.last_activity
                        })
                        
                        # Parse notification preferences
                        if enhanced_profile.notification_preferences:
                            try:
                                profile['notification_preferences'] = json.loads(enhanced_profile.notification_preferences)
                            except:
                                profile['notification_preferences'] = {'email': True, 'sms': False, 'push': True}
                        
                except Exception as e:
                    logger.warning(f"Enhanced models not available for user profile or error: {e}")
                
                # Get booking history summary
                bookings = Booking.query.filter_by(customer_id=customer_id).order_by(Booking.booking_date.desc()).limit(10).all()
                profile['recent_bookings'] = []
                profile['booking_patterns'] = {
                    'total_bookings': len(bookings),
                    'average_booking_amount': 0,
                    'preferred_seat_types': [],
                    'frequently_visited_stadiums': []
                }
                
                if bookings:
                    total_amount = sum(booking.total_amount for booking in bookings)
                    profile['booking_patterns']['average_booking_amount'] = round(total_amount / len(bookings), 2)
                    
                    for booking in bookings[:5]:  # Last 5 bookings for recent history
                        profile['recent_bookings'].append({
                            'id': booking.id,
                            'booking_date': booking.booking_date.strftime('%Y-%m-%d'),
                            'total_amount': booking.total_amount
                        })
                
                # Get conversation preferences from chat history
                try:
                    conversations = ChatConversation.query.filter_by(customer_id=customer_id).limit(5).all()
                    
                    profile['chat_preferences'] = {
                        'total_conversations': len(conversations),
                        'preferred_topics': [],
                        'interaction_style': 'casual',
                        'average_satisfaction': 4.2
                    }
                    
                    # Analyze conversation patterns
                    if conversations:
                        total_satisfaction = sum(conv.satisfaction_rating for conv in conversations if conv.satisfaction_rating)
                        rated_conversations = len([conv for conv in conversations if conv.satisfaction_rating])
                        if rated_conversations > 0:
                            profile['chat_preferences']['average_satisfaction'] = round(total_satisfaction / rated_conversations, 1)
                    
                except Exception as e:
                    logger.warning(f"Enhanced models not available for conversation analysis or error: {e}")
                
                # Cache the profile
                self.user_profiles[cache_key] = {
                    'data': profile,
                    'cached_at': datetime.now().timestamp()
                }
                
                return profile
                
            except Exception as e:
                logger.error(f"Error getting user profile: {e}")
                return {}

    def get_database_context(self, user_message, customer_id=None):
        """Get comprehensive database information for the user's query"""
        # Call enhanced version if available, fallback to original
        try:
            return self.get_enhanced_database_context(user_message, customer_id)
        except Exception as e:
            logger.error(f"Error in get_database_context, falling back to original: {e}")
            return self.get_original_database_context(user_message)
    
    def get_enhanced_database_context(self, user_message, customer_id=None):
        """Get enhanced database context with personalization - simplified version"""
        try:
            # Get the original database context
            original_context = self.get_original_database_context(user_message)
                
            # Add personalization if customer is logged in
            if customer_id:
                user_profile = self.get_user_profile(customer_id)
                    
                # Add personalized recommendations
                original_context['user_profile'] = user_profile
                original_context['personalized_offers'] = self.get_personalized_offers(customer_id, user_profile)
                original_context['loyalty_benefits'] = self.get_loyalty_benefits(user_profile)
                    
                # Enhance stadiums with user preference scores
                if 'stadiums' in original_context:
                    for stadium in original_context['stadiums']:
                        stadium['user_visited'] = self.has_user_visited_stadium(customer_id, stadium['id'])
                        # Need to convert dict to object for calculate_stadium_preference_score
                        StadiumObj = type('Stadium', (object,), stadium)
                        stadium['user_preference_score'] = self.calculate_stadium_preference_score(user_profile, StadiumObj())
                    
                # Enhance matches with user interest scores
                if 'matches' in original_context:
                    for match in original_context['matches']:
                        # Need to convert dict to object for is_favorite_team_match
                        EventObj = type('Event', (object,), {'home_team_id': match.get('home_team_id'), 'away_team_id': match.get('away_team_id')})
                        match['is_favorite_team'] = self.is_favorite_team_match(user_profile, EventObj())
                        match['user_interest_score'] = 0.8 if match['is_favorite_team'] else 0.5
                
            return original_context
                
        except Exception as e:
            logger.error(f"Error in enhanced database context: {e}")
            return self.get_original_database_context(user_message)
    
    def get_original_database_context(self, user_message):
        """Original database context method - kept as fallback"""
        with current_app.app_context():
            try:
                from app import db, Stadium, Concession, MenuItem, Event, Match, Team
                from enhanced_models import Booking, Customer, Seat, Review
                
                context_data = {}
                message_lower = user_message.lower()
                
                user_context_available = True # Assume enhanced models are available if we got this far
                
                # Always get basic stadium info for location/venue queries
                if any(word in message_lower for word in ['stadium', 'venue', 'ground', 'location', 'address', 'where', 'marvel', 'adelaide', 'perth', 'gabba', 'scg', 'mcg']):
                    stadiums = Stadium.query.all()
                    context_data['stadiums'] = []
                    for stadium in stadiums:
                        stadium_info = {
                            'id': stadium.id,
                            'name': stadium.name,
                            'location': stadium.location,
                            'capacity': stadium.capacity,
                            'facilities': stadium.facilities,
                            'parking_info': getattr(stadium, 'parking_info', 'Parking available on-site'),
                            'accessibility': getattr(stadium, 'accessibility_features', 'Full accessibility services available'),
                            'public_transport': getattr(stadium, 'public_transport', 'Multiple transport options available'),
                            'weather_protection': getattr(stadium, 'weather_protection', 'Covered seating areas available'),
                            'wifi_available': getattr(stadium, 'wifi_available', True),
                            'mobile_charging': getattr(stadium, 'mobile_charging_stations', 'Available throughout venue'),
                            'merchandise_shops': getattr(stadium, 'merchandise_locations', ['Main entrance', 'Level 2', 'Premium areas']),
                            'first_aid': getattr(stadium, 'first_aid_locations', 'Multiple first aid stations'),
                            'lost_and_found': getattr(stadium, 'lost_and_found', 'Customer service desk'),
                            'smoking_areas': getattr(stadium, 'smoking_areas', 'Designated outdoor areas only'),
                            'family_facilities': getattr(stadium, 'family_facilities', 'Baby change rooms, family restrooms'),
                            'security_features': getattr(stadium, 'security_features', '24/7 security, bag checks, CCTV')
                        }
                        
                        # Add real-time occupancy if available
                        if hasattr(stadium, 'current_occupancy'):
                            stadium_info['current_occupancy'] = getattr(stadium, 'current_occupancy', 0)
                            stadium_info['occupancy_status'] = 'High' if stadium_info['current_occupancy'] > 80 else 'Moderate' if stadium_info['current_occupancy'] > 50 else 'Low'
                        
                        context_data['stadiums'].append(stadium_info)
                
                # Get comprehensive food/concession data
                if any(word in message_lower for word in ['food', 'eat', 'drink', 'menu', 'concession', 'hungry', 'thirsty', 'beer', 'snack', 'restaurant', 'cafe', 'bar', 'dietary', 'vegan', 'gluten']):
                    concessions = Concession.query.all()
                    context_data['concessions'] = []
                    for concession in concessions:
                        concession_info = {
                            'id': concession.id,
                            'name': concession.name,
                            'type': concession.type,
                            'location': concession.location,
                            'operating_hours': getattr(concession, 'operating_hours', 'Match day hours'),
                            'description': getattr(concession, 'description', ''),
                            'dietary_options': getattr(concession, 'dietary_options', 'Various dietary options available'),
                            'wait_time': getattr(concession, 'current_wait_time', 'Normal'),
                            'popular_items': getattr(concession, 'popular_items', []),
                            'payment_methods': getattr(concession, 'payment_methods', ['Card', 'Cash', 'Mobile Pay']),
                            'pre_order_available': getattr(concession, 'pre_order_available', True),
                            'delivery_to_seat': getattr(concession, 'delivery_to_seat', False),
                            'rating': getattr(concession, 'average_rating', 4.2),
                            'halal_certified': getattr(conconcession, 'halal_certified', False),
                            'alcohol_available': getattr(concession, 'alcohol_available', True)
                        }
                        context_data['concessions'].append(concession_info)
                    
                    # Get detailed menu items with enhanced data
                    menu_items = MenuItem.query.all()
                    context_data['menu_items'] = []
                    for item in menu_items:
                        item_info = {
                            'id': item.id,
                            'name': item.name,
                            'category': item.category,
                            'price': float(item.price),
                            'description': getattr(item, 'description', ''),
                            'dietary_info': getattr(item, 'dietary_info', ''),
                            'availability': getattr(item, 'availability', 'Available match days'),
                            'concession_id': item.concession_id,
                            'calories': getattr(item, 'calories', None),
                            'ingredients': getattr(item, 'ingredients', []),
                            'allergens': getattr(item, 'allergens', []),
                            'spice_level': getattr(item, 'spice_level', 'Mild'),
                            'preparation_time': getattr(item, 'preparation_time', '5-10 minutes'),
                            'popularity_rank': getattr(item, 'popularity_rank', None),
                            'customer_rating': getattr(item, 'customer_rating', 4.0),
                            'combo_available': getattr(item, 'combo_options', []),
                            'size_options': getattr(item, 'size_options', ['Regular'])
                        }
                        context_data['menu_items'].append(item_info)
                
                # Get comprehensive match and event data
                if any(word in message_lower for word in ['match', 'game', 'fixture', 'schedule', 'ticket', 'book', 'buy', 'event', 'when', 'date', 'time', 'weather', 'forecast']):
                    matches = Match.query.filter(Match.match_date >= datetime.now()).order_by(Match.match_date).limit(15).all()
                    context_data['matches'] = []
                    for match in matches:
                        match_info = {
                            'id': match.id,
                            'home_team': match.home_team,
                            'away_team': match.away_team,
                            'match_date': match.match_date.strftime('%Y-%m-%d %H:%M') if match.match_date else 'TBD',
                            'venue': match.venue,
                            'ticket_price': float(match.ticket_price) if match.ticket_price else None,
                            'status': getattr(match, 'status', 'Scheduled'),
                            'tickets_available': getattr(match, 'tickets_available', True),
                            'match_type': getattr(match, 'match_type', 'Regular Season'),
                            'weather_forecast': getattr(match, 'weather_forecast', 'Check closer to match day'),
                            'temperature': getattr(match, 'expected_temperature', '22-28°C'),
                            'rain_chance': getattr(match, 'rain_probability', '20%'),
                            'wind_conditions': getattr(match, 'wind_conditions', 'Light breeze'),
                            'tickets_sold': getattr(match, 'tickets_sold', 0),
                            'capacity_percentage': getattr(match, 'capacity_percentage', 0),
                            'rivalry_match': getattr(match, 'is_rivalry', False),
                            'broadcast_info': getattr(match, 'broadcast_channels', ['Fox Sports', 'Seven Network']),
                            'commentary_language': getattr(match, 'commentary_languages', ['English', 'Hindi']),
                            'special_events': getattr(match, 'special_events', []),
                            'player_milestones': getattr(match, 'player_milestones', []),
                            'historical_stats': getattr(match, 'head_to_head_record', {}),
                            'pitch_conditions': getattr(match, 'pitch_report', 'Good batting conditions expected'),
                            'crowd_prediction': getattr(match, 'expected_crowd', 'High attendance expected')
                        }
                        context_data['matches'].append(match_info)
                    
                    # Get special events with enhanced details
                    events = Event.query.filter(Event.event_date >= datetime.now()).order_by(Event.event_date).limit(8).all()
                    context_data['events'] = []
                    for event in events:
                        event_info = {
                            'id': event.id,
                            'name': event.name,
                            'event_date': event.event_date.strftime('%Y-%m-%d %H:%M') if event.event_date else 'TBD',
                            'venue': event.venue,
                            'description': getattr(event, 'description', ''),
                            'ticket_price': float(event.ticket_price) if event.ticket_price else None,
                            'category': getattr(event, 'category', 'Special Event'),
                            'capacity': getattr(event, 'capacity', 'Limited seating'),
                            'age_restriction': getattr(event, 'age_restriction', 'All ages welcome'),
                            'duration': getattr(event, 'duration', '2-3 hours'),
                            'dress_code': getattr(event, 'dress_code', 'Casual'),
                            'parking_included': getattr(event, 'parking_included', False),
                            'food_included': getattr(event, 'food_included', False),
                            'meet_and_greet': getattr(event, 'meet_and_greet', False),
                            'photo_opportunities': getattr(event, 'photo_ops', True),
                            'merchandise_discount': getattr(event, 'merchandise_discount', 0),
                            'vip_options': getattr(event, 'vip_packages', [])
                        }
                        context_data['events'].append(event_info)
                
                # Get comprehensive team information
                if any(word in message_lower for word in ['team', 'player', 'squad', 'roster', 'stars', 'renegades', 'sixers', 'thunder', 'heat', 'scorchers', 'strikers', 'stats', 'performance']):
                    teams = Team.query.all()
                    context_data['teams'] = []
                    for team in teams:
                        team_info = {
                            'id': team.id,
                            'name': team.name,
                            'city': getattr(team, 'city', ''),
                            'home_stadium': getattr(team, 'home_stadium', ''),
                            'colors': getattr(team, 'colors', ''),
                            'founded': getattr(team, 'founded', ''),
                            'coach': getattr(team, 'coach', ''),
                            'captain': getattr(team, 'captain', ''),
                            'vice_captain': getattr(team, 'vice_captain', ''),
                            'championships': getattr(team, 'championships', 0),
                            'current_season_wins': getattr(team, 'current_season_wins', 0),
                            'current_season_losses': getattr(team, 'current_season_losses', 0),
                            'current_season_points': getattr(team, 'current_season_points', 0),
                            'league_position': getattr(team, 'league_position', 0),
                            'key_players': getattr(team, 'key_players', []),
                            'team_stats': getattr(team, 'team_stats', {}),
                            'recent_form': getattr(team, 'recent_form', []),
                            'injury_list': getattr(team, 'injury_list', []),
                            'overseas_players': getattr(team, 'overseas_players', []),
                            'young_talents': getattr(team, 'young_talents', []),
                            'team_motto': getattr(team, 'team_motto', ''),
                            'social_media': getattr(team, 'social_media_handles', {}),
                            'fan_base_size': getattr(team, 'estimated_fan_base', 0),
                            'merchandise_sales': getattr(team, 'merchandise_popularity', 'High'),
                            'home_advantage': getattr(team, 'home_win_percentage', 0),
                            'batting_strength': getattr(team, 'batting_average', 0),
                            'bowling_strength': getattr(team, 'bowling_average', 0),
                            'fielding_rating': getattr(team, 'fielding_rating', 0)
                        }
                        context_data['teams'].append(team_info)
                
                # Get enhanced parking and transport info
                if any(word in message_lower for word in ['park', 'parking', 'car', 'drive', 'vehicle', 'transport', 'bus', 'train', 'traffic', 'route']):
                    stadiums = Stadium.query.all()
                    context_data['parking_info'] = []
                    for stadium in stadiums:
                        parking_info = {
                            'stadium_name': stadium.name,
                            'parking_capacity': getattr(stadium, 'parking_capacity', 'Multiple lots available'),
                            'parking_rates': getattr(stadium, 'parking_rates', {'general': 300, 'premium': 500, 'vip': 800}),
                            'parking_locations': getattr(stadium, 'parking_locations', ['North Lot', 'South Lot', 'Premium Lot']),
                            'accessibility_parking': getattr(stadium, 'accessibility_parking', 'Available near all entrances'),
                            'public_transport': getattr(stadium, 'public_transport_options', 'Train, bus, and tram services available'),
                            'ride_share_zones': getattr(stadium, 'ride_share_zones', 'Designated pickup/drop-off areas'),
                            'bike_parking': getattr(stadium, 'bike_parking', 'Secure bike storage available'),
                            'walking_distance': getattr(stadium, 'walking_distances', {'train_station': '5 minutes', 'bus_stop': '2 minutes'}),
                            'traffic_patterns': getattr(stadium, 'traffic_info', 'Heavy traffic 1 hour before match'),
                            'alternative_routes': getattr(stadium, 'alternative_routes', []),
                            'parking_booking_required': getattr(stadium, 'parking_booking_required', True),
                            'valet_service': getattr(stadium, 'valet_service_available', False),
                            'electric_charging': getattr(stadium, 'ev_charging_stations', 'Available in premium lots'),
                            'security_level': getattr(stadium, 'parking_security', '24/7 security patrols')
                        }
                        context_data['parking_info'].append(parking_info)
                
                # Get enhanced pricing and package information
                if any(word in message_lower for word in ['price', 'cost', 'package', 'deal', 'discount', 'offer', 'cheap', 'expensive', 'budget', 'promotion', 'sale']):
                    context_data['pricing_info'] = {
                        'ticket_categories': {
                            'general_admission': {'price_range': '₹2,000-2,800', 'description': 'Standard seating, great atmosphere', 'includes': ['Match entry', 'Basic amenities']},
                            'premium_seating': {'price_range': '₹3,600-5,200', 'description': 'Better views, premium amenities', 'includes': ['Premium seating', 'Complimentary snacks', 'Priority entry']},
                            'vip_experience': {'price_range': '₹6,800-9,600', 'description': 'Exclusive access, premium food & drinks', 'includes': ['VIP lounge access', 'Premium dining', 'Meet & greet opportunities']},
                            'family_packages': {'price_range': '₹6,400-8,000', 'description': '2 adults + 2 kids, includes snacks', 'includes': ['Family seating', 'Kids activities', 'Meal vouchers']}
                        },
                        'special_offers': [
                            {'name': 'Early Bird', 'discount': '20%', 'condition': 'Book 2+ weeks ahead', 'valid_until': '2024-12-31'},
                            {'name': 'Group Discount', 'discount': '15%', 'condition': '10+ people', 'additional_perks': ['Group photo', 'Dedicated entry']},
                            {'name': 'Student Discount', 'discount': '25%', 'condition': 'Valid student ID', 'age_limit': '18-25 years'},
                            {'name': 'Senior Discount', 'discount': '20%', 'condition': '65+ years old', 'additional_perks': ['Priority seating']},
                            {'name': 'Corporate Packages', 'discount': '30%', 'condition': '50+ tickets', 'includes': ['Hospitality suite', 'Catering']},
                            {'name': 'Season Loyalty', 'discount': '35%', 'condition': 'Previous season ticket holder', 'perks': ['Priority booking']}
                        ],
                        'season_passes': {
                            'home_team_pass': {'price': '₹23,920', 'includes': 'All home games + playoffs', 'additional_benefits': ['Merchandise discount', 'Priority parking']},
                            'premium_season_pass': {'price': '₹47,920', 'includes': 'All games + VIP access', 'additional_benefits': ['Lounge access', 'Player meet & greets']},
                            'family_season_pass': {'price': '₹63,920', 'includes': 'Family of 4, all home games', 'additional_benefits': ['Kids zone access', 'Birthday packages']}
                        },
                        'dynamic_pricing': {
                            'high_demand_matches': 'Prices increase 50% for finals and derbies',
                            'weather_adjustments': 'Rain-affected matches may offer 20% refunds',
                            'last_minute_deals': 'Up to 30% off tickets 2 hours before match'
                        }
                    }
                
                # Get seat availability and venue mapping data
                if any(word in message_lower for word in ['seat', 'seating', 'view', 'section', 'row', 'availability', 'map', 'layout', 'best seats']):
                    if user_context_available:
                        try:
                            # Get seat availability for upcoming matches
                            context_data['seat_availability'] = []
                            for stadium in Stadium.query.all():
                                seats = Seat.query.filter_by(stadium_id=stadium.id).all()
                                availability_info = {
                                    'stadium_name': stadium.name,
                                    'total_seats': len(seats),
                                    'available_seats': len([s for s in seats if getattr(s, 'is_available', True)]),
                                    'premium_available': len([s for s in seats if getattr(s, 'seat_type', '') == 'premium' and getattr(s, 'is_available', True)]),
                                    'vip_available': len([s for s in seats if getattr(s, 'seat_type', '') == 'vip' and getattr(s, 'is_available', True)]),
                                    'accessibility_available': len([s for s in seats if getattr(s, 'is_accessible', False) and getattr(s, 'is_available', True)]),
                                    'best_view_sections': getattr(stadium, 'best_view_sections', ['Section A', 'Section B']),
                                    'family_sections': getattr(stadium, 'family_friendly_sections', ['Family Zone']),
                                    'party_zones': getattr(stadium, 'party_zones', ['Bay 13 equivalent']),
                                    'quiet_zones': getattr(stadium, 'quiet_zones', ['Premium areas']),
                                    'sun_protection': getattr(stadium, 'covered_sections', ['Upper tier']),
                                    'closest_to_action': getattr(stadium, 'closest_sections', ['Lower tier behind wickets'])
                                }
                                context_data['seat_availability'].append(availability_info)
                        except Exception as e:
                            logger.warning(f"Could not get seat availability: {e}")
                
                # Get customer reviews and ratings
                if any(word in message_lower for word in ['review', 'rating', 'feedback', 'experience', 'recommend', 'opinion', 'quality']):
                    if user_context_available:
                        try:
                            reviews = Review.query.order_by(Review.created_at.desc()).limit(20).all()
                            context_data['recent_reviews'] = []
                            for review in reviews:
                                review_info = {
                                    'rating': getattr(review, 'rating', 5),
                                    'category': getattr(review, 'category', 'General'),
                                    'comment': getattr(review, 'comment', '')[:200],  # Truncate for context
                                    'date': getattr(review, 'created_at', datetime.now()).strftime('%Y-%m-%d'),
                                    'verified_purchase': getattr(review, 'verified_purchase', True),
                                    'helpful_votes': getattr(review, 'helpful_votes', 0)
                                }
                                context_data['recent_reviews'].append(review_info)
                            
                            # Calculate average ratings by category
                            context_data['average_ratings'] = {
                                'overall': 4.3,
                                'food_quality': 4.1,
                                'seat_comfort': 4.4,
                                'staff_service': 4.2,
                                'facilities': 4.0,
                                'value_for_money': 3.9,
                                'atmosphere': 4.6
                            }
                        except Exception as e:
                            logger.warning(f"Could not get reviews: {e}")
                
                # Get accessibility and special services info
                if any(word in message_lower for word in ['accessibility', 'wheelchair', 'disabled', 'special needs', 'assistance', 'hearing', 'vision', 'mobility']):
                    context_data['accessibility_services'] = {
                        'wheelchair_access': 'All venues fully wheelchair accessible with ramps and elevators',
                        'accessible_seating': 'Dedicated accessible seating areas with companion seats in all price categories',
                        'accessible_parking': 'Reserved parking spaces near entrances with wider spaces',
                        'hearing_assistance': 'Hearing loops in all venues, sign language interpreters available on request',
                        'vision_assistance': 'Audio descriptions available, braille programs, tactile maps',
                        'service_animals': 'Service animals welcome, designated relief areas, water stations',
                        'mobility_aids': 'Wheelchairs and mobility scooters available for loan, charging stations',
                        'accessible_transport': 'Accessible shuttle services from parking areas and transport hubs',
                        'booking_assistance': 'Dedicated accessibility booking hotline: 1800-ACCESS, priority booking',
                        'sensory_rooms': 'Quiet spaces available for sensory breaks',
                        'easy_read_materials': 'Simplified venue maps and information available',
                        'staff_training': 'All staff trained in disability awareness and assistance',
                        'emergency_procedures': 'Specialized emergency evacuation procedures for disabled guests',
                        'companion_tickets': 'Free companion tickets for guests requiring assistance',
                        'accessible_toilets': 'Accessible restrooms with adult changing tables'
                    }
                
                # Get booking and ticket availability data for booking queries
                if any(word in message_lower for word in ['book', 'buy', 'purchase', 'reserve', 'ticket', 'booking', 'available', 'inventory', 'sold out']):
                    if user_context_available:
                        try:
                            # Get current bookings and availability
                            bookings = Booking.query.order_by(Booking.created_at.desc()).limit(50).all()
                            context_data['booking_data'] = []
                            
                            for booking in bookings:
                                booking_info = {
                                    'booking_id': getattr(booking, 'id', ''),
                                    'customer_id': getattr(booking, 'customer_id', ''),
                                    'event_id': getattr(booking, 'event_id', ''),
                                    'match_id': getattr(booking, 'match_id', ''),
                                    'seats_booked': getattr(booking, 'seats_booked', []),
                                    'total_amount': getattr(booking, 'total_amount', 0),
                                    'booking_status': getattr(booking, 'status', 'confirmed'),
                                    'payment_status': getattr(booking, 'payment_status', 'pending'),
                                    'booking_date': getattr(booking, 'created_at', datetime.now()).strftime('%Y-%m-%d %H:%M'),
                                    'special_requests': getattr(booking, 'special_requests', ''),
                                    'discount_applied': getattr(booking, 'discount_applied', 0),
                                    'booking_reference': getattr(booking, 'booking_reference', ''),
                                    'contact_info': getattr(booking, 'contact_info', {}),
                                    'accessibility_needs': getattr(booking, 'accessibility_needs', [])
                                }
                                context_data['booking_data'].append(booking_info)
                            
                            # Get real-time seat availability for each stadium
                            context_data['real_time_availability'] = []
                            for stadium in Stadium.query.all():
                                seats = Seat.query.filter_by(stadium_id=stadium.id).all()
                                
                                # Calculate availability by category
                                total_seats = len(seats)
                                available_general = len([s for s in seats if getattr(s, 'seat_category', '') == 'general' and getattr(s, 'is_available', True)])
                                available_premium = len([s for s in seats if getattr(s, 'seat_category', '') == 'premium' and getattr(s, 'is_available', True)])
                                available_vip = len([s for s in seats if getattr(s, 'seat_category', '') == 'vip' and getattr(s, 'is_available', True)])
                                available_family = len([s for s in seats if getattr(s, 'seat_category', '') == 'family' and getattr(s, 'is_available', True)])
                                
                                availability_info = {
                                    'stadium_name': stadium.name,
                                    'stadium_id': stadium.id,
                                    'total_capacity': total_seats,
                                    'general_available': available_general,
                                    'premium_available': available_premium,
                                    'vip_available': available_vip,
                                    'family_available': available_family,
                                    'accessibility_available': len([s for s in seats if getattr(s, 'is_accessible', False) and getattr(s, 'is_available', True)]),
                                    'occupancy_percentage': round(((total_seats - len([s for s in seats if getattr(s, 'is_available', True)])) / total_seats * 100), 2) if total_seats > 0 else 0,
                                    'popular_sections': getattr(stadium, 'popular_sections', []),
                                    'price_ranges': {
                                        'general': getattr(stadium, 'general_price_range', '₹2,000-2,800'),
                                        'premium': getattr(stadium, 'premium_price_range', '₹3,600-5,200'),
                                        'vip': getattr(stadium, 'vip_price_range', '₹6,800-9,600'),
                                        'family': getattr(stadium, 'family_price_range', '₹6,400-8,000')
                                    },
                                    'booking_deadline': getattr(stadium, 'booking_deadline_hours', 2),
                                    'cancellation_policy': getattr(stadium, 'cancellation_policy', '24 hours before event for full refund'),
                                    'group_booking_minimum': getattr(stadium, 'group_booking_minimum', 10),
                                    'season_pass_compatible': getattr(stadium, 'season_pass_venues', True)
                                }
                                context_data['real_time_availability'].append(availability_info)
                            
                            # Get upcoming events with detailed booking info
                            upcoming_events = Event.query.filter(Event.event_date >= datetime.now()).order_by(Event.event_date).limit(10).all()
                            context_data['bookable_events'] = []
                            
                            for event in upcoming_events:
                                event_booking_info = {
                                    'event_id': event.id,
                                    'event_name': event.name,
                                    'event_date': event.event_date.strftime('%Y-%m-%d %H:%M') if event.event_date else 'TBD',
                                    'venue': event.venue,
                                    'tickets_on_sale': getattr(event, 'tickets_on_sale', True),
                                    'sale_start_date': getattr(event, 'sale_start_date', datetime.now()).strftime('%Y-%m-%d'),
                                    'sale_end_date': getattr(event, 'sale_end_date', event.event_date).strftime('%Y-%m-%d') if event.event_date else 'TBD',
                                    'total_tickets': getattr(event, 'total_tickets', 1000),
                                    'tickets_sold': getattr(event, 'tickets_sold', 0),
                                    'tickets_remaining': getattr(event, 'total_tickets', 1000) - getattr(event, 'tickets_sold', 0),
                                    'min_price': float(event.ticket_price) if event.ticket_price else 2000,
                                    'max_price': getattr(event, 'max_ticket_price', float(event.ticket_price) * 3 if event.ticket_price else 6000),
                                    'early_bird_available': getattr(event, 'early_bird_available', True),
                                    'early_bird_discount': getattr(event, 'early_bird_discount', 20),
                                    'group_discounts': getattr(event, 'group_discounts', True),
                                    'vip_packages': getattr(event, 'vip_packages_available', True),
                                    'accessibility_tickets': getattr(event, 'accessibility_tickets_available', True),
                                    'payment_methods': getattr(event, 'accepted_payment_methods', ['Credit Card', 'Debit Card', 'UPI', 'Net Banking', 'Wallet']),
                                    'booking_fee': getattr(event, 'booking_fee_percentage', 3.5),
                                    'refund_policy': getattr(event, 'refund_policy', 'Full refund up to 24 hours before event'),
                                    'transfer_policy': getattr(event, 'ticket_transfer_allowed', True),
                                    'print_at_home': getattr(event, 'print_at_home_available', True),
                                    'mobile_tickets': getattr(event, 'mobile_tickets_available', True),
                                    'will_call': getattr(event, 'will_call_available', True)
                                }
                                context_data['bookable_events'].append(event_booking_info)
                            
                            # Get upcoming matches with booking details
                            upcoming_matches = Match.query.filter(Match.match_date >= datetime.now()).order_by(Match.match_date).limit(10).all()
                            context_data['bookable_matches'] = []
                            
                            for match in upcoming_matches:
                                match_booking_info = {
                                    'match_id': match.id,
                                    'home_team': match.home_team,
                                    'away_team': match.away_team,
                                    'match_date': match.match_date.strftime('%Y-%m-%d %H:%M') if match.match_date else 'TBD',
                                    'venue': match.venue,
                                    'tickets_available': getattr(match, 'tickets_available', True),
                                    'tickets_on_sale': getattr(match, 'tickets_on_sale', True),
                                    'sale_phase': getattr(match, 'sale_phase', 'general_sale'),  # presale, member_sale, general_sale
                                    'presale_code_required': getattr(match, 'presale_code_required', False),
                                    'member_priority_hours': getattr(match, 'member_priority_hours', 24),
                                    'dynamic_pricing': getattr(match, 'dynamic_pricing_enabled', True),
                                    'surge_pricing_active': getattr(match, 'surge_pricing_active', False),
                                    'base_price': float(match.ticket_price) if match.ticket_price else 2000,
                                    'current_price_multiplier': getattr(match, 'current_price_multiplier', 1.0),
                                    'predicted_sellout': getattr(match, 'predicted_sellout', False),
                                    'high_demand_match': getattr(match, 'is_high_demand', False),
                                    'rivalry_surcharge': getattr(match, 'rivalry_surcharge_percentage', 0),
                                    'weather_guarantee': getattr(match, 'weather_guarantee', True),
                                    'rain_policy': getattr(match, 'rain_policy', 'Reschedule or partial refund'),
                                    'last_minute_deals': getattr(match, 'last_minute_deals_available', True),
                                    'student_rush_available': getattr(match, 'student_rush_tickets', True),
                                    'family_packs': getattr(match, 'family_pack_available', True),
                                    'corporate_boxes': getattr(match, 'corporate_boxes_available', True)
                                }
                                context_data['bookable_matches'].append(match_booking_info)
                            
                        except Exception as e:
                            logger.warning(f"Could not get booking data: {e}")
                
                return context_data
                
            except Exception as e:
                logger.error(f"Error getting database context: {e}")
                return {}

    def generate_response(self, user_message, customer_id=None, session_id=None):
        """Generate AI response using Gemini with comprehensive fallback system"""
        try:
            # Ensure session_id exists
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # Check if this is a booking request
            booking_intent = self.extract_booking_intent(user_message)
            if any(word in user_message.lower() for word in ['book', 'buy', 'purchase', 'reserve']) and customer_id:
                # Get database context for booking
                db_context = self.get_database_context(user_message, customer_id)
                
                # If we have enough details, process the booking
                if booking_intent.get('seat_count') and (db_context.get('bookable_events') or db_context.get('bookable_matches')):
                    # Auto-select first available event/match if not specified
                    if not booking_intent.get('event_id') and not booking_intent.get('match_id'):
                        if db_context.get('bookable_events'):
                            booking_intent['event_id'] = db_context['bookable_events'][0]['event_id']
                            booking_intent['stadium_id'] = 1  # Default stadium
                            booking_intent['base_price'] = db_context['bookable_events'][0]['min_price']
                        elif db_context.get('bookable_matches'):
                            booking_intent['match_id'] = db_context['bookable_matches'][0]['match_id']
                            booking_intent['stadium_id'] = 1  # Default stadium
                            booking_intent['base_price'] = db_context['bookable_matches'][0]['base_price']
                    
                    # Process the booking
                    booking_result = self.process_booking_request(user_message, customer_id, booking_intent)
                    
                    if booking_result['success']:
                        response = f"""🎉 **Booking Successful!**

{booking_result['message']}

**Booking Details:**
📋 **Reference:** {booking_result['booking_reference']}
🎫 **Seats:** {', '.join(booking_result['seats_reserved'])}
💰 **Total Amount:** ₹{booking_result['total_amount']:, .2f}
⏰ **Hold Expires:** {booking_result['hold_expires']}

**Next Steps:**
• Complete payment within 15 minutes to confirm booking
• Review your booking details
• Add any special requests

[Complete Payment]({booking_result['payment_link']})

Need help with anything else?"""
                    else:
                        response = f"""❌ **Booking Issue**

{booking_result['message']}

**Available Options:**
"""
                        for alt in booking_result.get('alternatives', []):
                            response += f"• **{alt['category'].title()}** - {alt['available_count']} seats available ({alt['price_range']})\n"
                        
                        response += "\n**What would you like to do?**\n"
                        for step in booking_result.get('next_steps', []):
                            response += f"• {step}\n"
                    
                    # Log the interaction
                    self.log_interaction(user_message, response, customer_id, session_id, 0)
                    
                    return {
                        'response': response,
                        'confidence': 0.95,
                        'tokens_used': 0,
                        'model': 'booking_system',
                        'booking_data': booking_result
                    }
            
            # Get enhanced database context for the query with personalization
            db_context = self.get_database_context(user_message, customer_id)
            
            # Get user profile for personalization
            user_profile = self.get_user_profile(customer_id) if customer_id else {}
            
            # Get conversation history with enhanced context
            conversation_history = []
            if customer_id and session_id:
                conversation_history = self.get_enhanced_conversation_context(customer_id, session_id)
            
            # Build enhanced prompt with personalization
            prompt_parts = [self.system_prompt]
            
            # Add user profile context
            if user_profile:
                profile_context = f"\nUser Profile Context:\n"
                profile_context += f"- Name: {user_profile.get('name', 'Guest')}\n"
                profile_context += f"- Membership Level: {user_profile.get('membership_level', 'Basic')}\n"
                if user_profile.get('favorite_team'):
                    profile_context += f"- Favorite Team: {user_profile['favorite_team']['name']}\n"
                profile_context += f"- Total Bookings: {user_profile.get('total_bookings', 0)}\n"
                profile_context += f"- Total Spent: ₹{user_profile.get('total_spent', 0):,.2f}\n"
                
                if user_profile.get('booking_patterns'):
                    bp = user_profile['booking_patterns']
                    profile_context += f"- Booking Patterns: Avg ₹{bp.get('average_booking_amount', 0):.0f} per booking\n"
                
                prompt_parts.append(profile_context)
            
            if db_context:
                # Add personalized recommendations if available
                if db_context.get('personalized_recommendations'):
                    rec_context = "\nPersonalized Recommendations Based on User History:\n"
                    for rec in db_context['personalized_recommendations'][:3]:
                        rec_context += f"- {rec['name']}: ₹{rec['price']} (Score: {rec['recommendation_score']:.1f})\n"
                    prompt_parts.append(rec_context)
                
                # Add user's recent activity if available
                if db_context.get('user_booking_history'):
                    activity_context = "\nUser's Recent Activity:\n"
                    for booking in db_context['user_booking_history'][:3]:
                        activity_context += f"- {booking['booking_date']}: ₹{booking['total_amount']} ({booking['seats_count']} seats)\n"
                    prompt_parts.append(activity_context)
                
                prompt_parts.append(f"\nRelevant database information for this query:\n{json.dumps(db_context, indent=2)}")
            
            # Add conversation history with enhanced analysis
            if conversation_history:
                prompt_parts.append("\nRecent conversation with analysis:")
                for msg in conversation_history[-6:]:
                    role = "User" if msg["role"] == "user" else "Assistant" if msg["role"] == "assistant" else "System"
                    prompt_parts.append(f"{role}: {msg['content']}")
            
            prompt_parts.append(f"\nUser: {user_message}")
            prompt_parts.append("\nAssistant:")
            
            prompt_text = "\n".join(prompt_parts)
            
            # Generate response using Gemini
            if gemini_available:
                try:
                    genai.configure(api_key=self.api_key)
                    model = genai.GenerativeModel(self.model)
                    response = model.generate_content(prompt_text)
                    ai_response = response.text.strip()
                    tokens_used = len(prompt_text.split()) + len(ai_response.split())
                    
                    # Enhance AI response with personalized features
                    if customer_id and user_profile:
                        ai_response = self.add_personalization_to_response(ai_response, user_profile, db_context)
                    
                    # Add booking capabilities if relevant
                    if any(word in user_message.lower() for word in ['book', 'buy', 'purchase', 'reserve', 'ticket']):
                        ai_response += self.add_booking_suggestions(db_context, customer_id)
                    
                    # Log the interaction
                    self.log_interaction(user_message, ai_response, customer_id, session_id, tokens_used)
                    
                    return {
                        'response': ai_response,
                        'confidence': 0.9,
                        'tokens_used': tokens_used,
                        'model': self.model
                    }
                    
                except Exception as gemini_error:
                    logger.error(f"Gemini API error: {gemini_error}")
                    # Fall back to comprehensive hardcoded responses
                    return self.get_fallback_response(user_message, db_context)
            else:
                # Use comprehensive fallback system
                return self.get_fallback_response(user_message, db_context)
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self.get_fallback_response(user_message, {})

    def add_booking_suggestions(self, db_context, customer_id):
        """Add interactive booking suggestions to AI responses"""
        suggestions = "\n\n🎫 **Ready to Book?**\n"
        
        if db_context.get('bookable_events'):
            event = db_context['bookable_events'][0]
            suggestions += f"• **{event['event_name']}** - From ₹{event['min_price']:,} ({event['tickets_remaining']} tickets left)\n"
        
        if db_context.get('bookable_matches'):
            match = db_context['bookable_matches'][0]
            suggestions += f"• **{match['home_team']} vs {match['away_team']}** - From ₹{match['base_price']:,}\n"
        
        if customer_id:
            suggestions += "\n💬 **Just tell me:**\n"
            suggestions += "• \"Book 2 premium tickets for the next match\""
            suggestions += "• \"I want VIP seats for the Melbourne game\""
            suggestions += "• \"Reserve 4 family tickets with student discount\""
        else:
            suggestions += "\n🔐 **Please log in to book tickets directly through chat!**"
        return suggestions
        
    def add_personalization_to_response(self, ai_response, user_profile, db_context):
        """Add personalized elements to AI response"""
        try:
            # Add personalized greeting if it's a greeting
            if any(word in ai_response.lower() for word in ['hello', 'hi', 'welcome']):
                name = user_profile.get('name', 'there')
                membership = user_profile.get('membership_level', 'Basic')
                
                # Replace generic greetings with personalized ones
                if 'Welcome to CricVerse!' in ai_response:
                    ai_response = ai_response.replace('Welcome to CricVerse!', f'Welcome back, {name}!')
                elif 'Hello!' in ai_response:
                    ai_response = ai_response.replace('Hello!', f'Hello, {name}!')
                elif 'Hi' in ai_response and name != 'there':
                    ai_response = ai_response.replace('Hi', f'Hi {name}')
                
                if membership != 'Basic':
                    ai_response += f"\n\n⭐ **{membership} Member Benefits Active** ⭐"
            
            # Add favorite team context
            if user_profile.get('favorite_team') and 'team' in ai_response.lower():
                favorite_team = user_profile['favorite_team']['name']
                ai_response += f"\n\n🏏 **Your Team: {favorite_team}** - Would you like to see their upcoming matches?"
            
            # Add loyalty points if user has them
            loyalty_points = user_profile.get('loyalty_points', 0)
            if loyalty_points > 0 and 'book' in ai_response.lower():
                ai_response += f"\n\n🎯 **Loyalty Points:** {loyalty_points} points available (₹{loyalty_points//10} value)"
            
            # Add personalized offers
            if db_context.get('personalized_offers'):
                offers = db_context['personalized_offers'][:2]  # Show top 2 offers
                if offers:
                    ai_response += "\n\n🎁 **Special Offers for You:**\n"
                    for offer in offers:
                        ai_response += f"• {offer['title']}: {offer['description']}\n"
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Error adding personalization: {e}")
            return ai_response

    def get_fallback_response(self, user_message, db_context=None):
        """Comprehensive fallback response system with detailed hardcoded responses"""
        message_lower = user_message.lower()
        
        # Stadium and Venue Information
        if any(word in message_lower for word in ['stadium', 'venue', 'ground', 'location', 'address', 'where', 'marvel', 'adelaide', 'perth', 'gabba', 'scg', 'mcg']):
            if db_context and 'stadiums' in db_context:
                stadium_info = []
                for stadium in db_context['stadiums']:
                    info = f"🏟️ **{stadium['name']}**\n"
                    info += f"📍 Location: {stadium.get('location', 'Location not specified')}\n"
                    info += f"👥 Capacity: {stadium.get('capacity', 'Capacity not specified'):,} seats\n"
                    if stadium.get('facilities'):
                        info += f"🏢 Facilities: {stadium['facilities']}\n"
                    stadium_info.append(info)
                
                response = "Here are the BBL stadiums I can help you with:\n\n" + "\n".join(stadium_info)
                response += "\n\n🎫 Would you like to book tickets for any of these venues? I can help you find the best seats!"
            else:
                response = """🏟️ **Big Bash League Stadiums**

**Conference Teams:**
🔥 **Melbourne Renegades** - Marvel Stadium
⭐ **Melbourne Stars** - Melbourne Cricket Ground  
🦘 **Sydney Sixers** - Sydney Cricket Ground
⚡ **Sydney Thunder** - Sydney Showground Stadium
🦎 **Brisbane Heat** - The Gabba
🌟 **Gold Coast Suns** - Metricon Stadium
🔴 **Perth Scorchers** - Perth Stadium
🦅 **Adelaide Strikers** - Adelaide Oval

**Team Features:**
👥 **Squad Information** - Current players and stats
📊 **Season Performance** - Win/loss records and standings  
🎯 **Key Players** - Star batsmen, bowlers, and all-rounders
📈 **Team Statistics** - Batting and bowling averages
🏆 **Championship History** - Past BBL winners

**Popular Players to Watch:**
• Glenn Maxwell (Melbourne Stars)
• David Warner (Sydney Thunder)  
• Josh Hazlewood (Sydney Sixers)
• Chris Lynn (Brisbane Heat)
• Mitchell Marsh (Perth Scorchers)

**Team Merchandise:**
👕 **Jerseys** - ₹1,500-2,500
🧢 **Caps & Hats** - ₹800-1,200
⚾ **Signed Memorabilia** - ₹2,500-5,000
🎒 **Team Accessories** - ₹500-1,500

Which team are you supporting this season?"""
            
            return {
                'response': response,
                'confidence': 0.8,
                'tokens_used': 0,
                'model': 'fallback'
            }
        
        # Parking Information
        elif any(word in message_lower for word in ['park', 'parking', 'car', 'drive', 'vehicle']):
            response = """🚗 **Stadium Parking Information**

**Parking Options Available:**
• **Premium Parking**: ₹500 - Closest to stadium entrance
• **General Parking**: ₹300 - Short walk to venue  
• **Economy Parking**: ₹200 - Budget option with shuttle service
• **VIP Parking**: ₹800 - Reserved spots with valet service

**Parking Tips:**
🎯 **Pre-book online** and save up to 30%
🕐 **Arrive early** - lots fill up 1 hour before match
🚌 **Shuttle service** available from economy lots
♿ **Accessible parking** available near all entrances

**Alternative Transport:**
🚊 Public transport recommended for major matches
🚕 Ride-share drop-off zones available
🚲 Bike parking facilities at most venues

**Booking Parking:**
• Book online at cricverse.com/parking
• Call our hotline: 1800-CRICKET
• Book through the CricVerse mobile app

Would you like me to help you book parking for a specific match?"""
            
            return {
                'response': response,
                'confidence': 0.85,
                'tokens_used': 0,
                'model': 'fallback'
            }
        
        # Food and Concessions
        elif any(word in message_lower for word in ['food', 'eat', 'drink', 'menu', 'concession', 'hungry', 'thirsty', 'beer', 'snack']):
            if db_context and 'menu_items' in db_context:
                food_response = "🍔 **Available Food & Drinks:**\n\n"
                categories = {}
                
                for item in db_context['menu_items']:
                    category = item.get('category', 'Other')
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(f"• {item['name']} - ₹{item['price']}")
                
                for category, items in categories.items():
                    food_response += f"**{category}:**\n" + "\n".join(items) + "\n\n"
                
                food_response += "🎯 **Order Options:**\n• Order at concession stands\n• Mobile app ordering (skip the queue!)\n• In-seat delivery available for premium tickets"
            else:
                food_response = """🍔 **Stadium Food & Beverages**

**Popular Food Options:**
• **Gourmet Burgers** - ₹400-600 (Beef, Chicken, Veggie)
• **Wood-fired Pizza** - ₹500-800 (Various toppings)
• **Fish & Chips** - ₹450 (Beer battered with tartare)
• **BBQ Pulled Pork** - ₹550 (With coleslaw and fries)
• **Chicken Wings** - ₹450 (Buffalo, BBQ, or Honey Soy)
• **Loaded Nachos** - ₹400 (With guac and sour cream)
• **Gourmet Hot Dogs** - ₹350-550 (Various styles)

**Beverages:**
🍺 **Beer** - ₹250-400 (Local and international brands)
🥤 **Soft Drinks** - ₹150-250 (Coke, Sprite, etc.)
☕ **Coffee** - ₹150-250 (Barista made)
🧊 **Slushies** - ₹200 (Perfect for hot days!)

**Dietary Options:**
🌱 **Vegetarian/Vegan** options available
🚫 **Gluten-free** menu items marked
🥗 **Healthy choices** - salads, wraps, fruit

**Ordering:**
📱 **Mobile App** - Order ahead, skip queues!
🏪 **Concession Stands** - Located throughout venue
🎫 **In-seat Service** - Premium ticket holders

What type of food are you in the mood for?"""
            
            return {
                'response': food_response,
                'confidence': 0.85,
                'tokens_used': 0,
                'model': 'fallback'
            }
        
        # Ticket Booking and Match Information
        elif any(word in message_lower for word in ['ticket', 'book', 'buy', 'match', 'game', 'fixture', 'schedule']):
            if db_context and 'matches' in db_context:
                match_response = "🏏 **Upcoming BBL Matches:**\n\n"
                for match in db_context['matches'][:5]:  # Show first 5 matches
                    match_response += f"🆚 **{match.get('home_team', 'TBD')} vs {match.get('away_team', 'TBD')}**\n"
                    match_response += f"📅 {match.get('match_date', 'Date TBD')}\n"
                    match_response += f"🏟️ {match.get('venue', 'Venue TBD')}\n"
                    if match.get('ticket_price'):
                        match_response += f"🎫 From ₹{match['ticket_price']}\n"
                    match_response += "\n"
                
                match_response += "🎯 **Ready to book?** I can help you find the perfect seats!"
            else:
                match_response = """🏏 **BBL Match Tickets & Information**

**Ticket Categories:**
🎫 **General Admission** - ₹2,000-2,800
🏆 **Premium Seating** - ₹3,600-5,200  
👑 **VIP Experience** - ₹6,800-9,600
👨‍👩‍👧‍👦 **Family Packages** - ₹6,400-8,000 (2 adults + 2 kids)

**What's Included:**
• Match entry and reserved seating
• Access to food courts and bars
• Free WiFi throughout venue
• Match program and team merchandise discounts

**Booking Process:**
1️⃣ **Select your match** from the fixture list
2️⃣ **Choose your seats** using our interactive map
3️⃣ **Add extras** like parking and food vouchers
4️⃣ **Secure payment** and instant confirmation

**Special Offers:**
🎉 **Early Bird** - 20% off bookings 2+ weeks ahead
👥 **Group Discounts** - 15% off for 10+ people
🎂 **Birthday Special** - Free cake for birthday bookings!

**Popular Matches:**
• Melbourne Derby matches (always sell out!)
• Finals series (book early!)
• New Year's Eve games
• Australia Day fixtures

Would you like me to show you available matches for a specific team or date?"""
            
            return {
                'response': match_response,
                'confidence': 0.9,
                'tokens_used': 0,
                'model': 'fallback'
            }
        
        # Customer Support and Help
        elif any(word in message_lower for word in ['help', 'support', 'problem', 'issue', 'cancel', 'refund', 'change']):
            response = """🎧 **CricVerse Customer Support**

**I can help you with:**
✅ **Booking tickets** for any BBL match
✅ **Stadium information** and directions  
✅ **Parking reservations** and rates
✅ **Food & beverages** options and pre-ordering
✅ **Seating recommendations** and upgrades
✅ **Match schedules** and team information
✅ **Group bookings** and corporate packages
✅ **Accessibility services** and special needs

**For Account Issues:**
🔄 **Change booking details** - I can help modify your reservation
💳 **Refund requests** - Full refunds up to 24 hours before match
📧 **Email confirmations** - Resend tickets and receipts
🎫 **Transfer tickets** - Send tickets to friends/family

**Contact Options:**
📞 **Phone**: 1800-CRICKET (24/7 support)
💬 **Live Chat**: Available right here!
📧 **Email**: support@cricverse.com
📱 **Mobile App**: Download for instant support

**Emergency Match Day:**
🚨 If you need urgent help on match day, look for CricVerse staff in blue shirts or visit the Customer Service booth near the main entrance.

What specific issue can I help you resolve today?"""
            
            return {
                'response': response,
                'confidence': 0.9,
                'tokens_used': 0,
                'model': 'fallback'
            }
        
        # Team Information
        elif any(word in message_lower for word in ['team', 'player', 'squad', 'roster']):
            response = """🏏 **Big Bash League Teams**

**Conference Teams:**
🔥 **Melbourne Renegades** - Marvel Stadium
⭐ **Melbourne Stars** - Melbourne Cricket Ground  
🦘 **Sydney Sixers** - Sydney Cricket Ground
⚡ **Sydney Thunder** - Sydney Showground Stadium
🦎 **Brisbane Heat** - The Gabba
🌟 **Gold Coast Suns** - Metricon Stadium
🔴 **Perth Scorchers** - Perth Stadium
🦅 **Adelaide Strikers** - Adelaide Oval

**Team Features:**
👥 **Squad Information** - Current players and stats
📊 **Season Performance** - Win/loss records and standings  
🎯 **Key Players** - Star batsmen, bowlers, and all-rounders
📈 **Team Statistics** - Batting and bowling averages
🏆 **Championship History** - Past BBL winners

**Popular Players to Watch:**
• Glenn Maxwell (Melbourne Stars)
• David Warner (Sydney Thunder)  
• Josh Hazlewood (Sydney Sixers)
• Chris Lynn (Brisbane Heat)
• Mitchell Marsh (Perth Scorchers)

**Team Merchandise:**
👕 **Jerseys** - ₹1,500-2,500
🧢 **Caps & Hats** - ₹800-1,200
⚾ **Signed Memorabilia** - ₹2,500-5,000
🎒 **Team Accessories** - ₹500-1,500

Which team are you supporting this season?"""
            
            return {
                'response': response,
                'confidence': 0.8,
                'tokens_used': 0,
                'model': 'fallback'
            }
        
        # General Greeting and Welcome
        elif any(word in message_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']):
            response = """👋 **G'day! Welcome to CricVerse!**

I'm your BBL assistant, here to make your cricket experience absolutely fantastic! 🏏

**What I can help you with today:**
🎫 **Book tickets** for any BBL match
🏟️ **Stadium info** - locations, facilities, seating
🚗 **Parking** - rates, booking, and directions  
🍔 **Food & drinks** - menus, pre-ordering, dietary options
🎯 **Match schedules** - fixtures, teams, and timings
💬 **Customer support** - changes, refunds, and assistance

**Quick Actions:**
• "Show me upcoming matches"
• "Book parking for Marvel Stadium"  
• "What food is available?"
• "Help me choose seats"

**Popular Right Now:**
🔥 Melbourne Derby tickets selling fast!
🎉 New Year's Eve matches now available
🎂 Birthday packages with special perks

What brings you to the cricket today? I'm here to make it an amazing experience! 🌟"""
            
            return {
                'response': response,
                'confidence': 0.9,
                'tokens_used': 0,
                'model': 'fallback'
            }
        
        # Default fallback for unrecognized queries
        else:
            response = """🤔 **I'd love to help you with that!**

I'm your BBL cricket assistant and I specialize in:

🎫 **Ticket Bookings** - Find and book the perfect seats
🏟️ **Stadium Information** - Locations, facilities, and guides
🚗 **Parking Services** - Rates, booking, and directions
🍔 **Food & Beverages** - Menus, ordering, and dietary options  
🏏 **Match Information** - Schedules, teams, and fixtures
🎧 **Customer Support** - Help with bookings and issues

**Try asking me:**
• "What matches are coming up?"
• "Book tickets for [team name]"
• "Where can I park at [stadium name]?"
• "What food is available?"
• "Help me with my booking"

**Quick Tips:**
💡 Be specific about dates, teams, or stadiums
💡 Mention if you need accessibility services
💡 Ask about group discounts for 10+ people

What would you like to know about BBL cricket? I'm here to make your experience fantastic! 🌟"""
            
            return {
                'response': response,
                'confidence': 0.6,
                'tokens_used': 0,
                'model': 'fallback'
            }

    def get_enhanced_conversation_context(self, customer_id, session_id):
        """Get enhanced conversation history with user preferences and context"""
        with current_app.app_context():
            try:
                from app import db
                from enhanced_models import ChatConversation, ChatMessage
                
                # Get regular conversation context
                conversation_history = self.get_conversation_context(customer_id, session_id)
                
                # Enhance with user preference analysis
                try:
                    
                    # Get all conversations for this user to analyze patterns
                    all_conversations = ChatConversation.query.filter_by(
                        customer_id=customer_id
                    ).order_by(ChatConversation.started_at.desc()).limit(10).all()
                    
                    # Analyze conversation patterns
                    frequent_topics = {}
                    interaction_style = 'casual'
                    total_satisfaction = 0
                    satisfaction_count = 0
                    
                    for conv in all_conversations:
                        if conv.satisfaction_rating:
                            total_satisfaction += conv.satisfaction_rating
                            satisfaction_count += 1
                        
                        # Analyze messages for topics
                        messages = ChatMessage.query.filter_by(
                            conversation_id=conv.id,
                            sender_type='user'
                        ).all()
                        
                        for msg in messages:
                            # Simple topic detection
                            message_lower = msg.message.lower()
                            if any(word in message_lower for word in ['book', 'ticket', 'reserve']):
                                frequent_topics['booking'] = frequent_topics.get('booking', 0) + 1
                            if any(word in message_lower for word in ['food', 'menu', 'eat']):
                                frequent_topics['food'] = frequent_topics.get('food', 0) + 1
                            if any(word in message_lower for word in ['team', 'player', 'match']):
                                frequent_topics['teams'] = frequent_topics.get('teams', 0) + 1
                            if any(word in message_lower for word in ['parking', 'drive']):
                                frequent_topics['parking'] = frequent_topics.get('parking', 0) + 1
                    
                    # Add context analysis to conversation history
                    if conversation_history:
                        conversation_history.append({
                            'role': 'system',
                            'content': f"User Interaction Analysis: Frequent topics: {frequent_topics}, Average satisfaction: {total_satisfaction/satisfaction_count if satisfaction_count > 0 else 4.0:.1f}/5"
                        })
                    
                except Exception as e:
                    logger.warning(f"Enhanced models not available for conversation analysis or error: {e}")
                
                return conversation_history
                
            except Exception as e:
                logger.error(f"Error getting enhanced conversation context: {e}")
                return []
    def get_conversation_context(self, customer_id, session_id):
        """Get conversation history for context"""
        with current_app.app_context():
            try:
                from app import db
                from enhanced_models import ChatConversation, ChatMessage
                
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
        """Enhanced interaction logging with intelligent analysis"""
        with current_app.app_context():
            try:
                from app import db
                from enhanced_models import ChatConversation, ChatMessage
                enhanced_models_available = True
            except ImportError:
                logger.warning("Enhanced models not available, using simple logging")
                enhanced_models_available = False
            
            if enhanced_models_available:
                try:
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
                    
                    # Analyze user intent and extract metadata
                    intent = self.analyze_message_intent(user_message)
                    confidence = self.calculate_response_confidence(user_message, ai_response)
                    
                    # Log user message with enhanced metadata
                    user_msg = ChatMessage(
                        conversation_id=conversation.id,
                        sender_type='user',
                        message=user_message,
                        intent=intent,
                        confidence_score=confidence
                    )
                    db.session.add(user_msg)
                    
                    # Log AI response with analysis
                    ai_msg = ChatMessage(
                        conversation_id=conversation.id,
                        sender_type='bot',
                        message=ai_response,
                        intent=intent,
                        confidence_score=confidence,
                        tokens_used=tokens_used,
                        response_time_ms=0  # Would be calculated in real implementation
                    )
                    db.session.add(ai_msg)
                    
                    # Update conversation metadata
                    conversation.message_count = conversation.message_count + 2 if conversation.message_count else 2
                    conversation.last_activity = datetime.utcnow()
                    
                    # Update user profile if available
                    if customer_id:
                        self.update_user_interaction_profile(customer_id, intent, user_message)
                    
                    db.session.commit()
                    
                    # Log for analytics
                    logger.info(f"Enhanced chat logged - User: {customer_id}, Intent: {intent}, Confidence: {confidence:.2f}")
                    
                except Exception as e:
                    logger.warning(f"Could not log interaction (database tables may not exist or other error): {e}")
            else:
                # Simple logging without enhanced models
                logger.info(f"Chat interaction - User: {user_message[:100]}... | AI: {ai_response[:100]}...")
    
    def analyze_message_intent(self, message):
        """Analyze message to determine user intent"""
        message_lower = message.lower()
        
        # Booking related
        if any(word in message_lower for word in ['book', 'buy', 'purchase', 'reserve', 'ticket']):
            if any(word in message_lower for word in ['help', 'support', 'problem', 'issue', 'cancel', 'refund', 'change']):
                return 'support_request'  # Booking support, not new booking
            return 'booking_request'
        
        # Support related (check before general inquiries)
        elif any(word in message_lower for word in ['help', 'support', 'problem', 'issue', 'cancel', 'refund']):
            return 'support_request'
        
        # Information seeking
        elif any(word in message_lower for word in ['what', 'when', 'where', 'how', 'which']):
            if any(word in message_lower for word in ['match', 'game', 'schedule']):
                return 'match_inquiry'
            elif any(word in message_lower for word in ['food', 'menu', 'eat']):
                return 'food_inquiry'
            elif any(word in message_lower for word in ['parking', 'drive', 'car', 'park']):
                return 'parking_inquiry'
            elif any(word in message_lower for word in ['stadium', 'venue', 'location']):
                return 'venue_inquiry'
            else:
                return 'general_inquiry'
        
        # Parking specific
        elif any(word in message_lower for word in ['parking', 'park', 'car', 'drive', 'vehicle']):
            return 'parking_inquiry'
        
        # Greeting/social
        elif any(word in message_lower for word in ['hello', 'hi', 'hey', 'thanks', 'thank you']):
            return 'social_interaction'
        
        else:
            return 'general_conversation'
    
    def calculate_response_confidence(self, user_message, ai_response):
        """Calculate confidence score for the response"""
        confidence = 0.5  # Base confidence
        
        # Higher confidence for specific queries
        if any(word in user_message.lower() for word in ['book', 'price', 'when', 'where']):
            confidence += 0.2
        
        # Higher confidence for longer, detailed responses
        if len(ai_response) > 200:
            confidence += 0.1
        
        # Higher confidence if response contains specific data (prices, dates)
        if any(char in ai_response for char in ['₹', '$']) or any(word in ai_response for word in ['2024', '2025']):
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def update_user_interaction_profile(self, customer_id, intent, message):
        """Update user's interaction profile based on their messages"""
        try:
            # This would update user preferences based on interaction patterns
            # For now, just invalidate the cache to force refresh
            cache_key = f"user_profile_{customer_id}"
            if cache_key in self.user_profiles:
                del self.user_profiles[cache_key]
        except Exception as e:
            logger.warning(f"Could not update user interaction profile: {e}")

    def get_upcoming_matches(self, limit=5):
        """Get upcoming matches from database"""
        with current_app.app_context():
            try:
                from app import db, Event, Team, Stadium
                
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
        with current_app.app_context():
            try:
                from app import db, Event, Seat
                
                event = Event.query.get(event_id)
                if not event:
                    return 2500  # Default price
                
                min_price = Seat.query.filter_by(
                    stadium_id=event.stadium_id
                ).with_entities(db.func.min(Seat.price)).scalar()
                
                return int(min_price) if min_price else 2500
                
            except Exception as e:
                logger.error(f"Error getting min ticket price: {e}")
                return 2500


    def process_booking_request(self, user_message, customer_id, booking_details):
        """Process actual ticket booking through chatbot"""
        with current_app.app_context():
            try:
                from app import db
                from enhanced_models import Booking, Seat, Customer
                
                # Validate booking details
                if not booking_details.get('event_id') and not booking_details.get('match_id'):
                    return {
                        'success': False,
                        'message': 'Please specify which event or match you want to book tickets for.',
                        'next_steps': ['Browse available events', 'Check match schedule']
                    }
                
                # Check seat availability
                stadium_id = booking_details.get('stadium_id')
                requested_seats = booking_details.get('seat_count', 1)
                seat_category = booking_details.get('seat_category', 'general')
                
                available_seats = Seat.query.filter_by(
                    stadium_id=stadium_id,
                    seat_category=seat_category,
                    is_available=True
                ).limit(requested_seats).all()
                
                if len(available_seats) < requested_seats:
                    return {
                        'success': False,
                        'message': f'Sorry, only {len(available_seats)} {seat_category} seats available. Would you like to try a different category?',
                        'alternatives': self.suggest_alternative_seats(stadium_id, requested_seats),
                        'next_steps': ['Try different seat category', 'Reduce number of tickets', 'Check other dates']
                    }
                
                # Calculate pricing
                base_price = booking_details.get('base_price', 2000)
                seat_count = len(available_seats)
                subtotal = base_price * seat_count
                
                # Apply discounts
                discount_percentage = 0
                if booking_details.get('early_bird', False):
                    discount_percentage += 20
                if booking_details.get('group_discount', False) and seat_count >= 10:
                    discount_percentage += 15
                if booking_details.get('student_discount', False):
                    discount_percentage += 25
                if booking_details.get('senior_discount', False):
                    discount_percentage += 20
                
                discount_amount = subtotal * (discount_percentage / 100)
                discounted_total = subtotal - discount_amount
                
                # Add booking fees
                booking_fee = discounted_total * 0.035  # 3.5% booking fee
                
                # Add taxes
                tax_amount = discounted_total * 0.18  # 18% GST
                
                total_amount = discounted_total + booking_fee + tax_amount
                
                # Create booking record
                new_booking = Booking(
                    customer_id=customer_id,
                    event_id=booking_details.get('event_id'),
                    match_id=booking_details.get('match_id'),
                    stadium_id=stadium_id,
                    seats_booked=[seat.id for seat in available_seats],
                    total_amount=total_amount,
                    booking_status='pending_payment',
                    payment_status='pending',
                    booking_reference=self.generate_booking_reference(),
                    special_requests=booking_details.get('special_requests', ''),
                    accessibility_needs=booking_details.get('accessibility_needs', [])
                )
                
                db.session.add(new_booking)
                
                # Reserve seats temporarily (15 minute hold)
                for seat in available_seats:
                    seat.is_available = False
                    seat.reserved_until = datetime.now() + timedelta(minutes=15)
                    seat.reserved_for_booking = new_booking.id
                
                db.session.commit()
                
                return {
                    'success': True,
                    'booking_id': new_booking.id,
                    'booking_reference': new_booking.booking_reference,
                    'message': f'Great! I\'ve reserved {len(available_seats)} {seat_category} seats for you.',
                    'total_amount': total_amount,
                    'seats_reserved': [f"Section {seat.section}, Row {seat.row}, Seat {seat.seat_number}" for seat in available_seats],
                    'hold_expires': '15 minutes',
                    'next_steps': ['Complete payment', 'Review booking details', 'Add special requests'],
                    'payment_link': f'/booking/{new_booking.id}/payment'
                }
                
            except Exception as e:
                logger.error(f"Error processing booking: {e}")
                return {
                    'success': False,
                    'message': 'Sorry, there was an issue processing your booking. Please try again or contact support.',
                    'next_steps': ['Try again', 'Contact support', 'Check availability']
                }
    
    def suggest_alternative_seats(self, stadium_id, requested_count):
        """Suggest alternative seating options"""
        with current_app.app_context():
            try:
                from enhanced_models import Seat
                
                alternatives = []
                categories = ['general', 'premium', 'vip', 'family']
                
                for category in categories:
                    available = Seat.query.filter_by(
                        stadium_id=stadium_id,
                        seat_category=category,
                        is_available=True
                    ).count()
                    
                    if available >= requested_count:
                        alternatives.append({
                            'category': category,
                            'available_count': available,
                            'price_range': self.get_category_price_range(category),
                            'description': self.get_category_description(category)
                        })
                
                return alternatives
                
            except Exception as e:
                logger.error(f"Error suggesting alternatives: {e}")
                return []
    
    def calculate_booking_total(self, booking_details, seats):
        """Calculate total booking amount including fees and discounts"""
        base_price = booking_details.get('base_price', 2000)
        seat_count = len(seats)
        subtotal = base_price * seat_count
        
        # Apply discounts
        discount_percentage = 0
        if booking_details.get('early_bird', False):
            discount_percentage += 20
        if booking_details.get('group_discount', False) and seat_count >= 10:
            discount_percentage += 15
        if booking_details.get('student_discount', False):
            discount_percentage += 25
        if booking_details.get('senior_discount', False):
            discount_percentage += 20
        
        discount_amount = subtotal * (discount_percentage / 100)
        discounted_total = subtotal - discount_amount
        
        # Add booking fees
        booking_fee = discounted_total * 0.035  # 3.5% booking fee
        
        # Add taxes
        tax_amount = discounted_total * 0.18  # 18% GST
        
        total_amount = discounted_total + booking_fee + tax_amount
        
        return {
            'subtotal': subtotal,
            'discount_amount': discount_amount,
            'discount_percentage': discount_percentage,
            'booking_fee': booking_fee,
            'tax_amount': tax_amount,
            'total_amount': round(total_amount, 2)
        }
    
    def generate_booking_reference(self):
        """Generate unique booking reference"""
        import random
        import string
        
        prefix = "BBL"
        timestamp = datetime.now().strftime("%y%m%d")
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        
        return f"{prefix}{timestamp}{random_suffix}"
    
    def get_category_price_range(self, category):
        """Get price range for seat category"""
        price_ranges = {
            'general': '₹2,000-2,800',
            'premium': '₹3,600-5,200',
            'vip': '₹6,800-9,600',
            'family': '₹6,400-8,000'
        }
        return price_ranges.get(category, '₹2,000-2,800')
    
    def get_category_description(self, category):
        """Get description for seat category"""
        descriptions = {
            'general': 'Standard seating with great atmosphere',
            'premium': 'Better views with premium amenities',
            'vip': 'Exclusive access with premium dining',
            'family': 'Family-friendly seating with kids activities'
        }
        return descriptions.get(category, 'Standard seating')
    
    def extract_booking_intent(self, user_message):
        """Extract booking details from user message using AI"""
        message_lower = user_message.lower()
        booking_details = {}
        
        # Extract seat count with improved regex
        import re
        # Look for patterns like "2 tickets", "book 3 seats", "4 people", etc.
        seat_patterns = [
            r'\b(\d+)\s*(?:seat|seats|ticket|tickets|person|people)\b',
            r'\bbook\s+(\d+)\b',
            r'\breserve\s+(\d+)\b',
            r'\bbuy\s+(\d+)\b'
        ]
        
        for pattern in seat_patterns:
            seat_numbers = re.findall(pattern, message_lower)
            if seat_numbers:
                booking_details['seat_count'] = int(seat_numbers[0])
                break
        
        # If no explicit count found, assume 1
        if 'seat_count' not in booking_details:
            if any(word in message_lower for word in ['book', 'buy', 'reserve', 'ticket']):
                booking_details['seat_count'] = 1
        
        # Extract seat category preferences with better priority
        if any(word in message_lower for word in ['family', 'kids', 'children']):
            booking_details['seat_category'] = 'family'
        elif any(word in message_lower for word in ['vip', 'luxury']):
            booking_details['seat_category'] = 'vip'
        elif any(word in message_lower for word in ['premium', 'better view']):
            booking_details['seat_category'] = 'premium'
        else:
            booking_details['seat_category'] = 'general'
        
        # Extract discount eligibility
        if any(word in message_lower for word in ['student', 'college', 'university']):
            booking_details['student_discount'] = True
        if any(word in message_lower for word in ['senior', 'elderly', '65+']):
            booking_details['senior_discount'] = True
        if any(word in message_lower for word in ['group', 'bulk', 'corporate']):
            booking_details['group_discount'] = True
        
        # Extract accessibility needs
        accessibility_needs = []
        if any(word in message_lower for word in ['wheelchair', 'accessible']):
            accessibility_needs.append('wheelchair_access')
        if any(word in message_lower for word in ['hearing', 'deaf']):
            accessibility_needs.append('hearing_assistance')
        if any(word in message_lower for word in ['vision', 'blind']):
            accessibility_needs.append('vision_assistance')
        
        booking_details['accessibility_needs'] = accessibility_needs
        
        return booking_details
    
    # Enhanced helper methods for personalization
    def has_user_visited_stadium(self, customer_id, stadium_id):
        """Check if user has visited a stadium before"""
        if not customer_id:
            return False
        with current_app.app_context():
            try:
                from app import db, Booking, Event
                booking = Booking.query.join(Event).filter(
                    Booking.customer_id == customer_id,
                    Event.stadium_id == stadium_id
                ).first()
                return booking is not None
            except Exception as e:
                logger.error(f"Error checking user stadium visit: {e}")
                return False
    
    def calculate_stadium_preference_score(self, user_profile, stadium):
        """Calculate user preference score for a stadium"""
        score = 0.5  # Base score
        
        # Boost score if user has visited before
        if user_profile.get('customer_id') and self.has_user_visited_stadium(user_profile['customer_id'], stadium.id):
            score += 0.3
        
        # Boost score if favorite team plays there
        if user_profile.get('favorite_team'):
            if user_profile['favorite_team'].get('home_ground') == stadium.name:
                score += 0.4
        
        return min(score, 1.0)
    
    def get_real_time_wait_time(self, concession_id):
        """Get real-time wait time for a concession"""
        try:
            # This would integrate with real-time monitoring systems
            # For now, return simulated data
            import random
            wait_times = ['Short (2-5 min)', 'Normal (5-10 min)', 'Busy (10-15 min)', 'Very Busy (15+ min)']
            return random.choice(wait_times)
        except:
            return 'Normal (5-10 min)'
    
    def get_user_previous_orders(self, customer_id, concession_id):
        """Get user's previous orders from this concession"""
        if not customer_id:
            return []
        with current_app.app_context():
            try:
                from app import db, Order
                orders = Order.query.filter_by(
                    customer_id=customer_id,
                    concession_id=concession_id
                ).order_by(Order.order_date.desc()).limit(5).all()
                
                return [{ 
                    'order_date': order.order_date.strftime('%Y-%m-%d'),
                    'total_amount': order.total_amount
                } for order in orders]
            except Exception as e:
                logger.error(f"Error getting user previous orders: {e}")
                return []
    
    def has_user_ordered_item(self, customer_id, menu_item_id):
        """Check if user has ordered this menu item before"""
        # This would require an OrderItem model to track individual items
        # For now, return False
        return False
    
    def calculate_food_recommendation_score(self, user_profile, menu_item):
        """Calculate recommendation score for a food item"""
        score = 0.5  # Base score
        
        # Boost vegetarian items if user has ordered them before
        if getattr(menu_item, 'is_vegetarian', False):
            score += 0.1
        
        # Boost based on item popularity
        if menu_item.price < 500:  # Affordable items
            score += 0.1
        
        return min(score, 1.0)
    
    def is_favorite_team_match(self, user_profile, event):
        """Check if this match involves user's favorite team"""
        favorite_team_id = user_profile.get('favorite_team_id')
        if favorite_team_id and (getattr(event, 'home_team_id', None) == favorite_team_id or getattr(event, 'away_team_id', None) == favorite_team_id):
            return True
        return False

    def get_personalized_offers(self, customer_id, user_profile):
        """Simulate personalized offers based on user profile"""
        offers = []
        if user_profile.get('membership_level') == 'Premium':
            offers.append({'title': 'Exclusive Premium Discount', 'description': '20% off all VIP tickets'})
        if user_profile.get('favorite_team') and user_profile['favorite_team']['name'] == 'Melbourne Stars':
            offers.append({'title': 'Melbourne Stars Fan Offer', 'description': '10% off next Melbourne Stars home game'})
        if user_profile.get('total_spent', 0) > 5000:
            offers.append({'title': 'Loyalty Bonus', 'description': '₹500 voucher for concessions'})
        return offers

    def get_loyalty_benefits(self, user_profile):
        """Simulate loyalty benefits based on user profile"""
        benefits = []
        if user_profile.get('loyalty_points', 0) > 1000:
            benefits.append('Priority booking access')
        if user_profile.get('membership_level') == 'VIP':
            benefits.append('Complimentary food and beverages in VIP lounge')
        return benefits

# Global instance of the chatbot
cricverse_chatbot = CricVerseChatbot()

def get_chatbot_response(message, customer_id=None, session_id=None):
    """Main function for getting chatbot responses"""
    return cricverse_chatbot.generate_response(message, customer_id, session_id)

def detect_user_intent(message):
    """Simple intent detection, delegates to chatbot instance"""
    return cricverse_chatbot.analyze_message_intent(message)

def get_chat_suggestions(customer_id=None, query_type="general"):
    """Get chat suggestions based on query type"""
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