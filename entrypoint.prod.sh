#!/bin/sh

set -e

echo "Waiting for services to be ready..."
sleep 5

echo "Running database migrations..."
python manage.py migrate

echo "Updating static files volume ownership..."
chown -R appuser:appuser /app/staticfiles

echo "Collecting static files..."
sudo -E -u appuser python manage.py collectstatic --no-input

echo "Starting Gunicorn..."
exec sudo -E -u appuser gunicorn src.petcare.wsgi:application --bind 0.0.0.0:8000
