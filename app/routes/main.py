from flask import Blueprint, render_template, redirect, url_for, current_app, send_from_directory, jsonify, request
import os
from pathlib import Path
from flask_login import current_user
from app.models.stadium import Stadium, Concession, Parking, MenuItem
from app.models.match import Event, Team, Player
from app.models.booking import Ticket, Seat

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Optionally show featured teams/events on the homepage
    teams = Team.query.limit(8).all()
    events = Event.query.order_by(Event.event_date.asc()).limit(10).all()
    stadiums = Stadium.query.limit(8).all()
    return render_template('index.html', teams=teams, events=events, stadiums=stadiums)

@main_bp.route('/events')
def events():
    events = Event.query.order_by(Event.event_date.asc()).all()
    return render_template('events.html', events=events)

@main_bp.route('/event/<int:event_id>')
def event_detail(event_id: int):
    # Placeholder: redirect to events list until a dedicated detail page/template is implemented
    return redirect(url_for('main.events'))

@main_bp.route('/teams')
def teams():
    # Transform ORM Team into dicts expected by templates (name, logo_url, etc.)
    orm_teams = Team.query.order_by(Team.team_name.asc()).all()
    teams = []
    for t in orm_teams:
        teams.append({
            'id': t.id,
            'name': getattr(t, 'team_name', None),
            'logo_url': getattr(t, 'team_logo', None),
            'city': getattr(t, 'home_city', None),
            'about': None,
            'founding_year': None,
            'championships_won': None,
            'home_ground': getattr(t, 'home_ground', None),
            'color1': '#0ea5e9',
            'color2': '#1e293b',
        })
    return render_template('teams.html', teams=teams)

@main_bp.route('/team/<int:team_id>')
def team_detail(team_id: int):
    # Placeholder: redirect to teams list until a dedicated detail page/template is implemented
    return redirect(url_for('main.teams'))

@main_bp.route('/stadiums')
def stadiums():
    stadiums = Stadium.query.order_by(Stadium.name.asc()).all()
    return render_template('stadiums.html', stadiums=stadiums)

@main_bp.route('/stadium/<int:stadium_id>')
def stadium_detail(stadium_id: int):
    # Placeholder: redirect to stadiums list until a dedicated detail page/template is implemented
    return redirect(url_for('main.stadiums'))

@main_bp.route('/players')
def players():
    players = Player.query.order_by(Player.player_name.asc()).all()
    return render_template('players.html', players=players)

@main_bp.route('/concessions')
def concessions():
    # Filters
    selected_stadium_id = request.args.get('stadium_id', type=int)
    selected_category = request.args.get('category', type=str)

    q = Concession.query
    if selected_stadium_id:
        q = q.filter(Concession.stadium_id == selected_stadium_id)
    if selected_category:
        q = q.filter(Concession.category == selected_category)

    # Preload relationships for template grouping
    concessions_list = q.join(Stadium).all()

    # Build stadiums and categories for filters
    stadiums = Stadium.query.order_by(Stadium.name.asc()).all()
    cat_rows = Concession.query.with_entities(Concession.category).distinct().all()
    categories = sorted([c[0] for c in cat_rows if c and c[0]])

    return render_template(
        'concessions.html',
        concessions=concessions_list,
        stadiums=stadiums,
        categories=categories,
        selected_stadium_id=selected_stadium_id,
        selected_category=selected_category,
    )

@main_bp.route('/concessions/<int:concession_id>/order')
def order_concession(concession_id: int):
    # Placeholder action: enforce login before ordering, then route back
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    return redirect(url_for('main.concessions'))

@main_bp.route('/parking')
def parking():
    # Provide both stadiums and parking_zones as the template expects
    stadiums = Stadium.query.order_by(Stadium.name.asc()).all()
    parking_zones = Parking.query.all()
    return render_template('parking.html', stadiums=stadiums, parking_zones=parking_zones)

@main_bp.route('/parking/book/<int:stadium_id>')
def book_parking(stadium_id: int):
    # Placeholder: enforce login and redirect back for now
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    return redirect(url_for('main.parking'))

@main_bp.route('/tickets')
def tickets():
    tickets = Ticket.query.order_by(Ticket.created_at.desc()).limit(100).all()
    return render_template('tickets.html', tickets=tickets)

@main_bp.route('/seats')
def seats():
    seats = Seat.query.limit(500).all()
    return render_template('seats.html', seats=seats)

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

@main_bp.route('/about')
def about():
    return render_template('about.html')

# -------------------- Utility & API helpers --------------------
@main_bp.route('/logos/<slug>.png')
def team_logo(slug: str):
    """Serve team logos from static with smart fallbacks.
    Expected slugs: thunder, heat, renegades, strikers, hurricanes, stars, scorchers, sixers
    """
    # Known mappings to actual filenames in static/img/teams when available
    mapping = {
        'stars': 'Melbourne_Stars_logo.png',
        'sixers': 'Sydney_Sixers_logo.svg.png',
        'scorchers': 'Perth Scorchers.png',
        'heat': 'Brisbane Heat.png',
        'hurricanes': 'Hobart Hurricanes.png',
        'strikers': 'Adelaide Striker.png',
        'renegades': 'Melbourne Renegades.png',
        'thunder': 'Sydney Thunder.png',
    }
    teams_dir = Path(current_app.static_folder) / 'img' / 'teams'
    candidates = []
    # 1) mapped filename if present
    if slug in mapping:
        candidates.append(mapping[slug])
    # 2) common variants
    candidates += [
        f"{slug}.png",
        f"{slug}.svg.png",
        f"{slug.capitalize()}.png",
        f"{slug.title()}.png",
    ]
    for name in candidates:
        file_path = teams_dir / name
        if file_path.exists():
            return send_from_directory(teams_dir, name)
    # Fallback placeholder
    placeholder = teams_dir / 'placeholder_team.png'
    if placeholder.exists():
        return send_from_directory(teams_dir, 'placeholder_team.png')
    # Last resort: 404
    return ("", 404)

@main_bp.route('/api/realtime/stats')
def realtime_stats():
    """Lightweight stats endpoint to avoid 404s in UI probes."""
    return jsonify({
        'status': 'ok',
        'clients': None,  # could be wired to SocketIO metrics later
        'uptime': None,
        'ts': request.headers.get('Date')
    })
