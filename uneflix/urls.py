from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('movies.urls')),
    path('users/', include('users.urls')),
]

# Media (posters, avatars, backdrops): los sirve Django en cualquier entorno.
# `static()` de Django devuelve [] cuando DEBUG=False, así que usamos serve()
# directo para que las imágenes no den 404 en producción. Para escalar, mover
# la media a almacenamiento en la nube (S3/Cloudinary) y quitar esta ruta.
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

# Los estáticos en producción los sirve WhiteNoise (middleware); esto es para
# el server de desarrollo.
urlpatterns += staticfiles_urlpatterns()