from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from django.contrib.staticfiles.views import serve as serve_static
from django.views.static import serve as serve_media

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('catalog/', include('catalog.urls')),
    path('circulation/', include('circulation.urls')),
]

# Always serve CSS/JS/images and uploaded covers when running with `runserver`,
# even if DJANGO_DEBUG=False is set in the environment. Otherwise the pages show
# up as plain, unstyled HTML. (For a real production server, use nginx/WhiteNoise.)
urlpatterns += [
    re_path(r'^%s(?P<path>.*)$' % settings.STATIC_URL.lstrip('/'), serve_static, {'insecure': True}),
    re_path(r'^%s(?P<path>.*)$' % settings.MEDIA_URL.lstrip('/'), serve_media, {'document_root': settings.MEDIA_ROOT}),
]
