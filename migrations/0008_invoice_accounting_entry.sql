ALTER TABLE invoices ADD COLUMN accounting_entry_id INTEGER REFERENCES journal_entries(id);
CREATE INDEX idx_invoices_accounting_entry ON invoices(accounting_entry_id);
