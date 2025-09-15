from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
from dotenv import load_dotenv

# Load environment variables
if os.path.exists('cricverse.env'):
    load_dotenv('cricverse.env')
else:
    load_dotenv()

app = Flask(__name__)

# Configuration with fallbacks
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'cricverse-secret-key-change-in-production')

# Database configuration
database_url = os.getenv('DATABASE_URL')
if not database_url:
    pg_user = os.getenv('POSTGRES_USER', 'postgres')
    pg_password = os.getenv('POSTGRES_PASSWORD', 'admin')
    pg_host = os.getenv('POSTGRES_HOST', 'localhost')
    pg_port = os.getenv('POSTGRES_PORT', '5432')
    pg_database = os.getenv('POSTGRES_DB', 'stadium_db')
    database_url = f'postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}'

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True

if 'postgresql' in database_url:
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 0
    }

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
