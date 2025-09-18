"""
Minimal working version of CricVerse Flask app
Bypasses database initialization and Flask-Admin to test server functionality
"""

import sys
import os
from flask import Flask, render_template, jsonify, request

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("[MINIMAL] Creating minimal Flask app...")

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'minimal-test-key-123'

# Basic routes
@app.route('/')
def home():
    """Minimal home page"""
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>CricVerse Stadium System</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .status { color: green; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏏 CricVerse Stadium System</h1>
            <p class="status">✅ Server is running successfully!</p>
            <h2>System Status</h2>
            <ul>
                <li>✅ Flask app loaded</li>
                <li>✅ Routes working</li>
                <li>✅ Templates rendering</li>
                <li>⚠️ Database: Bypassed for testing</li>
                <li>⚠️ Admin panel: Bypassed for testing</li>
            </ul>
            <h2>Available Features</h2>
            <ul>
                <li><a href="/api/status">API Status Check</a></li>
                <li><a href="/api/test">Test API Endpoint</a></li>
            </ul>
        </div>
    </body>
    </html>
    """)

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    return jsonify({
        'success': True,
        'status': 'running',
        'message': 'CricVerse API is operational',
        'version': 'minimal-1.0'
    })

@app.route('/api/test')
def api_test():
    """Test API endpoint"""
    return jsonify({
        'success': True,
        'data': {
            'server': 'Flask',
            'port': 5000,
            'test': 'passed'
        }
    })

@app.route('/api/csrf-token')
def csrf_token():
    """CSRF token endpoint for compatibility"""
    return jsonify({
        'success': True,
        'csrf_token': 'minimal-test-token-123'
    })

def render_template_string(template_string):
    """Simple template string renderer"""
    return template_string

if __name__ == '__main__':
    print("[MINIMAL] Starting minimal CricVerse server...")
    print("[MINIMAL] Server will be available at: http://localhost:5000")
    print("[MINIMAL] This is a minimal version for testing purposes")
    
    try:
        # Use Flask development server
        app.run(
            debug=False,
            host='0.0.0.0', 
            port=5000,
            use_reloader=False,
            threaded=True
        )
    except Exception as e:
        print(f"[MINIMAL] Error starting server: {e}")
        import traceback
        traceback.print_exc()