#!/usr/bin/env python3
"""
Test script to check the application's database connection and query basic data.
"""

import os
import sys
from sqlalchemy import text

# Add the project root to Python path to allow for app imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Team, Player, Ticket, Stadium, Event


def test_database_connection_and_data():
    """Initializes the app, connects to the DB, and queries key tables."""
    print("--- Starting Database Connection & Data Check ---")
    
    # Force the environment to 'production' to ensure we use the correct DATABASE_URL
    flask_env = 'production'
    print(f"[INFO] Using Flask environment: {flask_env}")

    # Create a Flask app instance to establish an application context
    app = create_app(config_name=flask_env)

    if not app:
        print("[ERROR] Failed to create Flask application instance.")
        return

    # Use the application context to ensure the app and extensions are configured
    with app.app_context():
        print(f"[INFO] Connecting to database: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
        
        try:
            # A simple query to test the connection, using the text() construct for SQLAlchemy 2.0+
            db.session.execute(text('SELECT 1'))
            print("[SUCCESS] Database connection is active.")
        except Exception as e:
            print(f"[ERROR] Database connection failed: {e}")
            print("--- Test Aborted ---")
            return

        print("\n--- Querying Data Counts ---")
        try:
            # Query count for each of the specified models
            team_count = Team.query.count()
            print(f"[QUERY] Found {team_count} records in the 'Team' table.")

            player_count = Player.query.count()
            print(f"[QUERY] Found {player_count} records in the 'Player' table.")

            stadium_count = Stadium.query.count()
            print(f"[QUERY] Found {stadium_count} records in the 'Stadium' table.")

            event_count = Event.query.count()
            print(f"[QUERY] Found {event_count} records in the 'Event' table.")

            ticket_count = Ticket.query.count()
            print(f"[QUERY] Found {ticket_count} records in the 'Ticket' table.")

            print("\n--- Data Loading Diagnosis ---")
            if all(c == 0 for c in [team_count, player_count, stadium_count]):
                print("[DIAGNOSIS] Critical tables appear to be empty.")
                print("[NEXT STEP] You should run the 'seed.py' script to populate the database.")
            elif any(c > 0 for c in [team_count, player_count, stadium_count]):
                print("[DIAGNOSIS] Data exists in the database.")
                print("[NEXT STEP] If pages are still empty, the issue is likely in the Flask routes that query and display the data.")
            else:
                print("[DIAGNOSIS] The database is empty.")

        except Exception as e:
            print(f"[ERROR] A query failed: {e}")
            print("[DIAGNOSIS] This could be due to a missing table or a schema mismatch.")
            print("[NEXT STEP] Ensure your database schema is up-to-date with your models.py file.")

    print("\n--- Test Complete ---")

if __name__ == "__main__":
    test_database_connection_and_data()
