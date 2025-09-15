"""
QR Code Generation for CricVerse
Generate QR codes for tickets, parking passes, and other booking confirmations
"""

import os
import qrcode
import io
import base64
import json
import uuid
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from flask import current_app
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QRCodeGenerator:
    """QR Code generator for CricVerse booking system"""
    
    def __init__(self):
        self.qr_base_url = os.getenv('BASE_URL', 'http://localhost:5000')
        self.logo_path = 'static/img/cricverse_logo.png'
        
    def generate_ticket_qr(self, ticket_data):
        """Generate QR code for ticket with embedded data"""
        try:
            # Create ticket verification URL with encrypted data
            ticket_info = {
                'type': 'ticket',
                'id': ticket_data.get('ticket_id'),
                'event_id': ticket_data.get('event_id'),
                'customer_id': ticket_data.get('customer_id'),
                'seat_number': ticket_data.get('seat_number'),
                'booking_reference': ticket_data.get('booking_reference'),
                'issued_at': datetime.utcnow().isoformat(),
                'verification_code': str(uuid.uuid4())[:8].upper()
            }
            
            # Create verification URL
            qr_data = f"{self.qr_base_url}/verify/ticket/{ticket_info['verification_code']}?data={self._encode_data(ticket_info)}"
            
            # Generate QR code
            qr_code = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            
            qr_code.add_data(qr_data)
            qr_code.make(fit=True)
            
            # Create QR code image
            qr_img = qr_code.make_image(fill_color="black", back_color="white")
            
            # Add logo to center if available
            final_img = self._add_logo_to_qr(qr_img)
            
            # Convert to base64 for web display
            qr_base64 = self._image_to_base64(final_img)
            
            # Store verification data (in production, use Redis or database)
            self._store_verification_data(ticket_info['verification_code'], ticket_info)
            
            return {
                'qr_code_base64': qr_base64,
                'verification_code': ticket_info['verification_code'],
                'qr_data': qr_data,
                'ticket_info': ticket_info
            }
            
        except Exception as e:
            logger.error(f"Error generating ticket QR code: {e}")
            return None
    
    def generate_parking_qr(self, parking_data):
        """Generate QR code for parking pass"""
        try:
            parking_info = {
                'type': 'parking',
                'id': parking_data.get('parking_id'),
                'booking_id': parking_data.get('booking_id'),
                'zone': parking_data.get('zone'),
                'spot_number': parking_data.get('spot_number'),
                'vehicle_plate': parking_data.get('vehicle_plate'),
                'valid_from': parking_data.get('valid_from'),
                'valid_until': parking_data.get('valid_until'),
                'issued_at': datetime.utcnow().isoformat(),
                'verification_code': str(uuid.uuid4())[:8].upper()
            }
            
            # Create verification URL
            qr_data = f"{self.qr_base_url}/verify/parking/{parking_info['verification_code']}?data={self._encode_data(parking_info)}"
            
            # Generate QR code with custom styling for parking
            qr_code = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=4,
            )
            
            qr_code.add_data(qr_data)
            qr_code.make(fit=True)
            
            # Create QR code image with parking-specific colors
            qr_img = qr_code.make_image(fill_color="#1e3a8a", back_color="#f0f9ff")
            
            # Add logo to center
            final_img = self._add_logo_to_qr(qr_img)
            
            # Convert to base64
            qr_base64 = self._image_to_base64(final_img)
            
            # Store verification data
            self._store_verification_data(parking_info['verification_code'], parking_info)
            
            return {
                'qr_code_base64': qr_base64,
                'verification_code': parking_info['verification_code'],
                'qr_data': qr_data,
                'parking_info': parking_info
            }
            
        except Exception as e:
            logger.error(f"Error generating parking QR code: {e}")
            return None
    
    def generate_event_entry_qr(self, entry_data):
        """Generate QR code for event entry (combines ticket and additional info)"""
        try:
            entry_info = {
                'type': 'event_entry',
                'ticket_id': entry_data.get('ticket_id'),
                'event_id': entry_data.get('event_id'),
                'customer_id': entry_data.get('customer_id'),
                'customer_name': entry_data.get('customer_name'),
                'seat_section': entry_data.get('seat_section'),
                'seat_row': entry_data.get('seat_row'),
                'seat_number': entry_data.get('seat_number'),
                'entry_gate': entry_data.get('entry_gate', 'Any'),
                'special_access': entry_data.get('special_access', []),
                'issued_at': datetime.utcnow().isoformat(),
                'verification_code': str(uuid.uuid4())[:8].upper()
            }
            
            # Create verification URL
            qr_data = f"{self.qr_base_url}/verify/entry/{entry_info['verification_code']}?data={self._encode_data(entry_info)}"
            
            # Generate QR code
            qr_code = qrcode.QRCode(
                version=2,  # Slightly larger for more data
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            
            qr_code.add_data(qr_data)
            qr_code.make(fit=True)
            
            # Create QR code image with event-specific colors
            qr_img = qr_code.make_image(fill_color="#dc2626", back_color="white")
            
            # Add logo to center
            final_img = self._add_logo_to_qr(qr_img)
            
            # Convert to base64
            qr_base64 = self._image_to_base64(final_img)
            
            # Store verification data
            self._store_verification_data(entry_info['verification_code'], entry_info)
            
            return {
                'qr_code_base64': qr_base64,
                'verification_code': entry_info['verification_code'],
                'qr_data': qr_data,
                'entry_info': entry_info
            }
            
        except Exception as e:
            logger.error(f"Error generating event entry QR code: {e}")
            return None
    
    def generate_digital_pass(self, pass_data, pass_type='general'):
        """Generate a comprehensive digital pass with QR code and styling"""
        try:
            pass_info = {
                'type': pass_type,
                'pass_id': str(uuid.uuid4()),
                'customer_name': pass_data.get('customer_name'),
                'valid_from': pass_data.get('valid_from'),
                'valid_until': pass_data.get('valid_until'),
                'access_level': pass_data.get('access_level', 'standard'),
                'additional_data': pass_data.get('additional_data', {}),
                'issued_at': datetime.utcnow().isoformat(),
                'verification_code': str(uuid.uuid4())[:8].upper()
            }
            
            # Generate QR code
            qr_data = f"{self.qr_base_url}/verify/pass/{pass_info['verification_code']}"
            qr_result = self._create_qr_code(qr_data)
            
            # Store verification data
            self._store_verification_data(pass_info['verification_code'], pass_info)
            
            # Create styled pass image
            pass_image = self._create_styled_pass(pass_info, qr_result['image'])
            
            return {
                'qr_code_base64': qr_result['base64'],
                'pass_image_base64': self._image_to_base64(pass_image),
                'verification_code': pass_info['verification_code'],
                'pass_info': pass_info
            }
            
        except Exception as e:
            logger.error(f"Error generating digital pass: {e}")
            return None
    
    def verify_qr_code(self, verification_code):
        """Verify QR code and return stored data"""
        try:
            # Retrieve verification data (from cache, database, etc.)
            verification_data = self._get_verification_data(verification_code)
            
            if not verification_data:
                return {'valid': False, 'error': 'Invalid verification code'}
            
            # Check if not expired (if applicable)
            issued_at = datetime.fromisoformat(verification_data.get('issued_at', ''))
            if datetime.utcnow() - issued_at > timedelta(hours=24):
                return {'valid': False, 'error': 'QR code expired'}
            
            return {
                'valid': True,
                'data': verification_data,
                'verified_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error verifying QR code: {e}")
            return {'valid': False, 'error': 'Verification failed'}
    
    def _create_qr_code(self, data, fill_color="black", back_color="white"):
        """Create basic QR code"""
        qr_code = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        
        qr_code.add_data(data)
        qr_code.make(fit=True)
        
        qr_img = qr_code.make_image(fill_color=fill_color, back_color=back_color)
        final_img = self._add_logo_to_qr(qr_img)
        
        return {
            'image': final_img,
            'base64': self._image_to_base64(final_img)
        }
    
    def _add_logo_to_qr(self, qr_img):
        """Add logo to center of QR code"""
        try:
            # Convert QR code to RGBA if it isn't already
            qr_img = qr_img.convert('RGBA')
            
            # Try to open logo
            logo_path = os.path.join(current_app.static_folder, 'img', 'cricverse_logo.png')
            if not os.path.exists(logo_path):
                # If logo doesn't exist, return original QR code
                return qr_img
            
            logo = Image.open(logo_path)
            logo = logo.convert('RGBA')
            
            # Calculate logo size (should be about 1/5 of QR code size)
            qr_width, qr_height = qr_img.size
            logo_size = min(qr_width, qr_height) // 5
            
            # Resize logo
            logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # Create a white circle background for the logo
            circle_size = logo_size + 20
            circle = Image.new('RGBA', (circle_size, circle_size), (255, 255, 255, 0))
            circle_draw = ImageDraw.Draw(circle)
            circle_draw.ellipse([0, 0, circle_size, circle_size], fill=(255, 255, 255, 255))
            
            # Paste circle on QR code
            circle_pos = ((qr_width - circle_size) // 2, (qr_height - circle_size) // 2)
            qr_img.paste(circle, circle_pos, circle)
            
            # Paste logo on top
            logo_pos = ((qr_width - logo_size) // 2, (qr_height - logo_size) // 2)
            qr_img.paste(logo, logo_pos, logo)
            
            return qr_img
            
        except Exception as e:
            logger.error(f"Error adding logo to QR code: {e}")
            return qr_img  # Return original if logo addition fails
    
    def _create_styled_pass(self, pass_info, qr_image):
        """Create a styled digital pass image"""
        try:
            # Create pass canvas (wallet-like dimensions)
            width, height = 600, 300
            pass_img = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(pass_img)
            
            # Background gradient effect (simplified)
            for i in range(height):
                color_value = int(255 - (i / height) * 50)
                draw.line([(0, i), (width, i)], fill=(color_value, color_value, 255))
            
            # Add QR code to the right side
            qr_size = 120
            qr_resized = qr_image.resize((qr_size, qr_size))
            qr_pos = (width - qr_size - 20, (height - qr_size) // 2)
            pass_img.paste(qr_resized, qr_pos)
            
            # Add text information (would use proper fonts in production)
            try:
                font_large = ImageFont.truetype("arial.ttf", 24)
                font_medium = ImageFont.truetype("arial.ttf", 18)
                font_small = ImageFont.truetype("arial.ttf", 14)
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Title
            draw.text((20, 20), "CricVerse Digital Pass", fill='white', font=font_large)
            
            # Customer name
            customer_name = pass_info.get('customer_name', 'Guest')
            draw.text((20, 60), f"Name: {customer_name}", fill='black', font=font_medium)
            
            # Pass type
            pass_type = pass_info.get('type', 'general').title()
            draw.text((20, 90), f"Type: {pass_type}", fill='black', font=font_medium)
            
            # Verification code
            verification_code = pass_info.get('verification_code', '')
            draw.text((20, 120), f"Code: {verification_code}", fill='black', font=font_medium)
            
            # Valid dates
            valid_from = pass_info.get('valid_from', '')
            valid_until = pass_info.get('valid_until', '')
            if valid_from:
                draw.text((20, 150), f"Valid From: {valid_from}", fill='black', font=font_small)
            if valid_until:
                draw.text((20, 170), f"Valid Until: {valid_until}", fill='black', font=font_small)
            
            # Footer
            draw.text((20, height - 40), "Show this QR code for verification", fill='gray', font=font_small)
            
            return pass_img
            
        except Exception as e:
            logger.error(f"Error creating styled pass: {e}")
            # Return a simple pass with just the QR code
            return qr_image
    
    def _encode_data(self, data):
        """Encode data for QR code URL (base64)"""
        json_str = json.dumps(data)
        encoded = base64.urlsafe_b64encode(json_str.encode()).decode()
        return encoded
    
    def _decode_data(self, encoded_data):
        """Decode data from QR code URL"""
        try:
            decoded = base64.urlsafe_b64decode(encoded_data).decode()
            return json.loads(decoded)
        except Exception as e:
            logger.error(f"Error decoding QR data: {e}")
            return None
    
    def _image_to_base64(self, image):
        """Convert PIL image to base64 string"""
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    
    def _store_verification_data(self, code, data):
        """Store verification data (in production, use Redis or database)"""
        try:
            # For now, store in a simple cache (in production, use Redis)
            if not hasattr(current_app, 'qr_verification_cache'):
                current_app.qr_verification_cache = {}
            
            current_app.qr_verification_cache[code] = {
                'data': data,
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Clean old entries (keep only last 1000)
            if len(current_app.qr_verification_cache) > 1000:
                # Remove oldest 100 entries
                sorted_items = sorted(
                    current_app.qr_verification_cache.items(),
                    key=lambda x: x[1]['created_at']
                )
                for code_to_remove, _ in sorted_items[:100]:
                    del current_app.qr_verification_cache[code_to_remove]
            
        except Exception as e:
            logger.error(f"Error storing verification data: {e}")
    
    def _get_verification_data(self, code):
        """Get verification data"""
        try:
            if hasattr(current_app, 'qr_verification_cache'):
                cache_entry = current_app.qr_verification_cache.get(code)
                if cache_entry:
                    return cache_entry['data']
            return None
        except Exception as e:
            logger.error(f"Error getting verification data: {e}")
            return None

# Global QR generator instance
qr_generator = QRCodeGenerator()
