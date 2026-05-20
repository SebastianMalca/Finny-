# FINNY Finance App — Backend v3
# Application factory: registers extensions, blueprints and Flask-Login.

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, jsonify
from flask_cors import CORS
from flask_login import LoginManager

from backend.config import config
from backend.models import db

# ── Import all blueprints ──────────────────────────────────────────────────────
from backend.routes.auth_routes         import auth_bp
from backend.routes.purchase_routes     import purchase_bp
from backend.routes.budget_routes       import budget_bp
from backend.routes.stats_routes        import stats_bp
from backend.routes.profile_routes      import profile_bp
from backend.routes.gamification_routes import gamification_bp
from backend.routes.tips_routes         import tips_bp
from backend.routes.dashboard_routes    import dashboard_bp

login_manager = LoginManager()


def create_app(config_name: str = 'development') -> Flask:
    """Application factory — creates and configures the Flask app."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # ── Extensions ─────────────────────────────────────────────────────────────
    CORS(app, supports_credentials=True, origins=['http://localhost:8080', 'http://127.0.0.1:8080'])
    db.init_app(app)

    login_manager.init_app(app)
    login_manager.session_protection = 'strong'

    # ── User loader (required by Flask-Login) ──────────────────────────────────
    from backend.models.user import User

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(User, int(user_id))

    # Return JSON 401 instead of redirect for unauthenticated API calls
    @login_manager.unauthorized_handler
    def unauthorized():
        return jsonify({'error': 'Debes iniciar sesión para acceder a este recurso.'}), 401

    # ── Blueprints ─────────────────────────────────────────────────────────────
    app.register_blueprint(auth_bp)
    app.register_blueprint(purchase_bp)
    app.register_blueprint(budget_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(gamification_bp)
    app.register_blueprint(tips_bp)
    app.register_blueprint(dashboard_bp)

    # ── Root endpoint ──────────────────────────────────────────────────────────
    @app.route('/', methods=['GET'])
    def home():
        return jsonify({
            'app':     'FINNY Finance API',
            'version': '3.0.0',
            'auth_endpoints': {
                'POST /auth/register':       'Crear cuenta nueva',
                'POST /auth/login':          'Iniciar sesión',
                'POST /auth/logout':         'Cerrar sesión',
                'GET  /auth/me':             'Usuario autenticado actual',
                'POST /auth/forgot-password':'Solicitar reset de contraseña',
                'POST /auth/reset-password': 'Cambiar contraseña con token',
            },
            'private_endpoints': {
                'GET  /dashboard':           'Resumen completo del dashboard',
                'GET  /compras':             'Listar compras (opcional ?category=)',
                'POST /compras':             'Crear una compra',
                'GET  /compras/<id>':        'Obtener una compra por ID',
                'DELETE /compras/<id>':      'Eliminar una compra',
                'GET  /estadisticas':        'Estadísticas por categoría',
                'GET  /tendencia':           'Tendencia de gasto (?days=7)',
                'GET  /presupuesto':         'Obtener presupuesto actual',
                'POST /presupuesto':         'Guardar presupuesto mensual',
                'GET  /racha':              'Estado de la racha diaria',
                'GET  /misiones':           'Lista de misiones con progreso',
                'GET  /logros':             'Lista de logros',
                'GET  /consejos':           'Consejos personalizados (?limit=3)',
                'POST /consejos/leer':      'Marcar un consejo como leído (+XP)',
                'GET  /perfil':             'Perfil del usuario',
                'PUT  /perfil':             'Actualizar nombre o avatar',
                'GET  /categorias':         'Categorías disponibles',
                'GET  /health':             'Health check',
            }
        }), 200

    # ── DB init ────────────────────────────────────────────────────────────────
    with app.app_context():
        db.create_all()
        print('[DB] MySQL schema applied / verified.')

    return app


# ── Entry point ────────────────────────────────────────────────────────────────

app = create_app('development')

if __name__ == '__main__':
    print('=' * 58)
    print('  FINNY Finance App Backend v3.0  (MySQL + Auth)')
    print('  Server -> http://localhost:5000')
    print('=' * 58)
    app.run(debug=True, host='0.0.0.0', port=5000)
