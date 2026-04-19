from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
from factories import UserFactory

from users.utils import revoke_all_user_sessions

User = get_user_model()


@pytest.fixture
def scheduled_at_past():
    return timezone.now() - timezone.timedelta(hours=25)


@pytest.fixture
def scheduled_at_future():
    return timezone.now() + timezone.timedelta(days=1)


@pytest.mark.django_db
def test_delete_scheduled_users_deletes_due_users(
    scheduled_at_past, scheduled_at_future
):
    due = UserFactory(deletion_scheduled_at=scheduled_at_past)
    future = UserFactory(deletion_scheduled_at=scheduled_at_future)
    active = UserFactory(deletion_scheduled_at=None)

    call_command("delete_scheduled_users", dry_run=False)

    assert not User.objects.filter(pk=due.pk).exists()
    assert User.objects.filter(pk=future.pk).exists()
    assert User.objects.filter(pk=active.pk).exists()


@pytest.mark.django_db
def test_delete_scheduled_users_sends_email(scheduled_at_past):
    due = UserFactory(deletion_scheduled_at=scheduled_at_past)

    with patch(
        "users.management.commands.delete_scheduled_users.send_email_task"
    ) as mock_send:
        call_command("delete_scheduled_users", dry_run=False)

        mock_send.delay.assert_called_once()

        assert mock_send.delay.call_args.kwargs["to"] == due.email


@pytest.mark.django_db
def test_delete_scheduled_users_dry_run_does_not_delete(scheduled_at_past):
    due = UserFactory(deletion_scheduled_at=scheduled_at_past)

    call_command("delete_scheduled_users", dry_run=True)

    assert User.objects.filter(pk=due.pk).exists()


@pytest.mark.django_db
def test_delete_scheduled_users_no_due_users():
    # should complete cleanly with an empty table
    call_command("delete_scheduled_users", dry_run=False)


@pytest.mark.django_db
def test_delete_scheduled_users_revokes_sessions(scheduled_at_past):
    due = UserFactory(deletion_scheduled_at=scheduled_at_past)
    captured_pks = []

    def capture_user(user):
        captured_pks.append(user.pk)

    with patch(
        "users.management.commands.delete_scheduled_users.revoke_all_user_sessions",
        side_effect=capture_user,
    ):
        call_command("delete_scheduled_users", dry_run=False)

    assert captured_pks == [due.pk]


@pytest.mark.django_db
def test_delete_scheduled_users_continues_on_single_failure(scheduled_at_past):
    failing = UserFactory(deletion_scheduled_at=scheduled_at_past)
    succeeding = UserFactory(deletion_scheduled_at=scheduled_at_past)

    def revoke_side_effect(user):
        if user.pk == failing.pk:
            raise Exception("Simulated failure")
        return revoke_all_user_sessions(user)

    with patch(
        "users.management.commands.delete_scheduled_users.revoke_all_user_sessions",
        side_effect=revoke_side_effect,
    ):
        call_command("delete_scheduled_users", dry_run=False)

    assert User.objects.filter(pk=failing.pk).exists()
    assert not User.objects.filter(pk=succeeding.pk).exists()
