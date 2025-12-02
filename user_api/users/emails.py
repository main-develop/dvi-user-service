import datetime
from django.utils import timezone
from django.utils.formats import date_format
from django.contrib.auth.tokens import default_token_generator
from djoser import utils
from djoser.email import BaseDjoserEmail, ActivationEmail, ConfirmationEmail


class CustomActivationEmail(ActivationEmail):
    template_name = "emails/activation.html"


class CustomConfirmationEmail(ConfirmationEmail):
    template_name = "emails/confirmation.html"


class AccountDeletionEmail(BaseDjoserEmail):
    template_name = "emails/account_deletion.html"

    def get_context_data(self):
        context = super().get_context_data()
        user = context.get("user")

        context["uid"] = utils.encode_uid(user.pk)
        context["token"] = default_token_generator.make_token(user)
        context["cancel_deletion_url"] = "cancel-deletion/{uid}/{token}".format(**context)

        deletion_at = timezone.now() + timezone.timedelta(hours=24)
        utc = datetime.timezone.utc
        if timezone.is_naive(deletion_at):
            deletion_at = timezone.make_aware(deletion_at, timezone=utc)
        if deletion_at.tzinfo is None:
            deletion_at = deletion_at.replace(tzinfo=utc)

        deletion_utc = deletion_at.astimezone(utc)

        context["account_deletion_datetime_utc"] = deletion_at.strftime("%B %d, %Y at %H:%M UTC")
        context["account_deletion_date"] = deletion_at.strftime("%b %d, %Y")

        return context


class ChangeEmailAlertEmail(BaseDjoserEmail):
    """
    Security alert sent to the current (old) email address when someone
    requests to change the account's email.

    This email notifies the legitimate account owner that an email change has been requested
    and allows immediate action if this was an unauthorized attempt (account takeover).
    """
    
    template_name = "emails/change_email_alert.html"


class ChangeEmailConfirmationEmail(BaseDjoserEmail):
    """
    Email sent to the new address when a user requests to change their account email.

    This email contains a confirmation link with a UID and token that the user
    must click to activate the new email address.
    """

    template_name = "emails/change_email_confirmation.html"

    def get_context_data(self):
        context = super().get_context_data()
        user = context.get("user")

        context["uid"] = utils.encode_uid(user.pk)
        context["token"] = default_token_generator.make_token(user)
        context["url"] = "#/{uid}/{token}".format(**context)

        return context


class EmailChangedEmail(BaseDjoserEmail):
    """
    Notification email sent to the user's new email address after they have
    successfully changed their account email.
    """

    template_name = "emails/email_changed.html"
