# backend/services/tips_service.py
# Generates personalized financial tips for a user.

import random
import hashlib
from backend.services.dashboard_service import DashboardService
from backend.repositories.streak_repository import StreakRepository


def _tip_id(tip_type: str, title: str) -> str:
    """Generate a stable, short ID for a tip based on its type and title."""
    raw = f"{tip_type}:{title}"
    return hashlib.md5(raw.encode()).hexdigest()[:8]


def get_tips(user_id: int, limit: int = 3) -> list[dict]:
    dash   = DashboardService.get(user_id)
    streak = StreakRepository.find_by_user(user_id)
    s      = streak.to_dict() if streak else {'current_streak': 0}
    tips   = []

    # Contextual tips based on budget status
    if dash['budget'] == 0:
        tips.append({
            'type': 'setup', 'icon': '⚙️', 'title': 'Configura tu presupuesto',
            'text': 'Define tu presupuesto mensual para que FINNY pueda darte consejos personalizados y calcular tu dinero diario.',
            'color': 'purple',
        })
    elif dash['overspent']:
        extra = dash['month_spent'] - dash['budget']
        tips.append({
            'type': 'alert', 'icon': '🚨', 'title': '¡Superaste tu presupuesto!',
            'text': f'Ya gastaste ${extra:.2f} de más. Evita gastos adicionales y revisa tu lista.',
            'color': 'red',
        })
    elif dash['alert_mode']:
        tips.append({
            'type': 'warning', 'icon': '⚠️', 'title': 'Saldo en modo alerta',
            'text': f'Solo te quedan ${dash["remaining"]:.2f}. Con {dash["days_remaining"]} días restantes, tu límite diario es ${dash["daily_available"]:.2f}.',
            'color': 'orange',
        })
    elif dash['budget_used_pct'] < 40:
        tips.append({
            'type': 'success', 'icon': '🎉', 'title': '¡Vas increíble!',
            'text': f'Solo llevas el {dash["budget_used_pct"]}% del presupuesto gastado. ¡Sigue así y podrías ahorrar bastante!',
            'color': 'green',
        })

    # Streak tips — now oriented towards SAVING
    if s['current_streak'] == 0:
        tips.append({
            'type': 'motivation', 'icon': '🐷', 'title': '¡Inicia tu racha de ahorro!',
            'text': 'Si hoy gastas dentro de tu presupuesto diario, mañana arrancas una racha de ahorro. ¡Las rachas dan XP extra y desbloquean logros!',
            'color': 'blue',
        })
    elif s['current_streak'] >= 7:
        tips.append({
            'type': 'achievement', 'icon': '🌟', 'title': f'{s["current_streak"]} días ahorrando',
            'text': '¡Llevas más de una semana gastando dentro de tu presupuesto! Eso es un hábito real formándose.',
            'color': 'yellow',
        })
    elif s['current_streak'] >= 3:
        tips.append({
            'type': 'motivation', 'icon': '🔥', 'title': f'¡{s["current_streak"]} días de racha!',
            'text': 'Vas muy bien controlando tus gastos. Cada día que ahorras, tu racha crece. ¡No la pierdas!',
            'color': 'blue',
        })

    # Daily comparison tip
    if dash['today_vs_yesterday'] > 2 and dash['yesterday_spent'] > 0:
        tips.append({
            'type': 'info', 'icon': '📈', 'title': 'Hoy gastaste más que ayer',
            'text': f'Hoy llevas ${dash["today_spent"]:.2f}, mientras que ayer fueron ${dash["yesterday_spent"]:.2f}. ¿Fue planeado?',
            'color': 'purple',
        })
    elif dash['today_vs_yesterday'] < -2:
        tips.append({
            'type': 'success', 'icon': '💪', 'title': '¡Hoy ahorraste!',
            'text': f'Gastaste ${abs(dash["today_vs_yesterday"]):.2f} menos que ayer. Pequeñas victorias que suman mucho.',
            'color': 'green',
        })

    # General tips pool
    general = [
        {'type': 'tip', 'icon': '💡', 'title': 'Regla 50/30/20',
         'text': 'Destina el 50% a necesidades, 30% a deseos y 20% a ahorro. Es el punto de partida que usan millones de personas.',
         'color': 'blue'},
        {'type': 'tip', 'icon': '🛑', 'title': 'La prueba de las 24 horas',
         'text': 'Antes de comprar algo no planeado, espera un día. Te sorprenderá cuántas veces ya no lo quieres.',
         'color': 'purple'},
        {'type': 'tip', 'icon': '☕', 'title': 'El factor café',
         'text': '$3 diarios en café son $1,095 al año. No se trata de no tomar café, sino de ser consciente del efecto acumulado.',
         'color': 'pink'},
        {'type': 'tip', 'icon': '📱', 'title': 'El truco de las listas',
         'text': 'Revisar tus gastos semanalmente reduce el gasto impulsivo hasta un 18%. Solo necesitas 10 minutos.',
         'color': 'blue'},
        {'type': 'tip', 'icon': '🏦', 'title': 'Págate a ti primero',
         'text': 'Al recibir ingresos, aparta el ahorro antes de gastar. No ahorres "lo que sobra", porque rara vez sobra algo.',
         'color': 'green'},
        {'type': 'tip', 'icon': '🎯', 'title': 'Pequeñas metas, gran impacto',
         'text': 'Las metas específicas funcionan mejor que metas vagas. ¡Sé preciso con tus objetivos!',
         'color': 'purple'},
    ]
    random.shuffle(general)
    tips.extend(general)

    # Assign stable IDs to all tips
    result = []
    for tip in tips[:limit]:
        tip['id'] = _tip_id(tip['type'], tip['title'])
        result.append(tip)

    return result
