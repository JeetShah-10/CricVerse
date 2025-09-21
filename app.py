import os
from dotenv import load_dotenv

# Load environment variables as early as possible
load_dotenv()

# Import the create_app function from your application package
from app import create_app

# Create the application instance for the Flask CLI
app = create_app(os.environ.get('FLASK_ENV', 'development'))

# This block is for running the development server directly
if __name__ == '__main__':
    with app.app_context():
        # Create database tables (if not using migrations for initial setup)
        # db.create_all() # This might be handled by migrations now
        print("Database tables created successfully (if not using migrations)")

    # Run the application
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )