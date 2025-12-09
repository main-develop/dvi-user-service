from django.contrib.auth.tokens import default_token_generator
from djoser import utils
from djoser.email import (
    BaseDjoserEmail,
    ActivationEmail,
    ConfirmationEmail,
    PasswordResetEmail,
    PasswordChangedConfirmationEmail,
)


class CustomActivationEmail(ActivationEmail):
    template_name = "emails/email_verification.html"


class CustomConfirmationEmail(ConfirmationEmail):
    template_name = "emails/email_verified.html"


class AccountDeletionAlertEmail(BaseDjoserEmail):
    template_name = "emails/account_deletion_alert.html"

    def get_context_data(self):
        context = super().get_context_data()
        user = context.get("user")

        context["uid"] = utils.encode_uid(user.pk)
        context["token"] = default_token_generator.make_token(user)
        context["cancel_deletion_url"] = "cancel-deletion/{uid}/{token}".format(**context)
        context["account_security_lockdown_url"] = "account-security/lockdown/{uid}/{token}".format(**context)

        deletion_scheduled_at = user.deletion_scheduled_at

        context["account_deletion_datetime"] = deletion_scheduled_at.strftime("%B %d, %Y at %H:%M UTC")
        context["account_deletion_date"] = deletion_scheduled_at.strftime("%b %d, %Y")

        return context


class AccountDeletionSuccessEmail(BaseDjoserEmail):
    template_name = "emails/account_deletion_success.html"


class AccountDeletionCanceledEmail(BaseDjoserEmail):
    template_name = "emails/account_deletion_canceled.html"


class ChangeEmailAlertEmail(BaseDjoserEmail):
    """
    Security alert sent to the old email address after the account's
    email was changed.

    This email gives the legitimate owner an immediate way to revoke sessions,
    reset password, etc., to protect their account in case of a breach.
    """
    
    template_name = "emails/change_email_alert.html"

    def get_context_data(self):
        context = super().get_context_data()
        user = context.get("user")

        context["uid"] = utils.encode_uid(user.pk)
        context["token"] = default_token_generator.make_token(user)
        context["account_security_lockdown_url"] = "account-security/lockdown/{uid}/{token}".format(**context)

        return context


class ChangeEmailNoticeEmail(BaseDjoserEmail):
    """
    Security notice sent to the current email address when someone
    requests to change the account's email.

    This email notifies the legitimate account owner that an email change has been requested
    and allows immediate action if this was an unauthorized attempt (account takeover).
    """

    template_name = "emails/change_email_notice.html"

    def get_context_data(self):
        context = super().get_context_data()
        user = context.get("user")

        context["uid"] = utils.encode_uid(user.pk)
        context["token"] = default_token_generator.make_token(user)
        context["account_security_lockdown_url"] = "account-security/lockdown/{uid}/{token}".format(**context)

        return context


class ChangeEmailConfirmEmail(BaseDjoserEmail):
    """
    Email sent to the new address when a user requests to change their account email.

    This email contains a confirmation link with a UID and token that the user
    must click to activate the new email address.
    """

    template_name = "emails/change_email_confirm.html"

    def get_context_data(self):
        context = super().get_context_data()
        user = context.get("user")

        context["uid"] = utils.encode_uid(user.pk)
        context["token"] = default_token_generator.make_token(user)
        context["url"] = "#/{uid}/{token}".format(**context)

        return context


class ChangeEmailSuccessEmail(BaseDjoserEmail):
    """
    Notification email sent to the user's new email address after they have
    successfully changed their account email.
    """

    template_name = "emails/change_email_success.html"


class ResetPasswordConfirmEmail(PasswordResetEmail):
    template_name = "emails/reset_password_confirm.html"


class ResetPasswordSuccessEmail(PasswordChangedConfirmationEmail):
    template_name = "emails/reset_password_success.html"

    def get_context_data(self):
        context = super().get_context_data()
        user = context.get("user")

        context["uid"] = utils.encode_uid(user.pk)
        context["token"] = default_token_generator.make_token(user)
        context["url"] = "#/{uid}/{token}".format(**context)

        return context


class AccountLockdownNoticeEmail(BaseDjoserEmail):
    """
    Notification email sent to the user after their account has been locked down.
    
    This email contains a password reset link if user haven't reset their password yet.
    """
    template_name = "emails/account_security_lockdown_notice.html"
