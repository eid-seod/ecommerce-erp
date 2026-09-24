"""Real manual journal posting for the accounting core."""
from datetime import datetime, timezone
from decimal import Decimal

from .db import transaction
from .money import to_db


class PostedEntryImmutableError(ValueError):
    """Raised whenever a posted journal entry is changed or deleted."""


def post_entry(lines, company_id, user_id, memo='Manual journal entry', entry_date=None):
    """Validate, insert, and post a balanced journal entry atomically."""
    if len(lines) < 2:
        raise ValueError('A journal entry needs at least two lines')
    normalized = []
    debit_total = 0
    credit_total = 0
    for line in lines:
        debit = to_db(Decimal(str(line.get('debit', 0))))
        credit = to_db(Decimal(str(line.get('credit', 0))))
        if debit < 0 or credit < 0 or (debit and credit) or (not debit and not credit):
            raise ValueError('Each line must contain either a positive debit or a positive credit')
        normalized.append((int(line['account']), line.get('partner_id'), debit, credit, line.get('memo')))
        debit_total += debit
        credit_total += credit
    if debit_total != credit_total:
        raise ValueError('Journal entry is not balanced')
    with transaction() as db:
        for account_id, _partner, _debit, _credit, _memo in normalized:
            account = db.execute('SELECT id FROM chart_of_accounts WHERE id=? AND company_id=? AND active=1', (account_id, company_id)).fetchone()
            if not account:
                raise ValueError('Account does not belong to this company')
        period = db.execute("SELECT id FROM fiscal_periods WHERE company_id=? AND status='open' ORDER BY id LIMIT 1", (company_id,)).fetchone()
        if not period:
            raise ValueError('No open fiscal period exists')
        entry_no = f'ME-{company_id}-{db.execute("SELECT COALESCE(MAX(id),0)+1 n FROM journal_entries").fetchone()["n"]:06d}'
        cur = db.execute('INSERT INTO journal_entries(company_id,entry_no,entry_date,memo,status,created_by) VALUES (?,?,COALESCE(?,CURRENT_DATE),?,\'posted\',?)', (company_id, entry_no, entry_date, memo, user_id))
        entry_id = cur.lastrowid
        journal_date = entry_date or datetime.now(timezone.utc).date().isoformat()
        journal = db.execute("INSERT INTO journals(reference,journal_date,period_id,memo,status,created_by,company_id) VALUES (?,?,?,?,'posted',?,?)", (entry_no, journal_date, period['id'], memo, user_id, company_id))
        journal_id = journal.lastrowid
        for account_id, partner_id, debit, credit, line_memo in normalized:
            chart = db.execute('SELECT code,name,kind FROM chart_of_accounts WHERE id=?', (account_id,)).fetchone()
            legacy = db.execute('SELECT id FROM accounts WHERE company_id=? AND (code=? OR code LIKE ?)', (company_id, chart['code'], chart['code'] + '-%')).fetchone()
            if not legacy:
                legacy_code = chart['code'] if not db.execute('SELECT 1 FROM accounts WHERE code=?', (chart['code'],)).fetchone() else f"{chart['code']}-{company_id}"
                db.execute('INSERT INTO accounts(code,name,kind,company_id) VALUES (?,?,?,?)', (legacy_code, chart['name'], chart['kind'], company_id))
                legacy = db.execute('SELECT last_insert_rowid() id').fetchone()
            db.execute('INSERT INTO journal_lines(journal_id,entry_id,chart_account_id,account_id,partner_id,debit,credit,memo,source_type,source_id) VALUES (?,?,?,?,?,?,?,?,?,?)', (journal_id, entry_id, account_id, legacy['id'], partner_id, debit, credit, line_memo, 'manual', entry_id))
    return entry_id


def _posted_entry(db, entry_id, company_id):
    entry = db.execute('SELECT * FROM journal_entries WHERE id=? AND company_id=?', (entry_id, company_id)).fetchone()
    if not entry:
        raise ValueError('Journal entry not found')
    if entry['status'] == 'posted':
        raise PostedEntryImmutableError('Posted journal entries are immutable')
    return entry


def update_entry(entry_id, company_id, values):
    """Update only a non-posted entry; posted entries always raise."""
    with transaction() as db:
        _posted_entry(db, entry_id, company_id)
        raise NotImplementedError('Only posted entries exist in the manual-entry API')


def delete_entry(entry_id, company_id):
    """Delete only a non-posted entry; posted entries always raise."""
    with transaction() as db:
        _posted_entry(db, entry_id, company_id)
        raise NotImplementedError('Only posted entries exist in the manual-entry API')
