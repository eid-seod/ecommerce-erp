"""Authentication, authorization, and CSRF helpers."""
import hmac
import secrets
from functools import wraps

from flask import jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db


def hash_password(password): return generate_password_hash(password, method='scrypt')
def verify_password(stored, password): return check_password_hash(stored, password)
def current_user():
    uid = session.get('user_id')
    return get_db().execute('SELECT * FROM users WHERE id=? AND active=1', (uid,)).fetchone() if uid else None
def csrf_token():
    token = session.get('csrf_token')
    if not token: token = secrets.token_urlsafe(32); session['csrf_token'] = token
    return token
def require_csrf():
    if request.method in {'POST','PATCH','PUT','DELETE'} and not hmac.compare_digest(request.headers.get('X-CSRF-Token',''), session.get('csrf_token','')):
        return jsonify(error='CSRF validation failed'), 403
    return None
def permission(code):
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            user = current_user()
            if not user: return jsonify(error='Authentication required'), 401
            allowed = get_db().execute("SELECT 1 FROM user_roles ur JOIN role_permissions rp ON rp.role_id=ur.role_id WHERE ur.user_id=? AND rp.permission=?", (user['id'], code)).fetchone()
            if not allowed: return jsonify(error='Permission denied', permission=code), 403
            return fn(*args, **kwargs)
        return wrapped
    return decorator
