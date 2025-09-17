#!/usr/bin/env python3
"""
Minimal Flask app for testing the new CricVerse features
This allows testing the new API endpoints without complex dependencies
"""

from flask import Flask, request, jsonify
import json
import logging
from datetime import datetime, timedelta
import secrets

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-secret-key'

# Mock data for testing
mock_tickets = {
    1: {'id': 1, 'customer_id': 1, 'event_id': 1, 'seat_id': 1, 'status': 'Booked'},
    2: {'id': 2, 'customer_id': 1, 'event_id': 2, 'seat_id': 2, 'status': 'Booked'},
}

mock_events = {
    1: {'id': 1, 'name': 'Melbourne Stars vs Sydney Sixers', 'date': '2024-12-25', 'stadium_id': 1},
    2: {'id': 2, 'name': 'Perth Scorchers vs Brisbane Heat', 'date': '2024-12-26', 'stadium_id': 2},
}

mock_transfers = {}
mock_marketplace = {}
mock_season_tickets = {}
mock_accessibility = {}

# Mock current user
current_user = {'id': 1, 'email': 'test@cricverse.com', 'name': 'Test User'}

@app.route('/')
def index():
    return jsonify({
        'message': 'CricVerse New Features Test API',
        'features': [
            'Ticket Transfer',
            'Resale Marketplace', 
            'Season Tickets',
            'Accessibility Accommodations'
        ],
        'endpoints': [
            'POST /api/ticket/transfer',
            'POST /api/ticket/transfer/<code>/accept',
            'POST /api/marketplace/list-ticket',
            'GET /api/marketplace/search',
            'POST /api/season-ticket/purchase',
            'GET /api/season-ticket/<id>/matches',
            'POST /api/accessibility/register',
            'POST /api/accessibility/book',
            'GET /api/accessibility/status/<id>'
        ]
    })

# ===============================
# TICKET TRANSFER ENDPOINTS
# ===============================

@app.route('/api/ticket/transfer', methods=['POST'])
def initiate_ticket_transfer():
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'ticket_id' not in data or 'to_email' not in data:
            return jsonify({'error': 'Missing required fields: ticket_id, to_email'}), 400
            
        ticket_id = data['ticket_id']
        
        # Check if ticket exists and belongs to user
        if ticket_id not in mock_tickets:
            return jsonify({'error': 'Ticket not found'}), 404
            
        ticket = mock_tickets[ticket_id]
        if ticket['customer_id'] != current_user['id']:
            return jsonify({'error': 'You do not own this ticket'}), 403
            
        # Generate transfer code
        transfer_code = secrets.token_urlsafe(16)
        verification_code = f"{secrets.randbelow(999999):06d}"
        
        # Store transfer
        mock_transfers[transfer_code] = {
            'ticket_id': ticket_id,
            'from_customer_id': current_user['id'],
            'to_email': data['to_email'],
            'transfer_fee': data.get('transfer_fee', 0),
            'verification_code': verification_code,
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(hours=48)).isoformat()
        }
        
        logger.info(f"✅ Transfer initiated: {transfer_code} for ticket {ticket_id}")
        
        return jsonify({
            'success': True,
            'transfer_code': transfer_code,
            'verification_code': verification_code,  # Normally sent via email
            'message': 'Transfer initiated successfully'
        })
        
    except Exception as e:
        logger.error(f"❌ Transfer initiation failed: {e}")
        return jsonify({'error': 'Transfer initiation failed'}), 500

@app.route('/api/ticket/transfer/<transfer_code>/accept', methods=['POST']) 
def accept_ticket_transfer(transfer_code):
    try:
        # Find transfer
        if transfer_code not in mock_transfers:
            return jsonify({'error': 'Invalid transfer code'}), 404
            
        transfer = mock_transfers[transfer_code]
        
        if transfer['status'] != 'pending':
            return jsonify({'error': 'Transfer is no longer available'}), 400
            
        # Check expiration
        expires_at = datetime.fromisoformat(transfer['expires_at'])
        if expires_at < datetime.utcnow():
            transfer['status'] = 'expired'
            return jsonify({'error': 'Transfer has expired'}), 400
            
        # Verify code if provided
        data = request.get_json() or {}
        if 'verification_code' in data:
            if data['verification_code'] != transfer['verification_code']:
                return jsonify({'error': 'Invalid verification code'}), 400
                
        # Complete transfer (update ticket ownership)
        ticket_id = transfer['ticket_id']
        mock_tickets[ticket_id]['customer_id'] = 999  # New owner ID
        
        transfer['status'] = 'accepted'
        transfer['completed_at'] = datetime.utcnow().isoformat()
        
        logger.info(f"✅ Transfer completed: {transfer_code}")
        
        return jsonify({
            'success': True,
            'message': 'Ticket transfer completed successfully',
            'ticket_id': ticket_id
        })
        
    except Exception as e:
        logger.error(f"❌ Transfer acceptance failed: {e}")
        return jsonify({'error': 'Transfer acceptance failed'}), 500

# ===============================
# MARKETPLACE ENDPOINTS  
# ===============================

