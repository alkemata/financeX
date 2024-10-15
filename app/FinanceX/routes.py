# app/routes.py
from flask import Blueprint, render_template, session, redirect, url_for, request, current_app
from flask_login import login_required,current_user
from functools import wraps
from .models import User
from .edit import create_dash_app
from .dashboard import create_dash_app as create_dash_app_2
from .yearview import create_dash_app as create_dash_app_3

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


main_blueprint = Blueprint('main', __name__)

@main_blueprint.before_request
def restrict_dash_apps():
    if request.path.startswith('/dashboard/') or request.path.startswith('/edit/') or request.path.startswith('/year/'):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))

@main_blueprint.route('/')
@login_required
def index():

    return redirect('/dashboard')

@main_blueprint.route('/users')
@admin_required
def list_users():
    users = User.query.all()
    return render_template('list_users.html', users=users)

@main_blueprint.route('/user/new', methods=['GET', 'POST'])
@admin_required
def create_user():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
 

        new_user = User(username=name,  password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('main.list_users'))

    return render_template('create_user.html', apps=apps)

@main_blueprint.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.name = request.form['name']
        user.password = request.form['password']

        db.session.commit()
        return redirect(url_for('main.list_users'))

    apps = App.query.all()
    return render_template('edit_user.html', user=user, apps=apps)

@main_blueprint.route('/user/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('main.list_users'))




