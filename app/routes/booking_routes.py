from flask import Blueprint, request, jsonify
from app.services.booking_service import book_seat

bp = Blueprint('booking', __name__, url_prefix='/api/booking')

@bp.route('/book-seat', methods=['POST'])
def book_seat_route():
    """API endpoint for booking a seat."""
    try:
        data = request.get_json()
        
        # Extract required parameters
        seat_id = data.get('seat_id')
        event_id = data.get('event_id')
        customer_id = data.get('customer_id')
        
        # Validate required parameters
        if not all([seat_id, event_id, customer_id]):
            return jsonify({
                'success': False,
                'message': 'Missing required parameters: seat_id, event_id, and customer_id are required'
            }), 400
        
        # Call the booking service
        result = book_seat(seat_id, event_id, customer_id)
        
        # Return the result
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500