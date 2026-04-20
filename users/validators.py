from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from zxcvbn import zxcvbn


class ZxcvbnValidator:
    def validate(self, password, user=None):
        result = zxcvbn(password=password)
        if result["score"] < 2:
            raise ValidationError("Password is too weak", "password_too_weak")


class MaximumLengthValidator:
    """
    Validate that the password is of a maximum length.
    """

    def __init__(self, max_length=64):
        self.max_length = max_length

    def validate(self, password, user=None):
        if len(password) > self.max_length:
            raise ValidationError(
                _(
                    "This password is too long. "
                    "It must contain no more than %(max_length)d characters."
                ),
                code="password_too_long",
                params={"max_length": self.max_length},
            )

    def get_help_text(self):
        return _(
            "Your password must contain no more than %(max_length)d characters."
        ) % {"max_length": self.max_length}
