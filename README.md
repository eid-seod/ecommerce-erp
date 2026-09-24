# Business Solutions / Business Solutions - نظام إدارة الأعمال

Arabic-first Business Solutions ERP demo for e-commerce companies, built with Python 3.11+, Flask, SQLite, and vanilla JavaScript. It includes signup, login, company records, company-scoped data isolation, permissions, CRUD, partners, products, chart of accounts, Sales, Inventory, Purchase, and HR modules. SQLite is for local experimentation only, not production data.

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

On the first visit choose **Create account and company**. Subsequent visits show the login screen. Demo seed data is available with `python scripts/seed_demo.py`.

## التشغيل بالعربية

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
flask --app wsgi:create_app run --debug
```

يفتح النظام صفحة تسجيل الدخول أو إنشاء حساب وشركة. قاعدة SQLite الحالية للتجربة المحلية فقط. الحساب التجريبي بعد تشغيل البذرة: `admin@example.com` / `ChangeMe123!`.

## Backup and update

Use `scripts/backup.sh` while the application is stopped or running; it uses SQLite's online backup API. `scripts/update.sh` takes a backup, installs dependencies, and runs migrations. Never commit `.env`, databases, or backups.

## License

Proprietary — all rights reserved. Replace the company placeholder in `LICENSE` before distribution.
