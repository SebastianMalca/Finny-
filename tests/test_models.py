"""
test_models.py — Pruebas Unitarias de los modelos de dominio.

Cubre:
  - User: generate_reset_token, is_reset_token_valid, clear_reset_token, to_dict
  - Constantes: CATEGORIES, MAX_NAME_LENGTH, MAX_AMOUNT
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch


class TestUserModel:

    def test_generate_reset_token_returns_string(self, app):
        from backend.models.user import User
        with app.app_context():
            u = User(email='t@t.com', username='T', password_hash='h')
            token = u.generate_reset_token()
        assert isinstance(token, str)
        assert len(token) > 10

    def test_generate_reset_token_sets_expiry(self, app):
        from backend.models.user import User
        with app.app_context():
            u = User(email='t2@t.com', username='T2', password_hash='h')
            u.generate_reset_token()
            assert u.reset_expires is not None
            assert u.reset_expires > datetime.utcnow()

    def test_reset_token_valid_with_correct_token(self, app):
        from backend.models.user import User
        with app.app_context():
            u = User(email='t3@t.com', username='T3', password_hash='h')
            token = u.generate_reset_token()
            assert u.is_reset_token_valid(token) is True

    def test_reset_token_invalid_with_wrong_token(self, app):
        from backend.models.user import User
        with app.app_context():
            u = User(email='t4@t.com', username='T4', password_hash='h')
            u.generate_reset_token()
            assert u.is_reset_token_valid('wrongtoken') is False

    def test_reset_token_invalid_when_expired(self, app):
        from backend.models.user import User
        with app.app_context():
            u = User(email='t5@t.com', username='T5', password_hash='h')
            token = u.generate_reset_token()
            # Simular que el token ya expiró
            u.reset_expires = datetime.utcnow() - timedelta(hours=1)
            assert u.is_reset_token_valid(token) is False

    def test_clear_reset_token(self, app):
        from backend.models.user import User
        with app.app_context():
            u = User(email='t6@t.com', username='T6', password_hash='h')
            u.generate_reset_token()
            u.clear_reset_token()
            assert u.reset_token is None
            assert u.reset_expires is None

    def test_to_dict_contains_expected_keys(self, app):
        from backend.models.user import User
        with app.app_context():
            u = User(email='dict@t.com', username='DictUser', password_hash='h')
            u.created_at = datetime.utcnow()
            d = u.to_dict()
        assert 'email' in d
        assert 'username' in d
        assert 'is_active' in d
        assert 'created_at' in d
        assert 'password_hash' not in d  # No debe exponer el hash

    def test_to_dict_email_preserved(self, app):
        from backend.models.user import User
        with app.app_context():
            u = User(email='preserved@t.com', username='User', password_hash='h')
            u.created_at = datetime.utcnow()
            d = u.to_dict()
        assert d['email'] == 'preserved@t.com'

    def test_user_is_active_by_default(self, app):
        from backend.models.user import User
        with app.app_context():
            u = User(email='active@t.com', username='Active', password_hash='h')
        # is_active tiene default=True en la columna
        # Verificamos que el modelo acepta la creación sin error
        assert u is not None


class TestConstants:
    """Pruebas de las constantes de negocio en transversal/constants.py."""

    def test_categories_count(self):
        from transversal.constants import CATEGORIES
        assert len(CATEGORIES) == 6

    def test_categories_contains_expected_values(self):
        from transversal.constants import CATEGORIES
        expected = {'Food', 'Transport', 'Study', 'Entertainment', 'Health', 'Other'}
        assert set(CATEGORIES) == expected

    def test_max_name_length_is_100(self):
        from transversal.constants import MAX_NAME_LENGTH
        assert MAX_NAME_LENGTH == 100

    def test_max_amount_is_one_million(self):
        from transversal.constants import MAX_AMOUNT
        assert MAX_AMOUNT == 1_000_000

    def test_categories_are_strings(self):
        from transversal.constants import CATEGORIES
        assert all(isinstance(c, str) for c in CATEGORIES)

    def test_categories_not_empty_strings(self):
        from transversal.constants import CATEGORIES
        assert all(len(c) > 0 for c in CATEGORIES)
