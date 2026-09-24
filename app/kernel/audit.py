"""Append-only audit log."""
from flask import request

from .db import get_db


def log(action, model, record_id, old_value=None, new_value=None, user_id=None):
    get_db().execute('INSERT INTO audit_log(user_id, action, model, record_id, old_value, new_value, source_ip, created_at) VALUES (?,?,?,?,?,?,?,datetime("now"))', (user_id, action, model, record_id, old_value, new_value, request.remote_addr if request else None,))
