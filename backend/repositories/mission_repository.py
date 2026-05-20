# backend/repositories/mission_repository.py
# Data-access layer for Mission.

from datetime import datetime
from backend.models import db
from backend.models.mission import Mission


# Default mission definitions (key, title, description, icon, type, target, xp)
MISSION_SEEDS = [
    ('first_expense',  'Primer Gasto',        'Registra tu primer gasto',                    '💸', 'expense_count',  1,   30),
    ('expense_5',      'En Movimiento',        'Registra 5 gastos en total',                  '🚀', 'expense_count',  5,   50),
    ('expense_20',     'Imparable',            'Llega a 20 gastos registrados',               '⚡', 'expense_count',  20,  100),
    ('streak_3',       'Tres en Raya',         'Mantén una racha de 3 días',                  '🔥', 'streak',         3,   50),
    ('streak_7',       'Semana Épica',         'Mantén una racha de 7 días seguidos',         '🌟', 'streak',         7,   150),
    ('streak_30',      'Leyenda',              'Mantén una racha de 30 días',                 '👑', 'streak',         30,  500),
    ('all_categories', 'Explorador',           'Usa las 6 categorías de gasto',               '🗺️', 'category_count', 6,   100),
    ('tip_5',          'Aprendiz Sabio',       'Lee 5 consejos del día',                      '📚', 'tips_read',      5,   75),
    ('under_budget_m', 'Mes Disciplinado',     'No excedas tu presupuesto en un mes',        '💎', 'under_budget',   1,   200),
]


class MissionRepository:

    @staticmethod
    def seed_for_user(user_id: int):
        """Create the default missions for a newly registered user."""
        for key, title, desc, icon, mtype, target, xp in MISSION_SEEDS:
            exists = Mission.query.filter_by(user_id=user_id, key=key).first()
            if not exists:
                m = Mission(
                    user_id=user_id, key=key, title=title,
                    description=desc, icon=icon, type=mtype,
                    target_value=target, reward_xp=xp,
                    current_value=0, completed=False,
                )
                db.session.add(m)
        db.session.flush()

    @staticmethod
    def find_all(user_id: int) -> list[Mission]:
        return Mission.query.filter_by(user_id=user_id).order_by(
            Mission.completed.asc(), Mission.id.asc()
        ).all()

    @staticmethod
    def find_incomplete_by_type(user_id: int, mission_type: str) -> list[Mission]:
        return Mission.query.filter_by(
            user_id=user_id, type=mission_type, completed=False
        ).all()

    @staticmethod
    def count_completed(user_id: int) -> int:
        return Mission.query.filter_by(user_id=user_id, completed=True).count()

    @staticmethod
    def update_progress(mission: Mission, new_value: float) -> bool:
        """Update mission progress. Returns True if newly completed."""
        newly_completed = False
        mission.current_value = new_value
        if not mission.completed and new_value >= float(mission.target_value):
            mission.completed    = True
            mission.completed_at = datetime.utcnow()
            newly_completed      = True
        db.session.commit()
        return newly_completed
