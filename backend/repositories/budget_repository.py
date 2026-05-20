# backend/repositories/budget_repository.py
# Data-access layer for Budget.

from backend.models import db
from backend.models.budget import Budget


class BudgetRepository:

    @staticmethod
    def find_by_month(user_id: int, month: str) -> Budget | None:
        return Budget.query.filter_by(user_id=user_id, month=month).first()

    @staticmethod
    def upsert(user_id: int, month: str, amount: float) -> Budget:
        budget = Budget.query.filter_by(user_id=user_id, month=month).first()
        if budget:
            budget.monthly_amount = amount
        else:
            budget = Budget(user_id=user_id, month=month, monthly_amount=amount)
            db.session.add(budget)
        db.session.commit()
        return budget
