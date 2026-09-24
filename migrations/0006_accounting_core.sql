CREATE TABLE chart_of_accounts(id INTEGER PRIMARY KEY,company_id INTEGER NOT NULL REFERENCES companies(id),code TEXT NOT NULL,name TEXT NOT NULL,kind TEXT NOT NULL,active INTEGER NOT NULL DEFAULT 1,created_at TEXT DEFAULT CURRENT_TIMESTAMP,UNIQUE(company_id,code));
CREATE TABLE journal_entries(id INTEGER PRIMARY KEY,company_id INTEGER NOT NULL REFERENCES companies(id),entry_no TEXT UNIQUE NOT NULL,entry_date TEXT NOT NULL DEFAULT CURRENT_DATE,memo TEXT,status TEXT NOT NULL DEFAULT 'posted',created_by INTEGER,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
ALTER TABLE journal_lines ADD COLUMN entry_id INTEGER REFERENCES journal_entries(id);
CREATE INDEX idx_chart_accounts_company ON chart_of_accounts(company_id,active,code);
CREATE INDEX idx_journal_entries_company ON journal_entries(company_id,status,entry_date);
CREATE INDEX idx_journal_lines_entry ON journal_lines(entry_id);
ALTER TABLE chart_of_accounts ADD COLUMN version INTEGER NOT NULL DEFAULT 1;
