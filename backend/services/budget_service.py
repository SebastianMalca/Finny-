# backend/services/budget_service.py
# Business logic for monthly budgets.

from datetime import date
from backend.repositories.budget_repository import BudgetRepository


class BudgetService:

    @staticmethod
    def _current_month() -> str:
        return date.today().strftime('%Y-%m')

    @staticmethod
    def get(user_id: int, month: str = None) -> dict:
        month  = month or BudgetService._current_month()
        budget = BudgetRepository.find_by_month(user_id, month)
        if budget:
            return budget.to_dict()
        return {'monthly_amount': 0.0, 'month': month}

    @staticmethod
    def set(user_id: int, amount: float, month: str = None) -> dict:
        month  = month or BudgetService._current_month()
        budget = BudgetRepository.upsert(user_id, month, amount)
        return budget.to_dict()
