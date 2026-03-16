from django.urls import path

from users.views.user import CustomUserViewSet

urlpatterns = [
    path(
        "me/",
        CustomUserViewSet.as_view({"get": "me", "delete": "destroy"}),
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
    path(
        "account-security/lockdown/",
        CustomUserViewSet.as_view({"post": "lockdown_account"}),
        name="users_account_security_lockdown",
    ),
    path(
        "account-security/cancel-deletion/",
        CustomUserViewSet.as_view({"post": "cancel_deletion"}),
        name="users_account_security_cancel_deletion",
    ),
]
