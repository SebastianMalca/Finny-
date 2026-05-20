# backend/models/purchase.py
# Purchase model — each expense record belongs to one user.

from datetime import datetime
from backend.models import db


class Purchase(db.Model):
    __tablename__ = 'purchases'

    id         = db.Column(db.Integer,      primary_key=True, autoincrement=True)
    user_id    = db.Column(db.Integer,      db.ForeignKey('users.id', ondelete='CASCADE'),
                           nullable=False, index=True)
    name       = db.Column(db.String(100),  nullable=False)
    amount     = db.Column(db.Numeric(12, 2), nullable=False)
    category   = db.Column(db.String(50),   nullable=False, default='Other')
    created_at = db.Column(db.DateTime,     default=datetime.utcnow, nullable=False)

    user = db.relationship('User', back_populates='purchases')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self) -> dict:
        return {
            'id':         self.id,
            'user_id':    self.user_id,
            'name':       self.name,
            'amount':     float(self.amount),
            'category':   self.category,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<Purchase {self.name} ${self.amount}>'
