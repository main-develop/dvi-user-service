#!/bin/sh
set -e

echo "Starting service with args: $@"

if [ "$1" != "celery" ]; then
    echo "Collecting static files..."
    python manage.py collectstatic --noinput

    echo "Applying database migrations..."
    python manage.py migrate --noinput
fi

case "$1" in
    celery)
        shift  # Remove "celery" from arguments
        exec celery -A dvi_user_service.celery worker --loglevel=info --pool=prefork -Q celery,emails "$@"
        ;;
    *)
        echo "Starting Gunicorn..."
        exec gunicorn dvi_user_service.wsgi:application --bind 0.0.0.0:8000 --workers 4
        ;;
esac
