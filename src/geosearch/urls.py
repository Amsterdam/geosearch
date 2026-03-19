from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from .views import health

urlpatterns = [
    path("pulse", health),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if "debug_toolbar" in settings.INSTALLED_APPS:
    import debug_toolbar

    urlpatterns.append(path("__debug__/", include(debug_toolbar.urls)))
