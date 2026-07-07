# backend/services/dashboard_service.py
# Aggregates all data needed for the main dashboard view.

import calendar
from datetime import date, timedelta
from backend.repositories.purchase_repository import PurchaseRepository
from backend.repositories.budget_repository   import BudgetRepository
from backend.repositories.streak_repository   import StreakRepository


class DashboardService:

    @staticmethod
    def get(user_id: int) -> dict:
        today          = date.today()
        month_str      = today.strftime('%Y-%m')
        month_start    = today.replace(day=1)
        days_in_month  = calendar.monthrange(today.year, today.month)[1]
        days_remaining = days_in_month - today.day + 1

        budget_row     = BudgetRepository.find_by_month(user_id, month_str)
        monthly_budget = float(budget_row.monthly_amount) if budget_row else 0.0

        month_spent     = PurchaseRepository.sum_month(user_id, month_start)
        today_spent     = PurchaseRepository.sum_by_date(user_id, today)
        yesterday_spent = PurchaseRepository.sum_by_date(user_id, today - timedelta(days=1))

        week_start  = today - timedelta(days=today.weekday())
        week_spent  = PurchaseRepository.sum_since(user_id, week_start)

        remaining       = max(0.0, monthly_budget - month_spent)

        from backend.repositories.profile_repository import ProfileRepository
        profile = ProfileRepository.find_by_user(user_id)
        if profile and profile.daily_budget is not None and float(profile.daily_budget) > 0:
            daily_available = float(profile.daily_budget)
        else:
            daily_available = round(remaining / days_remaining, 2) if days_remaining > 0 else 0.0
        budget_used_pct = round(month_spent / monthly_budget * 100, 1) if monthly_budget > 0 else 0.0
        overspent       = monthly_budget > 0 and month_spent > monthly_budget
        alert_mode      = monthly_budget > 0 and not overspent and (remaining / monthly_budget) < 0.20

        return {
            'budget':             round(monthly_budget, 2),
            'month_spent':        round(month_spent, 2),
            'remaining':          round(remaining, 2),
            'daily_available':    daily_available,
            'today_spent':        round(today_spent, 2),
            'yesterday_spent':    round(yesterday_spent, 2),
            'week_spent':         round(week_spent, 2),
            'budget_used_pct':    budget_used_pct,
            'days_remaining':     days_remaining,
            'days_in_month':      days_in_month,
            'alert_mode':         alert_mode,
            'overspent':          overspent,
            'today_vs_yesterday': round(today_spent - yesterday_spent, 2),
        }

    @staticmethod
    def get_spending_trend(user_id: int, days: int = 7) -> list[dict]:
        today  = date.today()
        result = []
        for i in range(days - 1, -1, -1):
            d       = today - timedelta(days=i)
            total   = PurchaseRepository.sum_by_date(user_id, d)
            # count for that day
            from backend.models.purchase import Purchase
            from backend.models import db
            from sqlalchemy import func
            count = db.session.query(func.count(Purchase.id)).filter(
                Purchase.user_id == user_id,
                func.date(Purchase.created_at) == d,
            ).scalar() or 0
            result.append({
                'date':  d.isoformat(),
                'label': d.strftime('%a %d'),
                'short': d.strftime('%a'),
                'total': round(total, 2),
                'count': count,
            })
        return result

    @staticmethod
    def get_stats(user_id: int) -> dict:
        by_cat    = PurchaseRepository.stats_by_category(user_id)
        grand     = PurchaseRepository.grand_total(user_id)
        return {'by_category': by_cat, 'grand_total': grand}
