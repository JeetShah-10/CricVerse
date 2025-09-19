from flask import Blueprint, request, jsonify, session
import uuid
from app.services.chatbot_service import get_chatbot_response, detect_user_intent, get_chat_suggestions

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')

@chat_bp.route('', methods=['POST'])
def send_message():
    user_message = request.json.get('message')
    customer_id = session.get('customer_id') # Assuming customer_id is stored in session
    session_id = session.get('chat_session_id')

    if not session_id:
        session_id = str(uuid.uuid4())
        session['chat_session_id'] = session_id

    if not user_message:
        return jsonify({'error': 'Message is required'}), 400

    response_data = get_chatbot_response(user_message, customer_id, session_id)
    return jsonify(response_data)

@chat_bp.route('/suggestions', methods=['GET'])
def get_suggestions():
    customer_id = session.get('customer_id')
    query_type = request.args.get('query_type', 'general')
    suggestions = get_chat_suggestions(customer_id, query_type)
    return jsonify({'suggestions': suggestions})