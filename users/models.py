import uuid

from django.contrib.auth.models import AbstractUser
from django.db.models import DateTimeField, EmailField, UUIDField, CharField
from django.core.validators import MinLengthValidator


class User(AbstractUser):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = None
    last_name = None
    username = CharField(max_length=25, validators=[MinLengthValidator(3)], unique=True, blank=False, null=False)
    email = EmailField(max_length=254, unique=True, blank=False, null=False)
    pending_email = EmailField(max_length=254, blank=True, null=True)
    deletion_scheduled_at = DateTimeField(
        blank=True,
        null=True,
        db_index=True,
        help_text=(
            "If set, user will be deleted after 24 hours at the specified timestamp."
        ),
    )
