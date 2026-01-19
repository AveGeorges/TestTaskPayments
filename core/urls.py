import environ
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import path, include
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

env = environ.Env()


class ProtectedSpectacularSwaggerView(SpectacularSwaggerView):
    """
    Swagger UI с защитой через Django admin аутентификацию.
    Требует авторизации в Django admin.
    """
    @classmethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        return login_required(view, login_url='/admin/login/')


class ProtectedSpectacularAPIView(SpectacularAPIView):
    """
    OpenAPI схема с защитой через Django admin аутентификацию.
    """
    @classmethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        return login_required(view, login_url='/admin/login/')


urlpatterns = [
    path('', RedirectView.as_view(url='/api/v1/docs/', permanent=False)),
    path('admin/', admin.site.urls),
    
    # API v1
    path('api/v1/', include('payments.urls')),
    
    # OpenAPI схема и Swagger UI (защищены аутентификацией)
    path('api/v1/schema/', ProtectedSpectacularAPIView.as_view(), name='schema'),
    path('api/v1/docs/', ProtectedSpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

# Django Silk - профилирование запросов (только в development)
if env("DJANGO_ENV") == "development":
    urlpatterns += [
        path('silk/', include('silk.urls', namespace='silk')),
    ]
