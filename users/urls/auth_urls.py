from django.urls import path

from users.views.auth import LoginView, LogoutView
from users.views.user import CustomUserViewSet

urlpatterns = [
    path(
        "register/", CustomUserViewSet.as_view({"post": "create"}), name="auth_register"
    ),
    path(
        "verify/",
        CustomUserViewSet.as_view({"post": "verify"}),
        name="auth_verify",
    ),
    path(
        "resend-verification/",
        CustomUserViewSet.as_view({"post": "resend_verification_email"}),
        name="auth_resend_verification_email",
    ),
    path("login/", LoginView.as_view(), name="auth_login"),
    path("logout/", LogoutView.as_view(), name="auth_logout"),
]
