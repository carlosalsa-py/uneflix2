release: python manage.py migrate --noinput
web: gunicorn uneflix.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3 --log-file -
