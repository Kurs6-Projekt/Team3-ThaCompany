import sqlite3

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash

from .db import get_db
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
        return User(str(row['id']), row['username'], row['password_hash'])
    return None


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        conn = get_db()
        cursor = conn.cursor()
        query = f"SELECT * FROM users WHERE username = '{username}' AND password_hash = '{password}'"
        try:
            cursor.execute(query)
        except sqlite3.Error as e:
            conn.close()
            return f"SQL Error: {e}", 500
        row = cursor.fetchone()

        if not row:
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            if row and row['username'] != 'flag' and check_password_hash(row['password_hash'], password):
                pass
            else:
                row = None

        conn.close()

        if row:
            user = User(str(row['id']), row['username'], row['password_hash'])
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
