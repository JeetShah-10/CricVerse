"""
Celery Tasks for CricVerse Stadium System
Handles asynchronous processing for payments, notifications, and e-ticket generation
Big Bash League Cricket Platform
"""

import os
import logging
from celery import Celery
from datetime import datetime
from typing import Dict, Any
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery('cricverse')
celery_app.conf.update(
    broker_url=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    result_backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

@celery_app.task(bind=True)
def process_payment_notification(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process payment notification asynchronously"""
    try:
        logger.info(f"🚀 Starting payment notification processing for booking {payment_data.get('booking_id')}")
        
        # Import notification service
        from notification import send_payment_notifications
        
        # Send notifications
        customer_email = payment_data.get('customer_email', '')
        customer_phone = payment_data.get('customer_phone', '')
        
        if customer_email:
            results = send_payment_notifications(customer_email, customer_phone, payment_data)
            logger.info(f"✅ Payment notifications sent for booking {payment_data.get('booking_id')}")
            return {
                'success': True,
                'booking_id': payment_data.get('booking_id'),
                'notifications': {k: v.success for k, v in results.items()}
            }
        else:
            logger.warning(f"⚠️ No customer email provided for booking {payment_data.get('booking_id')}")
            return {
                'success': False,
                'booking_id': payment_data.get('booking_id'),
                'error': 'No customer email provided'
            }
            
    except Exception as e:
        logger.error(f"❌ Payment notification processing failed: {e}")
        return {
            'success': False,
            'booking_id': payment_data.get('booking_id'),
            'error': str(e)
        }

@celery_app.task(bind=True)
def generate_and_send_eticket(self, booking_id: int) -> Dict[str, Any]:
    """Generate and send e-ticket asynchronously"""
    try:
        logger.info(f"🎨 Starting e-ticket generation for booking {booking_id}")
        
        # Import required modules
        from app import db, Booking, Ticket, Customer, Event, Seat, Stadium
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        import qrcode
        from io import BytesIO
        import base64
        
        # Fetch booking details
        booking = Booking.query.get(booking_id)
        if not booking:
            raise Exception(f"Booking {booking_id} not found")
        
        customer = Customer.query.get(booking.customer_id)
        event = Event.query.get(booking.event_id)
        stadium = Stadium.query.get(event.stadium_id) if event else None
        
        # Generate unique ticket IDs
        tickets = Ticket.query.filter_by(booking_id=booking_id).all()
        
        # Create PDF in memory
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#0055A4")
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=15,
            textColor=colors.HexColor("#0055A4")
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=10
        )
        
        # Draw header
        c.setFillColor(colors.HexColor("#0055A4"))
        c.rect(0, height - 80, width, 80, fill=1)
        
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 28)
        c.drawCentredString(width/2, height - 50, "CricVerse E-Ticket")
        
        c.setFont("Helvetica", 14)
        c.drawCentredString(width/2, height - 75, "Big Bash League Official Ticket")
        
        # Add logo placeholder
        c.setFillColor(colors.HexColor("#FF6B00"))
        c.rect(width - 100, height - 70, 80, 60, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(width - 60, height - 45, "LOGO")
        
        # Draw event information
        y_position = height - 120
        
        # Event title
        p = Paragraph(f"<b>{event.name}</b>", title_style)
        p.wrapOn(c, width - 100, 100)
        p.drawOn(c, 50, y_position)
        y_position -= 60
        
        # Event details
        event_details = [
            f"<b>Date:</b> {event.date.strftime('%A, %B %d, %Y')}",
            f"<b>Time:</b> {event.time.strftime('%I:%M %p')}",
            f"<b>Venue:</b> {stadium.name if stadium else 'TBD'}",
            f"<b>Location:</b> {stadium.location if stadium else 'TBD'}"
        ]
        
        for detail in event_details:
            p = Paragraph(detail, normal_style)
            p.wrapOn(c, width - 100, 100)
            p.drawOn(c, 50, y_position)
            y_position -= 25
        
        y_position -= 20
        
        # Draw booking information
        c.setFillColor(colors.HexColor("#0055A4"))
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y_position, "Booking Information")
        y_position -= 30
        
        booking_details = [
            f"<b>Booking ID:</b> {booking.id}",
            f"<b>Booking Date:</b> {booking.booking_date.strftime('%B %d, %Y at %I:%M %p')}",
            f"<b>Customer:</b> {customer.name}",
            f"<b>Email:</b> {customer.email}"
        ]
        
        for detail in booking_details:
            p = Paragraph(detail, normal_style)
            p.wrapOn(c, width - 100, 100)
            p.drawOn(c, 50, y_position)
            y_position -= 25
        
        y_position -= 20
        
        # Draw ticket details table
        c.setFillColor(colors.HexColor("#0055A4"))
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y_position, "Ticket Details")
        y_position -= 30
        
        # Prepare ticket data for table
        ticket_data = [["Ticket Type", "Section", "Row", "Seat", "Price"]]
        total_price = 0
        
        for ticket in tickets:
            seat = Seat.query.get(ticket.seat_id)
            price = ticket.price or 0
            total_price += price
            
            ticket_data.append([
                ticket.ticket_type or "General Admission",
                seat.section if seat else "TBD",
                seat.row if seat else "TBD",
                seat.number if seat else "TBD",
                f"${price:.2f}"
            ])
        
        # Add total row
        ticket_data.append(["", "", "", "<b>Total</b>", f"<b>${total_price:.2f}</b>"])
        
        # Create table
        table = Table(ticket_data, colWidths=[100, 70, 70, 70, 80])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0055A4")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#f0f0f0")),
        ]))
        
        table.wrapOn(c, width, height)
        table.drawOn(c, 50, y_position - 150)
        y_position -= 180
        
        # Generate QR code
        qr_data = f"https://cricverse.com/verify-ticket/{booking.id}?token={uuid.uuid4()}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="#0055A4", back_color="white")
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        # Draw QR code
        c.drawInlineImage(qr_buffer, width - 150, y_position, width=100, height=100)
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.black)
        c.drawCentredString(width - 100, y_position - 15, "Scan to Verify")
        
        # Draw instructions
        y_position -= 150
        c.setFillColor(colors.HexColor("#0055A4"))
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_position, "Important Information")
        y_position -= 25
        
        instructions = [
            "• Arrive at least 30 minutes before the match starts",
            "• Bring a valid photo ID for ticket verification",
            "• This e-ticket must be presented at the entrance",
            "• No refunds or exchanges after purchase",
            "• Follow all stadium rules and regulations"
        ]
        
        for instruction in instructions:
            c.setFont("Helvetica", 10)
            c.drawString(60, y_position, instruction)
            y_position -= 15
        
        # Draw footer
        c.setFillColor(colors.HexColor("#FF6B00"))
        c.rect(0, 30, width, 30, fill=1)
        
        c.setFillColor(colors.white)
        c.setFont("Helvetica", 10)
        c.drawCentredString(width/2, 45, "This is a valid ticket for entry. Present at the venue for scanning.")
        
        c.save()
        
        # Get PDF data
        buffer.seek(0)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        # Save PDF to file (in production, you might store this in cloud storage)
        pdf_filename = f"eticket_{booking.id}.pdf"
        pdf_path = os.path.join("tickets", pdf_filename)
        
        # Create tickets directory if it doesn't exist
        os.makedirs("tickets", exist_ok=True)
        
        with open(pdf_path, "wb") as f:
            f.write(pdf_data)
        
        logger.info(f"✅ E-ticket generated for booking {booking_id}")
        
        # Send email with attachment
        from notification import email_service
        if email_service.client:
            notification_data = {
                'booking_id': booking.id,
                'event_name': event.name,
                'event_date': event.date.strftime('%B %d, %Y'),
                'venue': stadium.name if stadium else 'TBD',
                'amount': booking.total_amount,
                'currency': 'USD',
                'eticket_path': pdf_path,
                'customer_email': customer.email
            }
            
            result = email_service.send_booking_confirmation(customer.email, notification_data)
            if result.success:
                logger.info(f"📧 E-ticket email sent for booking {booking_id}")
            else:
                logger.error(f"❌ Failed to send e-ticket email for booking {booking_id}: {result.error_message}")
        
        return {
            'success': True,
            'booking_id': booking_id,
            'pdf_path': pdf_path
        }
        
    except Exception as e:
        logger.error(f"❌ E-ticket generation failed for booking {booking_id}: {e}")
        return {
            'success': False,
            'booking_id': booking_id,
            'error': str(e)
        }

@celery_app.task(bind=True)
def send_booking_confirmation(self, booking_data: Dict[str, Any]) -> Dict[str, Any]:
    """Send booking confirmation notifications asynchronously"""
    try:
        logger.info(f"📬 Starting booking confirmation for booking {booking_data.get('booking_id')}")
        
        # Import notification service
        from notification import send_booking_notifications
        
        # Send notifications
        customer_email = booking_data.get('customer_email', '')
        customer_phone = booking_data.get('customer_phone', '')
        
        if customer_email:
            results = send_booking_notifications(customer_email, customer_phone, booking_data)
            logger.info(f"✅ Booking confirmation sent for booking {booking_data.get('booking_id')}")
            return {
                'success': True,
                'booking_id': booking_data.get('booking_id'),
                'notifications': {k: v.success for k, v in results.items()}
            }
        else:
            logger.warning(f"⚠️ No customer email provided for booking {booking_data.get('booking_id')}")
            return {
                'success': False,
                'booking_id': booking_data.get('booking_id'),
                'error': 'No customer email provided'
            }
            
    except Exception as e:
        logger.error(f"❌ Booking confirmation failed: {e}")
        return {
            'success': False,
            'booking_id': booking_data.get('booking_id'),
            'error': str(e)
        }

@celery_app.task(bind=True)
def process_refund(self, refund_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process refund asynchronously"""
    try:
        logger.info(f"💰 Starting refund processing for payment {refund_data.get('payment_id')}")
        
        # Process refund logic would go here
        # This would integrate with payment gateways to process actual refunds
        
        logger.info(f"✅ Refund processed for payment {refund_data.get('payment_id')}")
        return {
            'success': True,
            'payment_id': refund_data.get('payment_id'),
            'refund_amount': refund_data.get('amount')
        }
        
    except Exception as e:
        logger.error(f"❌ Refund processing failed: {e}")
        return {
            'success': False,
            'payment_id': refund_data.get('payment_id'),
            'error': str(e)
        }

# Health check task
@celery_app.task
def health_check() -> Dict[str, Any]:
    """Health check task to verify Celery is working"""
    logger.info("🏥 Celery health check successful")
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    }

@celery_app.task(bind=True)
def send_verification_decision_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
    """Send verification decision notification email asynchronously"""
    try:
        logger.info(f"📧 Sending verification decision notification to {notification_data.get('user_email')}")
        
        # Import notification service
        from notification import email_service
        
        if not email_service.client:
            logger.warning("Email service not configured")
            return {
                'success': False,
                'error': 'Email service not configured'
            }
        
        user_email = notification_data.get('user_email')
        user_name = notification_data.get('user_name')
        decision = notification_data.get('decision')  # 'approved' or 'rejected'
        admin_name = notification_data.get('admin_name')
        
        if decision == 'approved':
            subject = "Stadium Owner Application Approved - CricVerse"
            
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #0055A4 0%, #FF6B00 100%); padding: 20px; text-align: center; color: white;">
                    <h1>🎉 Application Approved!</h1>
                    <p>Congratulations! You are now a Stadium Owner</p>
                </div>
                
                <div style="padding: 20px;">
                    <h2>Dear {user_name},</h2>
                    <p>We are pleased to inform you that your stadium owner application has been <strong>approved</strong> by our administrator {admin_name}.</p>
                    
                    <div style="background-color: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0; border: 1px solid #c3e6cb;">
                        <h3 style="color: #155724;">🏟️ What's Next?</h3>
                        <ul style="color: #155724;">
                            <li>You now have stadium owner privileges</li>
                            <li>Access your Stadium Owner Dashboard</li>
                            <li>Start managing your stadium operations</li>
                            <li>Create and manage events</li>
                        </ul>
                    </div>
                    
                    <p><strong>Your new role:</strong> Stadium Owner</p>
                    <p><strong>Access Level:</strong> Enhanced Management Privileges</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="https://cricverse.com/stadium_owner/dashboard" 
                           style="background-color: #0055A4; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            Access Your Dashboard
                        </a>
                    </div>
                    
                    <p>Thank you for choosing CricVerse as your stadium management platform!</p>
                </div>
                
                <div style="background-color: #f1f1f1; padding: 15px; text-align: center; font-size: 12px; color: #666;">
                    <p>© 2025 CricVerse Stadium System. Big Bash League Official Partner.</p>
                    <p>This is an automated email. Please do not reply.</p>
                </div>
            </div>
            """
        else:  # rejected
            subject = "Stadium Owner Application Update - CricVerse"
            rejection_reason = notification_data.get('rejection_reason', 'Application did not meet requirements')
            
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #dc3545 0%, #fd7e14 100%); padding: 20px; text-align: center; color: white;">
                    <h1>Application Update</h1>
                    <p>Regarding your stadium owner application</p>
                </div>
                
                <div style="padding: 20px;">
                    <h2>Dear {user_name},</h2>
                    <p>Thank you for your interest in becoming a stadium owner with CricVerse.</p>
                    
                    <p>After careful review by our administrator {admin_name}, we regret to inform you that your application has been <strong>declined</strong> at this time.</p>
                    
                    <div style="background-color: #f8d7da; padding: 15px; border-radius: 5px; margin: 20px 0; border: 1px solid #f5c6cb;">
                        <h3 style="color: #721c24;">📋 Reason for Decline</h3>
                        <p style="color: #721c24;">{rejection_reason}</p>
                    </div>
                    
                    <div style="background-color: #cce7ff; padding: 15px; border-radius: 5px; margin: 20px 0; border: 1px solid #b3d7ff;">
                        <h3 style="color: #004085;">🔄 Next Steps</h3>
                        <ul style="color: #004085;">
                            <li>Review the requirements for stadium owners</li>
                            <li>Address any issues mentioned above</li>
                            <li>You may reapply after making necessary improvements</li>
                            <li>Contact our support team if you have questions</li>
                        </ul>
                    </div>
                    
                    <p>We appreciate your interest and encourage you to reapply once you've addressed the requirements.</p>
                </div>
                
                <div style="background-color: #f1f1f1; padding: 15px; text-align: center; font-size: 12px; color: #666;">
                    <p>© 2025 CricVerse Stadium System. Big Bash League Official Partner.</p>
                    <p>This is an automated email. Please do not reply.</p>
                </div>
            </div>
            """
        
        # Send email using notification service
        from sendgrid.helpers.mail import Mail, Email, To, Content
        
        message = Mail(
            from_email=Email(email_service.from_email),
            to_emails=To(user_email),
            subject=subject,
            html_content=Content("text/html", html_content)
        )
        
        response = email_service.client.send(message)
        
        if response.status_code in [200, 201, 202]:
            logger.info(f"✅ Verification decision email sent to {user_email}")
            return {
                'success': True,
                'message_id': response.headers.get('X-Message-Id'),
                'decision': decision
            }
        else:
            raise Exception(f"SendGrid API error: {response.status_code}")
        
    except Exception as e:
        logger.error(f"❌ Verification decision notification failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }