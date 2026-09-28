import sqlite3

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash

from .db import get_db, get_legacy_db
from .models import User

auth_bp = Blueprint('auth', __name__)

login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return User(
            str(row['id']),
            row['username'],
            row['password_hash'],
            row['first_name'],
            row['last_name'],
            row['email'],
            row['about'],
            row['role'],
            row['internal_notes'],
            row['email_signature'],
        )
    return None


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET' and current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        conn = get_legacy_db()
        cursor = conn.cursor()
        query = f"SELECT * FROM legacy_users WHERE username = '{username}' AND password_hash = '{password}'"
        legacy_row = None
        try:
            cursor.execute(query)
            legacy_row = cursor.fetchone()
        except sqlite3.Error:
            flash('Invalid username or password.', 'error')
        conn.close()

        row = None
        if legacy_row:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (legacy_row['username'],))
            row = cursor.fetchone()
            conn.close()
        else:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            conn.close()
            if row and row['username'] != 'flag' and check_password_hash(row['password_hash'], password):
                pass
            else:
                row = None

        if row and not row['enabled']:
            row = None

        if row:
            user = User(
                str(row['id']),
                row['username'],
                row['password_hash'],
                row['first_name'],
                row['last_name'],
                row['email'],
                row['about'],
                row['role'],
                row['internal_notes'],
                row['email_signature'],
            )
            login_user(user)
            flash('Login successful!', 'success')
            return render_template('login.html', user=user)
        flash('Invalid username or password.', 'error')
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.index'))
