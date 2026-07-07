# backend/services/gamification_service.py
# XP, missions, achievements, and streak side-effects.

from datetime import datetime, date, timedelta
from backend.repositories.streak_repository      import StreakRepository
from backend.repositories.mission_repository     import MissionRepository
from backend.repositories.achievement_repository import AchievementRepository
from backend.repositories.profile_repository     import ProfileRepository
from backend.repositories.purchase_repository    import PurchaseRepository
from backend.repositories.budget_repository      import BudgetRepository
import calendar


class GamificationService:

    @staticmethod
    def on_new_purchase(user_id: int):
        """Run all side-effects triggered by a new purchase.
        NOTE: Streak is NO LONGER updated here — streaks now reward saving,
        not spending. The streak is evaluated on dashboard load.
        """
        # 1. Update missions and collect newly completed
        completed = []
        completed += GamificationService._update_missions(user_id, 'expense_count',
            PurchaseRepository.count_all(user_id))
        completed += GamificationService._update_missions(user_id, 'category_count',
            PurchaseRepository.count_distinct_categories(user_id))

        # 2. Award XP for completed missions + base XP per expense
        for m in completed:
            ProfileRepository.add_xp(user_id, m.reward_xp)
        ProfileRepository.add_xp(user_id, 5)  # base XP per expense

        # 3. Check achievements
        GamificationService._check_achievements(user_id)

    @staticmethod
    def on_tip_read(user_id: int) -> dict:
        """Run side-effects when a user reads a tip.
        Returns dict with 'already_read' flag if user already read today.
        """
        # Guard: only allow XP once per day
        if ProfileRepository.has_read_tip_today(user_id):
            return {'already_read': True, 'xp_awarded': 0}

        ProfileRepository.increment_tips_read(user_id)
        profile = ProfileRepository.find_by_user(user_id)
        completed = GamificationService._update_missions(user_id, 'tips_read',
            profile.tips_read if profile else 0)
        for m in completed:
            ProfileRepository.add_xp(user_id, m.reward_xp)
        ProfileRepository.add_xp(user_id, 5)
        GamificationService._check_achievements(user_id)
        return {'already_read': False, 'xp_awarded': 5}

    @staticmethod
    def evaluate_saving_streak(user_id: int):
        """Evaluate whether the user saved yesterday and update the streak accordingly.
        
        "Saving" means:
        - If budget is set: yesterday's spending ≤ daily_budget (budget / days_in_month)
        - If no budget: yesterday had $0 spending (encourages setting a budget)
        
        This is called on dashboard load to evaluate the previous day.
        """
        today     = date.today()
        yesterday = today - timedelta(days=1)

        # Check if streak already evaluated today (avoid double-counting)
        streak = StreakRepository.find_by_user(user_id)
        if streak and streak.last_active_date == today.isoformat():
            # Already evaluated today — just update mission progress
            GamificationService._update_missions(user_id, 'streak', streak.current_streak)
            return streak

        # Get yesterday's spending
        yesterday_spent = PurchaseRepository.sum_by_date(user_id, yesterday)

        # Get budget info
        month_str  = yesterday.strftime('%Y-%m')
        budget_row = BudgetRepository.find_by_month(user_id, month_str)

        if budget_row and float(budget_row.monthly_amount) > 0:
            days_in_month = calendar.monthrange(yesterday.year, yesterday.month)[1]
            daily_budget  = float(budget_row.monthly_amount) / days_in_month
            saved_yesterday = yesterday_spent <= daily_budget
        else:
            # No budget set: only $0 days count as saving
            saved_yesterday = yesterday_spent == 0

        # Update the streak
        streak = StreakRepository.update_saving_streak(user_id, saved_yesterday)

        # Update streak-related missions
        GamificationService._update_missions(user_id, 'streak', streak.current_streak)

        # Check achievements
        GamificationService._check_achievements(user_id)

        return streak

    # ── Internals ──────────────────────────────────────────────────────────────

    @staticmethod
    def _update_missions(user_id: int, mission_type: str, new_value) -> list:
        """Update progress for all incomplete missions of given type. Returns completed list."""
        missions  = MissionRepository.find_incomplete_by_type(user_id, mission_type)
        completed = []
        for m in missions:
            if MissionRepository.update_progress(m, float(new_value)):
                completed.append(m)
        return completed

    @staticmethod
    def _check_achievements(user_id: int):
        """Evaluate and unlock any achievements whose conditions are met."""
        repo = AchievementRepository

        # first_step: has at least 1 purchase
        if PurchaseRepository.count_all(user_id) >= 1:
            repo.unlock(user_id, 'first_step')

        # streak achievements (now saving streaks)
        streak = StreakRepository.find_by_user(user_id)
        if streak:
            if streak.current_streak >= 7:  repo.unlock(user_id, 'on_fire')
            if streak.current_streak >= 30: repo.unlock(user_id, 'legend')

        # explorer: used all 6 categories
        if PurchaseRepository.count_distinct_categories(user_id) >= 6:
            repo.unlock(user_id, 'explorer')

        # missions_3: completed 3 missions
        if MissionRepository.count_completed(user_id) >= 3:
            repo.unlock(user_id, 'missions_3')

        # level achievements
        profile = ProfileRepository.find_by_user(user_id)
        if profile:
            if profile.level   >= 5:  repo.unlock(user_id, 'level_5')
            if profile.tips_read >= 10: repo.unlock(user_id, 'wise_reader')
