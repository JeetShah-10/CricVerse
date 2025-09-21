"""
Live Cricket Routes for CricVerse
Routes for live cricket scoring like Cricbuzz
Simple live scores, overs, runs, and wickets
Big Bash League Cricket Platform
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
import logging
from datetime import datetime, date
from app.services.live_cricket_service import live_cricket_service
from app.services.supabase_service import supabase_service

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
live_cricket_bp = Blueprint('live_cricket', __name__, url_prefix='/live')

@live_cricket_bp.route('/')
def live_matches():
    """Display all live matches"""
    try:
        # Get all live matches
        live_matches = live_cricket_service.get_all_live_matches()
        
        # Get upcoming matches
        upcoming_events = supabase_service.get_upcoming_events(limit=10)
        
        return render_template('live_cricket/live_matches.html',
                             live_matches=live_matches,
                             upcoming_events=upcoming_events)
    
    except Exception as e:
        logger.error(f"Error loading live matches page: {str(e)}")
        flash('Error loading live matches', 'error')
        return render_template('live_cricket/live_matches.html',
                             live_matches=[],
                             upcoming_events=[],
                             error=str(e))

@live_cricket_bp.route('/match/<int:match_id>')
def match_details(match_id):
    """Display detailed view of a specific match"""
    try:
        # Get match summary
        match_summary = live_cricket_service.get_match_summary(match_id)
        
        if 'error' in match_summary:
            flash('Match not found', 'error')
            return redirect(url_for('live_cricket.live_matches'))
        
        return render_template('live_cricket/match_details.html',
                             match=match_summary)
    
    except Exception as e:
        logger.error(f"Error loading match details for {match_id}: {str(e)}")
        flash('Error loading match details', 'error')
        return redirect(url_for('live_cricket.live_matches'))

@live_cricket_bp.route('/api/matches/live')
def api_live_matches():
    """API endpoint for live matches"""
    try:
        live_matches = live_cricket_service.get_all_live_matches()
        return jsonify({
            'success': True,
            'matches': live_matches,
            'count': len(live_matches),
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting live matches API: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@live_cricket_bp.route('/api/match/<int:match_id>/status')
def api_match_status(match_id):
    """API endpoint for match status"""
    try:
        match_status = live_cricket_service.get_live_match_status(match_id)
        
        if 'error' in match_status:
            return jsonify({
                'success': False,
                'error': match_status['error']
            }), 404
        
        return jsonify({
            'success': True,
            'match': match_status,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting match status API for {match_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# Admin routes for match management
@live_cricket_bp.route('/admin')
@login_required
def admin_dashboard():
    """Admin dashboard for managing live matches"""
    try:
        # Check if user has admin access
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('live_cricket.live_matches'))
        
        # Get all matches
        from app.models import Match
        all_matches = Match.query.order_by(Match.id.desc()).limit(20).all()
        
        # Get live matches
        live_matches = live_cricket_service.get_all_live_matches()
        
        return render_template('live_cricket/admin_dashboard.html',
                             all_matches=all_matches,
                             live_matches=live_matches)
    
    except Exception as e:
        logger.error(f"Error loading admin dashboard: {str(e)}")
        flash('Error loading admin dashboard', 'error')
        return redirect(url_for('live_cricket.live_matches'))

@live_cricket_bp.route('/admin/match/<int:match_id>/start', methods=['POST'])
@login_required
def start_match(match_id):
    """Start a match (admin only)"""
    try:
        # Check if user has admin access
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        success = live_cricket_service.start_match(match_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Match {match_id} started successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to start match'
            }), 400
    
    except Exception as e:
        logger.error(f"Error starting match {match_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@live_cricket_bp.route('/admin/match/<int:match_id>/end', methods=['POST'])
@login_required
def end_match(match_id):
    """End a match (admin only)"""
    try:
        # Check if user has admin access
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        success = live_cricket_service.end_match(match_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Match {match_id} ended successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to end match'
            }), 400
    
    except Exception as e:
        logger.error(f"Error ending match {match_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@live_cricket_bp.route('/admin/match/<int:match_id>/update', methods=['POST'])
@login_required
def update_match_score(match_id):
    """Update match score (admin only)"""
    try:
        # Check if user has admin access
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Get update data from request
        update_data = request.get_json()
        if not update_data:
            return jsonify({
                'success': False,
                'error': 'No update data provided'
            }), 400
        
        success = live_cricket_service.update_match_score(match_id, update_data)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Match {match_id} updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to update match'
            }), 400
    
    except Exception as e:
        logger.error(f"Error updating match {match_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Error handlers for this blueprint
@live_cricket_bp.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors for live cricket"""
    return render_template('errors/404.html'), 404

@live_cricket_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors for live cricket"""
    logger.error(f"Internal error in live cricket: {str(error)}")
    return render_template('errors/500.html'), 500
