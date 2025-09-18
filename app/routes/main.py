from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/events')
def events():
    return render_template('events.html')

@main_bp.route('/teams')
def teams():
    return render_template('teams.html')

@main_bp.route('/stadiums')
def stadiums():
    return render_template('stadiums.html')

@main_bp.route('/players')
def players():
    return render_template('players.html')

@main_bp.route('/ai_options')
def ai_options():
    return render_template('ai_options.html')

@main_bp.route('/chat')
def chat_interface():
    return render_template('chat.html')

@main_bp.route('/ai_assistant')
def ai_assistant():
    return render_template('ai_assistant.html')

@main_bp.route('/realtime')
def realtime_demo():
    return render_template('realtime.html')

@main_bp.route('/stadium_owner')
def stadium_owner_dashboard():
    return render_template('stadium_owner_dashboard.html')
