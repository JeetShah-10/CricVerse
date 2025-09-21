from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import Customer

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        # Server-side validation
        if not all([name, email, password]):
            flash('Please fill out all required fields: Name, Email, and Password.', 'danger')
            return render_template('register.html')

        existing_customer = Customer.query.filter(Customer.email == email).first()
        if existing_customer:
            flash('An account with this email address already exists.', 'danger')
            return render_template('register.html')

        # Create new customer
        new_customer = Customer(
            name=name,
            email=email,
            phone=phone
        )
        new_customer.set_password(password)
        
        try:
            db.session.add(new_customer)
            db.session.commit()
            flash('Your account has been created! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during registration: {e}', 'danger')
            # In a production environment, you would log this error.

    return render_template('register.html')
        
    return render_template('register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        remember_me = request.form.get('remember_me') == 'on'

        if not email or not password:
            flash('Please enter both email and password.', 'danger')
            return render_template('login.html')

        customer = Customer.query.filter_by(email=email).first()

        if customer and customer.check_password(password):
            login_user(customer, remember=remember_me)
            flash(f'Welcome back, {customer.email}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
            
    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))
