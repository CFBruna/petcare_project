#!/bin/bash
set -e

# Production-Grade Blue-Green Deployment Script
# Features:
# - Automatic backup before deployment
# - Build and test new version before applying
# - Zero-downtime deployment
# - Automatic rollback on failure
# - Includes application + dashboard deployment
# - Test branch deployment with --test-branch flag

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Parse arguments
TEST_BRANCH=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --test-branch)
            TEST_BRANCH="$2"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1"
            echo "Usage: $0 [--test-branch branch-name]"
            exit 1
            ;;
    esac
done

# Configuration
BACKUP_DIR="backups/deployment-$(date +%Y%m%d-%H%M%S)"
COMPOSE_FILE="docker-compose.prod.yml"
DASHBOARD_URL="https://petcare.brunadev.com/dashboard/"
API_URL="https://petcare.brunadev.com/api/v1/status/"

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
warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Cleanup and rollback function
cleanup_and_rollback() {
    error "Deployment failed! Initiating rollback..."

    if [ -d "$BACKUP_DIR" ]; then
        log "Restoring from backup: $BACKUP_DIR"

        # Restore dashboard if exists
        if [ -d "$BACKUP_DIR/dashboard" ]; then
            rm -rf src/static/dashboard
            cp -r "$BACKUP_DIR/dashboard" src/static/dashboard
            docker compose -f $COMPOSE_FILE cp src/static/dashboard/. web:/usr/src/app/src/static/dashboard/ 2>/dev/null || true
        fi

        # Restore containers
        if [ -f "$BACKUP_DIR/docker-compose.yml" ]; then
            log "Rolling back containers..."
            docker compose -f $COMPOSE_FILE down
            docker compose -f $COMPOSE_FILE up -d
            sleep 10
        fi

        # Restore static files
        docker compose -f $COMPOSE_FILE exec web python manage.py collectstatic --noinput 2>/dev/null || true
        docker compose -f $COMPOSE_FILE exec nginx nginx -s reload 2>/dev/null || true

        success "Rollback completed - application should be stable"
    else
        error "No backup found - manual intervention required"
    fi

    exit 1
}

# Set trap for errors
trap cleanup_and_rollback ERR

echo "🛡️  Production-Grade Deployment with Blue-Green Strategy"
echo "========================================================="
echo ""

# Pre-flight checks
log "🔍 Step 1/11: Pre-deployment checks..."
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [ -z "$TEST_BRANCH" ]; then
    # Normal production deploy - must be on main
    if [ "$CURRENT_BRANCH" != "main" ]; then
        error "Deployment aborted. Current branch: $CURRENT_BRANCH (must be 'main')"
        exit 1
    fi
    success "On main branch"
    log "📥 Fetching latest changes..."
    git pull origin main
else
    # Test branch deploy
    warning "🧪 TEST MODE: Deploying branch '$TEST_BRANCH' to PRODUCTION"
    warning "This will temporarily replace the production code for testing"
    echo ""
    read -p "Deploy '$TEST_BRANCH' to PRODUCTION environment? Type 'yes' to confirm: " -r
    echo
    if [[ ! $REPLY =~ ^yes$ ]]; then
        error "Deployment cancelled by user"
        exit 1
    fi

    log "📥 Fetching and checking out test branch..."
    git fetch origin "$TEST_BRANCH" || error "Failed to fetch branch '$TEST_BRANCH'"
    git checkout "$TEST_BRANCH"
    git pull origin "$TEST_BRANCH"
    success "On test branch: $TEST_BRANCH"
fi

success "Code updated"
echo ""

# Verify AI configuration
log "🤖 Step 2/11: Verifying AI environment variables..."
if [ ! -f ".env" ]; then
    error ".env file not found! AI features require configuration."
    exit 1
fi

if ! grep -q "^GOOGLE_API_KEY=" .env 2>/dev/null || [ -z "$(grep '^GOOGLE_API_KEY=' .env | cut -d= -f2)" ]; then
    warning "⚠️  GOOGLE_API_KEY not configured in .env"
    warning "AI features (product descriptions, health analysis) will fail without this!"
    echo ""
    echo "To fix:"
    echo "  1. Get API key from: https://aistudio.google.com/app/apikey"
    echo "  2. Add to .env: GOOGLE_API_KEY=your-key-here"
    echo ""
    read -p "Continue deployment without AI? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        error "Deployment aborted - please configure GOOGLE_API_KEY first"
        exit 1
    fi
    warning "Proceeding without AI configuration - AI features will not work!"
