from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from drf_spectacular.views import SpectacularSwaggerView


@method_decorator(login_required(login_url="/admin/login/"), name="get")
class CustomSwaggerView(SpectacularSwaggerView):
    """
    Custom Swagger view that requires authentication.

    This class extends the base SpectacularSwaggerView to enforce login
    requirements on the ``GET`` method, preventing unauthenticated access to
    the Swagger UI documentation. Users attempting to access the view
    without being logged in will be redirected to the Django admin login page.
    """
