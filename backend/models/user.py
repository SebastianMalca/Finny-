# backend/models/user.py
# User model — stores authentication credentials with bcrypt-hashed passwords.

import secrets
from datetime import datetime, timedelta
from flask_login import UserMixin
from backend.models import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id            = db.Column(db.Integer,     primary_key=True, autoincrement=True)
    email         = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username      = db.Column(db.String(100), nullable=False)
    # password_hash stores the Werkzeug-generated bcrypt hash (never plain text)
    password_hash = db.Column(db.String(255), nullable=False)
    reset_token   = db.Column(db.String(255), nullable=True)
    reset_expires = db.Column(db.DateTime,    nullable=True)
    is_active     = db.Column(db.Boolean,     default=True, nullable=False)
    created_at    = db.Column(db.DateTime,    default=datetime.utcnow, nullable=False)

    # Relationships
    profile      = db.relationship('UserProfile', back_populates='user', uselist=False,
                                   cascade='all, delete-orphan')
    purchases    = db.relationship('Purchase',    back_populates='user',
                                   cascade='all, delete-orphan')
    budgets      = db.relationship('Budget',      back_populates='user',
                                   cascade='all, delete-orphan')
    streak       = db.relationship('Streak',      back_populates='user', uselist=False,
                                   cascade='all, delete-orphan')
    missions     = db.relationship('Mission',     back_populates='user',
                                   cascade='all, delete-orphan')
    achievements = db.relationship('Achievement', back_populates='user',
                                   cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # ── Password helpers ──────────────────────────────────────────────────────

    def generate_reset_token(self) -> str:
        """Generate a URL-safe reset token and store its expiry."""
        token = secrets.token_urlsafe(32)
        self.reset_token   = token
        self.reset_expires = datetime.utcnow() + timedelta(hours=1)
        return token

    def clear_reset_token(self):
        self.reset_token   = None
        self.reset_expires = None

    def is_reset_token_valid(self, token: str) -> bool:
        return (
            self.reset_token is not None
            and self.reset_token == token
            and self.reset_expires is not None
            and datetime.utcnow() < self.reset_expires
        )

    def to_dict(self) -> dict:
        return {
            'id':         self.id,
            'email':      self.email,
            'username':   self.username,
            'is_active':  self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<User {self.email}>'
