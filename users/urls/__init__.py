from django.urls import include, path

urlpatterns = [
    path("auth/", include("users.urls.auth_urls")),
    path("users/", include("users.urls.user_urls")),
]
