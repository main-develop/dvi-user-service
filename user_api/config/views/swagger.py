from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from drf_spectacular.views import SpectacularSwaggerView


# @method_decorator(login_required(login_url="/admin/login/"), name="get")
class CustomSwaggerView(SpectacularSwaggerView):
    pass
