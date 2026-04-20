from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
from factories import UserFactory

SCHEDULED_AT_PAST = timezone.now() - timezone.timedelta(hours=25)
SCHEDULED_AT_FUTURE = timezone.now() + timezone.timedelta(days=1)

User = get_user_model()


@pytest.mark.django_db
def test_delete_scheduled_users_deletes_due_users():
    due = UserFactory(deletion_scheduled_at=SCHEDULED_AT_PAST)
    future = UserFactory(deletion_scheduled_at=SCHEDULED_AT_FUTURE)
    active = UserFactory(deletion_scheduled_at=None)

    call_command("delete_scheduled_users", dry_run=False)

    assert not User.objects.filter(pk=due.pk).exists()
    assert User.objects.filter(pk=future.pk).exists()
    assert User.objects.filter(pk=active.pk).exists()


@pytest.mark.django_db
def test_delete_scheduled_users_sends_email():
    due = UserFactory(deletion_scheduled_at=SCHEDULED_AT_PAST)

    with patch(
        "users.management.commands.delete_scheduled_users.send_email_task"
    ) as mock_send:
        call_command("delete_scheduled_users", dry_run=False)

        mock_send.delay.assert_called_once()

        assert mock_send.delay.call_args.kwargs["to"] == due.email


@pytest.mark.django_db
def test_delete_scheduled_users_dry_run_does_not_delete():
    due = UserFactory(deletion_scheduled_at=SCHEDULED_AT_PAST)

    call_command("delete_scheduled_users", dry_run=True)

    assert User.objects.filter(pk=due.pk).exists()


@pytest.mark.django_db
def test_delete_scheduled_users_no_due_users():
    # should complete cleanly with an empty table
    call_command("delete_scheduled_users", dry_run=False)


@pytest.mark.django_db
def test_delete_scheduled_users_revokes_sessions():
    due = UserFactory(deletion_scheduled_at=SCHEDULED_AT_PAST)
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
def test_delete_scheduled_users_continues_on_single_failure():
    failing = UserFactory(deletion_scheduled_at=SCHEDULED_AT_PAST)
    succeeding = UserFactory(deletion_scheduled_at=SCHEDULED_AT_PAST)

    def revoke_side_effect(user):
        if user.pk == failing.pk:
            raise Exception("Simulated failure")

    with patch(
        "users.management.commands.delete_scheduled_users.revoke_all_user_sessions",
        side_effect=revoke_side_effect,
    ):
        call_command("delete_scheduled_users", dry_run=False)

    assert User.objects.filter(pk=failing.pk).exists()
    assert not User.objects.filter(pk=succeeding.pk).exists()
