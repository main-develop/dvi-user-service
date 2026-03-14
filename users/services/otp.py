import secrets
import string
from enum import StrEnum

from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.exceptions import ValidationError


class OTPPurpose(StrEnum):
    ACCOUNT_ACTIVATION = "account_activation"
    ACCOUNT_DELETION = "account_deletion"
    EMAIL_CHANGE = "email_change"
    PASSWORD_RESET = "password_reset"


User = get_user_model()


def generate_and_set_otp(email: str, purpose: OTPPurpose, timeout: int = 600) -> str:
    """Generate a 6-digit alphanumeric OTP and store it in cache."""
    if purpose not in OTPPurpose:
        raise ValidationError({"purpose": "Invalid verification purpose"})

    otp = "".join(
        secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6)
    )
    cache.set(f"{purpose}_otp_{email}", otp, timeout)

    return otp


def verify_otp(email: str, otp: str, purpose: OTPPurpose) -> User:
    """
    Reusable OTP verification service.

    Raises :class:`ValidationError` if OTP is invalid, expired, or purpose is unknown.
    Returns :class:`User` instance on success.
    """
    if purpose not in OTPPurpose:
        raise ValidationError({"purpose": "Invalid verification purpose"})

    cache_key = f"{purpose}_otp_{email}"
    stored_otp = cache.get(cache_key)

    if not stored_otp:
        raise ValidationError({"otp": "This code has expired"})
    if stored_otp != otp.upper():
        raise ValidationError({"otp": "This code is invalid"})

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist as exc:
        raise ValidationError({"email": "User not found"}) from exc

    cache.delete(cache_key)

    return user
