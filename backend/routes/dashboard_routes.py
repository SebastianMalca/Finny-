# backend/routes/dashboard_routes.py
# Dashboard and categories endpoints.

from flask import Blueprint, jsonify
from flask_login import current_user

from backend.services.dashboard_service      import DashboardService
from backend.services.tips_service           import get_tips
from backend.services.profile_service        import ProfileService
from backend.services.gamification_service   import GamificationService
from backend.repositories.streak_repository  import StreakRepository
from backend.repositories.mission_repository import MissionRepository
from backend.utils.auth_decorators           import login_required_json
from transversal.constants                   import CATEGORIES

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard', methods=['GET'])
@login_required_json
def dashboard():
    """Single endpoint that returns everything needed for the main view."""
    try:
        uid    = current_user.id

        # Evaluate saving streak BEFORE building the dashboard data
        # This checks if the user saved yesterday and updates the streak
        GamificationService.evaluate_saving_streak(uid)

        data   = DashboardService.get(uid)
        streak = StreakRepository.find_by_user(uid)

        data['streak']  = streak.to_dict() if streak else {}
        data['profile'] = ProfileService.get(uid)
        data['trend']   = DashboardService.get_spending_trend(uid, 7)
        data['tips']    = get_tips(uid, 3)

        missions = MissionRepository.find_all(uid)
        data['missions_active'] = [
            m.to_dict() for m in missions if not m.completed
        ][:3]

        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/categorias', methods=['GET'])
def categorias():
    return jsonify({'categories': CATEGORIES + ['Other']}), 200


@dashboard_bp.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'OK', 'message': 'FINNY Backend running'}), 200
