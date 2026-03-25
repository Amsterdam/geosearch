from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from .views import catalogus, health_check, pulse

urlpatterns = [
    path("pulse", pulse),
    path("health-check", health_check),
    path("geosearch/catalogus/", catalogus),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if "debug_toolbar" in settings.INSTALLED_APPS:
    import debug_toolbar

    urlpatterns.append(path("__debug__/", include(debug_toolbar.urls)))
