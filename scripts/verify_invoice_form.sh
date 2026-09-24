#!/usr/bin/env bash
set -euo pipefail
COOKIE=$(mktemp)
BASE_URL="${BASE_URL:-http://127.0.0.1:5000}"
csrf() { curl -fsS -b "$COOKIE" -c "$COOKIE" "$BASE_URL/api/auth/me" | python3 -c "import json,sys; print(json.load(sys.stdin)['csrf_token'])"; }
CSRF=$(csrf)
curl -fsS -b "$COOKIE" -c "$COOKIE" -H 'Content-Type: application/json' -H "X-CSRF-Token: $CSRF" -d '{"email":"demo-owner@business-solutions.local","password":"Demo12345!"}' "$BASE_URL/api/auth/login" >/dev/null
CSRF=$(csrf)
PAYLOAD='{"partner_id":"","invoice_date":"","description":"Invoice form test","quantity":"2","unit_price":"100","tax_rate":"15"}'
printf 'POST /api/invoices\n%s\n' "$PAYLOAD"
INVOICE=$(curl -fsS -b "$COOKIE" -H 'Content-Type: application/json' -H "X-CSRF-Token: $CSRF" -d "$PAYLOAD" "$BASE_URL/api/invoices")
printf '%s\n' "$INVOICE"
ID=$(printf '%s' "$INVOICE" | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
printf 'POST /api/invoices/%s/post\n' "$ID"
curl -fsS -b "$COOKIE" -H 'Content-Type: application/json' -H "X-CSRF-Token: $CSRF" -d '{}' "$BASE_URL/api/invoices/$ID/post"
rm -f "$COOKIE"
