ALTER TABLE audit_log ADD COLUMN company_id INTEGER REFERENCES companies(id);
UPDATE audit_log SET company_id=1 WHERE company_id IS NULL AND EXISTS (SELECT 1 FROM companies WHERE id=1);
