# backend/routes/purchase_routes.py
# Purchases CRUD endpoints — all protected by login.

from flask import Blueprint, request, jsonify
from flask_login import current_user

from backend.services.purchase_service import PurchaseService
from backend.utils.auth_decorators     import login_required_json
from transversal.constants             import CATEGORIES

purchase_bp = Blueprint('purchases', __name__, url_prefix='/compras')


@purchase_bp.route('', methods=['GET'])
@login_required_json
def list_purchases():
    cat = request.args.get('category', '').strip() or None
    if cat and cat not in (CATEGORIES + ['Other']):
        return jsonify({'error': f'Categoría inválida: "{cat}"'}), 400
    try:
        purchases = PurchaseService.get_all(current_user.id, cat)
        total = sum(p['amount'] for p in purchases)
        return jsonify({
            'purchases':   purchases,
            'total':       round(total, 2),
            'count':       len(purchases),
            'categories':  CATEGORIES + ['Other'],
            'filtered_by': cat,
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@purchase_bp.route('', methods=['POST'])
@login_required_json
def add_purchase():
    try:
        data = request.get_json(silent=True)
        err  = PurchaseService.validate(data)
        if err:
            return jsonify({'error': err}), 400
        purchase = PurchaseService.create(current_user.id, data)
        return jsonify({'message': 'Compra agregada correctamente.', 'purchase': purchase}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@purchase_bp.route('/<int:pid>', methods=['GET'])
@login_required_json
def get_purchase(pid):
    try:
        p = PurchaseService.get_by_id(current_user.id, pid)
        if not p:
            return jsonify({'error': f'Compra {pid} no encontrada.'}), 404
        return jsonify({'purchase': p}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@purchase_bp.route('/<int:pid>', methods=['DELETE'])
@login_required_json
def remove_purchase(pid):
    try:
        if not PurchaseService.delete(current_user.id, pid):
            return jsonify({'error': f'Compra {pid} no encontrada.'}), 404
        return jsonify({'message': f'Compra {pid} eliminada.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
