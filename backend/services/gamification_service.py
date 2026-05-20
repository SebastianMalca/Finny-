# backend/services/gamification_service.py
# XP, missions, achievements, and streak side-effects.

from datetime import datetime
from backend.repositories.streak_repository      import StreakRepository
from backend.repositories.mission_repository     import MissionRepository
from backend.repositories.achievement_repository import AchievementRepository
from backend.repositories.profile_repository     import ProfileRepository
from backend.repositories.purchase_repository    import PurchaseRepository


class GamificationService:

    @staticmethod
    def on_new_purchase(user_id: int):
        """Run all side-effects triggered by a new purchase."""
        # 1. Update streak
        streak = StreakRepository.update_on_activity(user_id)

        # 2. Update missions and collect newly completed
        completed = []
        completed += GamificationService._update_missions(user_id, 'expense_count',
            PurchaseRepository.count_all(user_id))
        completed += GamificationService._update_missions(user_id, 'category_count',
            PurchaseRepository.count_distinct_categories(user_id))
        completed += GamificationService._update_missions(user_id, 'streak',
            streak.current_streak)

        # 3. Award XP for completed missions + base XP per expense
        for m in completed:
            ProfileRepository.add_xp(user_id, m.reward_xp)
        ProfileRepository.add_xp(user_id, 5)  # base XP per expense

        # 4. Check achievements
        GamificationService._check_achievements(user_id)

    @staticmethod
    def on_tip_read(user_id: int):
        """Run side-effects when a user reads a tip."""
        ProfileRepository.increment_tips_read(user_id)
        profile = ProfileRepository.find_by_user(user_id)
        completed = GamificationService._update_missions(user_id, 'tips_read',
            profile.tips_read if profile else 0)
        for m in completed:
            ProfileRepository.add_xp(user_id, m.reward_xp)
        ProfileRepository.add_xp(user_id, 5)
        GamificationService._check_achievements(user_id)

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

        # streak achievements
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
