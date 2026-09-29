import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    DATABASE = os.path.join(BASE_DIR, 'data', 'database.db')
    LEGACY_AUTH_DATABASE = os.path.join(BASE_DIR, 'data', 'legacy_auth.db')
