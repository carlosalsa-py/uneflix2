from django.db import connection
from django.http import HttpResponse


def healthz(request):
    """Healthcheck para el host/monitor. Verifica que la app responde y que la
    base de datos está accesible. 200 = sano, 503 = DB caída."""
    try:
        connection.ensure_connection()
    except Exception:
        return HttpResponse('database unavailable', status=503, content_type='text/plain')
    return HttpResponse('ok', content_type='text/plain')


def robots_txt(request):
    lines = [
        'User-agent: *',
        'Disallow: /admin/',
        'Disallow: /users/',
        'Allow: /',
    ]
    return HttpResponse('\n'.join(lines) + '\n', content_type='text/plain')
