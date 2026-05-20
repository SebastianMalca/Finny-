# backend/models/mission.py
# Mission model — per-user missions with progress tracking.

from datetime import datetime
from backend.models import db


class Mission(db.Model):
    __tablename__ = 'missions'
    __table_args__ = (
        db.UniqueConstraint('user_id', 'key', name='uq_user_mission_key'),
    )

    id            = db.Column(db.Integer,      primary_key=True, autoincrement=True)
    user_id       = db.Column(db.Integer,      db.ForeignKey('users.id', ondelete='CASCADE'),
                              nullable=False, index=True)
    key           = db.Column(db.String(50),   nullable=False)
    title         = db.Column(db.String(100),  nullable=False)
    description   = db.Column(db.String(255),  nullable=False)
    icon          = db.Column(db.String(10),   default='🎯')
    type          = db.Column(db.String(50),   nullable=False)
    target_value  = db.Column(db.Numeric(10, 2), default=1)
    current_value = db.Column(db.Numeric(10, 2), default=0)
    completed     = db.Column(db.Boolean,      default=False, nullable=False)
    reward_xp     = db.Column(db.Integer,      default=50, nullable=False)
    completed_at  = db.Column(db.DateTime,     nullable=True)

    user = db.relationship('User', back_populates='missions')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self) -> dict:
        target  = float(self.target_value)  if self.target_value  else 1
        current = float(self.current_value) if self.current_value else 0
        pct     = min(100, int(current / target * 100)) if target > 0 else 0
        return {
            'id':            self.id,
            'user_id':       self.user_id,
            'key':           self.key,
            'title':         self.title,
            'description':   self.description,
            'icon':          self.icon,
            'type':          self.type,
            'target_value':  target,
            'current_value': current,
            'completed':     self.completed,
            'reward_xp':     self.reward_xp,
            'progress_pct':  pct,
            'completed_at':  self.completed_at.isoformat() if self.completed_at else None,
        }

    def __repr__(self):
        return f'<Mission {self.key} user={self.user_id} done={self.completed}>'
