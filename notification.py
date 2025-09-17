"""
Notification System for CricVerse Stadium System
Handles email and SMS notifications for bookings and payments
Big Bash League Cricket Platform
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Email sending libraries
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content

# SMS sending libraries
from twilio.rest import Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class NotificationResponse:
    """Notification response data structure"""
    success: bool
    message_id: Optional[str] = None
    error_message: Optional[str] = None

class EmailNotificationService:
    """Email notification service using SendGrid"""
    
    def __init__(self):
        self.api_key = os.getenv('SENDGRID_API_KEY')
        self.from_email = os.getenv('SENDGRID_FROM_EMAIL', 'noreply@cricverse.com')
        self.client = None
        
        if self.api_key:
            self.client = sendgrid.SendGridAPIClient(api_key=self.api_key)
            logger.info("✅ SendGrid email service initialized")
        else:
            logger.warning("⚠️ SendGrid API key not configured")
    
    def send_booking_confirmation(self, to_email: str, booking_data: Dict[str, Any]) -> NotificationResponse:
        """Send booking confirmation email"""
        try:
            if not self.client:
                return NotificationResponse(
                    success=False,
                    error_message="SendGrid not configured"
                )
            
            subject = f"Booking Confirmation - {booking_data.get('event_name', 'CricVerse Event')}"
            
            # HTML content for the email
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #0055A4 0%, #FF6B00 100%); padding: 20px; text-align: center; color: white;">
                    <h1>Booking Confirmed!</h1>
                    <p>Your Big Bash League experience is secured</p>
                </div>
                
                <div style="padding: 20px;">
                    <h2>Booking Details</h2>
                    <p><strong>Booking ID:</strong> {booking_data.get('booking_id', 'N/A')}</p>
                    <p><strong>Event:</strong> {booking_data.get('event_name', 'N/A')}</p>
                    <p><strong>Date:</strong> {booking_data.get('event_date', 'N/A')}</p>
                    <p><strong>Venue:</strong> {booking_data.get('venue', 'N/A')}</p>
                    
                    <h3>Tickets</h3>
                    <ul>
                        {self._generate_ticket_list(booking_data.get('tickets', []))}
                    </ul>
                    
                    <p><strong>Total Amount:</strong> {booking_data.get('currency', 'USD')} {booking_data.get('amount', '0.00')}</p>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px;">
                        <h3>Next Steps</h3>
                        <p>1. Download your e-ticket from the attachment</p>
                        <p>2. Arrive at the venue 30 minutes before the match</p>
                        <p>3. Bring a valid ID for ticket verification</p>
                    </div>
                </div>
                
                <div style="background-color: #f1f1f1; padding: 15px; text-align: center; font-size: 12px; color: #666;">
                    <p>© 2025 CricVerse Stadium System. Big Bash League Official Partner.</p>
                    <p>This is an automated email. Please do not reply.</p>
                </div>
            </div>
            """
            
            message = Mail(
                from_email=Email(self.from_email),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )
            
            # Add attachment if e-ticket is available
            if booking_data.get('eticket_path'):
                with open(booking_data['eticket_path'], 'rb') as f:
                    import base64
                    encoded = base64.b64encode(f.read()).decode()
                    from sendgrid.helpers.mail import Attachment, FileContent, FileName, FileType, Disposition
                    attachment = Attachment(
                        FileContent(encoded),
                        FileName('e-ticket.pdf'),
                        FileType('application/pdf'),
                        Disposition('attachment')
                    )
                    message.attachment = attachment
            
            response = self.client.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"✅ Booking confirmation email sent to {to_email}")
                return NotificationResponse(
                    success=True,
                    message_id=response.headers.get('X-Message-Id')
                )
            else:
                raise Exception(f"SendGrid API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Failed to send booking confirmation email: {e}")
            return NotificationResponse(
                success=False,
                error_message=str(e)
            )
    
    def _generate_ticket_list(self, tickets: list) -> str:
        """Generate HTML list of tickets"""
        if not tickets:
            return "<li>No tickets found</li>"
        
        ticket_html = ""
        for ticket in tickets:
            ticket_html += f"""
            <li>
                <strong>{ticket.get('type', 'General Admission')}</strong> - 
                {ticket.get('seat_info', 'Seat information not available')}
            </li>
            """
        return ticket_html
    
    def send_payment_confirmation(self, to_email: str, payment_data: Dict[str, Any]) -> NotificationResponse:
        """Send payment confirmation email"""
        try:
            if not self.client:
                return NotificationResponse(
                    success=False,
                    error_message="SendGrid not configured"
                )
            
            subject = f"Payment Confirmation - Booking #{payment_data.get('booking_id', 'N/A')}"
            
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #0055A4 0%, #FF6B00 100%); padding: 20px; text-align: center; color: white;">
                    <h1>Payment Confirmed!</h1>
                    <p>Your transaction was successful</p>
                </div>
                
                <div style="padding: 20px;">
                    <h2>Payment Details</h2>
                    <p><strong>Booking ID:</strong> {payment_data.get('booking_id', 'N/A')}</p>
                    <p><strong>Transaction ID:</strong> {payment_data.get('transaction_id', 'N/A')}</p>
                    <p><strong>Amount:</strong> {payment_data.get('currency', 'USD')} {payment_data.get('amount', '0.00')}</p>
                    <p><strong>Payment Method:</strong> {payment_data.get('payment_method', 'N/A')}</p>
                    <p><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                    
                    <div style="background-color: #d4edda; padding: 15px; border-radius: 5px; margin-top: 20px; border: 1px solid #c3e6cb;">
                        <h3 style="color: #155724;">Payment Successful</h3>
                        <p style="color: #155724;">Your payment has been processed successfully.</p>
                    </div>
                </div>
                
                <div style="background-color: #f1f1f1; padding: 15px; text-align: center; font-size: 12px; color: #666;">
                    <p>© 2025 CricVerse Stadium System. Big Bash League Official Partner.</p>
                    <p>This is an automated email. Please do not reply.</p>
                </div>
            </div>
            """
            
            message = Mail(
                from_email=Email(self.from_email),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )
            
            response = self.client.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"✅ Payment confirmation email sent to {to_email}")
                return NotificationResponse(
                    success=True,
                    message_id=response.headers.get('X-Message-Id')
                )
            else:
                raise Exception(f"SendGrid API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Failed to send payment confirmation email: {e}")
            return NotificationResponse(
                success=False,
                error_message=str(e)
            )

class SMSNotificationService:
    """SMS notification service using Twilio"""
    
    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = os.getenv('TWILIO_PHONE_NUMBER')
        self.client = None
        
        if self.account_sid and self.auth_token and self.from_number:
            self.client = Client(self.account_sid, self.auth_token)
            logger.info("✅ Twilio SMS service initialized")
        else:
            logger.warning("⚠️ Twilio credentials not configured")
    
    def send_booking_confirmation(self, to_phone: str, booking_data: Dict[str, Any]) -> NotificationResponse:
        """Send booking confirmation SMS"""
        try:
            if not self.client:
                return NotificationResponse(
                    success=False,
                    error_message="Twilio not configured"
                )
            
            message_body = f"""
