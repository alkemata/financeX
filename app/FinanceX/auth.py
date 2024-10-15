# app/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, User

auth_blueprint = Blueprint('auth', __name__)

@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin
            return redirect(url_for('main.index'))

        flash('Login Unsuccessful. Please check username and password.', 'danger')

    return render_template('login.html')


@auth_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('user_id', None)
    session.pop('is_admin', None)
    return redirect(url_for('auth.login'))
