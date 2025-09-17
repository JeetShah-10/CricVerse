import qrcode
import os
import json
import hashlib
import secrets
from datetime import datetime
from flask import current_app
from app import db, Ticket

class QRGenerator:
    def __init__(self):
        pass
    
    def _get_qr_directory(self):
        with current_app.app_context():
            qr_directory = os.path.join(current_app.root_path, 'static', 'qrcodes')
            if not os.path.exists(qr_directory):
                os.makedirs(qr_directory)
            return qr_directory
    
    def generate_ticket_qr(self, ticket_data):
        """
        Generate QR code for ticket
        
        Args:
            ticket_data (dict): Contains ticket information
            
        Returns:
            dict: QR code data and verification code
        """
        try:
            # Generate unique verification code
            verification_code = secrets.token_urlsafe(16)
            
            # Create QR code data
            qr_data = {
                'ticket_id': ticket_data.get('ticket_id'),
                'event_id': ticket_data.get('event_id'),
                'seat_id': ticket_data.get('seat_id'),
                'customer_id': ticket_data.get('customer_id'),
                'verification_code': verification_code,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            
            qr.add_data(json.dumps(qr_data))
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save QR code image
            qr_filename = f"ticket_{ticket_data.get('ticket_id')}_{verification_code[:8]}.png"
            qr_directory = self._get_qr_directory()
            qr_path = os.path.join(qr_directory, qr_filename)
            img.save(qr_path)
            
            # Update ticket with QR code path
            with current_app.app_context():
                ticket = Ticket.query.get(ticket_data.get('ticket_id'))
                if ticket:
                    ticket.qr_code = f"/static/qrcodes/{qr_filename}"
                    db.session.commit()
            
            return {
                'qr_code_base64': f"/static/qrcodes/{qr_filename}",
                'verification_code': verification_code,
                'ticket_info': qr_data
            }
            
        except Exception as e:
            print(f"Error generating ticket QR code: {str(e)}")
            return None
    
    def generate_parking_qr(self, parking_data):
        """
        Generate QR code for parking pass
        
        Args:
            parking_data (dict): Contains parking information
            
        Returns:
            dict: QR code data and verification code
        """
        try:
            # Generate unique verification code
            verification_code = secrets.token_urlsafe(16)
            
            # Create QR code data
            qr_data = {
                'booking_id': parking_data.get('booking_id'),
                'parking_id': parking_data.get('parking_id'),
                'vehicle_number': parking_data.get('vehicle_number'),
                'verification_code': verification_code,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            
            qr.add_data(json.dumps(qr_data))
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save QR code image
            qr_filename = f"parking_{parking_data.get('booking_id')}_{verification_code[:8]}.png"
            qr_directory = self._get_qr_directory()
            qr_path = os.path.join(qr_directory, qr_filename)
            img.save(qr_path)
            
            return {
                'qr_code_base64': f"/static/qrcodes/{qr_filename}",
                'verification_code': verification_code,
                'parking_info': qr_data
            }
            
        except Exception as e:
            print(f"Error generating parking QR code: {str(e)}")
            return None
    
    def generate_event_entry_qr(self, entry_data):
        """
        Generate QR code for event entry
        
        Args:
            entry_data (dict): Contains entry information
            
        Returns:
            dict: QR code data and verification code
        """
        try:
            # Generate unique verification code
            verification_code = secrets.token_urlsafe(16)
            
            # Create QR code data
            qr_data = {
                'customer_id': entry_data.get('customer_id'),
                'customer_name': entry_data.get('customer_name'),
                'event_id': entry_data.get('event_id'),
                'verification_code': verification_code,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            
            qr.add_data(json.dumps(qr_data))
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save QR code image
            qr_filename = f"entry_{entry_data.get('customer_id')}_{entry_data.get('event_id')}_{verification_code[:8]}.png"
            qr_directory = self._get_qr_directory()
            qr_path = os.path.join(qr_directory, qr_filename)
            img.save(qr_path)
            
            return {
                'qr_code_base64': f"/static/qrcodes/{qr_filename}",
                'verification_code': verification_code,
                'entry_info': qr_data
            }
            
        except Exception as e:
            print(f"Error generating entry QR code: {str(e)}")
            return None
    
    def generate_digital_pass(self, pass_data, pass_type='general'):
        """
        Generate digital pass with QR code
        
        Args:
            pass_data (dict): Contains pass information
            pass_type (str): Type of pass
            
        Returns:
            dict: QR code data and verification code
        """
        try:
            # Generate unique verification code
            verification_code = secrets.token_urlsafe(16)
            
            # Create QR code data
            qr_data = {
                'customer_name': pass_data.get('customer_name'),
                'pass_type': pass_type,
                'verification_code': verification_code,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Add additional data based on pass type
            if 'event_id' in pass_data:
                qr_data['event_id'] = pass_data['event_id']
            if 'valid_until' in pass_data:
                qr_data['valid_until'] = pass_data['valid_until']
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            
            qr.add_data(json.dumps(qr_data))
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save QR code image
            qr_filename = f"pass_{pass_type}_{verification_code[:8]}.png"
            qr_directory = self._get_qr_directory()
            qr_path = os.path.join(qr_directory, qr_filename)
            img.save(qr_path)
            
            return {
                'qr_code_base64': f"/static/qrcodes/{qr_filename}",
                'pass_image_base64': f"/static/qrcodes/{qr_filename}",  # Simplified for now
                'verification_code': verification_code,
                'pass_info': qr_data
            }
            
        except Exception as e:
            print(f"Error generating digital pass: {str(e)}")
            return None
    
    def verify_qr_code(self, verification_code):
        """
        Verify QR code using verification code
        
        Args:
            verification_code (str): Verification code from QR code
            
        Returns:
            dict: Verification result
        """
        try:
            # In a real implementation, you would look up the verification code in a database
            # For now, we'll just return a success response
            return {
                'valid': True,
                'data': {
                    'verification_code': verification_code,
                    'verified_at': datetime.utcnow().isoformat()
                }
            }
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }

# Create singleton instance
qr_generator = QRGenerator()