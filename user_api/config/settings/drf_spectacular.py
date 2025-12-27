import os

from .base import BASE_DIR

with open(
    os.path.join(BASE_DIR.parent, "docs/api_description.md"), encoding="utf-8"
) as file:
    api_description = file.read()

SPECTACULAR_SETTINGS = {
    "TITLE": "DVI User API Specification",
    "DESCRIPTION": api_description,
    "VERSION": None,
    "SERVE_INCLUDE_SCHEMA": False,
    "SERVE_PERMISSIONS": ["rest_framework.permissions.IsAuthenticatedOrReadOnly"],
    "AUTHENTICATION_WHITELIST": [],
    "TAGS": [
        {
            "name": "Auth",
            "description": "Authentication and authorization endpoints",
        },
        {
            "name": "Users",
            "description": "Endpoints for managing and viewing user's profile",
        },
    ],
}
