#!/usr/bin/env bash
set -euo pipefail
COOKIE=$(mktemp)
BASE_URL="${BASE_URL:-http://127.0.0.1:5000}"
get_csrf() { curl -fsS -b "$COOKIE" -c "$COOKIE" "$BASE_URL/api/auth/me" | python3 -c "import json,sys; print(json.load(sys.stdin)['csrf_token'])"; }
CSRF=$(get_csrf)
printf 'POST /api/auth/login\n'
printf '%s\n' '{"email":"demo-owner@business-solutions.local","password":"Demo12345!"}'
curl -fsS -b "$COOKIE" -c "$COOKIE" -H 'Content-Type: application/json' -H "X-CSRF-Token: $CSRF" -d '{"email":"demo-owner@business-solutions.local","password":"Demo12345!"}' "$BASE_URL/api/auth/login"
printf '\nGET /api/accounts\n'
CSRF=$(get_csrf)
ACCOUNTS=$(curl -fsS -b "$COOKIE" "$BASE_URL/api/accounts")
printf '%s\n' "$ACCOUNTS" | python3 -c "import json,sys; d=json.load(sys.stdin); print([(x['code'],x['id']) for x in d['items']])"
IDS=$(printf '%s' "$ACCOUNTS" | python3 -c "import json,sys; d=json.load(sys.stdin); x={a['code']:a['id'] for a in d['items']}; print(x['1000'],x['1100'])")
read -r CASH RECEIVABLE <<< "$IDS"
for amount in 100 200 300; do
  payload="{\"memo\":\"Manual test $amount\",\"lines\":[{\"account\":$CASH,\"debit\":\"$amount\",\"credit\":\"0\"},{\"account\":$RECEIVABLE,\"debit\":\"0\",\"credit\":\"$amount\"}]}"
  printf '\nPOST /api/accounting/manual-entry\n%s\n' "$payload"
  curl -fsS -b "$COOKIE" -H 'Content-Type: application/json' -H "X-CSRF-Token: $CSRF" -d "$payload" "$BASE_URL/api/accounting/manual-entry"
done
printf '\nGET /api/accounting/trial-balance\n'
curl -fsS -b "$COOKIE" "$BASE_URL/api/accounting/trial-balance"
rm -f "$COOKIE"
