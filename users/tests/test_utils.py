import pytest
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session

from users.utils import revoke_all_user_sessions


@pytest.mark.django_db
def test_revoke_all_user_sessions(user):
    session_key = "testkey"
    session_store = SessionStore(session_key)
    session_store["_auth_user_id"] = str(user.pk)
    session_store.save()

    revoke_all_user_sessions(user)

    assert not Session.objects.filter(session_key=session_key).exists()
