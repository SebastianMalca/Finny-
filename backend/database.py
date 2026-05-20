# FINNY Finance App - Database Layer v2
# SQLite persistence: purchases, budget, profile, streaks, missions, achievements

import sqlite3
import os
import calendar
import random
from datetime import datetime, date, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), 'finny.db')
XP_PER_LEVEL = 200  # XP needed to level up


# ── Connection ────────────────────────────────────────────────────────────────

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── Init ──────────────────────────────────────────────────────────────────────

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL,
            amount     REAL    NOT NULL CHECK(amount > 0),
            category   TEXT    NOT NULL DEFAULT 'Other',
            created_at TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS budget (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            monthly_amount REAL    NOT NULL DEFAULT 0,
            month          TEXT    NOT NULL UNIQUE,
            created_at     TEXT    DEFAULT (datetime('now','localtime'))
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS user_profile (
            id         INTEGER PRIMARY KEY CHECK(id=1),
            name       TEXT    DEFAULT 'Joven',
            xp         INTEGER DEFAULT 0,
            level      INTEGER DEFAULT 1,
            avatar     TEXT    DEFAULT 'JV',
            tips_read  INTEGER DEFAULT 0,
            created_at TEXT    DEFAULT (datetime('now','localtime'))
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS streak (
            id                INTEGER PRIMARY KEY CHECK(id=1),
            current_streak    INTEGER DEFAULT 0,
            longest_streak    INTEGER DEFAULT 0,
            last_active_date  TEXT,
            total_active_days INTEGER DEFAULT 0
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS missions (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            key           TEXT    NOT NULL UNIQUE,
            title         TEXT    NOT NULL,
            description   TEXT    NOT NULL,
            icon          TEXT    DEFAULT '🎯',
            type          TEXT    NOT NULL,
            target_value  REAL    DEFAULT 1,
            current_value REAL    DEFAULT 0,
            completed     INTEGER DEFAULT 0,
            reward_xp     INTEGER DEFAULT 50,
            completed_at  TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS achievements (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            key         TEXT    NOT NULL UNIQUE,
            title       TEXT    NOT NULL,
            description TEXT    NOT NULL,
            icon        TEXT    DEFAULT 'trophy',
            unlocked    INTEGER DEFAULT 0,
            unlocked_at TEXT
        )
    ''')

    conn.commit()

    # Seed singletons
    c.execute('INSERT OR IGNORE INTO user_profile (id) VALUES (1)')
    c.execute('INSERT OR IGNORE INTO streak       (id) VALUES (1)')
    _seed_missions(c)
    _seed_achievements(c)
    conn.commit()
    conn.close()
    print("[DB] Database initialized at:", DB_PATH)


def _seed_missions(c):
    rows = [
        ('first_expense',  'Primer Gasto',       'Registra tu primer gasto',                    '💸', 'expense_count',   1,   30),
        ('expense_5',      'En Movimiento',       'Registra 5 gastos en total',                  '🚀', 'expense_count',   5,   50),
        ('expense_20',     'Imparable',           'Llega a 20 gastos registrados',               '⚡', 'expense_count',   20,  100),
        ('streak_3',       'Tres en Raya',        'Mantén una racha de 3 días',                  '🔥', 'streak',          3,   50),
        ('streak_7',       'Semana Épica',        'Mantén una racha de 7 días seguidos',         '🌟', 'streak',          7,   150),
        ('streak_30',      'Leyenda',             'Mantén una racha de 30 días',                 '👑', 'streak',          30,  500),
        ('all_categories', 'Explorador',          'Usa las 6 categorías de gasto',               '🗺️','category_count',  6,   100),
        ('tip_5',          'Aprendiz Sabio',      'Lee 5 consejos del día',                      '📚', 'tips_read',       5,   75),
        ('under_budget_m', 'Mes Disciplinado',    'No excedas tu presupuesto en un mes completo','💎', 'under_budget',    1,   200),
    ]
    for key, title, desc, icon, type_, target, xp in rows:
        c.execute('''INSERT OR IGNORE INTO missions
                     (key,title,description,icon,type,target_value,reward_xp)
                     VALUES (?,?,?,?,?,?,?)''',
                  (key, title, desc, icon, type_, target, xp))


def _seed_achievements(c):
    rows = [
        ('first_step',  'Primer Paso',       'Registraste tu primer gasto',                '🎯'),
        ('on_fire',     'En Llamas',         'Alcanzaste una racha de 7 días',              '🔥'),
        ('legend',      'Leyenda Viva',      'Alcanzaste una racha de 30 días',             '👑'),
        ('explorer',    'Explorador',        'Usaste todas las categorías de gasto',        '🗺️'),
        ('missions_3',  'Misionero',         'Completaste 3 misiones',                      '🚀'),
        ('level_5',     'Mente Financiera',  'Llegaste al nivel 5',                         '🧠'),
        ('saver_pro',   'Ahorrador Pro',     'No excediste tu presupuesto un mes completo', '💰'),
        ('wise_reader', 'Sabio del Dinero',  'Leíste 10 consejos del día',                  '📚'),
    ]
    for key, title, desc, icon in rows:
        c.execute('''INSERT OR IGNORE INTO achievements
                     (key,title,description,icon) VALUES (?,?,?,?)''',
                  (key, title, desc, icon))


# ── Purchases ─────────────────────────────────────────────────────────────────

def create_purchase(name: str, amount: float, category: str) -> dict:
    conn = get_connection()
    c = conn.cursor()
    c.execute('INSERT INTO purchases (name,amount,category) VALUES (?,?,?)',
              (name, amount, category))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    _on_new_purchase(category)
    return get_purchase_by_id(new_id)


def get_all_purchases(category: str = None) -> list:
    conn = get_connection()
    c = conn.cursor()
    if category:
        c.execute('SELECT * FROM purchases WHERE category=? ORDER BY id DESC', (category,))
    else:
        c.execute('SELECT * FROM purchases ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_purchase_by_id(pid: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM purchases WHERE id=?', (pid,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_purchase(pid: int) -> bool:
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM purchases WHERE id=?', (pid,))
    conn.commit()
    affected = c.rowcount
    conn.close()
    return affected > 0


def get_stats() -> dict:
    conn = get_connection()
    c = conn.cursor()
    c.execute('''SELECT category,COUNT(*) AS count,SUM(amount) AS total,
                        AVG(amount) AS average,MIN(amount) AS minimum,MAX(amount) AS maximum
                 FROM purchases GROUP BY category ORDER BY total DESC''')
    rows = c.fetchall()
    c.execute('SELECT COUNT(*) AS count, COALESCE(SUM(amount),0) AS total FROM purchases')
    grand = c.fetchone()
    conn.close()
    return {'by_category': [dict(r) for r in rows], 'grand_total': dict(grand)}


# ── Budget ────────────────────────────────────────────────────────────────────

def _current_month():
    return date.today().strftime('%Y-%m')


def get_budget(month=None):
    month = month or _current_month()
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM budget WHERE month=?', (month,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else {'monthly_amount': 0, 'month': month}


def set_budget(amount: float, month=None) -> dict:
    month = month or _current_month()
    conn = get_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO budget (monthly_amount,month) VALUES (?,?)
                 ON CONFLICT(month) DO UPDATE SET monthly_amount=excluded.monthly_amount''',
              (amount, month))
    conn.commit()
    conn.close()
    return get_budget(month)


# ── Profile ───────────────────────────────────────────────────────────────────

def get_profile() -> dict:
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM user_profile WHERE id=1')
    row = c.fetchone()
    conn.close()
    p = dict(row) if row else {'id':1,'name':'Joven','xp':0,'level':1,'avatar':'JV','tips_read':0}
    p['xp_for_next']  = p['level'] * XP_PER_LEVEL
    p['xp_progress']  = p['xp'] % XP_PER_LEVEL
    p['xp_pct']       = int(p['xp_progress'] / (p['level'] * XP_PER_LEVEL) * 100)
    return p


def update_profile(name=None, avatar=None) -> dict:
    conn = get_connection()
    c = conn.cursor()
    if name:   c.execute('UPDATE user_profile SET name=?   WHERE id=1', (name,))
    if avatar: c.execute('UPDATE user_profile SET avatar=? WHERE id=1', (avatar,))
    conn.commit()
    conn.close()
    return get_profile()


def add_xp(amount: int) -> dict:
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE user_profile SET xp = xp + ? WHERE id=1', (amount,))
    c.execute('SELECT xp FROM user_profile WHERE id=1')
    row = c.fetchone()
    if row:
        new_level = max(1, row['xp'] // XP_PER_LEVEL + 1)
        c.execute('UPDATE user_profile SET level=? WHERE id=1', (new_level,))
    conn.commit()
    conn.close()
    return get_profile()


def increment_tips_read() -> dict:
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE user_profile SET tips_read = tips_read + 1 WHERE id=1')
    conn.commit()
    conn.close()
    _update_missions_for_type('tips_read')
    _check_and_unlock_achievements()
    return get_profile()


# ── Streak ────────────────────────────────────────────────────────────────────

def get_streak() -> dict:
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM streak WHERE id=1')
    row = c.fetchone()
    conn.close()
    return dict(row) if row else {
        'current_streak':0,'longest_streak':0,
        'last_active_date':None,'total_active_days':0
    }


def update_streak() -> dict:
    today     = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM streak WHERE id=1')
    s = dict(c.fetchone())

    last    = s.get('last_active_date')
    current = s.get('current_streak', 0)
    longest = s.get('longest_streak', 0)
    total   = s.get('total_active_days', 0)

    if last == today:
        pass  # already updated today
    elif last == yesterday:
        current += 1
        total   += 1
    else:
        current  = 1
        total   += 1

    longest = max(longest, current)
    c.execute('''UPDATE streak SET current_streak=?,longest_streak=?,
                 last_active_date=?,total_active_days=? WHERE id=1''',
              (current, longest, today, total))
    conn.commit()
    conn.close()
    return get_streak()


# ── Missions ──────────────────────────────────────────────────────────────────

def get_missions() -> list:
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM missions ORDER BY completed ASC, id ASC')
    rows = c.fetchall()
    conn.close()
    result = []
    for r in rows:
        m = dict(r)
        m['progress_pct'] = min(100, int(m['current_value'] / m['target_value'] * 100)) if m['target_value'] > 0 else 0
        result.append(m)
    return result


def _update_missions_for_type(mission_type: str):
    """Recalculate progress for all incomplete missions of given type. Returns newly completed list."""
    conn = get_connection()
    c = conn.cursor()
    newly = []
    now   = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Determine new_value based on type
    if mission_type == 'expense_count':
        c.execute('SELECT COUNT(*) as n FROM purchases')
        new_val = c.fetchone()['n']
    elif mission_type == 'streak':
        s = get_streak()
        new_val = s['current_streak']
    elif mission_type == 'category_count':
        c.execute('SELECT COUNT(DISTINCT category) as n FROM purchases')
        new_val = c.fetchone()['n']
    elif mission_type == 'tips_read':
        c.execute('SELECT tips_read FROM user_profile WHERE id=1')
        row = c.fetchone()
        new_val = row['tips_read'] if row else 0
    else:
        conn.close()
        return newly

    c.execute('SELECT * FROM missions WHERE type=? AND completed=0', (mission_type,))
    missions = [dict(r) for r in c.fetchall()]
    for m in missions:
        c.execute('UPDATE missions SET current_value=? WHERE id=?', (new_val, m['id']))
        if new_val >= m['target_value']:
            c.execute('''UPDATE missions SET completed=1,completed_at=? WHERE id=?''',
                      (now, m['id']))
            m['completed'] = 1
            newly.append(m)

    conn.commit()
    conn.close()
    return newly


# ── Achievements ──────────────────────────────────────────────────────────────

def get_achievements() -> list:
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM achievements ORDER BY unlocked DESC, id ASC')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _check_and_unlock_achievements() -> list:
    """Unlock any achievements whose conditions are now met."""
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    newly = []

    def _unlock(key):
        c.execute('''UPDATE achievements SET unlocked=1,unlocked_at=?
                     WHERE key=? AND unlocked=0''', (now, key))
        if c.rowcount > 0:
            c.execute('SELECT * FROM achievements WHERE key=?', (key,))
            row = c.fetchone()
            if row: newly.append(dict(row))

    c.execute('SELECT COUNT(*) as n FROM purchases')
    if c.fetchone()['n'] >= 1: _unlock('first_step')

    s = get_streak()
    if s['current_streak'] >= 7:  _unlock('on_fire')
    if s['current_streak'] >= 30: _unlock('legend')

    c.execute('SELECT COUNT(DISTINCT category) as n FROM purchases')
    if c.fetchone()['n'] >= 6: _unlock('explorer')

    c.execute('SELECT COUNT(*) as n FROM missions WHERE completed=1')
    if c.fetchone()['n'] >= 3: _unlock('missions_3')

    c.execute('SELECT level,tips_read FROM user_profile WHERE id=1')
    row = c.fetchone()
    if row:
        if row['level'] >= 5:    _unlock('level_5')
        if row['tips_read'] >= 10: _unlock('wise_reader')

    conn.commit()
    conn.close()
    return newly


# ── On new purchase (side effects) ────────────────────────────────────────────

def _on_new_purchase(category: str):
    update_streak()
    completed = []
    completed += _update_missions_for_type('expense_count')
    completed += _update_missions_for_type('category_count')
    completed += _update_missions_for_type('streak')
    for m in completed:
        add_xp(m['reward_xp'])
    add_xp(5)  # base XP per expense logged
    _check_and_unlock_achievements()
    return completed


# ── Dashboard summary ─────────────────────────────────────────────────────────

def get_dashboard_data() -> dict:
    today      = date.today()
    month_str  = today.strftime('%Y-%m')
    month_start = today.strftime('%Y-%m-01')
    days_in_month  = calendar.monthrange(today.year, today.month)[1]
    days_remaining = days_in_month - today.day + 1

    budget_row     = get_budget(month_str)
    monthly_budget = budget_row['monthly_amount']

    conn = get_connection()
    c = conn.cursor()

    c.execute('SELECT COALESCE(SUM(amount),0) as t FROM purchases WHERE created_at >= ?',
              (month_start,))
    month_spent = c.fetchone()['t']

    c.execute("SELECT COALESCE(SUM(amount),0) as t FROM purchases WHERE DATE(created_at)=?",
              (today.isoformat(),))
    today_spent = c.fetchone()['t']

    yesterday = (today - timedelta(days=1)).isoformat()
    c.execute("SELECT COALESCE(SUM(amount),0) as t FROM purchases WHERE DATE(created_at)=?",
              (yesterday,))
    yesterday_spent = c.fetchone()['t']

    week_start = (today - timedelta(days=today.weekday())).isoformat()
    c.execute("SELECT COALESCE(SUM(amount),0) as t FROM purchases WHERE DATE(created_at)>=?",
              (week_start,))
    week_spent = c.fetchone()['t']

    conn.close()

    remaining       = max(0.0, monthly_budget - month_spent)
    daily_available = round(remaining / days_remaining, 2) if days_remaining > 0 else 0.0
    budget_used_pct = round(month_spent / monthly_budget * 100, 1) if monthly_budget > 0 else 0.0
    overspent       = monthly_budget > 0 and month_spent > monthly_budget
    alert_mode      = monthly_budget > 0 and not overspent and (remaining / monthly_budget) < 0.20

    return {
        'budget':           round(monthly_budget, 2),
        'month_spent':      round(month_spent, 2),
        'remaining':        round(remaining, 2),
        'daily_available':  daily_available,
        'today_spent':      round(today_spent, 2),
        'yesterday_spent':  round(yesterday_spent, 2),
        'week_spent':       round(week_spent, 2),
        'budget_used_pct':  budget_used_pct,
        'days_remaining':   days_remaining,
        'days_in_month':    days_in_month,
        'alert_mode':       alert_mode,
        'overspent':        overspent,
        'today_vs_yesterday': round(today_spent - yesterday_spent, 2),
    }


# ── Spending trend (last N days) ──────────────────────────────────────────────

def get_spending_trend(days: int = 7) -> list:
    today = date.today()
    conn = get_connection()
    c = conn.cursor()
    result = []
    for i in range(days - 1, -1, -1):
        d = (today - timedelta(days=i))
        d_str = d.isoformat()
        c.execute('''SELECT COALESCE(SUM(amount),0) as total, COUNT(*) as count
                     FROM purchases WHERE DATE(created_at)=?''', (d_str,))
        row = c.fetchone()
        result.append({
            'date':  d_str,
            'label': d.strftime('%a %d'),
            'short': d.strftime('%a'),
            'total': round(row['total'], 2),
            'count': row['count'],
        })
    conn.close()
    return result


# ── Smart tips ────────────────────────────────────────────────────────────────

def get_tips(limit: int = 3) -> list:
    dash   = get_dashboard_data()
    streak = get_streak()
    tips   = []

    # Contextual tips first
    if dash['budget'] == 0:
        tips.append({'type':'setup','icon':'⚙️','title':'Configura tu presupuesto',
                     'text':'Define tu presupuesto mensual para que FINNY pueda darte consejos personalizados y calcular tu dinero diario.','color':'purple'})
    elif dash['overspent']:
        extra = dash['month_spent'] - dash['budget']
        tips.append({'type':'alert','icon':'🚨','title':'¡Superaste tu presupuesto!',
                     'text':f'Ya gastaste ${extra:.2f} de más. Evita gastos adicionales y revisa tu lista.','color':'red'})
    elif dash['alert_mode']:
        tips.append({'type':'warning','icon':'⚠️','title':'Saldo en modo alerta',
                     'text':f'Solo te quedan ${dash["remaining"]:.2f}. Con {dash["days_remaining"]} días restantes, tu límite diario es ${dash["daily_available"]:.2f}.','color':'orange'})
    elif dash['budget_used_pct'] < 40:
        tips.append({'type':'success','icon':'🎉','title':'¡Vas increíble!',
                     'text':f'Solo llevas el {dash["budget_used_pct"]}% del presupuesto gastado. ¡Sigue así y podrías ahorrar bastante!','color':'green'})

    if streak['current_streak'] == 0:
        tips.append({'type':'motivation','icon':'🔥','title':'¡Inicia tu racha hoy!',
                     'text':'Registrar cualquier gasto hoy activa tu racha diaria. Las rachas dan XP extra y desbloquean logros especiales.','color':'blue'})
    elif streak['current_streak'] >= 7:
        tips.append({'type':'achievement','icon':'🌟','title':f'{streak["current_streak"]} días de racha',
                     'text':'Llevas más de una semana registrando gastos. ¡Eso es un hábito real formándose!','color':'yellow'})

    if dash['today_vs_yesterday'] > 2 and dash['yesterday_spent'] > 0:
        tips.append({'type':'info','icon':'📈','title':'Hoy gastaste más que ayer',
                     'text':f'Hoy llevas ${dash["today_spent"]:.2f}, mientras que ayer fueron ${dash["yesterday_spent"]:.2f}. ¿Fue planeado?','color':'purple'})
    elif dash['today_vs_yesterday'] < -2:
        tips.append({'type':'success','icon':'💪','title':'¡Hoy ahorraste!',
                     'text':f'Gastaste ${abs(dash["today_vs_yesterday"]):.2f} menos que ayer. Pequeñas victorias que suman mucho.','color':'green'})

    # General tips pool
    general = [
        {'type':'tip','icon':'💡','title':'Regla 50/30/20',
         'text':'Destina el 50% a necesidades, 30% a deseos y 20% a ahorro. Es el punto de partida que usan millones de personas.','color':'blue'},
        {'type':'tip','icon':'🛑','title':'La prueba de las 24 horas',
         'text':'Antes de comprar algo no planeado, espera un día. Te sorprenderá cuántas veces ya no lo quieres.','color':'purple'},
        {'type':'tip','icon':'☕','title':'El factor café',
         'text':'$3 diarios en café son $1,095 al año. No se trata de no tomar café, sino de ser consciente del efecto acumulado.','color':'pink'},
        {'type':'tip','icon':'📱','title':'El truco de las listas',
         'text':'Revisar tus gastos semanalmente reduce el gasto impulsivo hasta un 18%. Solo necesitas 10 minutos.','color':'blue'},
        {'type':'tip','icon':'🏦','title':'Págate a ti primero',
         'text':'Al recibir ingresos, aparta el ahorro antes de gastar. No ahorres "lo que sobra", porque rara vez sobra algo.','color':'green'},
        {'type':'tip','icon':'🎯','title':'Pequeñas metas, gran impacto',
         'text':'Las metas específicas ($50 para el viernes) funcionan mejor que metas vagas ("ahorrar más"). ¡Sé preciso!','color':'purple'},
    ]
    random.shuffle(general)
    tips.extend(general)
    return tips[:limit]
