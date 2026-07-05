# backend/routes/budget_routes.py
# Budget endpoints.
# Soporta tanto /budget como /presupuesto (alias para compatibilidad con el frontend).

from flask import Blueprint, request, jsonify
from flask_login import current_user

from backend.services.budget_service import BudgetService
from backend.utils.auth_decorators   import login_required_json

budget_bp = Blueprint('budget', __name__)


# ── /budget (canonical) y /presupuesto (frontend alias) ───────────────────────

@budget_bp.route('/budget', methods=['GET'])
@budget_bp.route('/presupuesto', methods=['GET'])
@login_required_json
def get_budget():
    try:
        data = BudgetService.get(current_user.id)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@budget_bp.route('/budget', methods=['POST'])
@budget_bp.route('/presupuesto', methods=['POST'])
@login_required_json
def set_budget():
    try:
        data = request.get_json(silent=True)
        if not data or 'amount' not in data:
            return jsonify({'error': 'Se requiere el campo "amount".'}), 400
        amount = float(data['amount'])
        if amount < 0:
            return jsonify({'error': 'El presupuesto no puede ser negativo.'}), 400
        budget = BudgetService.set(current_user.id, amount)
        return jsonify({'message': 'Presupuesto guardado.', **budget}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
