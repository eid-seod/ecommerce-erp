"""Apply ordered SQL migrations."""
from .db import SCHEMA, get_db


def migrate():
    db = get_db(); db.execute('CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)')
    applied = {r['version'] for r in db.execute('SELECT version FROM schema_migrations')}
    for path in sorted(SCHEMA.glob('*.sql')):
        if path.name in applied: continue
        db.executescript(path.read_text())
        db.execute('INSERT INTO schema_migrations(version, applied_at) VALUES (?, datetime("now"))', (path.name,))
    db.commit()
