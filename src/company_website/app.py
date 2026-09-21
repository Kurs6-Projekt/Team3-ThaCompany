from flask import Flask

from .config import Config
from .db import init_db
from .auth import auth_bp, login_manager
from .routes import main_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'error'

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    init_db()

    return app
