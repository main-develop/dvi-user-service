from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from users.emails import EmailPurpose, send_email
from users.utils import revoke_all_user_sessions

User = get_user_model()


def format_log_message(message: str, type: str = "INFO"):
    return f"[{timezone.now().strftime('%Y-%m-%d %H:%M:%S %z')}] [{type}] {message}"


class Command(BaseCommand):
    """
    Permanently delete users that were scheduled for deletion 24 hours ago.

    Can be run frequently via cron/systemd/service.
    """

    help = "Permanently delete users that were scheduled for deletion 24 hours ago."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Number of users to process in one batch (default: 100).",
        )

    def handle(self, *args, **options):
        self.stdout.write(
            format_log_message("Started delete_scheduled_users job"), self.style.NOTICE
        )

        dry_run = options["dry_run"]
        batch_size = options["batch_size"]
        cutoff_time = timezone.now() - timezone.timedelta(hours=24)

        users_to_delete = User.objects.filter(
            deletion_scheduled_at__lte=cutoff_time,
            deletion_scheduled_at__isnull=False,
        ).only("id", "email")

        count = users_to_delete.count()
        if count == 0:
            self.stdout.write(
                format_log_message("No users scheduled for deletion"), self.style.NOTICE
            )
            self.stdout.write(
                format_log_message("Finished delete_scheduled_users job"),
                self.style.NOTICE,
            )
            return

        self.stdout.write(
            format_log_message(
                f"Found {count} user(s) scheduled for permanent deletion"
            ),
            self.style.SUCCESS,
        )

        if dry_run:
            self.stdout.write(
                format_log_message(
                    "DRY RUN MODE: No actual deletions will occur", "WARN"
                ),
                self.style.WARNING,
            )

            for user in users_to_delete.iterator():
                self.stdout.write(
                    format_log_message(f"Would delete user with ID: {user.id}"),
                    self.style.SUCCESS,
                )

            self.stdout.write(
                format_log_message("Finished delete_scheduled_users job"),
                self.style.NOTICE,
            )
            return

        deleted_count = 0

        for user in users_to_delete.iterator(chunk_size=batch_size):
            user_id, email = user.id, user.email

            try:
                with transaction.atomic():
                    revoke_all_user_sessions(user)
                    user.delete()

                deleted_count += 1

                self.stdout.write(
                    format_log_message(f"Deleted user with ID: {user_id}"),
                    self.style.SUCCESS,
                )

                send_email(
                    purpose=EmailPurpose.ACCOUNT_DELETED,
                    context={"deletion_datetime": timezone.now()},
                    to=email,
                )

            except Exception as e:
                self.stdout.write(
                    format_log_message(
                        f"Failed to delete user with ID: {user_id}\n{e}", "ERROR"
                    ),
                    self.style.ERROR,
                )

        self.stdout.write(
            format_log_message(f"Successfully deleted {deleted_count} user(s)"),
            self.style.SUCCESS,
        )
        self.stdout.write(
            format_log_message("Finished delete_scheduled_users job"), self.style.NOTICE
        )
