import uuid

from django.contrib.auth.models import AbstractUser
from django.core.validators import MinLengthValidator
from django.db.models import CharField, DateTimeField, EmailField, UUIDField


class User(AbstractUser):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = None
    last_name = None
    username = CharField(
        max_length=25,
        validators=[MinLengthValidator(3)],
        unique=True,
        blank=False,
        null=False,
        error_messages={"unique": "This username is already taken"},
    )
    email = EmailField(
        max_length=254,
        unique=True,
        blank=False,
        null=False,
        error_messages={"unique": "This email is already taken"},
    )
    pending_email = EmailField(max_length=254, blank=True, null=True)
    deletion_scheduled_at = DateTimeField(
        blank=True,
        null=True,
        db_index=True,
        help_text=(
            "If set, user will be deleted after 24 hours at the specified timestamp."
        ),
    )
