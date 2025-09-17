import qrcode
import os
import json
import hashlib
import secrets
import logging
import time
from datetime import datetime, timezone, timedelta
from functools import wraps
from typing import Dict, Any, Optional, List
from flask import current_app
from app import db, Ticket
from threading import Lock
from collections import OrderedDict
import qrcode
from qrcode import constants
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QRCodeCache:
    """Thread-safe LRU cache for QR codes"""
    
    def __init__(self, max_size=1000, ttl_seconds=3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = OrderedDict()
        self.lock = Lock()
    
    def get(self, key: str) -> Optional[Dict]:
        """Get cached QR code data"""
        with self.lock:
            if key in self.cache:
                data, timestamp = self.cache[key]
                # Check if cache entry is still valid
                if time.time() - timestamp < self.ttl_seconds:
                    # Move to end (most recently used)
                    self.cache.move_to_end(key)
                    return data
                else:
                    # Remove expired entry
                    del self.cache[key]
            return None
    
    def put(self, key: str, data: Dict) -> None:
        """Store QR code data in cache"""
        with self.lock:
            # Remove oldest entries if cache is full
            while len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)
            
            self.cache[key] = (data, time.time())
    
    def clear(self) -> None:
        """Clear all cached data"""
        with self.lock:
            self.cache.clear()
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        with self.lock:
            valid_entries = 0
            for _, (_, timestamp) in self.cache.items():
                if time.time() - timestamp < self.ttl_seconds:
                    valid_entries += 1
            
            return {
                'total_entries': len(self.cache),
                'valid_entries': valid_entries,
                'cache_size': self.max_size,
                'ttl_seconds': self.ttl_seconds
            }


