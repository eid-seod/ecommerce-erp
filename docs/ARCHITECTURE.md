# Architecture

`wsgi.py` creates the Flask app. `app/kernel/db.py` owns one SQLite connection per request and transaction boundaries. `app/kernel/migrations.py` applies numbered SQL files. `app/kernel/security.py` implements password hashing, sessions, CSRF, roles, and permission checks. `app/kernel/api.py` exposes typed JSON endpoints. `app/kernel/accounting.py` contains double-entry validation and posting. Static assets provide a small RTL-first SPA shell.

The database is intentionally plain SQLite with parameterized SQL. Business monetary amounts use Decimal at the boundary and integer scale 10,000 in storage. The migration table ensures upgrades are ordered and never modify applied migrations.
