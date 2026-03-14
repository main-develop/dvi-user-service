from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, validate_email
from djoser.compat import settings
from djoser.serializers import (
    CurrentPasswordSerializer,
    SendEmailResetSerializer,
    UserCreateSerializer,
    UserDeleteSerializer,
    UsernameSerializer,
)
from rest_framework import serializers

User = get_user_model()


class ActivationSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(max_length=6, min_length=6, required=True)


class ChangeEmailSerializer(CurrentPasswordSerializer):
    """
    Serializer for requesting email change.

    Requires current password confirmation (twice) and ensures
    the new email differs from the current one.
    """

    new_email = serializers.EmailField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        user = self.context["request"].user

        if attrs["new_email"] == user.email:
            raise serializers.ValidationError(
                {
                    "new_email": (
                        "The current email address cannot be used as the new one."
                    )
                }
            )
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})

        return attrs


class CustomUserCreatePasswordRetypeSerializer(UserCreateSerializer):
    default_error_messages = {
        "password_mismatch": settings.CONSTANTS.messages.PASSWORD_MISMATCH_ERROR
    }

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


class CustomUserDeleteSerializer(UserDeleteSerializer, CurrentPasswordSerializer):
    """
    Serializer for permanent user account deletion.

    Extends djoser's default :class:`UserDeleteSerializer` by requiring the user to
    confirm their current password twice as an extra security measure
    before allowing account deletion.
    """

    confirm_password = serializers.CharField(required=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})

        return attrs


class CustomSendEmailResetSerializer(SendEmailResetSerializer):
    """
    Serializer for requesting password reset.

    Modifies djoser's default :class:`SendEmailResetSerializer` by removing
    ``"if user.has_usable_password()"`` guard. This allows password reset to work
    even after ``"user.set_unusable_password()"`` was deliberately called
    during account security lockdown.
    """

    def get_user(self):
        try:
            user = User._default_manager.get(
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
    username or email, along with a password check.
    """

    username_or_email = serializers.CharField(
        validators=[MaxLengthValidator(254)], required=True
    )
    password = serializers.CharField(required=True)
    remember_me = serializers.BooleanField(required=False, default=False)

    def validate_username_or_email(self, value):
        try:
            validate_email(value)
            self.context["is_email"] = True
        except ValidationError:
            self.context["is_email"] = False

        return value


class EmptySerializer(serializers.Serializer):
    """
    An empty serializer used as a workaround for the :class:`LogoutView` view.

    This bypasses errors in drf-spectacular during OpenAPI schema generation,
    where a serializer_class is required even for non-serializing actions.
    See the issue for details: https://github.com/tfranzel/drf-spectacular/issues/1314
    https://github.com/tfranzel/drf-spectacular/issues/1314.

    Note: this is a temporary fix; the issue is still open and may be resolved
    in the future.
    """


class CustomSetUsernameSerializer(UsernameSerializer):
    """
    Serializer for changing a user's username without requiring the current password.

    Djoser's default :class:`UsernameSerializer` requires the ``current_password``
    field. This custom serializer removes that requirement, since the security policy of
    this application allows username changes without password confirmation.
    """
