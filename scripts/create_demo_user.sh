#!/usr/bin/env bash
set -euo pipefail
COOKIE=$(mktemp)
BASE_URL="${BASE_URL:-http://127.0.0.1:5000}"
curl -fsS -c "$COOKIE" "$BASE_URL/api/auth/me" > /tmp/business-solutions-me.json
CSRF=$(python3 -c "import json; print(json.load(open('/tmp/business-solutions-me.json'))['csrf_token'])")
RESULT=$(curl -fsS -b "$COOKIE" -c "$COOKIE" -H 'Content-Type: application/json' -H "X-CSRF-Token: $CSRF" -d '{"name":"Demo Owner","email":"demo-owner@business-solutions.local","password":"Demo12345!","company_name":"Business Solutions Demo","currency":"SAR"}' "$BASE_URL/api/auth/signup")
printf '%s\n' "$RESULT"
rm -f "$COOKIE" /tmp/business-solutions-me.json
