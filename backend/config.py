# FINNY — Configuration
# Soporta SQLite (dev/demo), MySQL y PostgreSQL vía DATABASE_URL.

import os
import secrets

# ── Detect environment ─────────────────────────────────────────────────────────
IS_PRODUCTION = os.environ.get('VERCEL_ENV') == 'production' or \
                os.environ.get('FLASK_ENV') == 'production'


def _build_db_uri() -> str:
    """
    Priority:
      1. DATABASE_URL env var (Neon, Railway, PlanetScale…)
      2. Individual MYSQL_* vars (legacy local MySQL)
      3. SQLite fallback (dev / Vercel demo)
    """
    db_url = os.environ.get('DATABASE_URL', '').strip()

    # Neon/Heroku usan el prefijo 'postgres://' — SQLAlchemy necesita 'postgresql://'
    if db_url.startswith('postgres://'):
        db_url = 'postgresql+psycopg2://' + db_url[len('postgres://'):]
    if db_url.startswith('postgresql://') and 'psycopg2' not in db_url:
        db_url = 'postgresql+psycopg2://' + db_url[len('postgresql://'):]

    if db_url:
        return db_url

    # Legacy MySQL vars
    mysql_user = os.environ.get('MYSQL_USER')
    mysql_pass = os.environ.get('MYSQL_PASSWORD')
    mysql_host = os.environ.get('MYSQL_HOST')
    mysql_db   = os.environ.get('MYSQL_DB')
    if mysql_user and mysql_host and mysql_db:
        pw = f':{mysql_pass}' if mysql_pass else ''
        return f'mysql+pymysql://{mysql_user}{pw}@{mysql_host}:3306/{mysql_db}?charset=utf8mb4'

    # SQLite fallback — almacena en /tmp en Vercel, localmente en backend/
    sqlite_path = os.path.join(os.path.dirname(__file__), 'finny.db')
    return f'sqlite:///{sqlite_path}'


class Config:
    # ── Secret key ────────────────────────────────────────────────────────────
    # IMPORTANTE: define SECRET_KEY como variable de entorno en Vercel.
    # Si no está definida cada despliegue genera una nueva clave e invalida las sesiones.
    SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))

    # ── Database ───────────────────────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI    = _build_db_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS  = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
    }

    # ── Session / Cookie ───────────────────────────────────────────────────────
    SESSION_COOKIE_HTTPONLY  = True
    # En producción (cross-origin Vercel) necesitamos SameSite=None + Secure
    SESSION_COOKIE_SAMESITE  = 'None' if IS_PRODUCTION else 'Lax'
    SESSION_COOKIE_SECURE    = IS_PRODUCTION
    REMEMBER_COOKIE_DURATION = 86400 * 7  # 7 days
    REMEMBER_COOKIE_SAMESITE = 'None' if IS_PRODUCTION else 'Lax'
    REMEMBER_COOKIE_SECURE   = IS_PRODUCTION

    # ── Password Reset Token ───────────────────────────────────────────────────
    RESET_TOKEN_EXPIRY_HOURS = 1


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'default':     DevelopmentConfig,
}
