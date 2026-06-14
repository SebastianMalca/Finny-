"""
test_api_integration.py — Pruebas de integración de los endpoints HTTP.

Usa el cliente de test de Flask con SQLite en memoria.
Contratos reales de la API FINNY verificados en código fuente:
  - POST /auth/register → 201 {message, user}
  - POST /auth/login → 200 {message, user}
  - GET /auth/me → 200 {user: {...}}
  - GET /compras → 200 {purchases: [...], total, count, categories, filtered_by}
  - POST /compras → 201 {message, purchase: {...}}
  - GET /compras/<pid> → 200 {purchase: {...}}
  - DELETE /compras/<pid> → 200 {message}
  - GET /presupuesto → 200 {monthly_amount, month, ...}
  - POST /presupuesto → 200 {message, budget} — campo requerido: "amount"
  - GET /dashboard → 200 {budget, month_spent, remaining, ...}
"""
import pytest
import json


class TestAuthEndpoints:
    """Pruebas de integración de /auth/register, /auth/login, /auth/logout."""

    def test_register_success(self, client):
        resp = client.post('/auth/register', json={
            'email': 'nuevo@finny.com',
            'username': 'NuevoUser',
            'password': 'password123',
        })
        data = resp.get_json()
        assert resp.status_code == 201
        assert 'user' in data
        assert data['user']['email'] == 'nuevo@finny.com'

    def test_register_duplicate_email(self, client):
        payload = {'email': 'dup@finny.com', 'username': 'Dup', 'password': 'password123'}
        client.post('/auth/register', json=payload)
        resp = client.post('/auth/register', json=payload)
        data = resp.get_json()
        assert resp.status_code == 400
        assert 'error' in data

    def test_register_missing_field(self, client):
        resp = client.post('/auth/register', json={'email': 'only@test.com'})
        assert resp.status_code == 400

    def test_register_invalid_email(self, client):
        resp = client.post('/auth/register', json={
            'email': 'notanemail',
            'username': 'User',
            'password': 'password123',
        })
        assert resp.status_code == 400

    def test_login_success(self, client):
        client.post('/auth/register', json={
            'email': 'login@finny.com',
            'username': 'LoginUser',
            'password': 'password123',
        })
        resp = client.post('/auth/login', json={
            'email': 'login@finny.com',
            'password': 'password123',
        })
        data = resp.get_json()
        assert resp.status_code == 200
        assert 'user' in data

    def test_login_wrong_password(self, client):
        """Con credenciales incorrectas, el servidor devuelve 401."""
        client.post('/auth/register', json={
            'email': 'wrong@finny.com',
            'username': 'WrongUser',
            'password': 'correctpass',
        })
        # Primero hacer logout explícito para asegurarnos de no tener sesión activa
        client.post('/auth/logout')

        # Crear cliente fresco para este test
        from tests.conftest import _create_test_app
        fresh_app = _create_test_app()
        from backend.models import db as _db
        with fresh_app.app_context():
            _db.drop_all()
            _db.create_all()
            from backend.services.auth_service import AuthService
            AuthService.register('wrong2@finny.com', 'WrongUser', 'correctpass')
            _db.session.commit()

        with fresh_app.test_client() as fc:
            with fresh_app.app_context():
                resp = fc.post('/auth/login', json={
                    'email': 'wrong2@finny.com',
                    'password': 'wrongpass',
                })
            assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        resp = client.post('/auth/login', json={
            'email': 'nobody@finny.com',
            'password': 'password123',
        })
        assert resp.status_code == 401

    def test_me_unauthenticated(self, client):
        resp = client.get('/auth/me')
        assert resp.status_code == 401

    def test_me_authenticated(self, client):
        """GET /auth/me retorna {user: {...}} con la clave 'email'."""
        client.post('/auth/register', json={
            'email': 'me@finny.com',
            'username': 'MeUser',
            'password': 'password123',
        })
        client.post('/auth/login', json={
            'email': 'me@finny.com',
            'password': 'password123',
        })
        resp = client.get('/auth/me')
        data = resp.get_json()
        assert resp.status_code == 200
        # La ruta retorna {'user': {...}}
        assert 'user' in data
        assert data['user']['email'] == 'me@finny.com'

    def test_logout(self, client):
        client.post('/auth/register', json={
            'email': 'logout@finny.com',
            'username': 'Logout',
            'password': 'password123',
        })
        client.post('/auth/login', json={
            'email': 'logout@finny.com',
            'password': 'password123',
        })
        resp = client.post('/auth/logout')
        assert resp.status_code == 200


