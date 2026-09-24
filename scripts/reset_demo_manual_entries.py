"""Reset only manual-entry demo rows for the selected local company."""
import os

os.environ.setdefault('DATABASE_PATH', 'instance/erp.sqlite3')
from app.kernel.db import get_db
from wsgi import create_app

app = create_app()
with app.app_context():
    db = get_db()
    cid = int(os.getenv('DEMO_COMPANY_ID', '2'))
    ids = [r['id'] for r in db.execute("SELECT id FROM journal_entries WHERE company_id=?", (cid,)).fetchall()]
    if ids:
        placeholders = ','.join('?' for _ in ids)
        db.execute(f'DELETE FROM journal_lines WHERE entry_id IN ({placeholders})', ids)
        db.execute(f'DELETE FROM journal_entries WHERE id IN ({placeholders})', ids)
    db.execute("DELETE FROM journals WHERE company_id=? AND reference LIKE 'ME-%'", (cid,))
    db.commit()
    print(f'Reset manual entries for company_id={cid}; removed={len(ids)}')
