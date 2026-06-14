"""
test_performance.py — Pruebas de Rendimiento con pytest-benchmark.

Mide el tiempo de ejecución de operaciones críticas:
  - Hashing de contraseñas (Werkzeug PBKDF2-SHA256)
  - Validación de compras
  - Lógica de cálculo del dashboard (pura, sin DB)
  - Generación de tips
  - Operaciones de modelo de usuario
  - Serialización de datos (to_dict)

Métricas capturadas por pytest-benchmark:
  - min, max, mean, stddev (en segundos)
  - median, IQR (robustez estadística)
  - ops/s (operaciones por segundo)
  - rounds: número de iteraciones ejecutadas
"""
import pytest
import time
from unittest.mock import patch, MagicMock
from datetime import date


# ─────────────────────────────────────────────────────────────────────────────
# 1. HASHING DE CONTRASEÑAS
# ─────────────────────────────────────────────────────────────────────────────

class TestPasswordPerformance:

    def test_benchmark_password_hash(self, benchmark):
        """
        Mide el tiempo de generate_password_hash (PBKDF2-SHA256).
        Valor esperado: < 500ms por operación (costo deliberado de seguridad).
        """
        from werkzeug.security import generate_password_hash
        result = benchmark(generate_password_hash, 'MyS3cur3P@ssw0rd!')
        assert result.startswith('pbkdf2:sha256') or result.startswith('scrypt')

    def test_benchmark_password_verify(self, benchmark):
        """
        Mide el tiempo de check_password_hash.
        Debe ser similar al hash (misma operación cripto).
        """
        from werkzeug.security import generate_password_hash, check_password_hash
        hashed = generate_password_hash('TestPassword123')
        result = benchmark(check_password_hash, hashed, 'TestPassword123')
        assert result is True

    def test_benchmark_wrong_password_verify(self, benchmark):
        """Verificación de contraseña incorrecta — no debe ser más rápida (timing-safe)."""
        from werkzeug.security import generate_password_hash, check_password_hash
        hashed = generate_password_hash('CorrectPassword')
        result = benchmark(check_password_hash, hashed, 'WrongPassword')
        assert result is False


# ─────────────────────────────────────────────────────────────────────────────
# 2. VALIDACIÓN DE COMPRAS
# ─────────────────────────────────────────────────────────────────────────────

class TestPurchaseValidationPerformance:

    def test_benchmark_validate_valid_purchase(self, benchmark):
        """
        Mide la validación de una compra válida.
        Esperado: operación pura de Python, < 1ms.
        """
        from backend.services.purchase_service import PurchaseService
        data = {'name': 'Coffee', 'amount': 3.50, 'category': 'Food'}
        result = benchmark(PurchaseService.validate, data)
        assert result is None

    def test_benchmark_validate_invalid_purchase(self, benchmark):
        """Mide validación con datos incorrectos — debe ser igualmente rápido."""
        from backend.services.purchase_service import PurchaseService
        data = {'name': '', 'amount': -100, 'category': 'InvalidCategory'}
        result = benchmark(PurchaseService.validate, data)
        assert result is not None  # hay error

    def test_benchmark_validate_boundary_amount(self, benchmark):
        """Validación con monto en el límite máximo."""
        from backend.services.purchase_service import PurchaseService
        data = {'name': 'Max Purchase', 'amount': 1_000_000, 'category': 'Other'}
        result = benchmark(PurchaseService.validate, data)
        assert result is None


# ─────────────────────────────────────────────────────────────────────────────
# 3. CÁLCULOS DEL DASHBOARD (SIN DB)
# ─────────────────────────────────────────────────────────────────────────────

class TestDashboardCalculationsPerformance:

    def _make_dashboard_result(self):
        """Simula el resultado puro de cálculo del dashboard."""
        import calendar
        today          = date.today()
        monthly_budget = 1000.0
        month_spent    = 450.0
        days_in_month  = calendar.monthrange(today.year, today.month)[1]
        days_remaining = days_in_month - today.day + 1

        remaining       = max(0.0, monthly_budget - month_spent)
        daily_available = round(remaining / days_remaining, 2) if days_remaining > 0 else 0.0
        budget_used_pct = round(month_spent / monthly_budget * 100, 1)
        overspent       = month_spent > monthly_budget
        alert_mode      = not overspent and (remaining / monthly_budget) < 0.20

        return {
            'budget': monthly_budget,
            'month_spent': month_spent,
            'remaining': remaining,
            'daily_available': daily_available,
            'budget_used_pct': budget_used_pct,
            'overspent': overspent,
            'alert_mode': alert_mode,
        }

    def test_benchmark_pure_dashboard_calculations(self, benchmark):
        """
        Mide solo la lógica aritmética del dashboard (sin I/O).
        Esperado: < 0.5ms por operación.
        """
        result = benchmark(self._make_dashboard_result)
        assert result['budget'] == 1000.0
        assert result['remaining'] == 550.0

    def test_benchmark_100_dashboard_calculations(self, benchmark):
        """Simula 100 cálculos de dashboard en batch."""
        def run_100():
            return [self._make_dashboard_result() for _ in range(100)]
        result = benchmark(run_100)
        assert len(result) == 100


# ─────────────────────────────────────────────────────────────────────────────
# 4. GENERACIÓN DE TIPS
# ─────────────────────────────────────────────────────────────────────────────

