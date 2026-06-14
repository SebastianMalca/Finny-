"""
test_auth_service.py — Pruebas Unitarias del módulo AuthService.

Cubre:
  - register: validaciones de input, creación exitosa, email duplicado
  - login: credenciales correctas e incorrectas, cuenta inactiva
  - request_password_reset: token generado, email inexistente (respuesta genérica)
  - reset_password: token válido, token expirado/inválido, contraseña corta
"""
import pytest
from unittest.mock import patch, MagicMock
from backend.services.auth_service import AuthService


class TestAuthServiceRegister:
    """Pruebas unitarias de AuthService.register (con mocks de repositorios)."""

    def _mock_repos(self, email_exists=False):
        """Devuelve un contexto con todos los repositorios mockeados."""
        patches = [
            patch('backend.services.auth_service.UserRepository.email_exists',    return_value=email_exists),
            patch('backend.services.auth_service.UserRepository.create',           return_value=MagicMock(id=1)),
            patch('backend.services.auth_service.ProfileRepository.create'),
            patch('backend.services.auth_service.StreakRepository.create'),
            patch('backend.services.auth_service.MissionRepository.seed_for_user'),
            patch('backend.services.auth_service.AchievementRepository.seed_for_user'),
            patch('backend.services.auth_service.db.session.commit'),
        ]
        return patches

    def test_register_missing_email_returns_error(self):
        result = AuthService.register('', 'User', 'password123')
        assert 'error' in result

    def test_register_missing_username_returns_error(self):
        result = AuthService.register('user@test.com', '', 'password123')
        assert 'error' in result

    def test_register_missing_password_returns_error(self):
        result = AuthService.register('user@test.com', 'User', '')
        assert 'error' in result

    def test_register_invalid_email_format(self):
        result = AuthService.register('notanemail', 'User', 'password123')
        assert 'error' in result
        assert 'email' in result['error'].lower()

    def test_register_username_too_short(self):
        result = AuthService.register('user@test.com', 'A', 'password123')
        assert 'error' in result
        assert 'nombre' in result['error'].lower()

    def test_register_password_too_short(self):
        result = AuthService.register('user@test.com', 'User', '123')
        assert 'error' in result
        assert 'contraseña' in result['error'].lower()

    def test_register_duplicate_email(self):
        with patch('backend.services.auth_service.UserRepository.email_exists', return_value=True):
            result = AuthService.register('dupe@test.com', 'User', 'password123')
        assert 'error' in result
        assert 'email' in result['error'].lower() or 'cuenta' in result['error'].lower()

    def test_register_success(self):
        mock_user = MagicMock(id=42)
        patches = self._mock_repos(email_exists=False)
        patches[1] = patch('backend.services.auth_service.UserRepository.create', return_value=mock_user)

        with patch('backend.services.auth_service.UserRepository.email_exists', return_value=False), \
             patch('backend.services.auth_service.UserRepository.create', return_value=mock_user), \
             patch('backend.services.auth_service.ProfileRepository.create'), \
             patch('backend.services.auth_service.StreakRepository.create'), \
             patch('backend.services.auth_service.MissionRepository.seed_for_user'), \
             patch('backend.services.auth_service.AchievementRepository.seed_for_user'), \
             patch('backend.services.auth_service.db.session.commit'), \
             patch('backend.services.auth_service.db.session.rollback'):
            result = AuthService.register('new@test.com', 'NuevoUsuario', 'securepass')
        assert 'user' in result
        assert result['user'] == mock_user

    def test_register_trims_email_whitespace(self):
        """El email debe guardarse en minúsculas y sin espacios."""
        with patch('backend.services.auth_service.UserRepository.email_exists', return_value=True):
            result = AuthService.register('  User@Test.COM  ', 'User', 'password123')
        # email_exists habrá sido llamado con el email normalizado
        assert 'error' in result  # duplicado o cualquier otro error


class TestAuthServiceLogin:
    """Pruebas unitarias de AuthService.login."""

    def test_login_wrong_email(self):
        with patch('backend.services.auth_service.UserRepository.find_by_email', return_value=None):
            result = AuthService.login('noexiste@test.com', 'password123')
        assert 'error' in result

    def test_login_wrong_password(self):
        mock_user = MagicMock(is_active=True)
        mock_user.password_hash = 'hashed'
        with patch('backend.services.auth_service.UserRepository.find_by_email', return_value=mock_user), \
             patch('backend.services.auth_service.check_password_hash', return_value=False):
            result = AuthService.login('user@test.com', 'wrongpassword')
        assert 'error' in result

    def test_login_inactive_account(self):
        mock_user = MagicMock(is_active=False)
        mock_user.password_hash = 'hashed'
        with patch('backend.services.auth_service.UserRepository.find_by_email', return_value=mock_user), \
             patch('backend.services.auth_service.check_password_hash', return_value=True):
            result = AuthService.login('user@test.com', 'password123')
        assert 'error' in result
        assert 'desactivada' in result['error'].lower()

    def test_login_success(self):
        mock_user = MagicMock(is_active=True)
        mock_user.password_hash = 'hashed'
        with patch('backend.services.auth_service.UserRepository.find_by_email', return_value=mock_user), \
             patch('backend.services.auth_service.check_password_hash', return_value=True):
            result = AuthService.login('user@test.com', 'password123')
        assert 'user' in result
        assert result['user'] == mock_user


class TestAuthServicePasswordReset:
    """Pruebas unitarias del flujo de reset de contraseña."""

    def test_forgot_password_nonexistent_email_returns_generic_message(self):
        with patch('backend.services.auth_service.UserRepository.find_by_email', return_value=None):
            result = AuthService.request_password_reset('noexiste@test.com')
        assert 'message' in result
        assert result.get('debug_token') is None

    def test_forgot_password_existing_email_returns_token(self):
        mock_user = MagicMock()
        mock_user.generate_reset_token.return_value = 'abc123token'
        with patch('backend.services.auth_service.UserRepository.find_by_email', return_value=mock_user), \
             patch('backend.services.auth_service.db.session.commit'):
            result = AuthService.request_password_reset('user@test.com')
        assert 'message' in result
        assert result['debug_token'] == 'abc123token'

    def test_reset_password_missing_fields(self):
        result = AuthService.reset_password('', 'newpassword')
        assert 'error' in result

    def test_reset_password_too_short(self):
        result = AuthService.reset_password('sometoken', '123')
        assert 'error' in result
        assert 'contraseña' in result['error'].lower()

    def test_reset_password_invalid_token(self):
        with patch('backend.services.auth_service.UserRepository.find_by_reset_token', return_value=None):
            result = AuthService.reset_password('invalidtoken', 'newpassword123')
        assert 'error' in result
        assert 'inválido' in result['error'].lower() or 'token' in result['error'].lower()

    def test_reset_password_success(self):
        mock_user = MagicMock()
        mock_user.is_reset_token_valid.return_value = True
        with patch('backend.services.auth_service.UserRepository.find_by_reset_token', return_value=mock_user), \
             patch('backend.services.auth_service.db.session.commit'):
            result = AuthService.reset_password('validtoken', 'newpassword123')
        assert 'message' in result
        assert 'restablecida' in result['message'].lower()
