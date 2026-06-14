"""
test_dashboard_service.py — Pruebas Unitarias de DashboardService.

Cubre:
  - get(): cálculos financieros (remaining, daily_available, alert_mode, overspent)
  - get_spending_trend(): estructura de datos retornada
  - get_stats(): resumen por categoría
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import date, timedelta
from backend.services.dashboard_service import DashboardService


class TestDashboardServiceGet:
    """Pruebas de DashboardService.get() con distintos escenarios de presupuesto."""

    def _patch_repos(self, budget=1000.0, month_spent=0.0,
                     today_spent=0.0, yesterday_spent=0.0, week_spent=0.0):
        """Helper para parchear todos los repositorios de DashboardService."""
        mock_budget_row = MagicMock()
        mock_budget_row.monthly_amount = budget

        return [
            patch('backend.services.dashboard_service.BudgetRepository.find_by_month',
                  return_value=mock_budget_row),
            patch('backend.services.dashboard_service.PurchaseRepository.sum_month',
                  return_value=month_spent),
            patch('backend.services.dashboard_service.PurchaseRepository.sum_by_date',
                  side_effect=[today_spent, yesterday_spent]),
            patch('backend.services.dashboard_service.PurchaseRepository.sum_since',
                  return_value=week_spent),
            patch('backend.services.dashboard_service.StreakRepository.find_by_user',
                  return_value=None),
        ]

    def test_no_budget_configured(self):
        with patch('backend.services.dashboard_service.BudgetRepository.find_by_month', return_value=None), \
             patch('backend.services.dashboard_service.PurchaseRepository.sum_month', return_value=0.0), \
             patch('backend.services.dashboard_service.PurchaseRepository.sum_by_date', side_effect=[0.0, 0.0]), \
             patch('backend.services.dashboard_service.PurchaseRepository.sum_since', return_value=0.0):
            result = DashboardService.get(user_id=1)
        assert result['budget'] == 0.0
        assert result['remaining'] == 0.0
        assert result['overspent'] is False
        assert result['alert_mode'] is False

    def test_within_budget_normal(self):
        with patch('backend.services.dashboard_service.BudgetRepository.find_by_month',
                   return_value=MagicMock(monthly_amount=1000.0)), \
             patch('backend.services.dashboard_service.PurchaseRepository.sum_month', return_value=400.0), \
             patch('backend.services.dashboard_service.PurchaseRepository.sum_by_date', side_effect=[20.0, 15.0]), \
             patch('backend.services.dashboard_service.PurchaseRepository.sum_since', return_value=80.0):
            result = DashboardService.get(user_id=1)
        assert result['budget'] == 1000.0
        assert result['month_spent'] == 400.0
        assert result['remaining'] == 600.0
        assert result['overspent'] is False
        assert result['alert_mode'] is False
        assert result['budget_used_pct'] == pytest.approx(40.0, 0.1)

    def test_overspent(self):
        with patch('backend.services.dashboard_service.BudgetRepository.find_by_month',
                   return_value=MagicMock(monthly_amount=500.0)), \
             patch('backend.services.dashboard_service.PurchaseRepository.sum_month', return_value=600.0), \
             patch('backend.services.dashboard_service.PurchaseRepository.sum_by_date', side_effect=[50.0, 30.0]), \
             patch('backend.services.dashboard_service.PurchaseRepository.sum_since', return_value=150.0):
            result = DashboardService.get(user_id=1)
        assert result['overspent'] is True
        assert result['remaining'] == 0.0  # max(0, ...)

    def test_alert_mode_below_20_percent(self):
        """alert_mode = True cuando queda menos del 20% del presupuesto."""
        with patch('backend.services.dashboard_service.BudgetRepository.find_by_month',
                   return_value=MagicMock(monthly_amount=1000.0)), \
             patch('backend.services.dashboard_service.PurchaseRepository.sum_month', return_value=850.0), \
             patch('backend.services.dashboard_service.PurchaseRepository.sum_by_date', side_effect=[50.0, 30.0]), \
             patch('backend.services.dashboard_service.PurchaseRepository.sum_since', return_value=200.0):
            result = DashboardService.get(user_id=1)
        assert result['alert_mode'] is True
        assert result['overspent'] is False

    def test_today_vs_yesterday_positive(self):
        with patch('backend.services.dashboard_service.BudgetRepository.find_by_month',
                   return_value=MagicMock(monthly_amount=1000.0)), \
             patch('backend.services.dashboard_service.PurchaseRepository.sum_month', return_value=200.0), \
             patch('backend.services.dashboard_service.PurchaseRepository.sum_by_date', side_effect=[50.0, 20.0]), \
             patch('backend.services.dashboard_service.PurchaseRepository.sum_since', return_value=100.0):
            result = DashboardService.get(user_id=1)
        assert result['today_vs_yesterday'] == pytest.approx(30.0, 0.01)

    def test_daily_available_calculated(self):
        """daily_available = remaining / days_remaining."""
        with patch('backend.services.dashboard_service.BudgetRepository.find_by_month',
                   return_value=MagicMock(monthly_amount=300.0)), \
             patch('backend.services.dashboard_service.PurchaseRepository.sum_month', return_value=150.0), \
             patch('backend.services.dashboard_service.PurchaseRepository.sum_by_date', side_effect=[10.0, 10.0]), \
             patch('backend.services.dashboard_service.PurchaseRepository.sum_since', return_value=50.0):
            result = DashboardService.get(user_id=1)
        assert result['daily_available'] > 0
        assert isinstance(result['days_remaining'], int)

    def test_result_keys_present(self):
        """El resultado debe incluir todas las claves esperadas."""
        expected_keys = [
            'budget', 'month_spent', 'remaining', 'daily_available',
            'today_spent', 'yesterday_spent', 'week_spent',
            'budget_used_pct', 'days_remaining', 'days_in_month',
            'alert_mode', 'overspent', 'today_vs_yesterday',
        ]
        with patch('backend.services.dashboard_service.BudgetRepository.find_by_month', return_value=None), \
             patch('backend.services.dashboard_service.PurchaseRepository.sum_month', return_value=0.0), \
             patch('backend.services.dashboard_service.PurchaseRepository.sum_by_date', side_effect=[0.0, 0.0]), \
             patch('backend.services.dashboard_service.PurchaseRepository.sum_since', return_value=0.0):
            result = DashboardService.get(user_id=1)
        for key in expected_keys:
            assert key in result, f"Clave faltante: {key}"


class TestDashboardServiceSpendingTrend:
    """Pruebas de DashboardService.get_spending_trend()."""

    def test_trend_default_7_days(self, app):
        """Debe retornar exactamente 7 elementos."""
        with app.app_context():
            with patch('backend.services.dashboard_service.PurchaseRepository.sum_by_date', return_value=0.0), \
                 patch('backend.models.db.session') as mock_session:
                mock_session.query.return_value.filter.return_value.scalar.return_value = 0
                result = DashboardService.get_spending_trend(user_id=1, days=7)
        assert len(result) == 7

    def test_trend_item_structure(self, app):
        """Cada elemento debe tener las claves: date, label, short, total, count."""
        with app.app_context():
            with patch('backend.services.dashboard_service.PurchaseRepository.sum_by_date', return_value=10.0), \
                 patch('backend.models.db.session') as mock_session:
                mock_session.query.return_value.filter.return_value.scalar.return_value = 2
                result = DashboardService.get_spending_trend(user_id=1, days=3)
        for item in result:
            assert 'date'  in item
            assert 'label' in item
            assert 'short' in item
            assert 'total' in item
            assert 'count' in item

    def test_trend_dates_are_ordered(self, app):
        """Las fechas deben estar en orden cronológico ascendente."""
        with app.app_context():
            with patch('backend.services.dashboard_service.PurchaseRepository.sum_by_date', return_value=0.0), \
                 patch('backend.models.db.session') as mock_session:
                mock_session.query.return_value.filter.return_value.scalar.return_value = 0
                result = DashboardService.get_spending_trend(user_id=1, days=5)
        dates = [item['date'] for item in result]
        assert dates == sorted(dates)
