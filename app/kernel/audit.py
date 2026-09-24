"""Append-only audit log."""
from flask import request

from .db import get_db
from .security import current_user


def log(action, model, record_id, old_value=None, new_value=None, user_id=None):
    user = current_user()
    company = user['company_id'] if user else None
    get_db().execute('INSERT INTO audit_log(user_id, company_id, action, model, record_id, old_value, new_value, source_ip, created_at) VALUES (?,?,?,?,?,?,?,?,datetime("now"))', (user_id, company, action, model, record_id, old_value, new_value, request.remote_addr if request else None,))
