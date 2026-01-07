from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from users.emails import AccountDeletionSuccessEmail
from users.utils import revoke_all_user_sessions

User = get_user_model()


class Command(BaseCommand):
    """
    Permanently delete user accounts that have been scheduled for deletion 24 hours ago.

    Designed to be run frequently (every 5 minutes via cron/systemd/timer) to enforce
    the 24-hour grace period for account deletion requests. This command is safe to run
    very frequently because the query is index-bound and extremely cheap.
    """

    help = "Permanently delete users that were scheduled for deletion 24 hours ago."

    def handle(self, *args, **options):
        users_to_delete = User.objects.filter(
            deletion_scheduled_at__lte=timezone.now(),
            deletion_scheduled_at__isnull=False,
        ).only("id", "email")

        if not users_to_delete.exists():
            self.stdout.write(msg="No users to delete.")
            return

        deleted_count = 0
        for user in users_to_delete.iterator():
            revoke_all_user_sessions(user)

            AccountDeletionSuccessEmail(
                context={"deletion_datetime": timezone.now()}
            ).send(to=[user.email])

            user.delete()
            deleted_count += 1

        self.stdout.write(
            style_func=self.style.SUCCESS(f"Deleted {deleted_count} user(s).")
        )
