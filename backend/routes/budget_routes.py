# backend/routes/budget_routes.py
# Budget endpoints.

from flask import Blueprint, request, jsonify
from flask_login import current_user

from backend.services.budget_service import BudgetService
from backend.utils.auth_decorators   import login_required_json

budget_bp = Blueprint('budget', __name__, url_prefix='/presupuesto')


@budget_bp.route('', methods=['GET'])
@login_required_json
def get_budget():
    try:
        return jsonify(BudgetService.get(current_user.id)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@budget_bp.route('', methods=['POST'])
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
        return jsonify({'message': 'Presupuesto guardado.', 'budget': budget}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
