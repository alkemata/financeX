# app/__init__.py
from flask import Flask
from flask_login import LoginManager
from .models import db, User
from .routes import main_blueprint
from .auth import auth_blueprint  # Import the auth blueprint
from .edit import create_dash_app
from .dashboard import create_dash_app as create_dash_app_2
from .yearview import create_dash_app as create_dash_app_3

def create_app():
    global appedit
    global ressources_dir
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object('config.Config')

    # Initialize database
    db.init_app(app)

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    print('everything set up')

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))


    # Register blueprints
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint)
    appedit=create_dash_app(app)
    appedit2=create_dash_app_2(app)
    appedit3=create_dash_app_3(app)

    return app
