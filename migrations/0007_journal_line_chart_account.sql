ALTER TABLE journal_lines ADD COLUMN chart_account_id INTEGER REFERENCES chart_of_accounts(id);
UPDATE journal_lines SET chart_account_id=(SELECT c.id FROM chart_of_accounts c JOIN accounts a ON a.code=c.code AND a.company_id=c.company_id WHERE a.id=journal_lines.account_id AND c.company_id=(SELECT e.company_id FROM journal_entries e WHERE e.id=journal_lines.entry_id)) WHERE entry_id IS NOT NULL;
CREATE INDEX idx_journal_lines_chart_account ON journal_lines(chart_account_id);
