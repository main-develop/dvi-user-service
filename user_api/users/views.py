from django.contrib.auth import authenticate, login, logout
from djoser.views import UserViewSet
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from users.serializers import EmptySerializer, LoginSerializer


@extend_schema_view(
    create=extend_schema(
        summary="Register a new user",
        description=(
            "Register a new user in the system. A unique `email`, `username`, "
            "and matching `password` and `re_password` are required for "
            "successful registration."
        ),
        tags=["Auth"],
    ),
    activation=extend_schema(
        summary="Verify user email",
        description=(
            "Verify the user's email address to complete the registration process. "
            "The `uid` and `token` values must be extracted from the link sent to the "
            "user's email address."
        ),
        tags=["Auth"],
    ),
    resend_activation=extend_schema(
        summary="Resend confirmation email",
        description=(
            "Resend the confirmation email. The number of attempts is limited to 4 per hour."
        ),
        tags=["Auth"],
    ),
)
class CustomUserViewSet(UserViewSet):
    pass


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = []

    @extend_schema(summary="Log user in", tags=["Auth"])
    def post(self, request, *args, **kwargs):
        """
        Log in using an existing user account.

        User can control the duration of their session using the `remember_me` value:
        - `True` will set the session cookie to expire in 2 weeks;
        - `False` will set the expiration to 0 making it a session cookie that expires
        when the browser closes.
        """

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data.get("username")
        email = serializer.validated_data.get("email")
        password = serializer.validated_data.get("password")
        remember_me = serializer.validated_data.get("remember_me")

        login_method = {"username": username} if username else {"email": email}
        user = authenticate(request=request, **login_method, password=password)

        if user is None:
            return Response(
                data={"detail": "Invalid credentials."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        login(request=request, user=user)

        if not remember_me:
            # Session cookie will expire at browser close, otherwise after 2 weeks
            request.session.set_expiry(0)

        return Response(status=status.HTTP_200_OK)


class LogoutView(generics.GenericAPIView):
    serializer_class = EmptySerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="Log user out", tags=["Auth"])
    def get(self, request, *args, **kwargs):
        """
        Log out by terminating the user's active session.
        """

        logout(request=request)
        return Response(status=status.HTTP_200_OK)
