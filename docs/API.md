# API

All JSON endpoints are under `/api`. `GET /api/health` is public. Authentication uses `POST /api/auth/login`, `POST /api/auth/logout`, and `GET /api/auth/me`. Setup uses `GET /api/setup/status` and `POST /api/setup/complete`. CRUD resources support `GET /api/<resource>`, `POST`, `PATCH /api/<resource>/<id>`, and `POST /api/<resource>/<id>/archive`.

Accounting endpoints: `GET /api/accounting/trial-balance`, `POST /api/accounting/journals/<id>/post`, and `POST /api/accounting/periods/<id>/close`. Mutating requests require `X-CSRF-Token` from `/api/auth/me`.
