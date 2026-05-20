# backend/repositories/profile_repository.py
# Data-access layer for UserProfile.

from backend.models import db
from backend.models.profile import UserProfile, XP_PER_LEVEL


class ProfileRepository:

    @staticmethod
    def find_by_user(user_id: int) -> UserProfile | None:
        return UserProfile.query.filter_by(user_id=user_id).first()

    @staticmethod
    def create(user_id: int, name: str = 'Joven', avatar: str = 'JV') -> UserProfile:
        profile = UserProfile(
            user_id=user_id,
            name=name,
            avatar=avatar,
            xp=0,
            level=1,
            tips_read=0
        )
        db.session.add(profile)
        db.session.flush()
        return profile

    @staticmethod
    def update(profile: UserProfile, name: str = None, avatar: str = None) -> UserProfile:
        if name:   profile.name   = name
        if avatar: profile.avatar = avatar
        db.session.commit()
        return profile

    @staticmethod
    def add_xp(user_id: int, amount: int) -> UserProfile:
        profile = ProfileRepository.find_by_user(user_id)
        if profile:
            profile.xp   += amount
            profile.level = max(1, profile.xp // XP_PER_LEVEL + 1)
            db.session.commit()
        return profile

    @staticmethod
    def increment_tips_read(user_id: int) -> UserProfile:
        profile = ProfileRepository.find_by_user(user_id)
        if profile:
            profile.tips_read += 1
            db.session.commit()
        return profile
