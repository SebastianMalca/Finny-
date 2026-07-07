# backend/repositories/streak_repository.py
# Data-access layer for Streak.

from datetime import date, timedelta
from backend.models import db
from backend.models.streak import Streak


class StreakRepository:

    @staticmethod
    def find_by_user(user_id: int) -> Streak | None:
        return Streak.query.filter_by(user_id=user_id).first()

    @staticmethod
    def create(user_id: int) -> Streak:
        streak = Streak(
            user_id=user_id,
            current_streak=0,
            longest_streak=0,
            total_active_days=0
        )
        db.session.add(streak)
        db.session.flush()
        return streak

    @staticmethod
    def update_saving_streak(user_id: int, saved_yesterday: bool) -> Streak:
        """Update the saving streak based on whether the user saved yesterday.
        
        If saved_yesterday is True, the streak continues/starts.
        If False, the streak resets to 0.
        """
        today = date.today().isoformat()

        streak = Streak.query.filter_by(user_id=user_id).first()
        if not streak:
            streak = Streak(
                user_id=user_id,
                current_streak=0,
                longest_streak=0,
                total_active_days=0
            )
            db.session.add(streak)

        # Avoid double-evaluation on same day
        if streak.last_active_date == today:
            return streak

        if saved_yesterday:
            streak.current_streak    += 1
            streak.total_active_days += 1
        else:
            streak.current_streak = 0

        streak.longest_streak   = max(streak.longest_streak, streak.current_streak)
        streak.last_active_date = today
        db.session.commit()
        return streak
