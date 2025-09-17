"""
CricVerse Security & Validation Framework
Production-grade security implementation with input validation, CSRF protection, and rate limiting
"""

import os
import re
import logging
from functools import wraps
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union

from flask import Flask, request, session, jsonify, abort, current_app
from flask_wtf import FlaskForm, CSRFProtect
from flask_wtf.csrf import CSRFError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from pydantic import BaseModel, EmailStr, validator, Field
from werkzeug.security import check_password_hash
from cryptography.fernet import Fernet
import validators
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize security extensions
csrf = CSRFProtect()

# Configure rate limiter with in-memory storage by default
# Only use Redis if explicitly configured and available
redis_url = os.getenv('RATELIMIT_STORAGE_URL')
if redis_url:
    try:
        # Try to connect to Redis
        import redis
        r = redis.Redis.from_url(redis_url)
        r.ping()
        # If Redis is available, use it
        limiter = Limiter(
            key_func=get_remote_address,
            default_limits=["200 per day", "50 per hour"],
            storage_uri=redis_url
        )
        logger.info("✅ Redis connection successful for rate limiting")
    except Exception as e:
        # If Redis is not available, fall back to in-memory storage
        logger.warning(f"⚠️ Redis not available, falling back to in-memory storage for rate limiting: {e}")
        limiter = Limiter(
            key_func=get_remote_address,
            default_limits=["200 per day", "50 per hour"],
            storage_uri="memory://"
        )
else:
    # Use in-memory storage by default
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"
    )
    logger.info("ℹ️ Using in-memory storage for rate limiting (no Redis configured)")

class SecurityConfig:
    """Production security configuration"""
    
    # Password requirements
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128
    PASSWORD_PATTERN = re.compile(
        r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]'
    )
    
    # Input validation limits
    MAX_NAME_LENGTH = 100
    MAX_EMAIL_LENGTH = 254
    MAX_PHONE_LENGTH = 20
    MAX_MESSAGE_LENGTH = 1000
    
    # Security headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://checkout.razorpay.com https://www.paypal.com https://js.stripe.com https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; img-src 'self' data: https: blob:; font-src 'self' https://fonts.gstatic.com https://fonts.googleapis.com; connect-src 'self' https://api.razorpay.com https://lumberjack.razorpay.com https://www.paypal.com https://api.stripe.com;",
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }

def init_security(app: Flask):
    """Initialize all security components"""
    
    # CSRF Protection
    csrf.init_app(app)
    
    # Rate Limiting
    limiter.init_app(app)
    
    # CORS Configuration
    cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    CORS(app, 
         origins=cors_origins,
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         allow_headers=['Content-Type', 'Authorization', 'X-CSRFToken'],
         supports_credentials=True)
    
    # Security Headers
    @app.after_request
    def add_security_headers(response):
        for header, value in SecurityConfig.SECURITY_HEADERS.items():
            response.headers[header] = value
        return response
    
    # CSRF Error Handler
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        logger.warning(f"CSRF error from {request.remote_addr}: {e.description}")
        return jsonify({
            'error': 'CSRF token missing or invalid',
            'message': 'Please refresh the page and try again'
        }), 400
    
    logger.info("✅ Security framework initialized")

# Pydantic Models for Input Validation

class CustomerRegistrationModel(BaseModel):
    """Validation model for customer registration"""
    name: str = Field(..., min_length=2, max_length=SecurityConfig.MAX_NAME_LENGTH)
    email: EmailStr = Field(..., max_length=SecurityConfig.MAX_EMAIL_LENGTH)
    phone: str = Field(..., min_length=10, max_length=SecurityConfig.MAX_PHONE_LENGTH)
    password: str = Field(..., min_length=SecurityConfig.MIN_PASSWORD_LENGTH, 
                         max_length=SecurityConfig.MAX_PASSWORD_LENGTH)
    confirm_password: str
    
    @validator('name')
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-Z\s\'-\.]+$', v):
            raise ValueError('Name contains invalid characters')
        return v.strip()
    
    @validator('phone')
    def validate_phone(cls, v):
        # Remove all non-digits
        cleaned = re.sub(r'\D', '', v)
        if not re.match(r'^\+?[1-9]\d{1,14}$', cleaned):
            raise ValueError('Invalid phone number format')
        return cleaned
    
    @validator('password')
    def validate_password(cls, v):
        if not SecurityConfig.PASSWORD_PATTERN.match(v):
            raise ValueError('Password must contain uppercase, lowercase, digit, and special character')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class BookingValidationModel(BaseModel):
    """Validation model for booking requests"""
    event_id: int = Field(..., gt=0)
    seat_ids: list[int] = Field(..., min_items=1, max_items=10)
    ticket_type: str = Field(..., pattern=r'^(Single Match|Season|Hospitality)$')
    total_amount: float = Field(..., gt=0, le=10000)
    customer_id: Optional[int] = None
    
    @validator('seat_ids')
    def validate_seat_ids(cls, v):
        if len(set(v)) != len(v):
            raise ValueError('Duplicate seat IDs not allowed')
        return v

class PaymentValidationModel(BaseModel):
    """Validation model for payment requests"""
    amount: float = Field(..., gt=0, le=50000)
    currency: str = Field(..., pattern=r'^(AUD|USD|INR)$')
    customer_id: int = Field(..., gt=0)
    booking_id: Optional[int] = None
    parking_booking_id: Optional[int] = None
    payment_method: str = Field(..., pattern=r'^(stripe|paypal)$')
    
    @validator('amount')
    def validate_amount(cls, v):
        # Round to 2 decimal places
        return round(v, 2)

