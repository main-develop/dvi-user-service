from rest_framework import serializers


class EmptySerializer(serializers.Serializer):
    """
    An empty serializer used as a workaround for the :class:`LogoutView` view.

    This bypasses errors in drf-spectacular during OpenAPI schema generation,
    where a serializer_class is required even for non-serializing actions.
    See the issue for details: https://github.com/tfranzel/drf-spectacular/issues/1314
    https://github.com/tfranzel/drf-spectacular/issues/1314.

    Note: this is a temporary fix; the issue is still open and may be resolved in the future.
    """


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
