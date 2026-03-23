import os

ENVIRONMENT = os.environ.get("DJANGO_ENVIRONMENT", "local").lower()

if ENVIRONMENT == "local":
    from .local import *
elif ENVIRONMENT == "production":
    from .production import *
else:
    raise ValueError(
        f"Unknown DJANGO_ENVIRONMENT: {ENVIRONMENT}. Use 'local' or 'production'."
    )
