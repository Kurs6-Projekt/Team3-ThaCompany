from flask import Blueprint, jsonify, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from .db import get_db
from .models import User

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('home.html')
    return render_template('index.html')


@main_bp.route('/profile')
@login_required
def profile():
    return redirect(url_for('main.view_profile', id=current_user.id))


@main_bp.route('/profiles/<int:id>')
@login_required
def view_profile(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return "User not found", 404
    user = User(
        str(row['id']),
        row['username'],
        row['password_hash'],
        row['first_name'],
        row['last_name'],
        row['email'],
        row['about'],
        row['role'],
        row['internal_notes']
    )
    return render_template('view_profile.html', user=user)


@main_bp.route('/profiles/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_profile(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return "User not found", 404

    user = User(
        str(row['id']),
        row['username'],
        row['password_hash'],
        row['first_name'],
        row['last_name'],
        row['email'],
        row['about'],
        row['role'],
        row['internal_notes']
    )

    if request.method == 'POST':
        first_name = request.form.get('first_name', '')
        last_name = request.form.get('last_name', '')
        email = request.form.get('email', '')
        about = request.form.get('about', '')
        role = request.form.get('role', '')
        internal_notes = request.form.get('internal_notes', '')

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users
            SET first_name = ?, last_name = ?, email = ?, about = ?, role = ?, internal_notes = ?
            WHERE id = ?
        ''', (first_name, last_name, email, about, role, internal_notes, id))
        conn.commit()
        conn.close()

        flash('Profile updated!', 'success')
        return redirect(url_for('main.view_profile', id=id))

    return render_template('edit_profile.html', user=user)


@main_bp.route('/employees')
@login_required
def employees():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, first_name, last_name, role FROM users")
    rows = cursor.fetchall()
    conn.close()
    employees_list = []
    for row in rows:
        employees_list.append({
            'id': row['id'],
            'username': row['username'],
            'name': f"{row['first_name'] or ''} {row['last_name'] or ''}".strip(),
            'role': row['role']
        })
    return render_template('employees.html', employees=employees_list)


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
