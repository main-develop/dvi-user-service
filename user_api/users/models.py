from django.db.models import EmailField, UUIDField
import uuid
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = None
    last_name = None
    email = EmailField(unique=True, blank=False, null=False)
    pending_email = EmailField(blank=True, null=True)
