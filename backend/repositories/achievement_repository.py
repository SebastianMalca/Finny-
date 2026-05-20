# backend/repositories/achievement_repository.py
# Data-access layer for Achievement.

from datetime import datetime
from backend.models import db
from backend.models.achievement import Achievement


ACHIEVEMENT_SEEDS = [
    ('first_step',  'Primer Paso',       'Registraste tu primer gasto',                 '🎯'),
    ('on_fire',     'En Llamas',         'Alcanzaste una racha de 7 días',               '🔥'),
    ('legend',      'Leyenda Viva',      'Alcanzaste una racha de 30 días',              '👑'),
    ('explorer',    'Explorador',        'Usaste todas las categorías de gasto',         '🗺️'),
    ('missions_3',  'Misionero',         'Completaste 3 misiones',                       '🚀'),
    ('level_5',     'Mente Financiera',  'Llegaste al nivel 5',                          '🧠'),
    ('saver_pro',   'Ahorrador Pro',     'No excediste tu presupuesto un mes completo',  '💰'),
    ('wise_reader', 'Sabio del Dinero',  'Leíste 10 consejos del día',                   '📚'),
]


class AchievementRepository:

    @staticmethod
    def seed_for_user(user_id: int):
        """Create locked achievements for a newly registered user."""
        for key, title, desc, icon in ACHIEVEMENT_SEEDS:
            exists = Achievement.query.filter_by(user_id=user_id, key=key).first()
            if not exists:
                a = Achievement(
                    user_id=user_id, key=key, title=title,
                    description=desc, icon=icon, unlocked=False,
                )
                db.session.add(a)
        db.session.flush()

    @staticmethod
    def find_all(user_id: int) -> list[Achievement]:
        return Achievement.query.filter_by(user_id=user_id).order_by(
            Achievement.unlocked.desc(), Achievement.id.asc()
        ).all()

    @staticmethod
    def find_by_key(user_id: int, key: str) -> Achievement | None:
        return Achievement.query.filter_by(user_id=user_id, key=key).first()

    @staticmethod
    def unlock(user_id: int, key: str) -> Achievement | None:
        """Unlock an achievement if not already unlocked. Returns the achievement or None."""
        a = Achievement.query.filter_by(user_id=user_id, key=key, unlocked=False).first()
        if a:
            a.unlocked    = True
            a.unlocked_at = datetime.utcnow()
            db.session.commit()
            return a
        return None
