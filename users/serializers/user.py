from enum import StrEnum

from django.contrib.auth import get_user_model
from djoser.compat import settings
from djoser.serializers import (
    PasswordSerializer,
    SendEmailResetSerializer,
    UidAndTokenSerializer,
    UserCreateSerializer,
    UsernameSerializer,
)
from rest_framework import serializers

DEFAULT_ERROR_MESSAGES = {
    "password_mismatch": "Passwords do not match",
    "invalid_password": "Invalid password",
}

User = get_user_model()


class VerificationPurpose(StrEnum):
    ACCOUNT_ACTIVATION = "account_activation"
    CHANGE_EMAIL = "change_email"
    RESET_PASSWORD = "reset_password"


class UserFunctionsMixin:
    """
    Mixin that modifies djoser's default :class:`UserFunctionsMixin` by removing
    ``"if user.has_usable_password()"`` guard. In particular, this allows password reset
    and password reset resend to work even after ``"user.set_unusable_password()"`` was
    deliberately called during account security lockdown.
    """

    def get_user(self, is_active=True):
        try:
            user = User._default_manager.get(
                is_active=is_active,
                **{self.email_field: self.data.get(self.email_field, "")},
            )
            return user
        except User.DoesNotExist:
            pass

        if (
            settings.PASSWORD_RESET_SHOW_EMAIL_NOT_FOUND
            or settings.USERNAME_RESET_SHOW_EMAIL_NOT_FOUND
        ): # pragma: no cover
            self.fail("email_not_found")


class UserCreatePasswordRetypeSerializer(UserCreateSerializer):
    """
    Serializer for user creation/registration that requires password
    confirmation.

    Extends :class:`UserCreateSerializer` by dynamically adding a
    `confirm_password` field.
    """

    default_error_messages = DEFAULT_ERROR_MESSAGES

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["confirm_password"] = serializers.CharField(
            style={"input_type": "password"}
        )

    def validate(self, attrs):
        self.fields.pop("confirm_password", None)
        confirm_password = attrs.pop("confirm_password")
        attrs = super().validate(attrs)
        if attrs["password"] == confirm_password:
            return attrs
        else:
            self.fail("password_mismatch")


class CurrentPasswordSerializer(serializers.Serializer):
    """Serializer for current password validation."""

    current_password = serializers.CharField(style={"input_type": "password"})

    default_error_messages = DEFAULT_ERROR_MESSAGES

    def validate_current_password(self, value):
        is_password_valid = self.context["request"].user.check_password(value)
        if is_password_valid:
            return value
        else:
            self.fail("invalid_password")


class ResendVerificationEmailSerializer(UserFunctionsMixin, SendEmailResetSerializer):
    """Serializer for requesting a resend of a verification email."""

    purpose = serializers.ChoiceField(choices=VerificationPurpose, required=True)


class VerifyOtpSerializer(serializers.Serializer):
    """Serializer for verifying a OTP code."""

    email = serializers.EmailField(required=True)
    otp = serializers.CharField(max_length=6, min_length=6, required=True)
    purpose = serializers.ChoiceField(choices=VerificationPurpose, required=True)


class ChangeEmailSerializer(CurrentPasswordSerializer):
    """
    Serializer for requesting email change.

    Requires current password confirmation and ensures
    the new email differs from the current one.
    """

    new_email = serializers.EmailField(required=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        user: User = self.context["request"].user

        if attrs["new_email"] == user.email:
            raise serializers.ValidationError(
                {
                    "new_email": (
                        "The current email address cannot be used as the new one"
                    )
                }
            )
        return attrs


class SetUsernameSerializer(UsernameSerializer):
    """
    Serializer for changing a user's username.

    Djoser's default :class:`UsernameSerializer` requires the ``current_password``
    field. This custom serializer removes that requirement.
    """


class PasswordRetypeSerializer(PasswordSerializer):
    """
    Serializer for password reset/change flows that requires the user
    to retype the new password for confirmation.

    Extends :class:`PasswordSerializer` by adding a required `confirm_password`
    field.
    """

    default_error_messages = DEFAULT_ERROR_MESSAGES
    confirm_password = serializers.CharField(
        required=True, style={"input_type": "password"}
    )

    def validate(self, attrs):
        self.fields.pop("confirm_password", None)
        confirm_password = attrs.pop("confirm_password")
        attrs = super().validate(attrs)
        if attrs["new_password"] == confirm_password:
            return attrs
        else:
            self.fail("password_mismatch")


class SetPasswordRetypeSerializer(PasswordRetypeSerializer, CurrentPasswordSerializer):
    """Serializer for setting a new password."""


class PasswordResetSerializer(UserFunctionsMixin, SendEmailResetSerializer):
    """Serializer for requesting password reset."""


class PasswordResetConfirmSerializer(UidAndTokenSerializer, PasswordRetypeSerializer):
    """
    Serializer for resetting password using `uid` and `token` from the OTP
    verification step.
    """


class UserDeleteSerializer(CurrentPasswordSerializer):
    """Serializer for requesting account deletion."""
