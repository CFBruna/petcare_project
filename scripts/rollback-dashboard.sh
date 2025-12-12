#!/bin/bash
set -e

# Manual Rollback Script for Dashboard Deployment
# Usage: ./scripts/rollback-dashboard.sh <backup_directory>

if [ -z "$1" ]; then
    echo "❌ Usage: $0 <backup_directory>"
    echo ""
    echo "Available backups:"
    ls -lth backups/ | head -6
    exit 1
fi

BACKUP_DIR="$1"
DASHBOARD_PATH="src/static/dashboard"
COMPOSE_FILE="docker-compose.prod.yml"

echo "🔄 Rolling back dashboard deployment"
echo "====================================="
echo ""
echo "Backup: $BACKUP_DIR"
echo ""

if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Backup directory not found: $BACKUP_DIR"
    exit 1
fi

echo "⚠️  WARNING: This will replace the current dashboard with backup"
read -p "Continue? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Rollback cancelled"
    exit 0
fi

echo ""
echo "📦 Step 1/4: Restoring files from backup..."
rm -rf "$DASHBOARD_PATH"
cp -r "$BACKUP_DIR" "$DASHBOARD_PATH"
echo "✅ Files restored"
echo ""

echo "📋 Step 2/4: Copying to container..."
docker compose -f $COMPOSE_FILE cp $DASHBOARD_PATH/. web:/usr/src/app/$DASHBOARD_PATH/
echo "✅ Files copied to container"
echo ""

echo "📂 Step 3/4: Collecting static files..."
docker compose -f $COMPOSE_FILE exec web python manage.py collectstatic --noinput
echo "✅ Static files collected"
echo ""

echo "🔄 Step 4/4: Reloading Nginx..."
docker compose -f $COMPOSE_FILE exec nginx nginx -s reload
echo "✅ Nginx reloaded"
echo ""

echo "🏥 Running health check..."
sleep 3
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://petcare.brunadev.com/dashboard/)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Rollback successful - Dashboard is live (HTTP $HTTP_CODE)"
else
    echo "⚠️  Warning: Dashboard returned HTTP $HTTP_CODE"
    echo "   Check logs: docker compose -f $COMPOSE_FILE logs nginx"
fi

echo ""
echo "🎉 Rollback completed!"
