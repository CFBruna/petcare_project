#!/bin/bash
set -e

# Production Rollback Script
# Restores complete system state from backup

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}
error() {
    echo -e "${RED}[ERROR] $1${NC}"
}
success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}
warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

echo "🔄 Production System Rollback"
echo "============================="
echo ""

# Check for backup directory argument
if [ -z "$1" ]; then
    error "Usage: $0 <backup_directory>"
    echo ""
    log "Available backups:"
    ls -lth backups/ 2>/dev/null | head -11 || echo "No backups found"
    echo ""
    echo "Example:"
    echo "  ./rollback.sh backups/deployment-20251212-120000"
    exit 1
fi

BACKUP_DIR="$1"
COMPOSE_FILE="docker-compose.prod.yml"
API_URL="https://petcare.brunadev.com/api/v1/status/"
DASHBOARD_URL="https://petcare.brunadev.com/dashboard/"

if [ ! -d "$BACKUP_DIR" ]; then
    error "Backup directory not found: $BACKUP_DIR"
    exit 1
fi

log "Backup location: $BACKUP_DIR"
echo ""

warning "⚠️  This will replace current deployment with backup"
warning "⚠️  Current state will NOT be backed up"
echo ""
read -p "Continue rollback? (yes/no): " -r
echo ""

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    log "Rollback cancelled"
    exit 0
fi

# Rollback dashboard if exists
if [ -d "$BACKUP_DIR/dashboard" ]; then
    log "Step 1/6: Restoring dashboard files..."
    rm -rf src/static/dashboard
    cp -r "$BACKUP_DIR/dashboard" src/static/dashboard
    success "Dashboard files restored"
  else
    warning "No dashboard backup found - skipping"
fi
echo ""

# Rollback containers if docker-compose backup exists
if [ -f "$BACKUP_DIR/docker-compose.yml" ]; then
    log "Step 2/6: Restoring container configuration..."
    
    log "Stopping current containers..."
    docker compose -f $COMPOSE_FILE down
    
    log "Starting containers with backup configuration..."
    docker compose -f $COMPOSE_FILE up -d
    
    log "Waiting for containers to stabilize..."
    sleep 10
    success "Containers restored"
else
    warning "No container backup - restarting with current config..."
    docker compose -f $COMPOSE_FILE restart
    sleep 10
fi
echo ""

# Copy dashboard to container
log "Step 3/6: Deploying dashboard to container..."
if [ -d "src/static/dashboard" ]; then
    docker compose -f $COMPOSE_FILE cp src/static/dashboard/. web:/usr/src/app/src/static/dashboard/
    success "Dashboard deployed to container"
else
    warning "No dashboard files to deploy"
fi
echo ""

# Collect static files
log "Step 4/6: Collecting static files..."
docker compose -f $COMPOSE_FILE exec web python manage.py collectstatic --noinput --clear
success "Static files collected"
echo ""

# Reload nginx
log "Step 5/6: Reloading Nginx..."
docker compose -f $COMPOSE_FILE exec nginx nginx -s reload 2>/dev/null || \
docker compose -f $COMPOSE_FILE restart nginx
success "Nginx reloaded"
echo ""

# Health checks
log "Step 6/6: Running health checks..."
sleep 5

# Check containers
EXPECTED=$(docker compose -f $COMPOSE_FILE config --services | wc -l)
RUNNING=$(docker compose -f $COMPOSE_FILE ps --filter "status=running" --quiet | wc -l)

if [ "$RUNNING" -ne "$EXPECTED" ]; then
    error "Container check failed! Expected: $EXPECTED, Running: $RUNNING"
    docker compose -f $COMPOSE_FILE ps
    exit 1
fi
success "Containers: $RUNNING/$EXPECTED running"

# Check API
API_CODE=$(curl -s -o /dev/null -w "%{http_code}" $API_URL 2>/dev/null || echo "000")
if [ "$API_CODE" = "200" ]; then
    success "API: HTTP $API_CODE ✓"
else
    warning "API: HTTP $API_CODE (may require investigation)"
fi

# Check dashboard
DASH_CODE=$(curl -s -o /dev/null -w "%{http_code}" $DASHBOARD_URL 2>/dev/null || echo "000")
if [ "$DASH_CODE" = "200" ]; then
    success "Dashboard: HTTP $DASH_CODE ✓"
else
    warning "Dashboard: HTTP $DASH_CODE (may need login)"
fi
echo ""

success "🎉 Rollback completed!"
echo ""
echo "📊 System Status:"
echo "   ├─ Containers: $RUNNING running"
echo "   ├─ API: HTTP $API_CODE"
echo "   ├─ Dashboard: HTTP $DASH_CODE"
echo "   └─ Backup used: $BACKUP_DIR"
echo ""
echo "🌐 Test the application:"
echo "   - Main: https://petcare.brunadev.com"
echo "   - Dashboard: $DASHBOARD_URL"
echo "   - API: https://petcare.brunadev.com/api/v1/schema/swagger-ui/"
echo ""
echo "📋 If issues persist:"
echo "   - Check logs: docker compose -f $COMPOSE_FILE logs"
echo "   - Try different backup: ./rollback.sh backups/deployment-YYYYMMDD-HHMMSS"
echo ""

docker compose -f $COMPOSE_FILE ps
