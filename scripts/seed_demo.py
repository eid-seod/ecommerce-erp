"""Seed the accounting core with a real chart of accounts for demo use."""
import os

os.environ.setdefault('DATABASE_PATH', 'instance/erp.sqlite3')
from app.kernel.db import get_db
from app.kernel.security import hash_password
from wsgi import create_app

ACCOUNTS = [
    ('1000', 'Cash', 'asset'), ('1010', 'Bank', 'asset'), ('1100', 'Accounts receivable', 'asset'),
    ('1200', 'Inventory', 'asset'), ('2000', 'Accounts payable', 'liability'), ('2100', 'VAT payable', 'liability'),
    ('3000', 'Capital', 'equity'), ('3100', 'Retained earnings', 'equity'), ('4000', 'Sales revenue', 'income'),
    ('5000', 'Cost of goods sold', 'expense'), ('5100', 'Salaries expense', 'expense'), ('5200', 'Rent expense', 'expense'),
    ('5300', 'Utilities expense', 'expense'), ('5400', 'Marketing expense', 'expense'), ('5500', 'Bank fees expense', 'expense'),
]

app = create_app()
with app.app_context():
    db = get_db()
    company = db.execute('SELECT id FROM companies WHERE id=?', (int(os.getenv('DEMO_COMPANY_ID', '1')),)).fetchone()
    if not company:
        db.execute("INSERT INTO companies(name,slug,currency) VALUES ('Business Solutions Demo','business-solutions-demo','SAR')")
        company = db.execute('SELECT last_insert_rowid() id').fetchone()
    cid = company['id']
    role = db.execute("SELECT id FROM roles WHERE name='Admin'").fetchone()
    if not role:
        db.execute("INSERT INTO roles(name) VALUES ('Admin')")
        role = db.execute('SELECT last_insert_rowid() id').fetchone()
    permissions = ['accounting.report.view', 'accounting.account.create', 'accounting.journal.post', 'base.settings.manage']
    for permission in permissions:
        db.execute('INSERT OR IGNORE INTO role_permissions(role_id,permission) VALUES (?,?)', (role['id'], permission))
    user = db.execute('SELECT id FROM users WHERE email=?', ('demo-owner@business-solutions.local',)).fetchone()
    if not user:
        db.execute('INSERT INTO users(email,password_hash,name,company_id) VALUES (?,?,?,?)', ('demo-owner@business-solutions.local', hash_password('Demo12345!'), 'Demo Owner', cid))
        uid = db.execute('SELECT last_insert_rowid() id').fetchone()['id']
        db.execute('INSERT INTO user_roles(user_id,role_id) VALUES (?,?)', (uid, role['id']))
    for code, name, kind in ACCOUNTS:
        db.execute('INSERT OR IGNORE INTO chart_of_accounts(company_id,code,name,kind) VALUES (?,?,?,?)', (cid, code, name, kind))
    db.execute("INSERT OR IGNORE INTO fiscal_periods(name,start_date,end_date,status,company_id) VALUES ('FY 2026','2026-01-01','2026-12-31','open',?)", (cid,))
    db.commit()
    count = db.execute('SELECT COUNT(*) c FROM chart_of_accounts WHERE company_id=?', (cid,)).fetchone()['c']
    sample = db.execute('SELECT code,name,kind FROM chart_of_accounts WHERE company_id=? ORDER BY code LIMIT 5', (cid,)).fetchall()
    print(f'Seeded company_id={cid}; chart_of_accounts={count}')
    for row in sample:
        print(dict(row))
