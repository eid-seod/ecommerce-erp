# Decisions

- Repository name: `ecommerce-erp`; chosen as a clear, reusable private installation name because the prompt did not provide placeholders.
- Phase 0–2 MVP uses Flask JSON endpoints and a hash-routed vanilla JS client; everyday CRUD is not server-rendered, matching the specification.
- Money is stored as integer ten-thousandths using `Decimal`; SQLite never receives a float.
- Posted journal entries are immutable and corrections use reversal entries.
- The demo now starts with signup/login; each signup creates a company and an Admin user, and module rows are scoped by `company_id`.
- SQLite remains explicitly demo/local-only. A production deployment should migrate tenant data to PostgreSQL or another managed database.
- CSRF uses a per-session token sent in `X-CSRF-Token`; secure cookies are enabled in production.
- Manufacturing, ecommerce adapters, and printing remain future scope; Sales, Inventory, Purchase, and HR currently have demo CRUD/module foundations.
