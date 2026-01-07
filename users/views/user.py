from django.db import transaction
from django.utils import timezone
from djoser.serializers import UidAndTokenSerializer
from djoser.views import UserViewSet
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from users import emails, serializers
from users.models import User
from users.utils import revoke_all_user_sessions


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
    me=extend_schema(
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
            return serializers.ChangeEmailSerializer
        if self.action in {
            "change_email_confirm",
            "lockdown_account",
            "cancel_deletion",
        }:
            return UidAndTokenSerializer

        return super().get_serializer_class()

    def get_permissions(self):
        if self.action in {"cancel_deletion", "lockdown_account"}:
            self.permission_classes = [permissions.AllowAny]

        return super().get_permissions()

    @extend_schema(summary="Request email change", tags=["Users"])
    @action(["post"], detail=False)
    def change_email(self, request, *args, **kwargs):
        """
        Allow an authenticated user to request a change of their email address.

        A confirmation link is sent to the new email address. Rate-limited to
        4 attempts per hour.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user: User = request.user
        user.pending_email = serializer.validated_data["new_email"]
        user.save()

        emails.ChangeEmailNoticeEmail(request=request, context={"user": user}).send(
            to=[user.email]
        )
        emails.ChangeEmailConfirmEmail(request=request, context={"user": user}).send(
            to=[user.pending_email]
        )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(summary="Confirm email change", tags=["Users"])
    @action(["post"], detail=False)
    def change_email_confirm(self, request, *args, **kwargs):
        """
        Confirm the new email address using the uid and token sent in the
        confirmation email, finalising the email change and notifying the user.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user: User = serializer.user
        with transaction.atomic():
            old_email = user.email
            user.email = user.pending_email
            user.pending_email = None
            user.save()

        emails.ChangeEmailAlertEmail(request=request, context={"user": user}).send(
            to=[old_email]
        )
        emails.ChangeEmailSuccessEmail(request=request, context={"user": user}).send(
            to=[user.email]
        )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(summary="Request password reset", tags=["Users"])
    @action(["post"], detail=False)
    def reset_password(self, request, *args, **kwargs):
        """
        Request a password reset to the specified email address.

        Rate-limited to 4 attempts per hour.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user: User = serializer.get_user()
        if user:
            emails.ResetPasswordConfirmEmail(
                request=request, context={"user": user}
            ).send(to=[user.email])

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(summary="Confirm password reset", tags=["Users"])
    @action(["post"], detail=False)
    def reset_password_confirm(self, request, *args, **kwargs):
        """
        Confirm password reset and set a new one.

        The uid and token values must be extracted from the link sent to
        the user's email address.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user: User = serializer.user
        with transaction.atomic():
            user.set_password(serializer.data["new_password"])
            user.is_active = True
            user.save(update_fields=["password", "is_active"])

        revoke_all_user_sessions(user)

        emails.ResetPasswordSuccessEmail(request=request, context={"user": user}).send(
            to=[user.email]
        )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(summary="Lockdown user's account", tags=["Users"])
    @action(["post"], detail=False)
    def lockdown_account(self, request, *args, **kwargs):
        """
        Immediate account security lockdown at the user's request to protect against
        potential unauthorized access (account takeover).

        This action invalidates current password and revokes all user sessions.
        If applicable, cancels scheduled account deletion and/or pending email.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user: User = serializer.user
        with transaction.atomic():
            user.set_unusable_password()
            user.deletion_scheduled_at = None
            user.pending_email = None
            user.save(
                update_fields=["password", "deletion_scheduled_at", "pending_email"]
            )

        revoke_all_user_sessions(user)

        emails.AccountLockdownNoticeEmail(request=request, context={"user": user}).send(
            to=[user.email]
        )

        return Response(status=status.HTTP_200_OK)

    @extend_schema(summary="Cancel scheduled account deletion", tags=["Users"])
    @action(["post"], detail=False)
    def cancel_deletion(self, request, *args, **kwargs):
        """
        Cancel a scheduled account deletion.

        If no deletion is scheduled, returns success anyway (idempotent).
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user: User = serializer.user
        if user.deletion_scheduled_at is None:
            return Response(
                data={"detail": "No deletion scheduled."}, status=status.HTTP_200_OK
            )

        with transaction.atomic():
            user.is_active = True
            user.deletion_scheduled_at = None
            user.save(update_fields=["is_active", "deletion_scheduled_at"])

        emails.AccountDeletionCanceledEmail().send(to=[user.email])

        return Response(status=status.HTTP_200_OK)

    @extend_schema(
        summary="Delete user's account",
        tags=["Users"],
        request=serializers.CustomUserDeleteSerializer,
    )
    def destroy(self, request, *args, **kwargs):
        """
        Schedule permanent account deletion in 24 hours.

        User can cancel it via ``/users/account-security/lockdown/``
        endpoint if they suspect takeover.
        """
        user: User = request.user
        serializer = self.get_serializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            user.is_active = False
            user.deletion_scheduled_at = timezone.now() + timezone.timedelta(hours=24)
            user.save(update_fields=["is_active", "deletion_scheduled_at"])

        revoke_all_user_sessions(user)

        emails.AccountDeletionAlertEmail(request=request, context={"user": user}).send(
            to=[user.email]
        )

        return Response(status=status.HTTP_200_OK)