class TestTipsPerformance:

    def test_benchmark_tips_generation_no_budget(self, benchmark):
        """
        Mide get_tips() cuando el usuario no tiene presupuesto configurado.
        La función es pura una vez mockeados los repos.
        """
        from backend.services.tips_service import get_tips

        mock_dash = {
            'budget': 0, 'overspent': False, 'alert_mode': False,
            'budget_used_pct': 0, 'remaining': 0, 'days_remaining': 15,
            'daily_available': 0, 'today_spent': 0, 'yesterday_spent': 0,
            'today_vs_yesterday': 0, 'month_spent': 0,
        }
        mock_streak = MagicMock()
        mock_streak.to_dict.return_value = {'current_streak': 0}

        with patch('backend.services.tips_service.DashboardService.get', return_value=mock_dash), \
             patch('backend.services.tips_service.StreakRepository.find_by_user', return_value=mock_streak):
            result = benchmark(get_tips, 1, 3)
        assert isinstance(result, list)
        assert len(result) <= 3

    def test_benchmark_tips_generation_with_streak(self, benchmark):
        """Tips con racha activa de 10 días."""
        from backend.services.tips_service import get_tips

        mock_dash = {
            'budget': 1000, 'overspent': False, 'alert_mode': False,
            'budget_used_pct': 30, 'remaining': 700, 'days_remaining': 10,
            'daily_available': 70, 'today_spent': 20, 'yesterday_spent': 30,
            'today_vs_yesterday': -10, 'month_spent': 300,
        }
        mock_streak = MagicMock()
        mock_streak.to_dict.return_value = {'current_streak': 10}

        with patch('backend.services.tips_service.DashboardService.get', return_value=mock_dash), \
             patch('backend.services.tips_service.StreakRepository.find_by_user', return_value=mock_streak):
            result = benchmark(get_tips, 1, 5)
        assert isinstance(result, list)


# ─────────────────────────────────────────────────────────────────────────────
# 5. MODELO DE USUARIO — OPERACIONES PURAS
# ─────────────────────────────────────────────────────────────────────────────

class TestUserModelPerformance:

    def test_benchmark_generate_reset_token(self, benchmark, app):
        """
        Mide generate_reset_token() — usa secrets.token_urlsafe (CSPRNG).
        Esperado: < 1ms.
        """
        from backend.models.user import User
        with app.app_context():
            user = User(
                email='bench@finny.com',
                username='BenchUser',
                password_hash='fakehash',
            )
            result = benchmark(user.generate_reset_token)
        assert isinstance(result, str)
        assert len(result) > 20

    def test_benchmark_is_reset_token_valid_true(self, benchmark, app):
        """Mide validación de token — operación de comparación de strings."""
        from backend.models.user import User
        with app.app_context():
            user = User(
                email='bench2@finny.com',
                username='BenchUser2',
                password_hash='fakehash',
            )
            token = user.generate_reset_token()
            result = benchmark(user.is_reset_token_valid, token)
        assert result is True

    def test_benchmark_user_to_dict(self, benchmark, app):
        """Mide serialización del modelo User a dict."""
        from backend.models.user import User
        from datetime import datetime
        with app.app_context():
            user = User(
                email='serial@finny.com',
                username='SerialUser',
                password_hash='fakehash',
            )
            user.created_at = datetime.utcnow()
            result = benchmark(user.to_dict)
        assert 'email' in result
        assert 'username' in result


# ─────────────────────────────────────────────────────────────────────────────
# 6. LATENCIA DE RESPUESTA DE LA API (INTEGRACIÓN)
# ─────────────────────────────────────────────────────────────────────────────

class TestAPIResponseTimePerformance:

    def test_benchmark_auth_me_endpoint(self, benchmark, client):
        """
        Mide la latencia de GET /auth/me (respuesta liviana).
        Sin sesión → 401 inmediato, dominado solo por routing Flask.
        Esperado: < 5ms.
        """
        result = benchmark(client.get, '/auth/me')
        # 401 es correcto — usuario no autenticado, respuesta inmediata
        assert result.status_code == 401

    def test_benchmark_login_endpoint(self, benchmark, client):
        """
        Mide POST /auth/login completo (incluye verify de password).
        Esperado: dominado por bcrypt (~200-400ms).
        """
        # Pre-registrar usuario
        client.post('/auth/register', json={
            'email': 'bench_login@finny.com',
            'username': 'BenchLogin',
            'password': 'BenchPass123',
        })

        def do_login():
            return client.post('/auth/login', json={
                'email': 'bench_login@finny.com',
                'password': 'BenchPass123',
            })

        result = benchmark(do_login)
        assert result.status_code == 200

    def test_benchmark_register_endpoint(self, benchmark, client):
        """
        Mide POST /auth/register (hash + escritura en DB).
        Se incrementa el email para evitar duplicados.
        """
        counter = {'n': 0}

        def do_register():
            counter['n'] += 1
            return client.post('/auth/register', json={
                'email': f'bench_reg_{counter["n"]}@finny.com',
                'username': f'BenchReg{counter["n"]}',
                'password': 'BenchPass123',
            })

        result = benchmark(do_register)
        assert result.status_code == 201

    def test_benchmark_list_purchases_empty(self, benchmark, client):
        """Mide GET /compras sin compras — respuesta vacía rápida."""
        client.post('/auth/register', json={
            'email': 'bench_purchases@finny.com',
            'username': 'BenchPurch',
            'password': 'password123',
        })
        client.post('/auth/login', json={
            'email': 'bench_purchases@finny.com',
            'password': 'password123',
        })
        result = benchmark(client.get, '/compras')
        assert result.status_code == 200

    def test_benchmark_dashboard_endpoint(self, benchmark, client):
        """Mide GET /dashboard — agrega múltiples queries."""
        client.post('/auth/register', json={
            'email': 'bench_dash@finny.com',
            'username': 'BenchDash',
            'password': 'password123',
        })
        client.post('/auth/login', json={
            'email': 'bench_dash@finny.com',
            'password': 'password123',
        })
        result = benchmark(client.get, '/dashboard')
        assert result.status_code == 200
