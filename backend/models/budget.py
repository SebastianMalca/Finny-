# backend/models/budget.py
# Budget model — monthly budget per user.

from datetime import datetime
from backend.models import db


class Budget(db.Model):
    __tablename__ = 'budgets'
    __table_args__ = (
        db.UniqueConstraint('user_id', 'month', name='uq_user_month'),
    )

    id             = db.Column(db.Integer,      primary_key=True, autoincrement=True)
    user_id        = db.Column(db.Integer,      db.ForeignKey('users.id', ondelete='CASCADE'),
                               nullable=False, index=True)
    monthly_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    month          = db.Column(db.String(7),    nullable=False)   # format: YYYY-MM
    created_at     = db.Column(db.DateTime,     default=datetime.utcnow, nullable=False)

    user = db.relationship('User', back_populates='budgets')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self) -> dict:
        return {
            'id':             self.id,
            'user_id':        self.user_id,
            'monthly_amount': float(self.monthly_amount),
            'month':          self.month,
        }

    def __repr__(self):
        return f'<Budget user={self.user_id} month={self.month} amount={self.monthly_amount}>'
