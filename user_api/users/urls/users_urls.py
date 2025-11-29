from django.urls import path
from users.views import CustomUserViewSet

urlpatterns = [
    path(
        "me/",
        CustomUserViewSet.as_view({"get": "retrieve", "delete": "destroy"}),
        name="users_me",
    ),
    path(
        "me/username/",
        CustomUserViewSet.as_view({"post": "set_username"}),
        name="users_me_username",
    ),
    path(
        "me/password/",
        CustomUserViewSet.as_view({"post": "set_password"}),
        name="users_me_password",
    ),
    path(
        "me/email/",
        CustomUserViewSet.as_view({"post": "change_email"}),
        name="users_me_email",
    ),
    path(
        "me/email/confirm/",
        CustomUserViewSet.as_view({"post": "change_email_confirm"}),
        name="users_me_email_confirm",
    ),
    path(
        "password/reset/",
        CustomUserViewSet.as_view({"post": "reset_password"}),
        name="users_password_reset",
    ),
    path(
        "password/reset/confirm/",
        CustomUserViewSet.as_view({"post": "reset_password_confirm"}),
        name="users_password_reset_confirm",
    ),
]
