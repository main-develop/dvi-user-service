from django.contrib.auth.tokens import default_token_generator
from djoser import utils
from djoser.email import BaseDjoserEmail


class ChangeEmailConfirmationEmail(BaseDjoserEmail):
    """
    Email sent when a user requests to change their account email address.

    This email contains a confirmation link with a UID and token that the user
    must click to activate the new email address.
    """

    template_name = "email/change_email_confirmation.html"

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

    template_name = "email/email_changed.html"