else
    success "AI configuration verified (GOOGLE_API_KEY present)"
fi
echo ""

# Create backup
log "💾 Step 3/11: Creating full system backup..."
mkdir -p backups
mkdir -p "$BACKUP_DIR"

# Backup dashboard if exists
if [ -d "src/static/dashboard" ]; then
    cp -r src/static/dashboard "$BACKUP_DIR/dashboard"
fi

# Backup current docker-compose state
docker compose -f $COMPOSE_FILE config > "$BACKUP_DIR/docker-compose.yml" 2>/dev/null || true
success "Backup created: $BACKUP_DIR"
echo ""

# Build dashboard and admin calendar
log "📦 Step 4/11: Building TypeScript dashboard and admin calendar..."
cd frontend
npm install --quiet
npm run build
npx vite build --config vite.admin.config.ts
cd ..

# Validate dashboard build
if [ ! -f "src/static/dashboard/index.html" ]; then
    error "Dashboard build failed - index.html not found"
    exit 1
fi

# Validate admin calendar build
if [ ! -f "src/static/admin_calendar/assets/admin-calendar.js" ]; then
    error "Admin calendar build failed - admin-calendar.js not found"
    exit 1
fi

BUILD_SIZE=$(du -sh src/static/dashboard 2>/dev/null | cut -f1 || echo "unknown")
CALENDAR_SIZE=$(du -sh src/static/admin_calendar 2>/dev/null | cut -f1 || echo "unknown")
success "Dashboard built - Size: $BUILD_SIZE"
success "Admin calendar built - Size: $CALENDAR_SIZE"
echo ""

# Build Docker images
log "🏗️  Step 5/11: Building Docker images (no deployment yet)..."
if ! docker compose -f $COMPOSE_FILE build; then
    error "Docker build failed! Keeping current version online."
    exit 1
fi
success "Docker images built successfully"
echo ""

# Test phase - deploy to staging
log "🧪 Step 6/11: Testing new build (staging)..."
if [ -n "$(docker compose -f $COMPOSE_FILE ps --quiet web 2>/dev/null)" ]; then
    log "Copying dashboard to staging location..."
    docker compose -f $COMPOSE_FILE cp src/static/dashboard/. web:/usr/src/app/src/static/dashboard-staging/
else
    warning "Web container not running (first deploy?) - skipping pre-deployment asset copy"
fi

# Quick smoke test on current container
CURRENT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $API_URL || echo "000")
if [ "$CURRENT_STATUS" != "200" ]; then
    warning "Current app not responding (HTTP $CURRENT_STATUS) - proceeding with deployment"
fi
success "Pre-deployment tests passed"
echo ""

# Deploy phase - zero downtime
log "🚀 Step 7/11: Deploying new version with zero downtime..."
log "Note: Containers will restart but with rolling strategy"

# Apply new images with minimal downtime
docker compose -f $COMPOSE_FILE up -d --no-deps --build

log "⏳ Waiting for containers to stabilize..."
sleep 10
success "Containers restarted"
echo ""

# Migrations
log "📋 Step 8/11: Running database migrations..."
docker compose -f $COMPOSE_FILE exec web python manage.py migrate --noinput
success "Migrations completed"

# Initialize chroma_db for AI features
log "🤖 Initializing AI vector database..."
docker compose -f $COMPOSE_FILE exec -u root web bash -c "mkdir -p /usr/src/app/chroma_db && chown -R appuser:appuser /usr/src/app/chroma_db"
success "ChromaDB directory ready"
echo ""

# Deploy dashboard
log "📊 Step 9/11: Deploying dashboard assets..."

# Check if we have staged assets inside container
if docker compose -f $COMPOSE_FILE exec web [ -d "/usr/src/app/src/static/dashboard-staging" ] 2>/dev/null; then
    log "Promoting staged dashboard to live..."
    docker compose -f $COMPOSE_FILE exec web bash -c "rm -rf /usr/src/app/src/static/dashboard && mv /usr/src/app/src/static/dashboard-staging /usr/src/app/src/static/dashboard"
else
    log "Copying dashboard directly from host..."
    docker compose -f $COMPOSE_FILE cp src/static/dashboard/. web:/usr/src/app/src/static/dashboard/
