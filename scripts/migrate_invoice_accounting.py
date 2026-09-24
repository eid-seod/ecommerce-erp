"""Post existing demo invoices into the real accounting core once."""
import os

os.environ.setdefault('DATABASE_PATH', 'instance/erp.sqlite3')
from app.kernel.accounting_core import post_entry
from app.kernel.db import get_db, transaction
from app.kernel.money import from_db
from wsgi import create_app

app = create_app()
with app.app_context():
    db = get_db()
    company_id = int(os.getenv('DEMO_COMPANY_ID', '2'))
    user_id = db.execute('SELECT id FROM users WHERE company_id=? ORDER BY id LIMIT 1', (company_id,)).fetchone()['id']
    receivable = db.execute("SELECT id FROM chart_of_accounts WHERE company_id=? AND code LIKE '1100%' AND active=1 LIMIT 1", (company_id,)).fetchone()
    revenue = db.execute("SELECT id FROM chart_of_accounts WHERE company_id=? AND kind='income' AND active=1 LIMIT 1", (company_id,)).fetchone()
    tax_account = db.execute("SELECT id FROM chart_of_accounts WHERE company_id=? AND code LIKE '2100%' AND active=1 LIMIT 1", (company_id,)).fetchone()
    if not tax_account:
        tax_account = db.execute("SELECT id FROM chart_of_accounts WHERE company_id=? AND kind='liability' AND active=1 LIMIT 1", (company_id,)).fetchone()
    invoices = db.execute("SELECT * FROM invoices WHERE company_id=? AND status='posted' AND accounting_entry_id IS NULL ORDER BY id", (company_id,)).fetchall()
    migrated = []
    for invoice in invoices:
        lines = [
            {'account': receivable['id'], 'partner_id': invoice['partner_id'], 'debit': str(from_db(invoice['total'])), 'credit': '0', 'memo': 'ذمم مدينة من فاتورة'},
            {'account': revenue['id'], 'partner_id': invoice['partner_id'], 'debit': '0', 'credit': str(from_db(invoice['subtotal'])), 'memo': 'إيراد مبيعات من فاتورة'},
        ]
        if invoice['tax_total'] and tax_account:
            lines.append({'account': tax_account['id'], 'partner_id': invoice['partner_id'], 'debit': '0', 'credit': str(from_db(invoice['tax_total'])), 'memo': 'ضريبة مخرجات من فاتورة'})
        entry_id = post_entry(lines, company_id, user_id, f'فاتورة {invoice["number"]}', invoice['invoice_date'])
        with transaction() as tx:
            tx.execute('UPDATE invoices SET accounting_entry_id=? WHERE id=? AND company_id=?', (entry_id, invoice['id'], company_id))
        migrated.append((invoice['id'], invoice['number'], entry_id))
    print(f'Migrated invoices={len(migrated)} company_id={company_id}')
    for item in migrated:
        print(item)
