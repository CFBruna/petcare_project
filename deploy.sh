#!/bin/bash
set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}
error() {
    echo -e "${RED}[ERROR] $1${NC}"
}
success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

# Pre-flight checks
log "🔍 Starting pre-deployment checks..."
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "main" ]; then
    error "Deployment aborted. Current branch: $CURRENT_BRANCH (must be 'main')"
    exit 1
fi

log "📥 Fetching latest changes..."
git pull origin main

# Preparation
log "📋 Running database migrations..."
docker compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput

log "📦 Collecting static files..."
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput --clear

# Deployment
log "🔄 Restarting containers..."
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build

# Verification
log "⏳ Waiting for application to initialize..."
sleep 15

log "✅ Verifying container status..."
EXPECTED_CONTAINERS=$(docker compose -f docker-compose.prod.yml config --services | wc -l)
RUNNING_CONTAINERS=$(docker compose -f docker-compose.prod.yml ps --filter "status=running" --quiet | wc -l)

if [ "$RUNNING_CONTAINERS" -ne "$EXPECTED_CONTAINERS" ]; then
    error "Container verification failed! Expected: $EXPECTED_CONTAINERS, Running: $RUNNING_CONTAINERS"
    docker compose -f docker-compose.prod.yml ps
    exit 1
fi
success "All $RUNNING_CONTAINERS containers are running."

log "🌐 Testing application connectivity..."
RETRIES=0
MAX_RETRIES=15
until [ $RETRIES -ge $MAX_RETRIES ]; do
    if curl --insecure --silent --fail https://petcare.brunadev.com/api/v1/status/ > /dev/null 2>&1; then
        success "Health check passed! Application is online."
        break
    fi
    RETRIES=$((RETRIES+1))
    log "Attempt $RETRIES/$MAX_RETRIES... waiting for application."
    sleep 2
done

if [ $RETRIES -ge $MAX_RETRIES ]; then
    error "Health check failed after $MAX_RETRIES attempts."
    docker compose -f docker-compose.prod.yml logs --tail=50 nginx
    docker compose -f docker-compose.prod.yml logs --tail=50 web
    exit 1
fi

# Cleanup
log "🧹 Cleaning up unused Docker images..."
docker system prune -a -f

success "🎉 Deployment completed successfully!"
docker compose -f docker-compose.prod.yml ps
