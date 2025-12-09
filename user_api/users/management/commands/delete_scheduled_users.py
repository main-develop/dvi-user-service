from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand
from django.utils import timezone
from users.emails import AccountDeletionSuccessEmail

User = get_user_model()


class Command(BaseCommand):
    """
    Permanently delete user accounts that have been scheduled for deletion 24 hours ago.

    This management command is designed to be run frequently
    (every 5 minutes via cron/systemd/timer) to enforce the 24-hour grace period for account
    deletion requests. This command is safe to run very frequently because the query is
    index-bound and extremely cheap.
    """

    help = "Permanently delete users that were scheduled for deletion 24 hours ago."

    def handle(self, *args, **options):
        users_to_delete = User.objects.filter(
            deletion_scheduled_at__lte=timezone.now(),
            deletion_scheduled_at__isnull=False,
        ).only("id", "email")

        if not users_to_delete.exists():
            self.stdout.write("No users to delete.")
            return

        deleted_count = 0
        for user in users_to_delete.iterator():
            for session in Session.objects.filter(expire_date__gte=timezone.now()):
                try:
                    if str(user.pk) == session.get_decoded().get("_auth_user_id"):
                        session.delete()
                except Exception:
                    print("Failed to decode/delete session during lockdown.")
                    continue

            AccountDeletionSuccessEmail(
                context={
                    "deletion_datetime": timezone.now().strftime(
                        "%B %d, %Y at %H:%M UTC"
                    )
                }
            ).send([user.email])

            user.delete()
            deleted_count += 1

        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted_count} user(s)."))
