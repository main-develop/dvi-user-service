from django.contrib.auth import get_user_model
from djoser.compat import settings
from djoser.serializers import (
    CurrentPasswordSerializer,
    SendEmailResetSerializer,
    UserDeleteSerializer,
    UsernameSerializer,
)
from rest_framework import serializers

User = get_user_model()


class ChangeEmailSerializer(CurrentPasswordSerializer):
    """
    Serializer for requesting email change. Requires current password confirmation
    (twice) and ensures the new email differs from the current one.
    """

    new_email = serializers.EmailField(required=True)
    re_current_password = serializers.CharField(required=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        user = self.context["request"].user

        if attrs["new_email"] == user.email:
            raise serializers.ValidationError(
                {
                    "new_email": "The current email address cannot be used as the new one."
                }
            )
        if attrs["current_password"] != attrs["re_current_password"]:
            raise serializers.ValidationError(
                {"current_password": "Passwords do not match."}
            )

        return attrs


class CustomUserDeleteSerializer(UserDeleteSerializer, CurrentPasswordSerializer):
    """
    Serializer for permanent user account deletion.

    Extends Djoser's default :class:`UserDeleteSerializer` by requiring the user to
    confirm their current password twice as an extra security measure
    before allowing account deletion.
    """

    re_current_password = serializers.CharField(required=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs["current_password"] != attrs["re_current_password"]:
            raise serializers.ValidationError(
                {"current_password": "Passwords do not match."}
            )

        return attrs


class CustomSendEmailResetSerializer(SendEmailResetSerializer):
    """
    Serializer for requesting password reset.

    Modifies Djoser's default :class:`SendEmailResetSerializer` by removing
    ``"if user.has_usable_password()"`` guard. This allows password reset to work
    even after ``"user.set_unusable_password()"`` was deliberately called
    during account security lockdown.
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
        ):
            self.fail("email_not_found")


class LoginSerializer(serializers.Serializer):
    """
    Serializer for handling user login credentials.

    Validates input for user authentication, allowing login via either
    username or email (but not both), along with a password check.
    """

    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    password = serializers.CharField(required=True)
    remember_me = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        username = attrs.get("username")
        email = attrs.get("email")
        password = attrs.get("password")

        if username and email:
            raise serializers.ValidationError(
                "Either provide email or username to login, not both."
            )
        if not (username or email):
            raise serializers.ValidationError(
                "Username or email is required to log in."
            )
        if len(password) < 8:
            raise serializers.ValidationError("Invalid credentials.")

        return attrs


class EmptySerializer(serializers.Serializer):
    """
    An empty serializer used as a workaround for the :class:`LogoutView` view.

    This bypasses errors in drf-spectacular during OpenAPI schema generation,
    where a serializer_class is required even for non-serializing actions.
    See the issue for details: https://github.com/tfranzel/drf-spectacular/issues/1314
    https://github.com/tfranzel/drf-spectacular/issues/1314.

    Note: this is a temporary fix; the issue is still open and may be resolved in the future.
    """


class CustomSetUsernameSerializer(UsernameSerializer):
    """
    Serializer for changing a user's username without requiring the current password.

    Djoser's default :class:`UsernameSerializer` requires the ``current_password``
    field. This custom serializer removes that requirement, since the security policy of
    this project allows username changes without password confirmation.
    """
