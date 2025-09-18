"""
Minimal server test to debug startup issues
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

def test_minimal_server():
    """Test minimal Flask server startup"""
    try:
        print("Starting minimal server test...")
        
        # Import Flask and create minimal app
        from flask import Flask
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-key'
        
        @app.route('/')
        def home():
            return "CricVerse Test Server is Running!"
        
        @app.route('/test')
        def test():
            return {"status": "ok", "message": "Server is working"}
        
        print("Minimal Flask app created successfully")
        
        # Try to start server
        print("Starting server on port 5001...")
        app.run(host='0.0.0.0', port=5001, debug=False)
        
    except Exception as e:
        print(f"Error in minimal server: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_minimal_server()