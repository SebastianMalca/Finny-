# backend/services/profile_service.py
# Profile retrieval and update logic.

from backend.repositories.profile_repository import ProfileRepository


class ProfileService:

    @staticmethod
    def get(user_id: int) -> dict:
        profile = ProfileRepository.find_by_user(user_id)
        return profile.to_dict() if profile else {}

    @staticmethod
    def update(user_id: int, name: str = None, avatar: str = None, daily_budget: float = None) -> dict:
        profile = ProfileRepository.find_by_user(user_id)
        if not profile:
            return {}
        return ProfileRepository.update(profile, name=name, avatar=avatar, daily_budget=daily_budget).to_dict()