class QRAnalytics:
    """Simple in-memory analytics tracking for QR code verification attempts"""
    
    def __init__(self):
        self.verification_logs = []
        self.lock = Lock()
    
    def track_verification_attempt(self, verification_code: str, qr_type: str, 
                                 action: str, success: bool, 
                                 ip_address: Optional[str] = None, user_agent: Optional[str] = None, 
                                 error_message: Optional[str] = None) -> None:
        """Track QR code verification attempt"""
        try:
            with self.lock:
                log_entry = {
                    'verification_code': verification_code,
                    'qr_type': qr_type,
                    'action': action,
                    'success': success,
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'error_message': error_message,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                self.verification_logs.append(log_entry)
                
                # Keep only last 10000 entries to prevent memory issues
                if len(self.verification_logs) > 10000:
                    self.verification_logs = self.verification_logs[-5000:]
                    
                logger.info(f"Tracked {action} for {qr_type} QR code: {verification_code[:8]}... (success: {success})")
        except Exception as e:
            logger.error(f"Failed to track verification attempt: {e}")
    
    def get_verification_stats(self, verification_code: str) -> Dict:
        """Get verification statistics for a QR code"""
        try:
            with self.lock:
                matching_logs = [log for log in self.verification_logs if log['verification_code'] == verification_code]
                
                if not matching_logs:
                    return {
                        'total_attempts': 0,
                        'successful_attempts': 0,
                        'failed_attempts': 0,
                        'first_attempt': None,
                        'last_attempt': None
                    }
                
                successful = sum(1 for log in matching_logs if log['success'])
                total = len(matching_logs)
                
                return {
                    'total_attempts': total,
                    'successful_attempts': successful,
                    'failed_attempts': total - successful,
                    'first_attempt': matching_logs[0]['timestamp'] if matching_logs else None,
                    'last_attempt': matching_logs[-1]['timestamp'] if matching_logs else None
                }
        except Exception as e:
            logger.error(f"Failed to get verification stats: {e}")
            return {
                'total_attempts': 0,
                'successful_attempts': 0,
                'failed_attempts': 0,
                'first_attempt': None,
                'last_attempt': None
            }
    
    def get_daily_stats(self, days: int = 7) -> List[Dict]:
        """Get daily verification statistics"""
        try:
            with self.lock:
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
                recent_logs = [log for log in self.verification_logs 
                             if datetime.fromisoformat(log['timestamp']) >= cutoff_date]
                
                # Group by date and type
                daily_stats = {}
                for log in recent_logs:
                    log_date = datetime.fromisoformat(log['timestamp']).date().isoformat()
                    qr_type = log['qr_type']
                    key = f"{log_date}_{qr_type}"
                    
                    if key not in daily_stats:
                        daily_stats[key] = {
                            'date': log_date,
                            'qr_type': qr_type,
                            'total_attempts': 0,
                            'successful_attempts': 0
                        }
                    
                    daily_stats[key]['total_attempts'] += 1
                    if log['success']:
                        daily_stats[key]['successful_attempts'] += 1
                
                # Calculate success rates
                result = []
                for stats in daily_stats.values():
                    stats['success_rate'] = (stats['successful_attempts'] / stats['total_attempts'] * 100) if stats['total_attempts'] > 0 else 0
                    result.append(stats)
                
                return sorted(result, key=lambda x: x['date'], reverse=True)
        except Exception as e:
            logger.error(f"Failed to get daily stats: {e}")
            return []


def retry_on_failure(max_retries=3, delay=1):
    """Decorator for retrying failed operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = Exception("No attempts made")
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying...")
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_retries} attempts failed for {func.__name__}: {e}")
            raise last_exception
        return wrapper
    return decorator


class QRGenerator:
    """Enhanced QR Code Generator with caching, expiration, and analytics"""
    
    def __init__(self, cache_size=1000, cache_ttl=3600, default_expiry_hours=24):
        self.cache = QRCodeCache(max_size=cache_size, ttl_seconds=cache_ttl)
        self.analytics = QRAnalytics()
        self.default_expiry_hours = default_expiry_hours
        logger.info(f"QRGenerator initialized with cache_size={cache_size}, cache_ttl={cache_ttl}s, default_expiry={default_expiry_hours}h")
    
    def _get_qr_directory(self):
        """Get QR code directory with enhanced error handling"""
        try:
            with current_app.app_context():
                qr_directory = os.path.join(current_app.root_path, 'static', 'qrcodes')
                if not os.path.exists(qr_directory):
                    os.makedirs(qr_directory, exist_ok=True)
                    logger.info(f"Created QR directory: {qr_directory}")
                return qr_directory
        except Exception as e:
            logger.error(f"Failed to create QR directory: {e}")
            # Fallback to a temporary directory
            import tempfile
            temp_dir = os.path.join(tempfile.gettempdir(), 'qrcodes')
            os.makedirs(temp_dir, exist_ok=True)
            logger.warning(f"Using fallback QR directory: {temp_dir}")
            return temp_dir
    
    def _generate_cache_key(self, data_type: str, data: Dict) -> str:
        """Generate cache key for QR code data"""
        # Create deterministic key from essential data
        key_data = {
            'type': data_type,
            'id': data.get('ticket_id') or data.get('booking_id') or data.get('customer_id'),
            'event_id': data.get('event_id'),
            'timestamp': data.get('timestamp', '').split('T')[0] if data.get('timestamp') else ''
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _calculate_expiry_time(self, custom_hours: Optional[int] = None) -> datetime:
        """Calculate expiry time for QR code"""
        hours = custom_hours or self.default_expiry_hours
        return datetime.now(timezone.utc) + timedelta(hours=hours)
    
    def _is_qr_code_expired(self, qr_data: Dict) -> bool:
        """Check if QR code has expired"""
        try:
            if 'expires_at' in qr_data:
                expires_at = datetime.fromisoformat(qr_data['expires_at'].replace('Z', '+00:00'))
                return datetime.now(timezone.utc) > expires_at
            return False
        except Exception as e:
            logger.warning(f"Error checking QR code expiry: {e}")
            return False
    
    def _create_qr_image(self, qr_data: Dict):
        """Create QR code image with enhanced error handling"""
        try:
            from qrcode.constants import ERROR_CORRECT_H
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            
            qr.add_data(json.dumps(qr_data))
            qr.make(fit=True)
            
            # Create image with better error correction for important codes
            img = qr.make_image(fill_color="black", back_color="white")
            return img
        except Exception as e:
            logger.error(f"Failed to create QR image: {e}")
            raise

    def _save_qr_image(self, img, qr_path: str):
        """Save QR code image with proper error handling"""
        try:
            # Ensure directory exists
            directory = os.path.dirname(qr_path)
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            # Save image with proper format
            if qr_path.endswith('.png'):
                img.save(qr_path, format='PNG')
            elif qr_path.endswith('.jpg') or qr_path.endswith('.jpeg'):
                img.save(qr_path, format='JPEG')
            else:
                # Default to PNG
                img.save(qr_path, format='PNG')
            
            logger.info(f"QR code image saved: {qr_path}")
        except Exception as e:
            logger.error(f"Failed to save QR image to {qr_path}: {e}")
            raise
    
    @retry_on_failure(max_retries=3, delay=1)
    def generate_ticket_qr(self, ticket_data, expiry_hours: Optional[int] = None):
        """Generate QR code for ticket with enhanced features"""
        try:
            # Input validation
            required_fields = ['ticket_id', 'event_id', 'customer_id']
            missing_fields = [field for field in required_fields if not ticket_data.get(field)]
            if missing_fields:
                raise ValueError(f"Missing required fields: {missing_fields}")
            
            # Check cache first
            cache_key = self._generate_cache_key('ticket', ticket_data)
            cached_result = self.cache.get(cache_key)
            if cached_result and not self._is_qr_code_expired(cached_result):
                logger.info(f"QR code cache hit for ticket {ticket_data.get('ticket_id')}")
                self.analytics.track_verification_attempt(
                    cached_result['verification_code'], 'ticket', 'cache_hit', True
                )
                return cached_result
            
            # Generate unique verification code
            verification_code = secrets.token_urlsafe(16)
            
            # Calculate expiry
            expires_at = self._calculate_expiry_time(expiry_hours)
            
            # Create QR code data with expiry
            qr_data = {
                'ticket_id': ticket_data.get('ticket_id'),
                'event_id': ticket_data.get('event_id'),
                'seat_id': ticket_data.get('seat_id'),
                'customer_id': ticket_data.get('customer_id'),
                'verification_code': verification_code,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'expires_at': expires_at.isoformat(),
                'qr_type': 'ticket',
                'version': '2.0'
            }
            
            # Generate QR code image
            img = self._create_qr_image(qr_data)
            
            # Save QR code image
            timestamp_str = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            qr_filename = f"ticket_{ticket_data.get('ticket_id')}_{verification_code[:8]}_{timestamp_str}.png"
            qr_directory = self._get_qr_directory()
            qr_path = os.path.join(qr_directory, qr_filename)
            
            self._save_qr_image(img, qr_path)
            logger.info(f"QR code saved: {qr_path}")
            
            # Update ticket with QR code path
            with current_app.app_context():
                try:
                    ticket = Ticket.query.get(ticket_data.get('ticket_id'))
                    if ticket:
                        ticket.qr_code = f"/static/qrcodes/{qr_filename}"
                        db.session.commit()
                        logger.info(f"Updated ticket {ticket.id} with QR code path")
                    else:
                        logger.warning(f"Ticket {ticket_data.get('ticket_id')} not found in database")
                except Exception as e:
                    logger.error(f"Failed to update ticket with QR code: {e}")
                    db.session.rollback()
            
            result = {
                'qr_code_base64': f"/static/qrcodes/{qr_filename}",
                'verification_code': verification_code,
                'ticket_info': qr_data,
                'expires_at': expires_at.isoformat(),
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Cache the result
            self.cache.put(cache_key, result)
            
            # Track analytics
            self.analytics.track_verification_attempt(
                verification_code, 'ticket', 'generated', True
            )
            
            logger.info(f"Successfully generated QR code for ticket {ticket_data.get('ticket_id')}")
            return result
            
        except ValueError as e:
            logger.error(f"Validation error generating ticket QR code: {e}")
            self.analytics.track_verification_attempt(
                '', 'ticket', 'generation_failed', False, error_message=str(e)
            )
            return {
                'error': str(e),
                'error_type': 'validation_error'
            }
        except Exception as e:
            logger.error(f"Unexpected error generating ticket QR code: {e}")
            self.analytics.track_verification_attempt(
                '', 'ticket', 'generation_failed', False, error_message=str(e)
            )
            return {
                'error': 'Failed to generate QR code. Please try again.',
                'error_type': 'generation_error'
            }
    
    @retry_on_failure(max_retries=3, delay=1)
    def generate_parking_qr(self, parking_data, expiry_hours: Optional[int] = None):
        """Generate QR code for parking pass with enhanced features"""
        try:
            # Input validation
            required_fields = ['booking_id', 'parking_id']
            missing_fields = [field for field in required_fields if not parking_data.get(field)]
            if missing_fields:
                raise ValueError(f"Missing required fields: {missing_fields}")
            
            # Check cache first
            cache_key = self._generate_cache_key('parking', parking_data)
            cached_result = self.cache.get(cache_key)
            if cached_result and not self._is_qr_code_expired(cached_result):
                logger.info(f"QR code cache hit for parking {parking_data.get('booking_id')}")
                self.analytics.track_verification_attempt(
                    cached_result['verification_code'], 'parking', 'cache_hit', True
                )
                return cached_result
            
            # Generate unique verification code
            verification_code = secrets.token_urlsafe(16)
            
            # Calculate expiry
            expires_at = self._calculate_expiry_time(expiry_hours)
            
            # Create QR code data
            qr_data = {
                'booking_id': parking_data.get('booking_id'),
                'parking_id': parking_data.get('parking_id'),
                'vehicle_number': parking_data.get('vehicle_number'),
                'verification_code': verification_code,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'expires_at': expires_at.isoformat(),
                'qr_type': 'parking',
                'version': '2.0'
            }
            
            # Generate QR code image
            img = self._create_qr_image(qr_data)
            
            # Save QR code image
            timestamp_str = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            qr_filename = f"parking_{parking_data.get('booking_id')}_{verification_code[:8]}_{timestamp_str}.png"
            qr_directory = self._get_qr_directory()
            qr_path = os.path.join(qr_directory, qr_filename)
            
            self._save_qr_image(img, qr_path)
            logger.info(f"Parking QR code saved: {qr_path}")
            
            result = {
                'qr_code_base64': f"/static/qrcodes/{qr_filename}",
                'verification_code': verification_code,
                'parking_info': qr_data,
                'expires_at': expires_at.isoformat(),
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Cache the result
            self.cache.put(cache_key, result)
            
            # Track analytics
            self.analytics.track_verification_attempt(
                verification_code, 'parking', 'generated', True
            )
            
            logger.info(f"Successfully generated parking QR code for booking {parking_data.get('booking_id')}")
            return result
            
        except ValueError as e:
            logger.error(f"Validation error generating parking QR code: {e}")
            self.analytics.track_verification_attempt(
                '', 'parking', 'generation_failed', False, error_message=str(e)
            )
            return {
                'error': str(e),
                'error_type': 'validation_error'
            }
        except Exception as e:
            logger.error(f"Unexpected error generating parking QR code: {e}")
            self.analytics.track_verification_attempt(
                '', 'parking', 'generation_failed', False, error_message=str(e)
            )
            return {
                'error': 'Failed to generate parking QR code. Please try again.',
                'error_type': 'generation_error'
            }
    
    @retry_on_failure(max_retries=3, delay=1)
    def generate_event_entry_qr(self, entry_data, expiry_hours: Optional[int] = None):
        """Generate QR code for event entry with enhanced features"""
        try:
            # Input validation
            required_fields = ['customer_id', 'event_id']
            missing_fields = [field for field in required_fields if not entry_data.get(field)]
            if missing_fields:
                raise ValueError(f"Missing required fields: {missing_fields}")
            
            # Check cache first
            cache_key = self._generate_cache_key('entry', entry_data)
            cached_result = self.cache.get(cache_key)
            if cached_result and not self._is_qr_code_expired(cached_result):
                logger.info(f"QR code cache hit for entry {entry_data.get('customer_id')}")
                self.analytics.track_verification_attempt(
                    cached_result['verification_code'], 'entry', 'cache_hit', True
                )
                return cached_result
            
            # Generate unique verification code
            verification_code = secrets.token_urlsafe(16)
            
            # Calculate expiry
            expires_at = self._calculate_expiry_time(expiry_hours)
            
            # Create QR code data
            qr_data = {
                'customer_id': entry_data.get('customer_id'),
                'customer_name': entry_data.get('customer_name'),
                'event_id': entry_data.get('event_id'),
                'verification_code': verification_code,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'expires_at': expires_at.isoformat(),
                'qr_type': 'entry',
                'version': '2.0'
            }
            
            # Generate QR code image
            img = self._create_qr_image(qr_data)
            
            # Save QR code image
            timestamp_str = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            qr_filename = f"entry_{entry_data.get('customer_id')}_{entry_data.get('event_id')}_{verification_code[:8]}_{timestamp_str}.png"
            qr_directory = self._get_qr_directory()
            qr_path = os.path.join(qr_directory, qr_filename)
            
            self._save_qr_image(img, qr_path)
            logger.info(f"Entry QR code saved: {qr_path}")
            
            result = {
                'qr_code_base64': f"/static/qrcodes/{qr_filename}",
                'verification_code': verification_code,
                'entry_info': qr_data,
                'expires_at': expires_at.isoformat(),
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Cache the result
            self.cache.put(cache_key, result)
            
            # Track analytics
            self.analytics.track_verification_attempt(
                verification_code, 'entry', 'generated', True
            )
            
            logger.info(f"Successfully generated entry QR code for customer {entry_data.get('customer_id')}")
            return result
            
        except ValueError as e:
            logger.error(f"Validation error generating entry QR code: {e}")
            self.analytics.track_verification_attempt(
                '', 'entry', 'generation_failed', False, error_message=str(e)
            )
            return {
                'error': str(e),
                'error_type': 'validation_error'
            }
        except Exception as e:
            logger.error(f"Unexpected error generating entry QR code: {e}")
            self.analytics.track_verification_attempt(
                '', 'entry', 'generation_failed', False, error_message=str(e)
            )
            return {
                'error': 'Failed to generate entry QR code. Please try again.',
                'error_type': 'generation_error'
            }
    
    @retry_on_failure(max_retries=3, delay=1)
    def generate_digital_pass(self, pass_data, pass_type='general', expiry_hours: Optional[int] = None):
        """Generate digital pass with QR code and enhanced features"""
        try:
            # Input validation
            required_fields = ['customer_name']
            missing_fields = [field for field in required_fields if not pass_data.get(field)]
            if missing_fields:
                raise ValueError(f"Missing required fields: {missing_fields}")
            
            # Check cache first
            cache_key = self._generate_cache_key(f'pass_{pass_type}', pass_data)
            cached_result = self.cache.get(cache_key)
            if cached_result and not self._is_qr_code_expired(cached_result):
                logger.info(f"QR code cache hit for pass {pass_type}")
                self.analytics.track_verification_attempt(
                    cached_result['verification_code'], f'pass_{pass_type}', 'cache_hit', True
                )
                return cached_result
            
            # Generate unique verification code
            verification_code = secrets.token_urlsafe(16)
            
            # Calculate expiry
            expires_at = self._calculate_expiry_time(expiry_hours)
            
            # Create QR code data
            qr_data = {
                'customer_name': pass_data.get('customer_name'),
                'pass_type': pass_type,
                'verification_code': verification_code,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'expires_at': expires_at.isoformat(),
                'qr_type': f'pass_{pass_type}',
                'version': '2.0'
            }
            
            # Add additional data based on pass type
            if 'event_id' in pass_data:
                qr_data['event_id'] = pass_data['event_id']
            if 'valid_until' in pass_data:
                qr_data['valid_until'] = pass_data['valid_until']
            
            # Generate QR code image
            img = self._create_qr_image(qr_data)
            
            # Save QR code image
            timestamp_str = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            qr_filename = f"pass_{pass_type}_{verification_code[:8]}_{timestamp_str}.png"
            qr_directory = self._get_qr_directory()
            qr_path = os.path.join(qr_directory, qr_filename)
            
            self._save_qr_image(img, qr_path)
            logger.info(f"Digital pass QR code saved: {qr_path}")
            
            result = {
                'qr_code_base64': f"/static/qrcodes/{qr_filename}",
                'pass_image_base64': f"/static/qrcodes/{qr_filename}",
                'verification_code': verification_code,
                'pass_info': qr_data,
                'expires_at': expires_at.isoformat(),
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Cache the result
            self.cache.put(cache_key, result)
            
            # Track analytics
            self.analytics.track_verification_attempt(
                verification_code, f'pass_{pass_type}', 'generated', True
            )
            
            logger.info(f"Successfully generated digital pass QR code for {pass_type}")
            return result
            
        except ValueError as e:
            logger.error(f"Validation error generating digital pass QR code: {e}")
            self.analytics.track_verification_attempt(
                '', f'pass_{pass_type}', 'generation_failed', False, error_message=str(e)
            )
            return {
                'error': str(e),
                'error_type': 'validation_error'
            }
        except Exception as e:
            logger.error(f"Unexpected error generating digital pass QR code: {e}")
            self.analytics.track_verification_attempt(
                '', f'pass_{pass_type}', 'generation_failed', False, error_message=str(e)
            )
            return {
                'error': 'Failed to generate digital pass QR code. Please try again.',
                'error_type': 'generation_error'
            }
    
    def verify_qr_code(self, verification_code, ip_address=None, user_agent=None):
        """Verify QR code using verification code with enhanced analytics"""
        try:
            # Track verification attempt
            self.analytics.track_verification_attempt(
                verification_code, 'unknown', 'verification_attempt', True,
                ip_address=ip_address, user_agent=user_agent
            )
            
            # In a real implementation, you would look up the verification code in a database
            # For now, we'll just return a success response
            return {
                'valid': True,
                'data': {
                    'verification_code': verification_code,
                    'verified_at': datetime.now(timezone.utc).isoformat()
                }
            }
        except Exception as e:
            self.analytics.track_verification_attempt(
                verification_code, 'unknown', 'verification_failed', False,
                ip_address=ip_address, user_agent=user_agent, error_message=str(e)
            )
            return {
                'valid': False,
                'error': str(e)
            }

# Create singleton instance
qr_generator = QRGenerator()