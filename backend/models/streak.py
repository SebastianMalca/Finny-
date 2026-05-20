# backend/models/streak.py
# Streak model — daily activity streak per user.

from backend.models import db


class Streak(db.Model):
    __tablename__ = 'streaks'

    id                = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id           = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                                  nullable=False, unique=True, index=True)
    current_streak    = db.Column(db.Integer, default=0, nullable=False)
    longest_streak    = db.Column(db.Integer, default=0, nullable=False)
    last_active_date  = db.Column(db.String(10), nullable=True)   # ISO date: YYYY-MM-DD
    total_active_days = db.Column(db.Integer, default=0, nullable=False)

    user = db.relationship('User', back_populates='streak')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self) -> dict:
        return {
            'user_id':           self.user_id,
            'current_streak':    self.current_streak,
            'longest_streak':    self.longest_streak,
            'last_active_date':  self.last_active_date,
            'total_active_days': self.total_active_days,
        }

    def __repr__(self):
        return f'<Streak user={self.user_id} current={self.current_streak}>'
