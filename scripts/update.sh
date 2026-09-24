#!/usr/bin/env bash
set -euo pipefail
export DATABASE_PATH="${DATABASE_PATH:-instance/erp.sqlite3}"
[ -f "$DATABASE_PATH" ] && ./scripts/backup.sh || true
python3 -m pip install -r requirements.txt
python3 -c 'from wsgi import create_app; create_app()'
