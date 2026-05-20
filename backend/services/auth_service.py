# backend/services/auth_service.py
# Authentication business logic:
#   register, login, logout, reset password flow.
# Passwords hashed with Werkzeug Security (PBKDF2-SHA256).

from werkzeug.security import generate_password_hash, check_password_hash
from backend.models import db
from backend.repositories.user_repository        import UserRepository
from backend.repositories.profile_repository     import ProfileRepository
from backend.repositories.streak_repository      import StreakRepository
from backend.repositories.mission_repository     import MissionRepository
from backend.repositories.achievement_repository import AchievementRepository


class AuthService:

    # ── Register ──────────────────────────────────────────────────────────────

    @staticmethod
    def register(email: str, username: str, password: str) -> dict:
        """
        Create a new user account.
        Returns dict with 'user' on success, or 'error' string on failure.
        """
        email    = email.strip().lower()
        username = username.strip()

        # Validate inputs
        if not email or not username or not password:
            return {'error': 'Todos los campos son requeridos.'}
        if '@' not in email or '.' not in email:
            return {'error': 'El email no tiene un formato válido.'}
        if len(username) < 2:
            return {'error': 'El nombre debe tener al menos 2 caracteres.'}
        if len(password) < 8:
            return {'error': 'La contraseña debe tener al menos 8 caracteres.'}
        if UserRepository.email_exists(email):
            return {'error': 'Ya existe una cuenta con ese email.'}

        # Hash password using Werkzeug (PBKDF2-SHA256 by default)
        password_hash = generate_password_hash(password)

        # Create user + related records in a single transaction
        try:
            user = UserRepository.create(email, username, password_hash)

            # Derive avatar from first 2 letters of username
            avatar = username[:2].upper()
            ProfileRepository.create(user.id, name=username, avatar=avatar)
            StreakRepository.create(user.id)
            MissionRepository.seed_for_user(user.id)
            AchievementRepository.seed_for_user(user.id)

            db.session.commit()
            return {'user': user}
        except Exception as exc:
            db.session.rollback()
            return {'error': f'Error al crear la cuenta: {str(exc)}'}

    # ── Login ─────────────────────────────────────────────────────────────────

    @staticmethod
    def login(email: str, password: str) -> dict:
        """
        Validate credentials.
        Returns {'user': User} on success or {'error': str} on failure.
        """
        email = email.strip().lower()
        user  = UserRepository.find_by_email(email)

        if not user or not check_password_hash(user.password_hash, password):
            return {'error': 'Email o contraseña incorrectos.'}
        if not user.is_active:
            return {'error': 'Esta cuenta está desactivada.'}

        return {'user': user}

    # ── Forgot password ───────────────────────────────────────────────────────

    @staticmethod
    def request_password_reset(email: str) -> dict:
        """
        Generate a reset token for the given email.
        Always returns success to prevent email enumeration.
        Token is returned directly (demo mode — no SMTP required).
        """
        email = email.strip().lower()
        user  = UserRepository.find_by_email(email)

        if not user:
            # Respond generically to avoid leaking whether email exists
            return {
                'message': 'Si el email existe, recibirás instrucciones para restablecer tu contraseña.',
                'debug_token': None,
            }

        token = user.generate_reset_token()
        db.session.commit()

        return {
            'message': 'Si el email existe, recibirás instrucciones para restablecer tu contraseña.',
            'debug_token': token,   # visible in API for dev/demo; remove in production
        }

    # ── Reset password ────────────────────────────────────────────────────────

    @staticmethod
    def reset_password(token: str, new_password: str) -> dict:
        """Apply a new hashed password if the reset token is valid and not expired."""
        if not token or not new_password:
            return {'error': 'Token y nueva contraseña son requeridos.'}
        if len(new_password) < 8:
            return {'error': 'La contraseña debe tener al menos 8 caracteres.'}

        user = UserRepository.find_by_reset_token(token)

        if not user or not user.is_reset_token_valid(token):
            return {'error': 'Token inválido o expirado.'}

        user.password_hash = generate_password_hash(new_password)
        user.clear_reset_token()
        db.session.commit()
        return {'message': 'Contraseña restablecida correctamente. Ya puedes iniciar sesión.'}
