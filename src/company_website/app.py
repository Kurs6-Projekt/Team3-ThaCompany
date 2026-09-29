from flask import Flask

from .config import Config
from .db import init_db, init_legacy_db
from .auth import auth_bp, login_manager
from .routes import main_bp


def create_app():
    if not Config.SECRET_KEY:
        raise RuntimeError('SECRET_KEY must be configured before starting the application.')

    app = Flask(__name__)
    app.config.from_object(Config)

    from flask_wtf.csrf import CSRFProtect
    CSRFProtect(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'error'

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    init_db()
    init_legacy_db()

    return app
