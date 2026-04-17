import logging
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session

from users.utils import revoke_all_user_sessions
from factories import UserFactory


@pytest.mark.django_db
def test_revoke_all_user_sessions(user):
    session_store = SessionStore()
    session_store["_auth_user_id"] = str(user.pk)
    session_store.save()
    session_key = session_store.session_key

    revoke_all_user_sessions(user)

    assert not Session.objects.filter(session_key=session_key).exists()


@pytest.mark.django_db
def test_revoke_all_user_sessions_does_not_affect_other_users(user):
    other_user = UserFactory()
    session_store = SessionStore()
    session_store["_auth_user_id"] = str(other_user.pk)
    session_store.save()
    session_key = session_store.session_key

    revoke_all_user_sessions(user)

    assert Session.objects.filter(session_key=session_key).exists()


@pytest.mark.django_db
def test_revoke_all_user_sessions_force_delete_on_error(user, caplog):
    bad_session = MagicMock(spec=Session)
    bad_session.get_decoded.side_effect = Exception("Corrupt session")

    with patch("users.utils.Session.objects.filter") as mock_filter:
        mock_filter.return_value = [bad_session]

        with caplog.at_level(logging.ERROR, logger="users.utils"):
            revoke_all_user_sessions(user)

    assert len(caplog.records) == 1
    assert "Failed to decode session" in caplog.records[0].message
    bad_session.delete.assert_not_called()
