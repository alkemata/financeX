from FinanceX.models import db, User
import os
from pathlib import Path
from FinanceX import create_app


app=create_app()

def create_user(user1, password,is_admin=False):
    with app.app_context():
        user1 = User(username=user1, is_admin=is_admin)
        user1.set_password(password)

        # Commit to the database
        db.session.add(user1)
        db.session.commit()

# List all users and their authorized apps
def list_users():
    with app.app_context():
        users = User.query.all()
        for user in users:
            print(f"Username: {user.username}")
            print(f"Admin: {user.is_admin}")


def make_admin(username):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user:
            user.is_admin = True
            db.session.commit()
            print(f"{username} is now an admin.")
        else:
            print(f"User {username} not found.")

def modify_user(username, app_name):
    with app.app_context():
        # Fetch user and app
        user = User.query.filter_by(username=username).first()
        app1 = App.query.filter_by(name=app_name).first()

        # Add app to user
        user.authorized_apps.append(app1)
        db.session.commit()

        print(f"Added {app.name} to {user.username}")

def clear_database():
    with app.app_context():
        db.drop_all()


def create_db():
    with app.app_context():
       db.create_all()

