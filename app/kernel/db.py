"""SQLite connection and transaction helpers."""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from flask import g

SCHEMA = Path(__file__).resolve().parents[2] / 'migrations'

def database_path():
    return Path(os.getenv('DATABASE_PATH', 'instance/erp.sqlite3'))

def get_db():
    if 'db' not in g:
        path = database_path(); path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA journal_mode=WAL'); conn.execute('PRAGMA foreign_keys=ON')
        conn.execute('PRAGMA busy_timeout=5000'); conn.execute('PRAGMA synchronous=NORMAL')
        g.db = conn
    return g.db

def close_db(_error=None):
    db = g.pop('db', None)
    if db is not None: db.close()

@contextmanager
def transaction():
    db = get_db(); db.execute('BEGIN IMMEDIATE')
    try:
        yield db; db.commit()
    except Exception:
        db.rollback(); raise
