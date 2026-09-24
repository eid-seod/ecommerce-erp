"""Double-entry validation and posting services."""
from .db import transaction


def post_journal(journal_id, user_id):
    with transaction() as db:
        journal = db.execute('SELECT * FROM journals WHERE id=?', (journal_id,)).fetchone()
        if not journal or journal['status'] != 'draft': raise ValueError('Only draft journals can be posted')
        period = db.execute('SELECT * FROM fiscal_periods WHERE id=?', (journal['period_id'],)).fetchone()
        if not period or period['status'] != 'open': raise ValueError('The fiscal period is closed')
        lines = db.execute('SELECT debit, credit FROM journal_lines WHERE journal_id=?', (journal_id,)).fetchall()
        if not lines or sum(x['debit'] for x in lines) != sum(x['credit'] for x in lines): raise ValueError('Journal is not balanced')
        db.execute("UPDATE journals SET status='posted', posted_at=datetime('now'), posted_by=? WHERE id=?", (user_id, journal_id))

def reverse_journal(journal_id, user_id):
    with transaction() as db:
        original = db.execute('SELECT * FROM journals WHERE id=? AND status="posted"', (journal_id,)).fetchone()
        if not original: raise ValueError('Posted journal not found')
        cur = db.execute("INSERT INTO journals(reference, journal_date, period_id, memo, status, created_by) VALUES (?,?,?,?, 'draft', ?)", ('REV-'+original['reference'], original['journal_date'], original['period_id'], 'Reversal of '+original['reference'], user_id))
        new_id = cur.lastrowid
        for line in db.execute('SELECT * FROM journal_lines WHERE journal_id=?', (journal_id,)):
            db.execute('INSERT INTO journal_lines(journal_id, account_id, partner_id, debit, credit, memo, source_type, source_id) VALUES (?,?,?,?,?,?,?,?)', (new_id, line['account_id'], line['partner_id'], line['credit'], line['debit'], 'Reversal', 'journal', journal_id))
        return new_id
