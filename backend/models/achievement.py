# backend/models/achievement.py
# Achievement model — per-user achievements/badges.

from datetime import datetime
from backend.models import db


class Achievement(db.Model):
    __tablename__ = 'achievements'
    __table_args__ = (
        db.UniqueConstraint('user_id', 'key', name='uq_user_achievement_key'),
    )

    id          = db.Column(db.Integer,  primary_key=True, autoincrement=True)
    user_id     = db.Column(db.Integer,  db.ForeignKey('users.id', ondelete='CASCADE'),
                            nullable=False, index=True)
    key         = db.Column(db.String(50),  nullable=False)
    title       = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    icon        = db.Column(db.String(10),  default='🏆')
    unlocked    = db.Column(db.Boolean,     default=False, nullable=False)
    unlocked_at = db.Column(db.DateTime,    nullable=True)

    user = db.relationship('User', back_populates='achievements')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self) -> dict:
        return {
            'id':          self.id,
            'user_id':     self.user_id,
            'key':         self.key,
            'title':       self.title,
            'description': self.description,
            'icon':        self.icon,
            'unlocked':    self.unlocked,
            'unlocked_at': self.unlocked_at.isoformat() if self.unlocked_at else None,
        }

    def __repr__(self):
        return f'<Achievement {self.key} user={self.user_id} unlocked={self.unlocked}>'
