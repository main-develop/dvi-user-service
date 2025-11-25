from rest_framework import serializers


class EmptySerializer(serializers.Serializer):
    pass


class LoginSerializer(serializers.Serializer):
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
