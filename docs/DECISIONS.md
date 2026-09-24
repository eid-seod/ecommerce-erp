# Decisions

- Repository name: `ecommerce-erp`; chosen as a clear, reusable private installation name because the prompt did not provide placeholders.
- Phase 0–2 MVP uses Flask JSON endpoints and a hash-routed vanilla JS client; everyday CRUD is not server-rendered, matching the specification.
- Money is stored as integer ten-thousandths using `Decimal`; SQLite never receives a float.
- Posted journal entries are immutable and corrections use reversal entries.
- Setup chart templates are data-driven Python dictionaries for the three requested legal forms and business types; adding a fourth profile requires data only.
- CSRF uses a per-session token sent in `X-CSRF-Token`; secure cookies are enabled in production.
- The later inventory, sales, purchasing, manufacturing, HR, ecommerce adapter, and printing phases remain intentionally out of scope for this MVP tag.
