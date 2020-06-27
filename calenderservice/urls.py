from django.contrib import admin
from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from django.conf.urls import include
from calenderapp.views import test_redirect


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('calenderapp.urls')),
    path('', test_redirect),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
