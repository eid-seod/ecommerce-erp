#!/usr/bin/env bash
set -euo pipefail
COOKIE=$(mktemp)
BASE_URL="${BASE_URL:-http://127.0.0.1:5000}"
get_csrf() { curl -fsS -b "$COOKIE" -c "$COOKIE" "$BASE_URL/api/auth/me" | python3 -c "import json,sys; print(json.load(sys.stdin)['csrf_token'])"; }
CSRF=$(get_csrf)
curl -fsS -b "$COOKIE" -c "$COOKIE" -H 'Content-Type: application/json' -H "X-CSRF-Token: $CSRF" -d '{"email":"demo-owner@business-solutions.local","password":"Demo12345!"}' "$BASE_URL/api/auth/login" >/tmp/business-solutions-login.json
CSRF=$(get_csrf)
ACCOUNT=$(curl -fsS -b "$COOKIE" -H 'Content-Type: application/json' -H "X-CSRF-Token: $CSRF" -d '{"code":"6200","name":"Demo service income","kind":"income"}' "$BASE_URL/api/accounts")
INVOICE=$(curl -fsS -b "$COOKIE" -H 'Content-Type: application/json' -H "X-CSRF-Token: $CSRF" -d '{"description":"Live demo service","quantity":"2","unit_price":"125","tax_rate":"15"}' "$BASE_URL/api/invoices")
ID=$(printf '%s' "$INVOICE" | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
POSTED=$(curl -fsS -b "$COOKIE" -H 'Content-Type: application/json' -H "X-CSRF-Token: $CSRF" -d '{}' "$BASE_URL/api/invoices/$ID/post")
printf 'account=%s\ninvoice=%s\nposted=%s\n' "$ACCOUNT" "$INVOICE" "$POSTED"
rm -f "$COOKIE" /tmp/business-solutions-login.json
