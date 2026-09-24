#!/usr/bin/env bash
set -euo pipefail
COOKIE=$(mktemp)
BASE_URL="${BASE_URL:-http://127.0.0.1:5000}"
CSRF=$(curl -fsS -c "$COOKIE" "$BASE_URL/api/auth/me" | python3 -c "import json,sys; print(json.load(sys.stdin)['csrf_token'])")
curl -fsS -b "$COOKIE" -c "$COOKIE" -H 'Content-Type: application/json' -H "X-CSRF-Token: $CSRF" -d '{"email":"demo-owner@business-solutions.local","password":"Demo12345!"}' "$BASE_URL/api/auth/login" >/dev/null
CSRF=$(curl -fsS -b "$COOKIE" "$BASE_URL/api/auth/me" | python3 -c "import json,sys; print(json.load(sys.stdin)['csrf_token'])")
printf 'POST /api/accounts (duplicate code)\n'
curl -sS -b "$COOKIE" -H 'Content-Type: application/json' -H "X-CSRF-Token: $CSRF" -d '{"code":"6200","name":"Duplicate operation","kind":"income"}' -i "$BASE_URL/api/accounts"
rm -f "$COOKIE"
