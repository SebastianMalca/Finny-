# FINNY Finance App — Backend v3
# Application factory: registers extensions, blueprints and Flask-Login.

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, jsonify
from flask_cors import CORS
from flask_login import LoginManager

from backend.config import config, IS_PRODUCTION
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


def create_app(config_name: str = None) -> Flask:
    """Application factory — creates and configures the Flask app."""
    if config_name is None:
        config_name = 'production' if IS_PRODUCTION else 'development'

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # ── CORS ────────────────────────────────────────────────────────────────────
    # En desarrollo: solo localhost.
    # En producción: el dominio de Vercel se detecta automáticamente.
    vercel_url = os.environ.get('VERCEL_URL', '')
    allowed_origins = [
        'http://localhost:8080',
        'http://127.0.0.1:8080',
        'http://localhost:5000',
        'http://127.0.0.1:5000',
    ]
    if vercel_url:
        allowed_origins.append(f'https://{vercel_url}')

    # NEXT_PUBLIC_FRONTEND_URL permite definir un dominio custom (ej. finny.vercel.app)
    custom_origin = os.environ.get('FRONTEND_URL', '')
    if custom_origin:
        allowed_origins.append(custom_origin)

    CORS(
        app,
        supports_credentials=True,
        origins=allowed_origins,
        allow_headers=['Content-Type', 'Authorization'],
        methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    )

    # ── Extensions ─────────────────────────────────────────────────────────────
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
            'status':  'running',
            'db':      str(app.config.get('SQLALCHEMY_DATABASE_URI', ''))[:30] + '…',
        }), 200

    # ── DB init ────────────────────────────────────────────────────────────────
    with app.app_context():
        db.create_all()
        print('[DB] Schema applied / verified.')

    return app


# ── Entry point ────────────────────────────────────────────────────────────────

app = create_app()

if __name__ == '__main__':
    print('=' * 58)
    print('  FINNY Finance App Backend v3.0')
    print(f'  DB → {app.config["SQLALCHEMY_DATABASE_URI"][:50]}')
    print('  Server → http://localhost:5000')
    print('=' * 58)
    app.run(debug=True, host='0.0.0.0', port=5000)
