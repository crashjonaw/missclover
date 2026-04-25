"""Flask extension singletons. Imported by app.py and blueprints."""
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()

login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"