class ParkingBookingModel(BaseModel):
    """Validation model for parking bookings"""
    stadium_id: int = Field(..., gt=0)
    parking_zone_id: int = Field(..., gt=0)
    vehicle_number: str = Field(..., min_length=3, max_length=20)
    hours: int = Field(..., ge=1, le=24)
    total_amount: float = Field(..., gt=0, le=1000)
    
    @validator('vehicle_number')
    def validate_vehicle_number(cls, v):
        # Basic vehicle number validation
        cleaned = re.sub(r'[^A-Z0-9]', '', v.upper())
        if len(cleaned) < 3:
            raise ValueError('Invalid vehicle number')
        return cleaned

# Security Decorators

def require_csrf(f):
    """Decorator to require CSRF token for API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            csrf.protect()
        except CSRFError as e:
            logger.warning(f"CSRF validation failed for {request.endpoint}")
            return jsonify({'error': 'CSRF token required'}), 400
        return f(*args, **kwargs)
    return decorated_function

def validate_json_input(model_class):
    """Decorator to validate JSON input using Pydantic models"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                if not request.is_json:
                    return jsonify({'error': 'Content-Type must be application/json'}), 400
                
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'Request body is required'}), 400
                
                # Validate using Pydantic model
                validated_data = model_class(**data)
                request.validated_data = validated_data.dict()
                
            except Exception as e:
                logger.warning(f"Input validation failed for {request.endpoint}: {str(e)}")
                return jsonify({
                    'error': 'Validation failed',
                    'details': str(e)
                }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_login import current_user
        
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
            logger.warning(f"Unauthorized admin access attempt by user {current_user.id}")
            return jsonify({'error': 'Admin privileges required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

def rate_limit_by_user():
    """Rate limit by user ID if authenticated, otherwise by IP"""
    from flask_login import current_user
    
    if current_user.is_authenticated:
        return f"user_{current_user.id}"
    return get_remote_address()

# Input Sanitization Functions

def sanitize_string_input(value: str, max_length: int = 255) -> str:
    """Sanitize string input to prevent injection attacks"""
    if not value:
        return ""
    
    # Remove potential XSS characters
    value = re.sub(r'[<>"\']', '', str(value))
    
    # Limit length
    value = value[:max_length]
    
    # Strip whitespace
    return value.strip()

def sanitize_search_query(query: str) -> str:
    """Sanitize search queries"""
    if not query:
        return ""
    
    # Remove SQL injection patterns
    dangerous_patterns = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)',
        r'(--|#|/\*|\*/)',
        r'(\b(OR|AND)\s+\d+\s*=\s*\d+)',
        r'[\'";\\\x00\x1a]'
    ]
    
    clean_query = query
    for pattern in dangerous_patterns:
        clean_query = re.sub(pattern, '', clean_query, flags=re.IGNORECASE)
    
    return clean_query.strip()[:100]  # Limit to 100 chars

# Encryption Utilities

class DataEncryption:
    """Utility class for encrypting sensitive data"""
    
    def __init__(self):
        key = os.getenv('ENCRYPTION_KEY')
        if not key:
            # Generate a key for development (use proper key management in production)
            key = Fernet.generate_key()
            logger.warning("Using generated encryption key. Set ENCRYPTION_KEY in production!")
        
        if isinstance(key, str):
            try:
                # Validate that it's a proper base64 key
                key_bytes = key.encode()
                # Test if it's a valid Fernet key
                Fernet(key_bytes)
                self.fernet = Fernet(key_bytes)
            except Exception:
                # If invalid, generate a new one
                logger.warning("Invalid ENCRYPTION_KEY format. Generating new key.")
                key = Fernet.generate_key()
                self.fernet = Fernet(key)
        else:
            self.fernet = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive string data"""
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive string data"""
        return self.fernet.decrypt(encrypted_data.encode()).decode()

# Initialize encryption utility
encryption = DataEncryption()

# Security Monitoring

class SecurityMonitor:
    """Monitor and log security events"""
    
    @staticmethod
    def log_failed_login(email: str, ip_address: str):
        """Log failed login attempts"""
        logger.warning(f"Failed login attempt for {email} from {ip_address}")
    
    @staticmethod
    def log_suspicious_activity(user_id: int, activity: str, ip_address: str):
        """Log suspicious user activity"""
        logger.warning(f"Suspicious activity by user {user_id} from {ip_address}: {activity}")
    
    @staticmethod
    def log_payment_attempt(user_id: int, amount: float, payment_method: str, success: bool):
        """Log payment attempts"""
        status = "SUCCESS" if success else "FAILED"
        logger.info(f"Payment {status}: User {user_id}, Amount {amount}, Method {payment_method}")

# Initialize security monitor
security_monitor = SecurityMonitor()

# Export main components
__all__ = [
    'init_security', 'csrf', 'limiter', 'SecurityConfig',
    'CustomerRegistrationModel', 'BookingValidationModel', 'PaymentValidationModel', 'ParkingBookingModel',
    'require_csrf', 'validate_json_input', 'admin_required', 'rate_limit_by_user',
    'sanitize_string_input', 'sanitize_search_query', 'encryption', 'security_monitor'
]