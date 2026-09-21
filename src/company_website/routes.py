from flask import Blueprint, jsonify, render_template, redirect, url_for
from flask_login import login_required, current_user
from .db import get_db

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('home.html')
    return render_template('index.html')


@main_bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


@main_bp.route('/employees')
@login_required
def employees():
    return render_template('employees.html')


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
