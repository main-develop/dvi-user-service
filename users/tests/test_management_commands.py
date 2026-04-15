from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
from factories import UserFactory

User = get_user_model()

PAST = timezone.now() - timezone.timedelta(hours=25)
FUTURE = timezone.now() + timezone.timedelta(days=1)


@pytest.mark.django_db
def test_delete_scheduled_users_deletes_due_users():
    due = UserFactory(deletion_scheduled_at=PAST)
    future = UserFactory(deletion_scheduled_at=FUTURE)
    active = UserFactory(deletion_scheduled_at=None)

    call_command("delete_scheduled_users", dry_run=False)

    assert not User.objects.filter(pk=due.pk).exists()
    assert User.objects.filter(pk=future.pk).exists()
    assert User.objects.filter(pk=active.pk).exists()


@pytest.mark.django_db
def test_delete_scheduled_users_sends_email():
    due = UserFactory(deletion_scheduled_at=PAST)

    with patch(
        "users.management.commands.delete_scheduled_users.send_email"
    ) as mock_send:
        call_command("delete_scheduled_users", dry_run=False)

        mock_send.assert_called_once()

        assert mock_send.call_args.kwargs["to"] == due.email


@pytest.mark.django_db
def test_delete_scheduled_users_dry_run_does_not_delete():
    due = UserFactory(deletion_scheduled_at=PAST)

    call_command("delete_scheduled_users", dry_run=True)

    assert User.objects.filter(pk=due.pk).exists()


@pytest.mark.django_db
def test_delete_scheduled_users_no_due_users():
    # should complete cleanly with an empty table
    call_command("delete_scheduled_users", dry_run=False)


@pytest.mark.django_db
def test_delete_scheduled_users_revokes_sessions():
    due = UserFactory(deletion_scheduled_at=PAST)
    captured_pks = []

    def capture_user(user):
        captured_pks.append(user.pk)

    with patch(
        "users.management.commands.delete_scheduled_users.revoke_all_user_sessions",
        side_effect=capture_user,
    ):
        call_command("delete_scheduled_users", dry_run=False)

    assert captured_pks == [due.pk]
