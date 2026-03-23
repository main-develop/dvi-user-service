#!/bin/sh
set -e

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Applying database migrations..."
python manage.py migrate

echo "Starting Gunicorn..."
exec gunicorn dvi_user_service.wsgi:application --bind 0.0.0.0:8000 --workers 3