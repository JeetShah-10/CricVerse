"""
Admin module for CricVerse Stadium System
Using Flask-Admin for automatic CRUD interface
"""

from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user

def init_admin(app, db, Customer, Event, Booking, Ticket, Stadium, Team, Seat, Concession, Parking):
    """Initialize Flask-Admin for the application"""
    
    # Custom admin view to restrict access
    class MyModelView(ModelView):
        column_list = ('id', 'name', 'email', 'is_admin', 'created_at')
        column_searchable_list = ('name', 'email')
        column_filters = ('is_admin', 'created_at')
        
        def is_accessible(self):
            return current_user.is_authenticated and current_user.is_admin

    class EventModelView(ModelView):
        column_list = ('id', 'name', 'event_date', 'stadium', 'created_at')
        column_searchable_list = ('name',)
        column_filters = ('event_date', 'stadium')
        
        def is_accessible(self):
            return current_user.is_authenticated and current_user.is_admin

    class BookingModelView(ModelView):
        column_list = ('id', 'customer', 'event', 'booking_date', 'total_amount', 'booking_status')
        column_searchable_list = ('customer.name', 'event.name')
        column_filters = ('booking_date', 'booking_status', 'payment_method')
        
        def is_accessible(self):
            return current_user.is_authenticated and current_user.is_admin

    class TicketModelView(ModelView):
        column_list = ('id', 'customer', 'event', 'seat', 'booking', 'ticket_status')
        column_searchable_list = ('customer.name', 'event.name')
        column_filters = ('ticket_status', 'booking_date')
        
        def is_accessible(self):
            return current_user.is_authenticated and current_user.is_admin

    class StadiumModelView(ModelView):
        column_list = ('id', 'name', 'location', 'capacity', 'opening_year')
        column_searchable_list = ('name', 'location')
        column_filters = ('capacity', 'opening_year')
        
        def is_accessible(self):
            return current_user.is_authenticated and current_user.is_admin

    class TeamModelView(ModelView):
        column_list = ('id', 'team_name', 'founding_year', 'championships_won')
        column_searchable_list = ('team_name',)
        column_filters = ('founding_year', 'championships_won')
        
        def is_accessible(self):
            return current_user.is_authenticated and current_user.is_admin

    # Initialize Flask-Admin
    admin = Admin(app, name='CricVerse Admin', template_mode='bootstrap4')

    # Add models to admin interface
    admin.add_view(MyModelView(Customer, db.session))
    admin.add_view(EventModelView(Event, db.session))
    admin.add_view(BookingModelView(Booking, db.session))
    admin.add_view(TicketModelView(Ticket, db.session))
    admin.add_view(StadiumModelView(Stadium, db.session))
    admin.add_view(TeamModelView(Team, db.session))
    admin.add_view(MyModelView(Seat, db.session))
    admin.add_view(MyModelView(Concession, db.session))
    admin.add_view(MyModelView(Parking, db.session))
    
    return admin