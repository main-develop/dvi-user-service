import logging

from django.contrib.sessions.models import Session
from django.utils import timezone

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
                "Failed to decode/delete session for user %s."
                "Attempting force delete...",
                user.pk,
            )
            session.delete()
            continue
