#!/usr/bin/env bash
# Script de build portable para el deploy. Lo corre el host (Render, Railway,
# etc.) antes de arrancar gunicorn. Idempotente: se puede correr en cada deploy.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --noinput
