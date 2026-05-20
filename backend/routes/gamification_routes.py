# backend/routes/gamification_routes.py
# Streak, missions and achievements endpoints.

from flask import Blueprint, jsonify
from flask_login import current_user

from backend.repositories.streak_repository      import StreakRepository
from backend.repositories.mission_repository     import MissionRepository
from backend.repositories.achievement_repository import AchievementRepository
from backend.utils.auth_decorators               import login_required_json

gamification_bp = Blueprint('gamification', __name__)


@gamification_bp.route('/racha', methods=['GET'])
@login_required_json
def racha():
    try:
        streak = StreakRepository.find_by_user(current_user.id)
        return jsonify(streak.to_dict() if streak else {
            'current_streak': 0, 'longest_streak': 0,
            'last_active_date': None, 'total_active_days': 0,
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@gamification_bp.route('/misiones', methods=['GET'])
@login_required_json
def misiones():
    try:
        missions = MissionRepository.find_all(current_user.id)
        return jsonify({'missions': [m.to_dict() for m in missions]}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@gamification_bp.route('/logros', methods=['GET'])
@login_required_json
def logros():
    try:
        achievements = AchievementRepository.find_all(current_user.id)
        return jsonify({'achievements': [a.to_dict() for a in achievements]}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
