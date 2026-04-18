import logging

from django.contrib.auth.tokens import default_token_generator
from django.contrib.sessions.models import Session
from django.utils import timezone
from djoser import utils

from users.models import User

logger = logging.getLogger(__name__)


def revoke_all_user_sessions(user: User):
    """Revoke all active sessions for the given user."""
    for session in Session.objects.filter(expire_date__gte=timezone.now()):
        try:
            if str(user.pk) == session.get_decoded().get("_auth_user_id"):
                session.delete()
        except Exception:
            logger.exception(
                "Failed to decode session %s for user %s, skipping.",
                session.session_key,
                user.pk,
            )
            continue


def generate_uid_and_token(user: User) -> dict[str, str] | {}:
    """Generate `uid` and `token` based on the given user for the email context."""
    context = {}

    if user:
        context["uid"] = utils.encode_uid(user.pk)
        context["token"] = default_token_generator.make_token(user)

    return context
