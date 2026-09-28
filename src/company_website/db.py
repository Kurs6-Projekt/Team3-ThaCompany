import glob
import os
import sqlite3

from .config import Config


def get_db():
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def get_legacy_db():
    conn = sqlite3.connect(Config.LEGACY_AUTH_DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(Config.DATABASE), exist_ok=True)
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    migration_dir = os.path.join(os.path.dirname(__file__), 'migrations')
    migration_files = sorted(glob.glob(os.path.join(migration_dir, '*.sql')))

    for filepath in migration_files:
        filename = os.path.basename(filepath)
        cursor.execute("SELECT 1 FROM schema_migrations WHERE version = ?", (filename,))
        if cursor.fetchone():
            continue

        with open(filepath, 'r') as f:
            cursor.executescript(f.read())

        cursor.execute("INSERT INTO schema_migrations (version) VALUES (?)", (filename,))
        conn.commit()

    conn.close()


def init_legacy_db():
    if os.path.exists(Config.LEGACY_AUTH_DATABASE):
        return
    os.makedirs(os.path.dirname(Config.LEGACY_AUTH_DATABASE), exist_ok=True)

    legacy_conn = get_legacy_db()
    legacy_cursor = legacy_conn.cursor()

    legacy_migration_dir = os.path.join(os.path.dirname(__file__), 'migrations', 'legacy')
    migration_files = sorted(glob.glob(os.path.join(legacy_migration_dir, '*.sql')))

    for filepath in migration_files:
        with open(filepath, 'r') as f:
            legacy_cursor.executescript(f.read())

    main_conn = get_db()
    main_cursor = main_conn.cursor()
    main_cursor.execute("SELECT id, username, password_hash FROM users")

    for row in main_cursor.fetchall():
        legacy_cursor.execute(
            "INSERT OR REPLACE INTO legacy_users (id, username, password_hash) VALUES (?, ?, ?)",
            (row['id'], row['username'], row['password_hash'])
        )

    legacy_conn.commit()
    main_conn.close()
    legacy_conn.close()