class TestPurchaseEndpoints:
    """Pruebas de integración de /compras.
    
    Contratos reales:
      - POST /compras → 201 {'message': ..., 'purchase': {...}}
      - GET /compras → 200 {'purchases': [...], 'total', 'count', 'categories', 'filtered_by'}
      - GET /compras/<pid> → 200 {'purchase': {...}}
    """

    def _login(self, client, email='purchase@finny.com', pw='password123'):
        client.post('/auth/register', json={
            'email': email, 'username': 'PurchUser', 'password': pw,
        })
        client.post('/auth/login', json={'email': email, 'password': pw})

    def test_create_purchase_success(self, client):
        self._login(client)
        resp = client.post('/compras', json={
            'name': 'Lunch', 'amount': 12.50, 'category': 'Food',
        })
        data = resp.get_json()
        assert resp.status_code == 201
        # La ruta retorna {'message': ..., 'purchase': {...}}
        assert 'purchase' in data
        assert data['purchase']['name'] == 'Lunch'
        assert data['purchase']['amount'] == 12.50

    def test_create_purchase_unauthenticated(self, client):
        resp = client.post('/compras', json={'name': 'Test', 'amount': 5.0})
        assert resp.status_code == 401

    def test_create_purchase_invalid_data(self, client):
        self._login(client)
        resp = client.post('/compras', json={'name': '', 'amount': -1})
        assert resp.status_code == 400

    def test_list_purchases_empty(self, client):
        """GET /compras retorna un dict con clave 'purchases' (lista)."""
        self._login(client)
        resp = client.get('/compras')
        data = resp.get_json()
        assert resp.status_code == 200
        assert 'purchases' in data
        assert isinstance(data['purchases'], list)

    def test_list_purchases_after_creation(self, client):
        self._login(client)
        client.post('/compras', json={'name': 'Coffee', 'amount': 3.0, 'category': 'Food'})
        client.post('/compras', json={'name': 'Bus', 'amount': 1.5, 'category': 'Transport'})
        resp = client.get('/compras')
        data = resp.get_json()
        assert data['count'] == 2
        assert len(data['purchases']) == 2

    def test_get_purchase_by_id(self, client):
        """GET /compras/<pid> retorna {'purchase': {...}}."""
        self._login(client)
        create_resp = client.post('/compras', json={'name': 'Book', 'amount': 20.0, 'category': 'Study'})
        purchase_id = create_resp.get_json()['purchase']['id']
        resp = client.get(f'/compras/{purchase_id}')
        assert resp.status_code == 200
        assert resp.get_json()['purchase']['id'] == purchase_id

    def test_get_nonexistent_purchase(self, client):
        self._login(client)
        resp = client.get('/compras/99999')
        assert resp.status_code == 404

    def test_delete_purchase(self, client):
        self._login(client)
        create_resp = client.post('/compras', json={'name': 'Soda', 'amount': 2.0, 'category': 'Food'})
        pid = create_resp.get_json()['purchase']['id']
        resp = client.delete(f'/compras/{pid}')
        assert resp.status_code == 200
        # Verificar que ya no existe
        assert client.get(f'/compras/{pid}').status_code == 404

    def test_filter_by_category(self, client):
        """GET /compras?category=Food retorna solo compras de Food."""
        self._login(client)
        client.post('/compras', json={'name': 'Coffee', 'amount': 3.0, 'category': 'Food'})
        client.post('/compras', json={'name': 'Taxi', 'amount': 8.0, 'category': 'Transport'})
        resp = client.get('/compras?category=Food')
        data = resp.get_json()
        assert all(p['category'] == 'Food' for p in data['purchases'])

    def test_list_purchases_total_calculated(self, client):
        """El campo 'total' debe ser la suma de los montos."""
        self._login(client)
        client.post('/compras', json={'name': 'A', 'amount': 10.0, 'category': 'Food'})
        client.post('/compras', json={'name': 'B', 'amount': 20.0, 'category': 'Transport'})
        resp = client.get('/compras')
        data = resp.get_json()
        assert data['total'] == pytest.approx(30.0, 0.01)

    def test_list_purchases_contains_categories(self, client):
        """El campo 'categories' lista las categorías disponibles."""
        self._login(client)
        resp = client.get('/compras')
        data = resp.get_json()
        assert 'categories' in data
        assert 'Food' in data['categories']