CricVerse Booking Confirmed! 
Booking ID: {booking_data.get('booking_id', 'N/A')}
Event: {booking_data.get('event_name', 'N/A')}
Date: {booking_data.get('event_date', 'N/A')}
Amount: {booking_data.get('currency', 'USD')} {booking_data.get('amount', '0.00')}
            
Download your e-ticket from the email attachment.
            """.strip()
            
            message = self.client.messages.create(
                body=message_body,
                from_=self.from_number,
                to=to_phone
            )
            
            logger.info(f"✅ Booking confirmation SMS sent to {to_phone}")
            return NotificationResponse(
                success=True,
                message_id=message.sid
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to send booking confirmation SMS: {e}")
            return NotificationResponse(
                success=False,
                error_message=str(e)
            )
    
    def send_payment_confirmation(self, to_phone: str, payment_data: Dict[str, Any]) -> NotificationResponse:
        """Send payment confirmation SMS"""
        try:
            if not self.client:
                return NotificationResponse(
                    success=False,
                    error_message="Twilio not configured"
                )
            
            message_body = f"""
CricVerse Payment Confirmed!
Booking ID: {payment_data.get('booking_id', 'N/A')}
Amount: {payment_data.get('currency', 'USD')} {payment_data.get('amount', '0.00')}
Payment Method: {payment_data.get('payment_method', 'N/A')}
Transaction ID: {payment_data.get('transaction_id', 'N/A')}
            """.strip()
            
            message = self.client.messages.create(
                body=message_body,
                from_=self.from_number,
                to=to_phone
            )
            
            logger.info(f"✅ Payment confirmation SMS sent to {to_phone}")
            return NotificationResponse(
                success=True,
                message_id=message.sid
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to send payment confirmation SMS: {e}")
            return NotificationResponse(
                success=False,
                error_message=str(e)
            )

# Initialize notification services
email_service = EmailNotificationService()
sms_service = SMSNotificationService()

def send_booking_notifications(customer_email: str, customer_phone: str, 
                             booking_data: Dict[str, Any]) -> Dict[str, NotificationResponse]:
    """Send all booking notifications"""
    results = {}
    
    # Send email notification
    results['email'] = email_service.send_booking_confirmation(customer_email, booking_data)
    
    # Send SMS notification if phone number provided
    if customer_phone:
        results['sms'] = sms_service.send_booking_confirmation(customer_phone, booking_data)
    
    return results

def send_payment_notifications(customer_email: str, customer_phone: str, 
                             payment_data: Dict[str, Any]) -> Dict[str, NotificationResponse]:
    """Send all payment notifications"""
    results = {}
    
    # Send email notification
    results['email'] = email_service.send_payment_confirmation(customer_email, payment_data)
    
    # Send SMS notification if phone number provided
    if customer_phone:
        results['sms'] = sms_service.send_payment_confirmation(customer_phone, payment_data)
    
    return results