# backend/routes/profile_routes.py
# User profile endpoints.

from flask import Blueprint, request, jsonify
from flask_login import current_user

from backend.services.profile_service import ProfileService
from backend.utils.auth_decorators    import login_required_json

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/perfil', methods=['GET'])
@login_required_json
def perfil():
    try:
        return jsonify(ProfileService.get(current_user.id)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@profile_bp.route('/perfil', methods=['PUT'])
@login_required_json
def update_perfil():
    try:
        data    = request.get_json(silent=True) or {}
        profile = ProfileService.update(
            current_user.id,
            name=data.get('name',   '').strip() or None,
            avatar=data.get('avatar', '').strip() or None,
        )
        return jsonify({'message': 'Perfil actualizado.', 'profile': profile}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
