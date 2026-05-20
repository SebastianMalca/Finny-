# backend/repositories/user_repository.py
# Data-access layer for User: find, create, update.

from backend.models import db
from backend.models.user import User


class UserRepository:

    @staticmethod
    def find_by_id(user_id: int) -> User | None:
        return db.session.get(User, user_id)

    @staticmethod
    def find_by_email(email: str) -> User | None:
        return User.query.filter_by(email=email.lower().strip()).first()

    @staticmethod
    def email_exists(email: str) -> bool:
        return User.query.filter_by(email=email.lower().strip()).count() > 0

    @staticmethod
    def create(email: str, username: str, password_hash: str) -> User:
        user = User(
            email=email.lower().strip(),
            username=username.strip(),
            password_hash=password_hash,
        )
        db.session.add(user)
        db.session.flush()   # get user.id without committing yet
        return user

    @staticmethod
    def save(user: User) -> User:
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def find_by_reset_token(token: str) -> User | None:
        return User.query.filter_by(reset_token=token).first()
