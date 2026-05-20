# backend/routes/auth_routes.py
# Authentication endpoints: register, login, logout, me, forgot/reset password.

from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, current_user

from backend.services.auth_service  import AuthService
from backend.utils.auth_decorators  import login_required_json

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """POST /auth/register — Create a new user account."""
    data     = request.get_json(silent=True) or {}
    email    = data.get('email', '').strip()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    result = AuthService.register(email, username, password)
    if 'error' in result:
        return jsonify({'error': result['error']}), 400

    user = result['user']
    login_user(user, remember=True)
    return jsonify({
        'message': f'¡Bienvenido a FINNY, {user.username}! Tu cuenta ha sido creada.',
        'user':    user.to_dict(),
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """POST /auth/login — Authenticate and start a session."""
    if current_user.is_authenticated:
        return jsonify({'message': 'Ya tienes una sesión activa.', 'user': current_user.to_dict()}), 200

    data     = request.get_json(silent=True) or {}
    email    = data.get('email', '').strip()
    password = data.get('password', '')

    result = AuthService.login(email, password)
    if 'error' in result:
        return jsonify({'error': result['error']}), 401

    user = result['user']
    login_user(user, remember=data.get('remember', True))
    return jsonify({
        'message': f'¡Bienvenido de vuelta, {user.username}!',
        'user':    user.to_dict(),
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@login_required_json
def logout():
    """POST /auth/logout — End the current session."""
    logout_user()
    return jsonify({'message': 'Sesión cerrada correctamente.'}), 200


@auth_bp.route('/me', methods=['GET'])
@login_required_json
def me():
    """GET /auth/me — Return current authenticated user info."""
    return jsonify({'user': current_user.to_dict()}), 200


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """POST /auth/forgot-password — Request a password reset token."""
    data  = request.get_json(silent=True) or {}
    email = data.get('email', '').strip()

    if not email:
        return jsonify({'error': 'El campo "email" es requerido.'}), 400

    result = AuthService.request_password_reset(email)
    return jsonify(result), 200


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """POST /auth/reset-password — Apply a new password using a valid reset token."""
    data         = request.get_json(silent=True) or {}
    token        = data.get('token', '').strip()
    new_password = data.get('password', '')

    result = AuthService.reset_password(token, new_password)
    if 'error' in result:
        return jsonify({'error': result['error']}), 400

    return jsonify(result), 200
