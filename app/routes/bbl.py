from flask import Blueprint, jsonify
import asyncio
from supabase_bbl_integration import BBLDataService

bbl_bp = Blueprint('bbl', __name__, url_prefix='/api/bbl')

# We will reuse a single service instance
_service = BBLDataService()

@bbl_bp.route('/live-scores', methods=['GET'])
def live_scores():
    try:
        matches = asyncio.run(_service.get_live_scores())
        return jsonify({
            'success': True,
            'matches': matches
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bbl_bp.route('/standings', methods=['GET'])
def standings():
    try:
        table = asyncio.run(_service.get_standings())
        return jsonify({
            'success': True,
            'standings': table
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bbl_bp.route('/top-performers', methods=['GET'])
def top_performers():
    try:
        data = asyncio.run(_service.get_top_performers())
        return jsonify({
            'success': True,
            **data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bbl_bp.route('/teams', methods=['GET'])
def teams():
    try:
        items = asyncio.run(_service.get_teams())
        return jsonify({
            'success': True,
            'teams': items
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
