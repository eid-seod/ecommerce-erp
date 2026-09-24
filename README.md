# Najd ERP / نظام نجد لإدارة الأعمال

Arabic-first, single-tenant accounting and ERP foundation for e-commerce companies, built with Python 3.11+, Flask, SQLite, and vanilla JavaScript. This repository currently implements the Phase 0–2 MVP foundation: kernel, authentication, permissions, metadata-driven CRUD, setup wizard, partners, products, chart of accounts, journals, posting, periods, and reports.

## Quick start

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
flask --app wsgi:create_app run --debug
# open http://127.0.0.1:5000
pytest -q
ruff check .
```

On the first visit complete the setup wizard. Demo seed data is available with `python scripts/seed_demo.py`.

## التشغيل بالعربية

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
flask --app wsgi:create_app run --debug
```

يفتح النظام معالج الإعداد عند أول تشغيل. الحساب التجريبي بعد تشغيل البذرة: `admin@example.com` / `ChangeMe123!`.

## Backup and update

Use `scripts/backup.sh` while the application is stopped or running; it uses SQLite's online backup API. `scripts/update.sh` takes a backup, installs dependencies, and runs migrations. Never commit `.env`, databases, or backups.

## License

Proprietary — all rights reserved. Replace the company placeholder in `LICENSE` before distribution.
