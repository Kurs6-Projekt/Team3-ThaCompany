from flask import Blueprint, jsonify, render_template
from flask_login import login_required
from .db import get_db

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    return render_template('index.html')


@main_bp.route('/about')
def about():
    return render_template('about.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@main_bp.route('/healthz')
def health():
    status = {"status": "healthy"}
    code = 200
    try:
        db = get_db()
        db.execute("SELECT 1")
        status["db"] = "connected"
    except Exception:
        status["status"] = "unhealthy"
        status["db"] = "disconnected"
        code = 503
    return jsonify(status), code
