from enum import Enum

from django.contrib.auth.tokens import default_token_generator
from django.http import HttpRequest
from djoser import utils
from djoser.email import (
    BaseDjoserEmail,
)

from users.models import User
from users.services.otp import generate_and_set_otp

DATETIME_FORMAT = "%B %d, %Y at %H:%M UTC"


class AccountSecurityLockdownMixin:
    """
    Add a secure account lockdown URL to the email context.

    This mixin is intended for use in emails related to sensitive account actions.
    Generates a URL pointing to a lockdown endpoint that requires both the
    `uid` and `token` to proceed.
    """

    def get_context_data(self):
        context = super().get_context_data()
        context["account_security_lockdown_url"] = (
            f"account-security/lockdown/{context['uid']}/{context['token']}"
        )

        return context


class UidAndTokenMixin:
    """
    Add `uid` and `token` to email context data.

    Assumes user is available in the context from the base class.
    """

    def get_context_data(self):
        context = super().get_context_data()
        user: User = context.get("user")

        if user:
            context["uid"] = utils.encode_uid(user.pk)
            context["token"] = default_token_generator.make_token(user)

        return context


class AccountActivationEmail(BaseDjoserEmail):
    """Sent when a user needs to activate their account."""

    template_name = "emails/account_activation.html"


class AccountActivatedEmail(BaseDjoserEmail):
    """Sent after a user successfully activates their account."""

    template_name = "emails/account_activated.html"


class AccountDeletionEmail(
    AccountSecurityLockdownMixin, UidAndTokenMixin, BaseDjoserEmail
):
    """
    Sent after user's account has been scheduled for deletion.

    Includes a link to cancel the deletion and a security lockdown URL
    for additional protection.
    """

    template_name = "emails/account_deletion.html"

    def get_context_data(self):
        context = super().get_context_data()
        context["cancel_deletion_url"] = (
            f"cancel-deletion/{context['uid']}/{context['token']}"
        )

        deletion_scheduled_at = context["user"].deletion_scheduled_at
        context["account_deletion_datetime"] = deletion_scheduled_at.strftime(
            DATETIME_FORMAT
        )
        context["account_deletion_date"] = deletion_scheduled_at.strftime("%b %d, %Y")

        return context


class AccountDeletedEmail(BaseDjoserEmail):
    """Sent after user's account has been successfully deleted."""

    template_name = "emails/account_deleted.html"

    def get_context_data(self):
        context = super().get_context_data()
        context["deletion_datetime"].strftime(DATETIME_FORMAT)

        return context


class AccountDeletionCanceledEmail(BaseDjoserEmail):
    """Sent after user's scheduled account deletion has been canceled."""

    template_name = "emails/account_deletion_canceled.html"


class AccountLockdownEmail(BaseDjoserEmail):
    """
    Sent after user's account has been locked down.

    Contains a password reset link if user haven't reset their password yet.
    """

    template_name = "emails/account_lockdown.html"

    def get_context_data(self):
        context = super().get_context_data()
        context["password_reset_url"] = (
            f"password/reset/{context['uid']}/{context['token']}"
        )

        return context


class ChangeEmailEmail(BaseDjoserEmail):
    """
    Sent to the new address when a user requests to change their account email.
    """

    template_name = "emails/change_email.html"


class ChangeEmailNoticeEmail(
    AccountSecurityLockdownMixin, UidAndTokenMixin, BaseDjoserEmail
):
    """
    Sent to the current email address when someone requests to
    change the account's email.

    Notifies the legitimate account owner that an email change has
    been requested and allows immediate action if this was an unauthorized
    attempt (account takeover).
    """

    template_name = "emails/change_email_notice.html"


class EmailChangedEmail(BaseDjoserEmail):
    """
    Sent to the user's new email address after they have
    successfully changed their account email.
    """

    template_name = "emails/email_changed.html"


class EmailChangedNoticeEmail(
    AccountSecurityLockdownMixin, UidAndTokenMixin, BaseDjoserEmail
):
    """
    Sent to the old email address after the account's email was changed.

    Gives the legitimate owner an immediate way to revoke sessions,
    reset password, etc., to protect their account in case of a breach.
    """

    template_name = "emails/email_changed_notice.html"


class ResetPasswordEmail(BaseDjoserEmail):
    """
    Sent when a user requests a password reset.
    """

    template_name = "emails/reset_password.html"


class PasswordChangedEmail(
    AccountSecurityLockdownMixin, UidAndTokenMixin, BaseDjoserEmail
):
    """Sent when the user's password has been changed."""

    template_name = "emails/password_changed.html"


class EmailPurpose(Enum):
    ACCOUNT_ACTIVATION = AccountActivationEmail
    ACCOUNT_ACTIVATED = AccountActivatedEmail
    ACCOUNT_DELETION = AccountDeletionEmail
    ACCOUNT_DELETION_CANCELED = AccountDeletionCanceledEmail
    ACCOUNT_DELETED = AccountDeletedEmail
    ACCOUNT_LOCKDOWN = AccountLockdownEmail
    CHANGE_EMAIL = ChangeEmailEmail
    CHANGE_EMAIL_NOTICE = ChangeEmailNoticeEmail
    EMAIL_CHANGED = EmailChangedEmail
    EMAIL_CHANGED_NOTICE = EmailChangedNoticeEmail
    RESET_PASSWORD = ResetPasswordEmail
    PASSWORD_CHANGED = PasswordChangedEmail


def send_email(
    purpose: EmailPurpose, request: HttpRequest, to: str, context: dict = {}
) -> None:
    """
    Send an email for the specified purpose.

    If the purpose requires an OTP (ACCOUNT_ACTIVATION, RESET_PASSWORD,
    or CHANGE_EMAIL), generates one via `generate_and_set_otp` and adds
    it to the context.
    """
    include_otp = purpose in {
        EmailPurpose.ACCOUNT_ACTIVATION,
        EmailPurpose.RESET_PASSWORD,
        EmailPurpose.CHANGE_EMAIL,
    }
    if include_otp:
        context["otp"] = generate_and_set_otp(email=to)

    email = purpose.value
    email(request=request, context=context).send(to=[to])
