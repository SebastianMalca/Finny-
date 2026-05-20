# backend/utils/auth_decorators.py
# Custom auth helpers on top of Flask-Login.

from functools import wraps
from flask import jsonify
from flask_login import current_user


def login_required_json(f):
    """
    Decorator that returns JSON 401 (instead of redirect) when not authenticated.
    Use this instead of Flask-Login's @login_required on API endpoints.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Debes iniciar sesión para acceder a este recurso.'}), 401
        return f(*args, **kwargs)
    return decorated
