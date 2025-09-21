from flask import Blueprint, jsonify
import asyncio
from supabase_bbl_integration import bbl_data_service

bbl_bp = Blueprint('bbl', __name__, url_prefix='/api/bbl')

# Use the global BBL service instance
bbl_service = bbl_data_service

@bbl_bp.route('/live-scores', methods=['GET'])
def live_scores():
    if not bbl_service:
        return jsonify({
            'success': False,
            'error': 'Supabase BBL service not available. Please check your Supabase configuration.'
        }), 503
    
    try:
        matches = asyncio.run(bbl_service.get_live_scores())
        return jsonify({
            'success': True,
            'matches': matches
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to fetch live scores from Supabase: {str(e)}'
        }), 500

@bbl_bp.route('/standings', methods=['GET'])
def standings():
    if not bbl_service:
        return jsonify({
            'success': False,
            'error': 'Supabase BBL service not available. Please check your Supabase configuration.'
        }), 503
    
    try:
        standings = asyncio.run(bbl_service.get_standings())
        return jsonify({
            'success': True,
            'standings': standings
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to fetch standings from Supabase: {str(e)}'
        }), 500

@bbl_bp.route('/teams', methods=['GET'])
def teams():
    if not bbl_service:
        return jsonify({
            'success': False,
            'error': 'Supabase BBL service not available. Please check your Supabase configuration.'
        }), 503
    
    try:
        teams = asyncio.run(bbl_service.get_teams())
        return jsonify({
            'success': True,
            'teams': teams
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to fetch teams from Supabase: {str(e)}'
        }), 500

@bbl_bp.route('/top-performers', methods=['GET'])
def top_performers():
    if not bbl_service:
        return jsonify({
            'success': False,
            'error': 'Supabase BBL service not available. Please check your Supabase configuration.'
        }), 503
    
    try:
        performers = asyncio.run(bbl_service.get_top_performers())
        return jsonify({
            'success': True,
            'performers': performers
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to fetch top performers from Supabase: {str(e)}'
        }), 500
