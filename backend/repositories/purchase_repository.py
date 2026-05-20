# backend/repositories/purchase_repository.py
# Data-access layer for Purchase.

from datetime import date, timedelta
from sqlalchemy import func
from backend.models import db
from backend.models.purchase import Purchase


class PurchaseRepository:

    @staticmethod
    def create(user_id: int, name: str, amount: float, category: str) -> Purchase:
        p = Purchase(user_id=user_id, name=name, amount=amount, category=category)
        db.session.add(p)
        db.session.commit()
        return p

    @staticmethod
    def find_all(user_id: int, category: str = None) -> list[Purchase]:
        q = Purchase.query.filter_by(user_id=user_id)
        if category:
            q = q.filter_by(category=category)
        return q.order_by(Purchase.id.desc()).all()

    @staticmethod
    def find_by_id(user_id: int, purchase_id: int) -> Purchase | None:
        return Purchase.query.filter_by(id=purchase_id, user_id=user_id).first()

    @staticmethod
    def delete(purchase: Purchase) -> bool:
        db.session.delete(purchase)
        db.session.commit()
        return True

    @staticmethod
    def count_all(user_id: int) -> int:
        return Purchase.query.filter_by(user_id=user_id).count()

    @staticmethod
    def count_distinct_categories(user_id: int) -> int:
        return db.session.query(
            func.count(func.distinct(Purchase.category))
        ).filter(Purchase.user_id == user_id).scalar() or 0

    @staticmethod
    def sum_by_date(user_id: int, target_date: date) -> float:
        result = db.session.query(func.coalesce(func.sum(Purchase.amount), 0)).filter(
            Purchase.user_id == user_id,
            func.date(Purchase.created_at) == target_date,
        ).scalar()
        return float(result)

    @staticmethod
    def sum_month(user_id: int, month_start: date) -> float:
        result = db.session.query(func.coalesce(func.sum(Purchase.amount), 0)).filter(
            Purchase.user_id == user_id,
            Purchase.created_at >= month_start,
        ).scalar()
        return float(result)

    @staticmethod
    def sum_since(user_id: int, since_date: date) -> float:
        result = db.session.query(func.coalesce(func.sum(Purchase.amount), 0)).filter(
            Purchase.user_id == user_id,
            func.date(Purchase.created_at) >= since_date,
        ).scalar()
        return float(result)

    @staticmethod
    def stats_by_category(user_id: int) -> list[dict]:
        rows = db.session.query(
            Purchase.category,
            func.count(Purchase.id).label('count'),
            func.sum(Purchase.amount).label('total'),
            func.avg(Purchase.amount).label('average'),
            func.min(Purchase.amount).label('minimum'),
            func.max(Purchase.amount).label('maximum'),
        ).filter(
            Purchase.user_id == user_id
        ).group_by(Purchase.category).order_by(func.sum(Purchase.amount).desc()).all()
        return [
            {
                'category': r.category,
                'count':    r.count,
                'total':    float(r.total),
                'average':  float(r.average),
                'minimum':  float(r.minimum),
                'maximum':  float(r.maximum),
            }
            for r in rows
        ]

    @staticmethod
    def grand_total(user_id: int) -> dict:
        row = db.session.query(
            func.count(Purchase.id).label('count'),
            func.coalesce(func.sum(Purchase.amount), 0).label('total'),
        ).filter(Purchase.user_id == user_id).one()
        return {'count': row.count, 'total': float(row.total)}
