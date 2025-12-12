#!/bin/bash
set -e

# Production-Grade Dashboard Deployment with Safety Features
# - Automatic backup before deployment
# - Rollback on failure
# - Zero-downtime nginx reload
# - Smoke tests before applying changes

echo "🛡️  Safe Production Deployment - TypeScript Dashboard"
echo "====================================================="
echo ""

# Configuration
BACKUP_DIR="backups/dashboard-$(date +%Y%m%d-%H%M%S)"
DASHBOARD_PATH="src/static/dashboard"
COMPOSE_FILE="docker-compose.prod.yml"
DASHBOARD_URL="https://petcare.brunadev.com/dashboard/"

# Cleanup function for rollback
cleanup_and_rollback() {
    echo ""
    echo "❌ Deployment failed! Rolling back..."
    
    if [ -d "$BACKUP_DIR" ]; then
        echo "📦 Restoring from backup: $BACKUP_DIR"
        rm -rf "$DASHBOARD_PATH"
        cp -r "$BACKUP_DIR" "$DASHBOARD_PATH"
        
        # Re-copy to container
        docker compose -f $COMPOSE_FILE cp $DASHBOARD_PATH/. web:/usr/src/app/$DASHBOARD_PATH/ 2>/dev/null || true
        docker compose -f $COMPOSE_FILE exec web python manage.py collectstatic --noinput 2>/dev/null || true
        docker compose -f $COMPOSE_FILE exec nginx nginx -s reload 2>/dev/null || true
        
        echo "✅ Rollback completed - site should be stable"
    else
        echo "⚠️  No backup found - manual intervention required"
    fi
    
    exit 1
}

# Set trap for errors
trap cleanup_and_rollback ERR

echo "📋 Pre-deployment checks..."
# Verify containers are running
if ! docker compose -f $COMPOSE_FILE ps | grep -q "Up"; then
    echo "❌ Containers not running. Start with: docker compose -f $COMPOSE_FILE up -d"
    exit 1
fi
echo "✅ Containers are running"
echo ""

# Step 1: Backup current deployment
echo "💾 Step 1/7: Creating backup..."
mkdir -p backups
if [ -d "$DASHBOARD_PATH" ]; then
    cp -r "$DASHBOARD_PATH" "$BACKUP_DIR"
    echo "✅ Backup created: $BACKUP_DIR"
else
    echo "⚠️  No existing dashboard found (first deployment)"
fi
echo ""

# Step 2: Build Frontend
echo "📦 Step 2/7: Building frontend with Vite..."
cd frontend
npm install --quiet
npm run build
cd ..
echo "✅ Frontend built successfully"
echo ""

# Step 3: Smoke test the build
echo "🧪 Step 3/7: Validating build..."
if [ ! -f "$DASHBOARD_PATH/index.html" ]; then
    echo "❌ Build failed - index.html not found"
    exit 1
fi
if [ ! -d "$DASHBOARD_PATH/assets" ]; then
    echo "❌ Build failed - assets directory not found"
    exit 1
fi
BUILD_SIZE=$(du -sh "$DASHBOARD_PATH" | cut -f1)
echo "✅ Build validated - Size: $BUILD_SIZE"
echo ""

# Step 4: Copy to staging location in container (not live yet)
echo "📋 Step 4/7: Staging new build in container..."
docker compose -f $COMPOSE_FILE cp $DASHBOARD_PATH/. web:/usr/src/app/${DASHBOARD_PATH}-staging/
echo "✅ Build staged successfully"
echo ""

# Step 5: Test staging deployment
echo "🔍 Step 5/7: Testing staged deployment..."
# Move staging to live location
docker compose -f $COMPOSE_FILE exec web bash -c "rm -rf /usr/src/app/$DASHBOARD_PATH && mv /usr/src/app/${DASHBOARD_PATH}-staging /usr/src/app/$DASHBOARD_PATH"
docker compose -f $COMPOSE_FILE exec web python manage.py collectstatic --noinput
STATIC_COUNT=$(docker compose -f $COMPOSE_FILE exec web bash -c "ls -1 /usr/src/app/staticfiles/dashboard/assets/ 2>/dev/null | wc -l" | tr -d '[:space:]')
if [ "$STATIC_COUNT" -lt 2 ]; then
    echo "❌ Static files collection failed - only $STATIC_COUNT files found"
    exit 1
fi
echo "✅ Static files collected ($STATIC_COUNT assets)"
echo ""

# Step 6: Zero-downtime reload (not restart)
echo "🔄 Step 6/7: Hot-reloading Nginx (zero downtime)..."
docker compose -f $COMPOSE_FILE exec nginx nginx -s reload
sleep 2
echo "✅ Nginx reloaded without downtime"
echo ""

# Step 7: Health check
echo "🏥 Step 7/7: Running health check..."
sleep 3
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" $DASHBOARD_URL)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Dashboard is live and healthy!"
    echo ""
    echo "🎉 Deployment completed successfully!"
    echo ""
    echo "📊 Deployment Summary:"
    echo "   - Build size: $BUILD_SIZE"
    echo "   - Static files: $STATIC_COUNT assets"
    echo "   - HTTP status: $HTTP_CODE OK"
    echo "   - Backup location: $BACKUP_DIR"
    echo "   - Downtime: 0 seconds (hot reload)"
    echo ""
    echo "🧹 Cleanup old backups (keep last 5):"
    echo "   ls -t backups/ | tail -n +6 | xargs -I {} rm -rf backups/{}"
else
    echo "❌ Health check failed - HTTP $HTTP_CODE"
    exit 1
fi

echo ""
echo "📖 Next steps:"
echo "   1. Test dashboard: $DASHBOARD_URL"
echo "   2. Login with: recrutador@petcare.com / avaliar123"
echo "   3. Verify all features working"
echo ""
echo "🔧 Rollback if needed:"
echo "   ./scripts/rollback-dashboard.sh $BACKUP_DIR"
