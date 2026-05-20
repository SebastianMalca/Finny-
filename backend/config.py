# FINNY — Configuration
# Centralizes all settings: database, sessions, security tokens.

import os
import secrets

class Config:
    # ── Secret key ────────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))

    # ── MySQL Database ─────────────────────────────────────────────────────────
    MYSQL_USER     = os.environ.get('MYSQL_USER',     'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_HOST     = os.environ.get('MYSQL_HOST',     'localhost')
    MYSQL_PORT     = os.environ.get('MYSQL_PORT',     '3306')
    MYSQL_DB       = os.environ.get('MYSQL_DB',       'finny_db')

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
    }

    # ── Session / Cookie ───────────────────────────────────────────────────────
    SESSION_COOKIE_HTTPONLY  = True
    SESSION_COOKIE_SAMESITE  = 'Lax'
    SESSION_COOKIE_SECURE    = False   # Set True in production (HTTPS)
    REMEMBER_COOKIE_DURATION = 86400 * 7  # 7 days

    # ── Password Reset Token ───────────────────────────────────────────────────
    RESET_TOKEN_EXPIRY_HOURS = 1


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


config = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'default':     DevelopmentConfig,
}
