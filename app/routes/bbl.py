from flask import Blueprint, jsonify, current_app
import asyncio

bbl_bp = Blueprint('bbl', __name__, url_prefix='/api/bbl')

@bbl_bp.route('/live-scores', methods=['GET'])
def live_scores():
    bbl_service = current_app.bbl_data_service

@bbl_bp.route('/standings', methods=['GET'])
def standings():
    bbl_service = current_app.bbl_data_service
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
    bbl_service = current_app.bbl_data_service
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
    bbl_service = current_app.bbl_data_service
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
