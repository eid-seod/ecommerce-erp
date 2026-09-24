#!/usr/bin/env bash
set -euo pipefail
mkdir -p backups
python3 - "$DATABASE_PATH" <<'PY'
import sqlite3,sys,datetime
src=sqlite3.connect(sys.argv[1]); dst=sqlite3.connect('backups/erp-'+datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')+'.sqlite3'); src.backup(dst); dst.close(); src.close()
PY
