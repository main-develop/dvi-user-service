from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.utils import timezone
from djoser import signals, utils
from djoser.compat import settings
from djoser.serializers import UidAndTokenSerializer, UserDeleteSerializer
from djoser.views import UserViewSet
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from users.emails import EmailPurpose, send_email
from users.models import User
from users.serializers.user import (
    ChangeEmailSerializer,
    ResendVerificationEmailSerializer,
    VerificationPurpose,
    VerifyOtpSerializer,
)
from users.services.otp import verify_otp
from users.utils import revoke_all_user_sessions


@extend_schema_view(
    create=extend_schema(
        summary="Register a new user",
        description=(
            "Register a new user in the system. A unique `email`, `username`, "
            "and matching `password` with `confirm_password` are required for "
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
)
class CustomUserViewSet(UserViewSet):
    """
    Custom user management :class:`ViewSet` that extends djoser's :class:`UserViewSet`
    with additional functionality for email change workflow and improved account
    deletion handling.
    """

    def get_serializer_class(self):
        if self.action == "verify":
            return VerifyOtpSerializer
        if self.action == "resend_verification_email":
            return ResendVerificationEmailSerializer
        if self.action == "change_email":
            return ChangeEmailSerializer
        if self.action in {
            "change_email_confirm",
            "lockdown_account",
            "cancel_deletion",
        }:
            return UidAndTokenSerializer

        return super().get_serializer_class()

    def get_permissions(self):
        if self.action in {
            "verify",
            "resend_verification_email",
            "reset_password_confirm",
            "cancel_deletion",
            "lockdown_account",
        }:
            self.permission_classes = [permissions.AllowAny]

        return super().get_permissions()

    def perform_create(self, serializer, *args, **kwargs):
        user: User = serializer.save(*args, **kwargs)
        signals.user_registered.send(
            sender=self.__class__, user=user, request=self.request
        )

        if settings.SEND_ACTIVATION_EMAIL:
            send_email(
                purpose=EmailPurpose.ACCOUNT_ACTIVATION,
                request=self.request,
                to=user.email,
            )

    @extend_schema(summary="Verify user's email", tags=["Auth"])
    @action(["post"], detail=False)
    def verify(self, request, *args, **kwargs):
        """
        Verify user's email address to complete specific purpose.

        If purpose of verification is password reset, return the `uid` and `token`
        values that are needed in the confirmation step.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user: User = verify_otp(
            serializer.validated_data["email"],
            serializer.validated_data["otp"],
        )

        if not user.is_active:
            user.is_active = True
            user.save()

            signals.user_activated.send(
                sender=self.__class__, user=user, request=self.request
            )

            if settings.SEND_CONFIRMATION_EMAIL:
                send_email(
                    purpose=EmailPurpose.ACCOUNT_ACTIVATED,
                    request=self.request,
                    to=user.email,
                )

        if serializer.validated_data["purpose"] == VerificationPurpose.RESET_PASSWORD:
            uid = utils.encode_uid(user.pk)
            token = default_token_generator.make_token(user)

            return Response(
                data={"uid": uid, "token": token}, status=status.HTTP_200_OK
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(summary="Resend verification email", tags=["Auth"])
    @action(["post"], detail=False)
    def resend_verification_email(self, request, *args, **kwargs):
        """
        Resend a verification email with 6-digit OTP.

        Rate-limited to 4 attempts per hour.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        purpose = serializer.validated_data["purpose"]

        user: User = serializer.get_user(
            is_active=purpose != VerificationPurpose.ACCOUNT_ACTIVATION
        )
        if user:
            if purpose == VerificationPurpose.RESET_PASSWORD:
                email_purpose = EmailPurpose.RESET_PASSWORD
            else:
                email_purpose = EmailPurpose.ACCOUNT_ACTIVATION

            send_email(purpose=email_purpose, request=self.request, to=user.email)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(summary="Request email change", tags=["Users"])
    @action(["post"], detail=False)
    def change_email(self, request, *args, **kwargs):
        """
        Request a change of user's email address to a new one.

        A verification OTP is sent to the new email address. Rate-limited to
        4 attempts per hour.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user: User = request.user
        user.pending_email = serializer.validated_data["new_email"]
        user.save()

        send_email(
            purpose=EmailPurpose.CHANGE_EMAIL_NOTICE,
            request=request,
            context={"user": user},
            to=user.email,
        )
        send_email(
            purpose=EmailPurpose.CHANGE_EMAIL,
            request=request,
            context={"user": user},
            to=user.pending_email
        )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(summary="Confirm email change", tags=["Users"])
    @action(["post"], detail=False)
    def change_email_confirm(self, request, *args, **kwargs):
        """
        Confirm the new email address using 6-digit OTP.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user: User = verify_otp(serializer.user.email)
        with transaction.atomic():
            old_email = user.email
            user.email = user.pending_email
            user.pending_email = None
            user.save()

        send_email(
            purpose=EmailPurpose.EMAIL_CHANGED_NOTICE,
            request=request,
            context={"user": user},
            to=old_email,
        )
        send_email(
            purpose=EmailPurpose.EMAIL_CHANGED,
            request=request,
            context={"user": user},
            to=user.email,
        )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(summary="Request password reset", tags=["Users"])
    @action(["post"], detail=False)
    def reset_password(self, request, *args, **kwargs):
        """
        Request a password reset for an existing user.

        Rate-limited to 4 attempts per hour.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user: User = serializer.get_user()
        if user:
            send_email(
                purpose=EmailPurpose.RESET_PASSWORD, request=request, to=user.email
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(summary="Set new password", tags=["Users"])
    @action(["post"], detail=False)
    def reset_password_confirm(self, request, *args, **kwargs):
        """
        Set new password using `uid` and `token` from the OTP verification step.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user: User = serializer.user
        with transaction.atomic():
            user.set_password(serializer.validated_data["new_password"])
            user.is_active = True
            user.save(update_fields=["password", "is_active"])

        revoke_all_user_sessions(user)
        send_email(
            purpose=EmailPurpose.PASSWORD_CHANGED,
            request=request,
            context={"user": user},
            to=user.email,
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
        send_email(
            purpose=EmailPurpose.ACCOUNT_LOCKDOWN, request=request, to=user.email
        )

        return Response(status=status.HTTP_200_OK)

    @extend_schema(summary="Cancel scheduled account deletion", tags=["Users"])
    @action(["post"], detail=False)
    def cancel_deletion(self, request, *args, **kwargs):
        """
        Cancel a scheduled account deletion.
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

        send_email(purpose=EmailPurpose.ACCOUNT_DELETION_CANCELED, to=user.email)

        return Response(status=status.HTTP_200_OK)

    @extend_schema(
        summary="Delete user's account",
        tags=["Users"],
        request=UserDeleteSerializer,
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

        send_email(
            purpose=EmailPurpose.ACCOUNT_DELETION,
            request=request,
            context={"user": user},
            to=user.email,
        )

        return Response(status=status.HTTP_200_OK)
