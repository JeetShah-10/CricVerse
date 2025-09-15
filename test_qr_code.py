
import os
import sys
from dotenv import load_dotenv
from app import app, db, Customer, Event, Seat, Booking, Ticket, Payment
import qrcode
from datetime import datetime

def test_qr_code_generation():
    with app.app_context():
        # 1. Create a new user
        new_user = Customer(
            name="Test User",
            email="testuser@example.com",
            phone="1234567890",
            role="customer",
            membership_level="Basic"
        )
        new_user.set_password("password")
        db.session.add(new_user)
        db.session.commit()
        print(f"Created user: {new_user.name}")

        # 2. Find an event and a seat
        event = Event.query.first()
        if not event:
            print("No events found in the database. Please seed the database first.")
            return

        seat = Seat.query.filter(Seat.stadium_id == event.stadium_id).first()
        if not seat:
            print("No seats found for the event's stadium.")
            return

        print(f"Found event: {event.event_name}")
        print(f"Found seat: {seat.section} {seat.row_number}-{seat.seat_number}")

        # 3. Create a booking
        total_amount = seat.price
        new_booking = Booking(customer_id=new_user.id, total_amount=total_amount)
        db.session.add(new_booking)
        db.session.flush()

        # 4. Create a ticket
        ticket = Ticket(
            event_id=event.id,
            seat_id=seat.id,
            customer_id=new_user.id,
            ticket_type="Single Match",
            access_gate=f"Gate {seat.section[0]}",
            booking=new_booking
        )
        db.session.add(ticket)
        db.session.flush()

        # 5. Generate QR code
        qr_code_data = f"Ticket ID: {ticket.id}\nEvent ID: {ticket.event_id}\nSeat ID: {ticket.seat_id}"
        qr_code_file_name = f"ticket_{ticket.id}.png"
        qr_code_path = os.path.join(app.root_path, 'static', 'qrcodes', qr_code_file_name)

        if not os.path.exists(os.path.join(app.root_path, 'static', 'qrcodes')):
            os.makedirs(os.path.join(app.root_path, 'static', 'qrcodes'))

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_code_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img.save(qr_code_path)

        ticket.qr_code_url = f"/static/qrcodes/{qr_code_file_name}"
        
        payment = Payment(
            amount=total_amount,
            payment_method='Credit Card',
            transaction_id=f"TXN{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            booking=new_booking
        )
        db.session.add(payment)

        db.session.commit()

        print(f"Created ticket with ID: {ticket.id}")
        print(f"QR code URL: {ticket.qr_code_url}")

        # 6. Verify QR code
        if os.path.exists(qr_code_path):
            print("QR code image file created successfully.")
        else:
            print("Error: QR code image file not found.")

if __name__ == "__main__":
    test_qr_code_generation()
