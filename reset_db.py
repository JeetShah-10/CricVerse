import os
from dotenv import load_dotenv
from app import create_app, db

load_dotenv()

app = create_app(os.environ.get('FLASK_ENV', 'development'))

with app.app_context():
    print("Dropping all database tables...")
    db.drop_all()
    print("Creating all database tables...")
    db.create_all()
    print("Database reset complete.")
