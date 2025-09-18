from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from app.services import booking_service

bp = Blueprint('booking', __name__, url_prefix='/api/booking')

@bp.route('/book-seat', methods=['POST'])
def book_seat_route():
    """API endpoint for booking a seat."""
    try:
        data = request.get_json()
        seat_id = data.get('seat_id')
        event_id = data.get('event_id')
        # Use current_user instead of passing customer_id in request
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
        
        if not all([seat_id, event_id]):
            return jsonify({'success': False, 'message': 'Missing seat_id or event_id'}), 400
        
        result = booking_service.book_seat(seat_id, event_id, current_user.id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500

@bp.route('/create-order', methods=['POST'])
@login_required
def create_order_route():
    """API endpoint for creating a payment order."""
    data = request.get_json()
    event_id = data.get('event_id')
    seat_ids = data.get('seat_ids')

    if not all([event_id, seat_ids]):
        return jsonify({'success': False, 'message': 'Missing event_id or seat_ids.'}), 400

    result = booking_service.create_payment_order(
        event_id=event_id,
        seat_ids=seat_ids,
        customer_id=current_user.id
    )

    return jsonify(result)


@bp.route('/capture-order', methods=['POST'])
@login_required
def capture_order_route():
    """API endpoint for capturing a payment and creating a booking."""
    data = request.get_json()
    order_id = data.get('orderID')

    if not order_id:
        return jsonify({'success': False, 'message': 'Missing orderID.'}), 400

    result = booking_service.capture_payment_and_create_booking(
        order_id=order_id,
        customer_id=current_user.id
    )

    return jsonify(result)
