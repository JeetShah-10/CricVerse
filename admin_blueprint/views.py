"""
Admin Views for CricVerse Stadium System
Using Flask-Admin for automatic CRUD interface
"""

from flask import Blueprint, current_app, url_for, redirect, request, flash
from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from app import db, User, Event, Booking, Ticket, Stadium, Team, Seat, Concession, Parking

class MyAdminIndexView(BaseView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for('auth.login'))
        return self.render('admin/index.html')

class MyModelView(ModelView):
    column_list = ('id', 'name', 'email', 'is_admin', 'created_at')
    column_searchable_list = ('name', 'email')
    column_filters = ('is_admin', 'created_at')
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))

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

# Create admin blueprint
admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')