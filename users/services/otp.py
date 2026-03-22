import secrets
import string

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Q
from rest_framework.exceptions import ValidationError

User = get_user_model()


def generate_and_set_otp(email: str, timeout: int = 600) -> str:
    """Generate a 6-digit alphanumeric OTP and store it in cache."""
    otp = "".join(
        secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6)
    )
    cache.set(f"otp_{email}", otp, timeout)

    return otp


def verify_otp(email: str, otp: str) -> User:
    """
    Reusable OTP verification service.

    Raises :class:`ValidationError` if OTP is invalid, expired, or purpose is unknown.
    Returns :class:`User` instance on success.
    """
    cache_key = f"otp_{email}"
    stored_otp = cache.get(cache_key)

    if not stored_otp:
        raise ValidationError({"otp": "This code has expired"})
    if stored_otp != otp.upper():
        raise ValidationError({"otp": "This code is invalid"})

    try:
        user = User.objects.get(Q(email=email) | Q(pending_email=email))
    except User.DoesNotExist as exc:
        raise ValidationError({"email": "User not found"}) from exc

    cache.delete(cache_key)

    return user
