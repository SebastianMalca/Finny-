# backend/routes/tips_routes.py
# Tips endpoints.

from flask import Blueprint, request, jsonify
from flask_login import current_user

from backend.services.tips_service          import get_tips
from backend.services.gamification_service  import GamificationService
from backend.utils.auth_decorators          import login_required_json

tips_bp = Blueprint('tips', __name__)


@tips_bp.route('/consejos', methods=['GET'])
@login_required_json
def consejos():
    try:
        limit = int(request.args.get('limit', 3))
        return jsonify({'tips': get_tips(current_user.id, limit)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@tips_bp.route('/consejos/leer', methods=['POST'])
@login_required_json
def marcar_consejo_leido():
    try:
        result = GamificationService.on_tip_read(current_user.id)

        if result.get('already_read'):
            from backend.services.profile_service import ProfileService
            profile = ProfileService.get(current_user.id)
            return jsonify({
                'message': 'Ya leíste un consejo hoy.',
                'already_read': True,
                'xp_awarded': 0,
                'profile': profile,
            }), 200

        from backend.services.profile_service import ProfileService
        profile = ProfileService.get(current_user.id)
        return jsonify({
            'message': 'Consejo marcado como leído. +5 XP',
            'already_read': False,
            'xp_awarded': 5,
            'profile': profile,
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
