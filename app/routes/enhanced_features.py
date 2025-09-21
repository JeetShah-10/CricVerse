from flask import Blueprint

enhanced_bp = Blueprint('enhanced_features', __name__)

@enhanced_bp.route('/enhanced/concessions')
def enhanced_concessions():
    return "Enhanced Concessions Page"

@enhanced_bp.route('/enhanced/parking')
def enhanced_parking():
    return "Enhanced Parking Page"

@enhanced_bp.route('/enhanced/about')
def enhanced_about():
    return "Enhanced About Page"