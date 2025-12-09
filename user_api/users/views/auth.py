from django.contrib.auth import authenticate, login, logout
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from users import serializers
from users.models import User


class LoginView(generics.GenericAPIView):
    """
    Authenticates a user using either their username or email.
    Upon successful authentication, the user is logged in and a session is created.
    """

    serializer_class = serializers.LoginSerializer
    permission_classes = []

    @extend_schema(summary="Log user in", tags=["Auth"])
    def post(self, request, *args, **kwargs):
        """
        Log in using an existing user account.

        User can control the duration of their session using the ``remember_me`` value:
        - ``True`` will set the session cookie to expire in 2 weeks;
        - ``False`` will set the expiration to 0 making it a session cookie that expires
        when the browser closes.
        """

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data.get("username")
        email = serializer.validated_data.get("email")
        password = serializer.validated_data.get("password")
        remember_me = serializer.validated_data.get("remember_me")

        login_method = {"username": username} if username else {"email": email}
        user: User = authenticate(request=request, **login_method, password=password)

        if user is None:
            return Response(
                data={"detail": "Invalid credentials."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        login(request=request, user=user)

        if not remember_me:
            # Session expires when browser is closed
            request.session.set_expiry(0)
        # else: Default Django session expiry (2 weeks)

        return Response(status=status.HTTP_200_OK)


class LogoutView(generics.GenericAPIView):
    """
    Log out the currently authenticated user by terminating their session.
    """

    serializer_class = serializers.EmptySerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="Log user out", tags=["Auth"])
    def get(self, request, *args, **kwargs):
        """
        Log out by terminating the user's active session.
        """

        logout(request)
        return Response(status=status.HTTP_200_OK)