@app.route('/api/marketplace/list-ticket', methods=['POST'])
def list_ticket_for_resale():
    try:
        data = request.get_json()
        
        if not data or 'ticket_id' not in data or 'listing_price' not in data:
            return jsonify({'error': 'Missing required fields: ticket_id, listing_price'}), 400
            
        ticket_id = data['ticket_id']
        
        # Validate ticket ownership
        if ticket_id not in mock_tickets:
            return jsonify({'error': 'Ticket not found'}), 404
            
        ticket = mock_tickets[ticket_id]
        if ticket['customer_id'] != current_user['id']:
            return jsonify({'error': 'You do not own this ticket'}), 403
            
        # Mock price validation (max 150% of original)
        original_price = 100.0  # Mock original price
        max_price = original_price * 1.5
        listing_price = data['listing_price']
        
        if listing_price > max_price:
            return jsonify({'error': f'Listing price cannot exceed ${max_price:.2f}'}), 400
            
        # Calculate fees
        platform_fee = listing_price * 0.05
        seller_fee = listing_price * 0.03
        net_amount = listing_price - platform_fee - seller_fee
        
        # Create listing
        listing_id = len(mock_marketplace) + 1
        mock_marketplace[listing_id] = {
            'id': listing_id,
            'ticket_id': ticket_id,
            'seller_id': current_user['id'],
            'original_price': original_price,
            'listing_price': listing_price,
            'platform_fee': platform_fee,
            'seller_fee': seller_fee,
            'description': data.get('description', ''),
            'is_negotiable': data.get('is_negotiable', False),
            'status': 'active',
            'listed_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Ticket listed: {listing_id} for ${listing_price}")
        
        return jsonify({
            'success': True,
            'listing_id': listing_id,
            'platform_fee': platform_fee,
            'seller_fee': seller_fee,
            'net_amount': net_amount,
            'message': 'Ticket listed successfully'
        })
        
    except Exception as e:
        logger.error(f"❌ Marketplace listing failed: {e}")
        return jsonify({'error': 'Listing failed'}), 500

@app.route('/api/marketplace/search', methods=['GET'])
def search_marketplace():
    try:
        # Get search parameters
        max_price = request.args.get('max_price', type=float)
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Filter listings
        results = []
        for listing in mock_marketplace.values():
            if listing['status'] != 'active':
                continue
                
            if max_price and listing['listing_price'] > max_price:
                continue
                
            # Mock event and stadium data
            event = mock_events.get(1, {})
            
            results.append({
                'listing_id': listing['id'],
                'ticket_id': listing['ticket_id'],
                'event': {
                    'id': 1,
                    'name': event.get('name', 'Mock Event'),
                    'date': event.get('date', '2024-12-25'),
                    'start_time': '19:30'
                },
                'stadium': {
                    'id': 1,
                    'name': 'Melbourne Cricket Ground',
                    'location': 'Melbourne, VIC'
                },
                'seat': {
                    'section': 'Premium',
                    'row': 'A',
                    'number': '10',
                    'type': 'Premium'
                },
                'pricing': {
                    'original_price': listing['original_price'],
                    'listing_price': listing['listing_price'],
                    'savings': max(0, listing['original_price'] - listing['listing_price'])
                },
                'description': listing['description'],
                'is_negotiable': listing['is_negotiable'],
                'listed_at': listing['listed_at']
            })
            
        # Simple pagination
        start = (page - 1) * per_page
        end = start + per_page
        paginated_results = results[start:end]
        
        logger.info(f"✅ Marketplace search: {len(paginated_results)} results")
        
        return jsonify({
            'success': True,
            'listings': paginated_results,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': len(results),
                'pages': (len(results) + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Marketplace search failed: {e}")
        return jsonify({'error': 'Search failed'}), 500

# ===============================
# SEASON TICKET ENDPOINTS
# ===============================

@app.route('/api/season-ticket/purchase', methods=['POST'])
def purchase_season_ticket():
    try:
        data = request.get_json()
        
        required_fields = ['stadium_id', 'seat_id', 'season_name']
        for field in required_fields:
            if not data or field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
                
        # Mock calculations
        total_matches = data.get('total_matches', 10)
        price_per_match = 100.0  # Mock price
        total_price = price_per_match * total_matches * 0.85  # 15% discount
        savings = (price_per_match * total_matches) - total_price
        
        # Create season ticket
        season_ticket_id = len(mock_season_tickets) + 1
        mock_season_tickets[season_ticket_id] = {
            'id': season_ticket_id,
            'customer_id': current_user['id'],
            'stadium_id': data['stadium_id'],
            'seat_id': data['seat_id'],
            'season_name': data['season_name'],
            'total_matches': total_matches,
            'price_per_match': price_per_match,
            'total_price': total_price,
            'status': 'active',
            'purchased_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Season ticket purchased: {season_ticket_id}")
        
        return jsonify({
            'success': True,
            'season_ticket_id': season_ticket_id,
            'total_price': total_price,
            'savings': savings,
            'matches_included': total_matches,
            'message': 'Season ticket purchased successfully'
        })
        
    except Exception as e:
        logger.error(f"❌ Season ticket purchase failed: {e}")
        return jsonify({'error': 'Purchase failed'}), 500

@app.route('/api/season-ticket/<int:season_ticket_id>/matches', methods=['GET'])
def get_season_ticket_matches(season_ticket_id):
    try:
        if season_ticket_id not in mock_season_tickets:
            return jsonify({'error': 'Season ticket not found'}), 404
            
        season_ticket = mock_season_tickets[season_ticket_id]
        
        if season_ticket['customer_id'] != current_user['id']:
            return jsonify({'error': 'Access denied'}), 403
            
        # Mock matches
        matches = []
        for i in range(season_ticket['total_matches']):
            matches.append({
                'match_id': i + 1,
                'event': {
                    'id': i + 1,
                    'name': f'Match {i + 1}',
                    'date': f'2024-{(i % 12) + 1:02d}-{((i % 28) + 1):02d}',
                    'start_time': '19:30'
                },
                'status': {
                    'is_used': i < 2,  # Mock: first 2 matches used
                    'used_at': datetime.utcnow().isoformat() if i < 2 else None,
                    'is_transferred': False,
                    'transferred_at': None,
                    'transfer_price': 0
                }
            })
            
        logger.info(f"✅ Season ticket matches retrieved: {season_ticket_id}")
        
        return jsonify({
            'success': True,
            'season_ticket': {
                'id': season_ticket['id'],
                'season_name': season_ticket['season_name'],
                'matches_used': 2,  # Mock
                'matches_transferred': 0,
                'transfer_limit': 5
            },
            'matches': matches
        })
        
    except Exception as e:
        logger.error(f"❌ Season ticket matches retrieval failed: {e}")
        return jsonify({'error': 'Failed to retrieve matches'}), 500

# ===============================
# ACCESSIBILITY ENDPOINTS
# ===============================

@app.route('/api/accessibility/register', methods=['POST'])
def register_accessibility_needs():
    try:
        data = request.get_json()
        
        if not data or 'accommodation_type' not in data:
            return jsonify({'error': 'accommodation_type is required'}), 400
            
        # Create or update accessibility record
        accommodation_id = 1  # Mock ID
        mock_accessibility[current_user['id']] = {
            'id': accommodation_id,
            'customer_id': current_user['id'],
            'accommodation_type': data['accommodation_type'],
            'description': data.get('description', ''),
            'severity_level': data.get('severity_level', 'moderate'),
            'requires_wheelchair_access': data.get('requires_wheelchair_access', False),
            'requires_companion_seat': data.get('requires_companion_seat', False),
            'is_verified': False,
            'created_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Accessibility needs registered: {accommodation_id}")
        
        return jsonify({
            'success': True,
            'accommodation_id': accommodation_id,
            'message': 'Accessibility needs registered successfully',
            'verification_required': True
        })
        
    except Exception as e:
        logger.error(f"❌ Accessibility registration failed: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/accessibility/book', methods=['POST'])
def book_with_accessibility():
    try:
        data = request.get_json()
        
        required_fields = ['event_id', 'seat_ids', 'requested_accommodations']
        for field in required_fields:
            if not data or field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
                
        # Check if user has accessibility profile
        if current_user['id'] not in mock_accessibility:
            return jsonify({'error': 'Please register accessibility needs first'}), 400
            
        # Mock booking creation
        booking_id = 100 + len(mock_accessibility)
        accessibility_booking_id = 200 + len(mock_accessibility)
        total_amount = len(data['seat_ids']) * 100.0  # Mock price
        
        logger.info(f"✅ Accessibility booking created: {booking_id}")
        
        return jsonify({
            'success': True,
            'booking_id': booking_id,
            'accessibility_booking_id': accessibility_booking_id,
            'total_amount': total_amount,
            'message': 'Booking created with accessibility accommodations',
            'next_steps': 'Staff will review accommodations within 24 hours'
        })
        
    except Exception as e:
        logger.error(f"❌ Accessibility booking failed: {e}")
        return jsonify({'error': 'Booking failed'}), 500

@app.route('/api/accessibility/status/<int:booking_id>', methods=['GET'])
def get_accessibility_status(booking_id):
    try:
        # Mock status response
        return jsonify({
            'success': True,
            'booking_id': booking_id,
            'accommodation_status': 'requested',
            'requested_accommodations': ['wheelchair_access', 'companion_seat'],
            'provided_accommodations': [],
            'staff_notes': 'Accommodation request under review',
            'special_instructions': 'Electric wheelchair access required',
            'fulfilled_at': None,
            'accommodation_type': 'wheelchair'
        })
        
    except Exception as e:
        logger.error(f"❌ Accessibility status retrieval failed: {e}")
        return jsonify({'error': 'Failed to retrieve status'}), 500

if __name__ == '__main__':
    print("🏏 Starting CricVerse New Features Test API...")
    print("🚀 Server starting on http://localhost:5001")
    print("📚 Visit http://localhost:5001 for API documentation")
    
    app.run(debug=True, host='0.0.0.0', port=5001)