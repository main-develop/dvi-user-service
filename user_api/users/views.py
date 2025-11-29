from django.contrib.auth import authenticate, login, logout
from djoser.serializers import ActivationSerializer, UserDeleteSerializer
from djoser.views import UserViewSet
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from users.emails import ChangeEmailConfirmationEmail, EmailChangedEmail
from users.serializers import (
    ChangeEmailSerializer,
    EmptySerializer,
    LoginSerializer,
)


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
    retrieve=extend_schema(
        summary="Get user's profile",
        description="Get general information about the user.",
        tags=["Users"],
    ),
    set_username=extend_schema(
        summary="Change user's username",
        description="Change user's username to a new one.",
        tags=["Users"],
    ),
    set_password=extend_schema(
        summary="Change user's password",
        description="Change user's password to a new one.",
        tags=["Users"],
    ),
    reset_password=extend_schema(
        summary="Request password reset",
        description=(
            "Request a password reset to the specified email address. "
            "The number of attempts is limited to 4 per hour."
        ),
        tags=["Users"],
    ),
    reset_password_confirm=extend_schema(
        summary="Confirm password reset",
        description=(
            "Confirm password reset and set a new one. "
            "The `uid` and `token` values must be extracted from the link sent to the "
            "user's email address."
        ),
        tags=["Users"],
    ),
    activation=extend_schema(
        summary="Confirm user email",
        description=(
            "Confirm the user's email address to complete the registration process. "
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
    """
    Custom user management :class:`ViewSet` that extends djoser's :class:`UserViewSet`
    with additional functionality for email change workflow and improved account
    deletion handling.
    """

    def get_serializer_class(self):
        if self.action == "change_email":
            return ChangeEmailSerializer
        elif self.action == "change_email_confirm":
            return ActivationSerializer
        return super().get_serializer_class()

    @extend_schema(
        summary="Request email change",
        tags=["Users"],
    )
    @action(["post"], detail=False)
    def change_email(self, request, *args, **kwargs):
        """
        Allows an authenticated user to request a change of their email address.
        A confirmation link is sent to the new email address. Rate-limited to 4 attempts per hour.
        """

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        new_email = serializer.validated_data["new_email"]

        user.pending_email = new_email
        user.save()

        context = {"user": user}
        to = [new_email]
        ChangeEmailConfirmationEmail(request, context).send(to)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="Confirm email change",
        tags=["Users"],
    )
    @action(["post"], detail=False)
    def change_email_confirm(self, request, *args, **kwargs):
        """
        Confirms the new email address using the ``uid`` and ``token`` sent
        in the confirmation email, finalising the email change and notifying the user.
        """

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.user
        user.email = user.pending_email
        user.pending_email = None
        user.save()

        context = {"user": user}
        to = [user.email]
        EmailChangedEmail(request, context).send(to)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="Delete user's account",
        tags=["Users"],
        request=UserDeleteSerializer,
    )
    def destroy(self, request, *args, **kwargs):
        """
        Ensures the user is logged out before their account is permanently deleted.
        Returns ``200 OK`` on successful deletion instead of the default ``204 NO CONTENT``.
        """

        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        if instance == request.user:
            logout(self.request)

        self.perform_destroy(instance=instance)

        return Response(status=status.HTTP_200_OK)


class LoginView(generics.GenericAPIView):
    """
    Authenticates a user using either their username or email.
    Upon successful authentication, the user is logged in and a session is created.
    """

    serializer_class = LoginSerializer
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
        user = authenticate(request=request, **login_method, password=password)

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

    serializer_class = EmptySerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="Log user out", tags=["Auth"])
    def get(self, request, *args, **kwargs):
        """
        Log out by terminating the user's active session.
        """

        logout(request=request)
        return Response(status=status.HTTP_200_OK)
