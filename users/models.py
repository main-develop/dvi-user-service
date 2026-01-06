import uuid

from django.contrib.auth.models import AbstractUser
from django.db.models import DateTimeField, EmailField, UUIDField


class User(AbstractUser):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = None
    last_name = None
    email = EmailField(unique=True, blank=False, null=False)
    pending_email = EmailField(blank=True, null=True)
    deletion_scheduled_at = DateTimeField(
        blank=True,
        null=True,
        db_index=True,
        help_text="If set, user will be deleted after 24 hours at the specified timestamp.",
    )
