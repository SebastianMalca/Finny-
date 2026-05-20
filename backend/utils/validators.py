# backend/utils/validators.py
# Shared validation utilities.

import re


def is_valid_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_strong_password(password: str) -> bool:
    """At least 8 characters."""
    return len(password) >= 8
