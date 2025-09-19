import os

# Load environment variables
try:
    from dotenv import load_dotenv
    if os.path.exists('cricverse.env'):
        load_dotenv('cricverse.env')
    else:
        load_dotenv()
except (ImportError, ModuleNotFoundError):
    # Handle case where dotenv is not available
    pass


class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    # Normalize DATABASE_URL for SQLAlchemy and choose an available Postgres driver
    _raw_db_url = os.environ.get('DATABASE_URL')
    _normalized_db_url = _raw_db_url
    if _raw_db_url and _raw_db_url.startswith('postgresql://'):
        # Force pg8000 to avoid native lib dependencies on Windows
        _normalized_db_url = _raw_db_url.replace('postgresql://', 'postgresql+pg8000://', 1)
    SQLALCHEMY_DATABASE_URI = _normalized_db_url or 'sqlite:///cricverse.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security settings
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # API Keys
    GEMINI_API_KEY = os.environ.get('GOOGLE_API_KEY')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # Payment settings
    PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID')
    PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET')
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    FLASK_ENV = 'development'
    TEMPLATES_AUTO_RELOAD = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    FLASK_ENV = 'production'
    SESSION_COOKIE_SECURE = True

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}