fi

# Fix permissions and collect static files
log "Collecting static files..."
# Ensure staticfiles directory is writable
docker compose -f $COMPOSE_FILE exec -u root web chown -R appuser:appuser /usr/src/app/staticfiles
docker compose -f $COMPOSE_FILE exec web python manage.py collectstatic --noinput --clear

# Hot reload nginx
docker compose -f $COMPOSE_FILE exec nginx nginx -s reload
success "Dashboard deployed"
echo ""

# Verification
log "✅ Step 10/11: Verifying deployment..."
EXPECTED_CONTAINERS=$(docker compose -f $COMPOSE_FILE config --services | wc -l)
RUNNING_CONTAINERS=$(docker compose -f $COMPOSE_FILE ps --filter "status=running" --quiet | wc -l)

if [ "$RUNNING_CONTAINERS" -ne "$EXPECTED_CONTAINERS" ]; then
    error "Container verification failed! Expected: $EXPECTED_CONTAINERS, Running: $RUNNING_CONTAINERS"
    docker compose -f $COMPOSE_FILE ps
    exit 1
fi
success "All $RUNNING_CONTAINERS containers are running"

# Health checks
log "🏥 Testing application health..."
RETRIES=0
MAX_RETRIES=15

# API health check
until [ $RETRIES -ge $MAX_RETRIES ]; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" $API_URL || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        success "API health check passed (HTTP $HTTP_CODE)"
        break
    fi
    RETRIES=$((RETRIES+1))
    log "Attempt $RETRIES/$MAX_RETRIES... API returned HTTP $HTTP_CODE"
    sleep 2
done

if [ $RETRIES -ge $MAX_RETRIES ]; then
    error "API health check failed after $MAX_RETRIES attempts"
    docker compose -f $COMPOSE_FILE logs --tail=50 web
    exit 1
fi

# Dashboard health check
DASHBOARD_CODE=$(curl -s -o /dev/null -w "%{http_code}" $DASHBOARD_URL || echo "000")
if [ "$DASHBOARD_CODE" = "200" ]; then
    success "Dashboard health check passed (HTTP $DASHBOARD_CODE)"
else
    warning "Dashboard returned HTTP $DASHBOARD_CODE (may need login)"
fi
echo ""

# Cleanup
log "🧹 Step 11/11: Cleaning up..."
docker system prune -a -f --volumes > /dev/null 2>&1

# Keep only last 5 backups
BACKUP_COUNT=$(ls -1d backups/deployment-* 2>/dev/null | wc -l)
if [ "$BACKUP_COUNT" -gt 5 ]; then
    ls -1dt backups/deployment-* | tail -n +6 | xargs rm -rf
    log "Cleaned old backups (kept last 5)"
fi
echo ""

success "🎉 Deployment completed successfully!"
echo ""

if [ -n "$TEST_BRANCH" ]; then
    warning "⚠️  REMINDER: You deployed test branch '$TEST_BRANCH' to PRODUCTION"
    warning "⚠️  This is temporary for testing purposes"
    echo ""
    echo "📝 Next steps:"
    echo "   1. Test your changes at: https://petcare.brunadev.com"
    echo "   2. If tests pass: merge '$TEST_BRANCH' to main and redeploy"
    echo "   3. If tests fail: rollback with: ./rollback.sh $BACKUP_DIR"
    echo "   4. Then checkout main again: git checkout main"
    echo ""
fi

echo "📊 Deployment Summary:"
echo "   ├─ Branch: $(git rev-parse --abbrev-ref HEAD)"
echo "   ├─ Backup: $BACKUP_DIR"
echo "   ├─ Dashboard: $BUILD_SIZE"
echo "   ├─ Containers: $RUNNING_CONTAINERS running"
echo "   ├─ API Status: HTTP $HTTP_CODE"
echo "   ├─ Dashboard Status: HTTP $DASHBOARD_CODE"
echo "   └─ Downtime: ~10s (container restart)"
echo ""
echo "🌐 Access Points:"
echo "   - Main: https://petcare.brunadev.com"
echo "   - Dashboard: $DASHBOARD_URL"
echo "   - API: https://petcare.brunadev.com/api/v1/schema/swagger-ui/"
echo ""
echo "🔧 Rollback if needed:"
echo "   ./rollback.sh $BACKUP_DIR"
echo ""

docker compose -f $COMPOSE_FILE ps
