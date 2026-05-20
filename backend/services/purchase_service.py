# backend/services/purchase_service.py
# Business logic for purchases, including validation and side-effects.

from backend.repositories.purchase_repository    import PurchaseRepository
from backend.services.gamification_service       import GamificationService
from transversal.constants                       import CATEGORIES, MAX_NAME_LENGTH, MAX_AMOUNT


class PurchaseService:

    @staticmethod
    def validate(data: dict) -> str | None:
        """Returns error string or None if valid."""
        if not data:
            return 'El cuerpo de la solicitud debe ser JSON válido.'
        name = str(data.get('name', '')).strip()
        if not name:
            return 'El campo "name" es requerido.'
        if len(name) > MAX_NAME_LENGTH:
            return f'El nombre no puede superar {MAX_NAME_LENGTH} caracteres.'
        raw = data.get('amount')
        if raw is None:
            return 'El campo "amount" es requerido.'
        try:
            amount = float(raw)
        except (TypeError, ValueError):
            return 'El campo "amount" debe ser un número.'
        if amount <= 0:
            return 'El monto debe ser mayor que 0.'
        if amount > MAX_AMOUNT:
            return f'El monto no puede superar {MAX_AMOUNT:,.2f}.'
        cat   = data.get('category', '')
        valid = CATEGORIES + ['Other']
        if cat and cat not in valid:
            return f'Categoría inválida. Use: {", ".join(valid)}'
        return None

    @staticmethod
    def create(user_id: int, data: dict) -> dict:
        """Create a purchase and run gamification side-effects."""
        name     = data['name'].strip()
        amount   = round(float(data['amount']), 2)
        category = (data.get('category', 'Other') or 'Other').strip()

        purchase = PurchaseRepository.create(user_id, name, amount, category)

        # Gamification side-effects (XP, missions, achievements, streak)
        GamificationService.on_new_purchase(user_id)

        return purchase.to_dict()

    @staticmethod
    def get_all(user_id: int, category: str = None) -> list[dict]:
        purchases = PurchaseRepository.find_all(user_id, category)
        return [p.to_dict() for p in purchases]

    @staticmethod
    def get_by_id(user_id: int, purchase_id: int) -> dict | None:
        p = PurchaseRepository.find_by_id(user_id, purchase_id)
        return p.to_dict() if p else None

    @staticmethod
    def delete(user_id: int, purchase_id: int) -> bool:
        p = PurchaseRepository.find_by_id(user_id, purchase_id)
        if not p:
            return False
        return PurchaseRepository.delete(p)
