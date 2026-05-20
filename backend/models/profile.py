# backend/models/profile.py
# UserProfile model — XP, level and avatar for each user.

from datetime import datetime
from backend.models import db

XP_PER_LEVEL = 200


class UserProfile(db.Model):
    __tablename__ = 'user_profiles'

    id         = db.Column(db.Integer,  primary_key=True, autoincrement=True)
    user_id    = db.Column(db.Integer,  db.ForeignKey('users.id', ondelete='CASCADE'),
                           nullable=False, unique=True, index=True)
    name       = db.Column(db.String(100), default='Joven')
    xp         = db.Column(db.Integer,  default=0, nullable=False)
    level      = db.Column(db.Integer,  default=1, nullable=False)
    avatar     = db.Column(db.String(10), default='JV')
    tips_read  = db.Column(db.Integer,  default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', back_populates='profile')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self) -> dict:
        xp_for_next = self.level * XP_PER_LEVEL
        xp_progress = self.xp % XP_PER_LEVEL
        xp_pct      = int(xp_progress / xp_for_next * 100) if xp_for_next > 0 else 0
        return {
            'id':          self.id,
            'user_id':     self.user_id,
            'name':        self.name,
            'xp':          self.xp,
            'level':       self.level,
            'avatar':      self.avatar,
            'tips_read':   self.tips_read,
            'xp_for_next': xp_for_next,
            'xp_progress': xp_progress,
            'xp_pct':      xp_pct,
        }

    def __repr__(self):
        return f'<UserProfile user={self.user_id} level={self.level} xp={self.xp}>'
