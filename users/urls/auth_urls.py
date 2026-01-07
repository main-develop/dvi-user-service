from django.urls import path

from users.views.auth import LoginView, LogoutView
from users.views.user import CustomUserViewSet

urlpatterns = [
    path(
        "register/", CustomUserViewSet.as_view({"post": "create"}), name="auth_register"
    ),
    path(
        "register/verify/",
        CustomUserViewSet.as_view({"post": "activation"}),
        name="auth_register_verify",
    ),
    path(
        "register/resend-verification/",
        CustomUserViewSet.as_view({"post": "resend_activation"}),
        name="auth_register_resend_verification",
    ),
    path("login/", LoginView.as_view(), name="auth_login"),
    path("logout/", LogoutView.as_view(), name="auth_logout"),
]