class TestBudgetEndpoints:
    """Pruebas de integración de /presupuesto.
    
    Contrato real: POST /presupuesto requiere campo 'amount' (no 'monthly_amount').
    """

    def _login(self, client, email='budget@finny.com'):
        client.post('/auth/register', json={
            'email': email, 'username': 'BudgetUser', 'password': 'password123',
        })
        client.post('/auth/login', json={'email': email, 'password': 'password123'})

    def test_get_budget_empty(self, client):
        self._login(client)
        resp = client.get('/presupuesto')
        assert resp.status_code == 200

    def test_set_budget(self, client):
        """POST /presupuesto requiere campo 'amount' según budget_routes.py."""
        self._login(client)
        resp = client.post('/presupuesto', json={'amount': 500.0})
        data = resp.get_json()
        assert resp.status_code == 200
        assert 'budget' in data or 'message' in data

    def test_set_budget_missing_amount_field(self, client):
        """Sin campo 'amount' debe retornar 400."""
        self._login(client)
        resp = client.post('/presupuesto', json={'monthly_amount': 500.0})
        assert resp.status_code == 400

    def test_set_budget_negative_amount(self, client):
        """Presupuesto negativo debe retornar 400."""
        self._login(client)
        resp = client.post('/presupuesto', json={'amount': -100.0})
        assert resp.status_code == 400

    def test_set_budget_unauthenticated(self, client):
        resp = client.post('/presupuesto', json={'amount': 500.0})
        assert resp.status_code == 401


class TestDashboardEndpoint:
    """Pruebas de integración del endpoint /dashboard."""

    def _login(self, client, email='dash@finny.com'):
        client.post('/auth/register', json={
            'email': email, 'username': 'DashUser', 'password': 'password123',
        })
        client.post('/auth/login', json={'email': email, 'password': 'password123'})

    def test_dashboard_unauthenticated(self, client):
        resp = client.get('/dashboard')
        assert resp.status_code == 401

    def test_dashboard_returns_all_keys(self, client):
        self._login(client)
        resp = client.get('/dashboard')
        data = resp.get_json()
        assert resp.status_code == 200
        expected = ['budget', 'month_spent', 'remaining', 'today_spent',
                    'daily_available', 'overspent', 'alert_mode']
        for key in expected:
            assert key in data, f"Clave faltante en dashboard: {key}"

    def test_dashboard_zero_without_budget(self, client):
        """Sin presupuesto configurado, budget debe ser 0."""
        self._login(client)
        resp = client.get('/dashboard')
        data = resp.get_json()
        assert data['budget'] == 0.0

    def test_dashboard_reflects_purchases(self, client):
        """month_spent debe reflejar las compras realizadas."""
        self._login(client)
        client.post('/compras', json={'name': 'Coffee', 'amount': 15.0, 'category': 'Food'})
        resp = client.get('/dashboard')
        data = resp.get_json()
        assert data['month_spent'] >= 15.0


class TestProfileEndpoints:
    """Pruebas de integración de /perfil."""

    def _login(self, client, email='profile@finny.com'):
        client.post('/auth/register', json={
            'email': email, 'username': 'ProfileUser', 'password': 'password123',
        })
        client.post('/auth/login', json={'email': email, 'password': 'password123'})

    def test_get_profile(self, client):
        self._login(client)
        resp = client.get('/perfil')
        data = resp.get_json()
        assert resp.status_code == 200
        # Al menos uno de estos campos debe estar presente
        assert any(k in data for k in ('name', 'username', 'level', 'xp'))

    def test_update_profile_name(self, client):
        self._login(client)
        resp = client.put('/perfil', json={'name': 'Nuevo Nombre'})
        assert resp.status_code == 200

    def test_profile_unauthenticated(self, client):
        resp = client.get('/perfil')
        assert resp.status_code == 401
