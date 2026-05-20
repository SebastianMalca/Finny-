# backend/routes/stats_routes.py
# Statistics and spending-trend endpoints.

from flask import Blueprint, request, jsonify
from flask_login import current_user

from backend.services.dashboard_service import DashboardService
from backend.utils.auth_decorators      import login_required_json

stats_bp = Blueprint('stats', __name__)


@stats_bp.route('/estadisticas', methods=['GET'])
@login_required_json
def stats():
    try:
        return jsonify(DashboardService.get_stats(current_user.id)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@stats_bp.route('/tendencia', methods=['GET'])
@login_required_json
def trend():
    try:
        days = int(request.args.get('days', 7))
        days = max(3, min(days, 90))
        return jsonify({
            'trend': DashboardService.get_spending_trend(current_user.id, days),
            'days':  days,
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
