#!/bin/sh

set -e

echo "Waiting for services to be ready..."
sleep 5

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn server..."
exec gunicorn src.petcare.wsgi:application --bind 0.0.0.0:8000
