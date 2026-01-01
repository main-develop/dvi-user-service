from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView

from users.views.swagger import CustomSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        CustomSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/v1/", include("users.urls")),
]
