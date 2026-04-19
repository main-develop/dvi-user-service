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

from users.emails import EmailPurpose
from users.models import User
from users.serializers.user import (
    ChangeEmailSerializer,
    ResendVerificationEmailSerializer,
    VerificationPurpose,
    VerifyOtpSerializer,
)
from users.services.otp import verify_otp
from users.tasks import send_email_task
from users.utils import generate_uid_and_token, revoke_all_user_sessions


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
        if self.action == "lockdown_account":
            return UidAndTokenSerializer

        return super().get_serializer_class()

    def get_permissions(self):
        if self.action in {
            "verify",
            "resend_verification_email",
            "reset_password_confirm",
            "lockdown_account",
        }:
            self.permission_classes = [permissions.AllowAny]

        return super().get_permissions()

    def perform_create(self, serializer, *args, **kwargs):
        user: User = serializer.save(*args, **kwargs)
        signals.user_registered.send(
            sender=self.__class__, user=user, request=self.request
        )

        if settings.SEND_ACTIVATION_EMAIL:  # pragma: no branch
            send_email_task.delay(
                purpose=EmailPurpose.ACCOUNT_ACTIVATION.name,
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
            user.save(update_fields=["is_active"])

            signals.user_activated.send(
                sender=self.__class__, user=user, request=self.request
            )

            if settings.SEND_CONFIRMATION_EMAIL:  # pragma: no branch
                send_email_task.delay(
                    purpose=EmailPurpose.ACCOUNT_ACTIVATED.name,
                    to=user.email,
                )

        if user.pending_email:
            with transaction.atomic():
                old_email = user.email
                user.email = user.pending_email
                user.pending_email = None
                user.save(update_fields=["email", "pending_email"])

            send_email_task.delay(
                purpose=EmailPurpose.EMAIL_CHANGED_NOTICE.name,
                context=generate_uid_and_token(user),
                to=old_email,
            )
            send_email_task.delay(
                purpose=EmailPurpose.EMAIL_CHANGED.name,
                context={"email": user.email},
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
        if user:  # pragma: no branch
            context = {}

            if purpose == VerificationPurpose.RESET_PASSWORD:
                email_purpose = EmailPurpose.RESET_PASSWORD.name
            elif purpose == VerificationPurpose.CHANGE_EMAIL:
                email_purpose = EmailPurpose.CHANGE_EMAIL_NOTICE.name
                context = {"pending_email": user.pending_email}

                send_email_task.delay(
                    purpose=EmailPurpose.CHANGE_EMAIL.name,
                    context=context,
                    to=user.pending_email,
                )
            else:
                email_purpose = EmailPurpose.ACCOUNT_ACTIVATION.name

            send_email_task.delay(
                purpose=email_purpose,
                context=context,
                to=user.email,
            )

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
        user.save(update_fields=["pending_email"])

        send_email_task.delay(
            purpose=EmailPurpose.CHANGE_EMAIL_NOTICE.name,
            context={"pending_email": user.pending_email},
            to=user.email,
        )
        send_email_task.delay(
            purpose=EmailPurpose.CHANGE_EMAIL.name,
            context={"pending_email": user.pending_email},
            to=user.pending_email,
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
        if user:  # pragma: no branch
            send_email_task.delay(
                purpose=EmailPurpose.RESET_PASSWORD.name, to=user.email
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
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])

        revoke_all_user_sessions(user)
        send_email_task.delay(
            purpose=EmailPurpose.PASSWORD_CHANGED.name,
            context=generate_uid_and_token(user),
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

        send_email_task.delay(
            purpose=EmailPurpose.ACCOUNT_LOCKDOWN.name,
            context=generate_uid_and_token(user),
            to=user.email,
        )

        return Response(status=status.HTTP_200_OK)

    @extend_schema(
        summary="Delete user's account",
        tags=["Users"],
        request=UserDeleteSerializer,
    )
    def destroy(self, request, *args, **kwargs):
        """
        Schedule permanent account deletion in 24 hours.

        User can cancel it by logging in to their account.
        """
        user: User = request.user
        serializer = self.get_serializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)

        user.deletion_scheduled_at = timezone.now() + timezone.timedelta(hours=24)
        user.save(update_fields=["deletion_scheduled_at"])

        revoke_all_user_sessions(user)

        send_email_task.delay(
            purpose=EmailPurpose.ACCOUNT_DELETION.name,
            context={
                **generate_uid_and_token(user),
                "deletion_scheduled_at": user.deletion_scheduled_at,
            },
            to=user.email,
        )

        return Response(status=status.HTTP_200_OK)
