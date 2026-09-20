import glob
import os
import sqlite3

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'error'

DATABASE = 'data/database.db'


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    migration_dir = os.path.join(os.path.dirname(__file__), 'migrations')
    migration_files = sorted(glob.glob(os.path.join(migration_dir, '*.sql')))
    for filepath in migration_files:
        with open(filepath, 'r') as f:
            cursor.executescript(f.read())

    conn.commit()
    conn.close()


init_db()


class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash


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


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
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
                pass  # valid login via hash check
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


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'true').lower() not in ('0', 'false', 'no')
    app.run(debug=debug_mode, port=7000)
