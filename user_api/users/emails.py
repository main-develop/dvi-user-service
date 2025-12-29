from django.contrib.auth.tokens import default_token_generator
from djoser import utils
from djoser.email import (
    ActivationEmail,
    BaseDjoserEmail,
    ConfirmationEmail,
    PasswordChangedConfirmationEmail,
    PasswordResetEmail,
)
from users.models import User

DATETIME_FORMAT = "%B %d, %Y at %H:%M UTC"


class AccountSecurityLockdownMixin:
    """
    Adds a secure account lockdown URL to the email context.

    This mixin is intended for use in emails related to sensitive account actions.
    It generates a URL pointing to a lockdown endpoint that requires both the ``uid`` and a
    ``token`` to proceed.
    """

    def get_context_data(self):
        context = super().get_context_data()
        context["account_security_lockdown_url"] = (
            f"account-security/lockdown/{context["uid"]}/{context["token"]}"
        )

        return context


class UidAndTokenMixin:
    """
    This mixin is intended to add ``uid`` and ``token`` to email context data.
    Assumes ``user`` is available in the context from the base class.
    """

    def get_context_data(self):
        context = super().get_context_data()
        user: User = context.get("user")

        if user:
            context["uid"] = utils.encode_uid(user.pk)
            context["token"] = default_token_generator.make_token(user)

        return context


class CustomActivationEmail(ActivationEmail):
    """
    Activation email sent when a user needs to activate their account.
    """

    template_name = "emails/email_verification.html"


class CustomConfirmationEmail(ConfirmationEmail):
    """
    Confirmation email sent after a user successfully activates their account.
    """

    template_name = "emails/email_verified.html"


class AccountDeletionAlertEmail(
    BaseDjoserEmail, UidAndTokenMixin, AccountSecurityLockdownMixin
):
    """
    Email alerting the user that their account is scheduled for deletion.

    Sent when a deletion request is initiated. The email includes a link to
    cancel the deletion and a security lockdown URL for additional protection.
    """

    template_name = "emails/account_deletion_alert.html"

    def get_context_data(self):
        context = super().get_context_data()
        context["cancel_deletion_url"] = (
            f"cancel-deletion/{context["uid"]}/{context["token"]}"
        )

        deletion_scheduled_at = context["user"].deletion_scheduled_at
        context["account_deletion_datetime"] = deletion_scheduled_at.strftime(
            DATETIME_FORMAT
        )
        context["account_deletion_date"] = deletion_scheduled_at.strftime("%b %d, %Y")

        return context


class AccountDeletionSuccessEmail(BaseDjoserEmail):
    """
    Notification email sent after user's account has been successfully deleted.
    """

    template_name = "emails/account_deletion_success.html"

    def get_context_data(self):
        context = super().get_context_data()
        context["deletion_datetime"].strftime(DATETIME_FORMAT)

        return context


class AccountDeletionCanceledEmail(BaseDjoserEmail):
    """
    Notification email sent after user's scheduled account deletion has been canceled.

    Sent when the user clicks the cancellation link in the deletion alert email.
    """

    template_name = "emails/account_deletion_canceled.html"


class AccountLockdownNoticeEmail(BaseDjoserEmail):
    """
    Notification email sent to the user after their account has been locked down.
    This email contains a password reset link if user haven't reset their password yet.
    """

    template_name = "emails/account_security_lockdown_notice.html"


class ChangeEmailAlertEmail(
    BaseDjoserEmail, UidAndTokenMixin, AccountSecurityLockdownMixin
):
    """
    Security alert sent to the old email address after the account's
    email was changed.

    This email gives the legitimate owner an immediate way to revoke sessions,
    reset password, etc., to protect their account in case of a breach.
    """

    template_name = "emails/change_email_alert.html"


class ChangeEmailNoticeEmail(
    BaseDjoserEmail, UidAndTokenMixin, AccountSecurityLockdownMixin
):
    """
    Security notice sent to the current email address when someone
    requests to change the account's email.

    This email notifies the legitimate account owner that an email change has been requested
    and allows immediate action if this was an unauthorized attempt (account takeover).
    """

    template_name = "emails/change_email_notice.html"


class ChangeEmailConfirmEmail(BaseDjoserEmail, UidAndTokenMixin):
    """
    Email sent to the new address when a user requests to change their account email.

    This email contains a confirmation link with a UID and token that the user
    must click to activate the new email address.
    """

    template_name = "emails/change_email_confirm.html"

    def get_context_data(self):
        context = super().get_context_data()
        context["confirm_email_url"] = (
            f"confirm-email/{context["uid"]}/{context["token"]}"
        )

        return context


class ChangeEmailSuccessEmail(BaseDjoserEmail):
    """
    Notification email sent to the user's new email address after they have
    successfully changed their account email.
    """

    template_name = "emails/change_email_success.html"


class ResetPasswordConfirmEmail(PasswordResetEmail):
    """
    Notification email containing the password reset link.

    Sent when user requests a password reset.
    """

    template_name = "emails/reset_password_confirm.html"


class ResetPasswordSuccessEmail(
    PasswordChangedConfirmationEmail, UidAndTokenMixin, AccountSecurityLockdownMixin
):
    """
    Notification email confirming that the user's password has been successfully changed.
    """

    template_name = "emails/reset_password_success.html"
