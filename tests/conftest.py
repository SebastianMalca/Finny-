"""
conftest.py — Fixtures compartidos para todas las pruebas de FINNY.
Usa SQLite en memoria para no depender de MySQL durante los tests.

NOTA: Importamos los módulos internos de backend directamente en lugar de
      importar backend.app, ya que ese módulo crea la app con MySQL al importarse.
"""
import sys
import os
import pytest

# Asegura que el root del proyecto esté en sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# ── Configuración de test (SQLite en memoria) ─────────────────────────────────

class TestingConfig:
    TESTING                        = True
    SECRET_KEY                     = 'test-secret-key-finny-2024'
    SQLALCHEMY_DATABASE_URI        = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED               = False
    SESSION_COOKIE_HTTPONLY        = True
    SESSION_COOKIE_SAMESITE        = 'Lax'
    SESSION_COOKIE_SECURE          = False
    REMEMBER_COOKIE_DURATION       = 86400 * 7
    RESET_TOKEN_EXPIRY_HOURS       = 1


def _create_test_app():
    """
    Construye la app Flask con configuración de test (SQLite en memoria).
    NO importa backend.app para evitar la conexión a MySQL al módulo-nivel.
    """
    from flask import Flask, jsonify
    from flask_cors import CORS
    from flask_login import LoginManager
    # Importar modelos y extensiones
    from backend.models import db

    app = Flask(__name__)
    app.config.from_object(TestingConfig)

    CORS(app)
    db.init_app(app)

    lm = LoginManager()
    lm.init_app(app)

    @lm.user_loader
    def load_user(user_id):
        from backend.models.user import User
        return db.session.get(User, int(user_id))

    @lm.unauthorized_handler
    def unauthorized():
        return jsonify({'error': 'No autenticado'}), 401

    # Registrar blueprints
    from backend.routes.auth_routes         import auth_bp
    from backend.routes.purchase_routes     import purchase_bp
    from backend.routes.budget_routes       import budget_bp
    from backend.routes.stats_routes        import stats_bp
    from backend.routes.profile_routes      import profile_bp
    from backend.routes.gamification_routes import gamification_bp
    from backend.routes.tips_routes         import tips_bp
    from backend.routes.dashboard_routes    import dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(purchase_bp)
    app.register_blueprint(budget_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(gamification_bp)
    app.register_blueprint(tips_bp)
    app.register_blueprint(dashboard_bp)

    with app.app_context():
        db.create_all()

    return app


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture(scope='session')
def app():
    """App Flask con SQLite en memoria — compartida en toda la sesión."""
    return _create_test_app()


@pytest.fixture(scope='function')
def db(app):
    """
    Provee la extensión db con el esquema recreado antes de cada test.
    Garantiza aislamiento total entre tests.
    """
    from backend.models import db as _db
    with app.app_context():
        _db.drop_all()
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope='function')
def client(app, db):
    """Cliente HTTP de Flask para pruebas de integración."""
    with app.test_client() as c:
        with app.app_context():
            yield c


@pytest.fixture(scope='function')
def registered_user(client):
    """Registra y autentica un usuario de prueba. Retorna (user_dict, credentials)."""
    payload = {
        'email':    'test@finny.com',
        'username': 'TestUser',
        'password': 'securepass123',
    }
    client.post('/auth/register', json=payload)
    resp = client.post('/auth/login', json={
        'email':    payload['email'],
        'password': payload['password'],
    })
    return resp.get_json().get('user', {}), payload
