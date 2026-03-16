from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, validate_email
from rest_framework import serializers


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


class LogoutSerializer(serializers.Serializer):
    """
    An empty serializer used as a workaround for the :class:`LogoutView` view.

    This bypasses errors in drf-spectacular during OpenAPI schema generation,
    where a serializer_class is required even for non-serializing actions.
    See the issue for details: https://github.com/tfranzel/drf-spectacular/issues/1314
    https://github.com/tfranzel/drf-spectacular/issues/1314.

    Note: this is a temporary fix; the issue is still open and may be resolved
    in the future.
    """
