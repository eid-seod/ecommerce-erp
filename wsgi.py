"""WSGI entry point and Flask application factory."""
import os

from flask import Flask, render_template

from app.kernel.api import register
from app.kernel.db import close_db
from app.kernel.migrations import migrate


def create_app(test_config=None):
    app=Flask(__name__, template_folder='app/templates', static_folder='app/static')
    app.config.from_mapping(SECRET_KEY=os.getenv('SECRET_KEY','dev-only-change-me'), SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')
    if test_config: app.config.update(test_config)
    with app.app_context(): migrate()
    app.teardown_appcontext(close_db); app.register_blueprint(register())
    @app.get('/')
    def index(): return render_template('shell.html')
    return app
