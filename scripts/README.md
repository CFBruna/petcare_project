# Dashboard Deployment Scripts

This directory contains scripts for deploying the TypeScript/React analytics dashboard to production.

## Scripts Overview

### 1. `deploy-dashboard.sh` (Simple)
**Use when:** Quick deployments, low-risk changes

**Features:**
- ✅ Build frontend with Vite
- ✅ Copy to container
- ✅ Collect static files
- ✅ Restart Nginx
- ✅ Health check
- ⚠️  1-3 seconds downtime (nginx restart)
- ❌ No automatic rollback

**Usage:**
```bash
./scripts/deploy-dashboard.sh
```

---

### 2. `deploy-dashboard-safe.sh` (Production-Grade) ⭐ **Recommended**
**Use when:** Production deployments, important changes

**Features:**
- ✅ **Automatic backup** before deployment
- ✅ **Smoke tests** on build
- ✅ **Staging validation** before going live
- ✅ **Zero-downtime** (nginx reload, not restart)
- ✅ **Automatic rollback** on any error
- ✅ Detailed deployment summary
- ✅ **0 seconds downtime**

**Usage:**
```bash
./scripts/deploy-dashboard-safe.sh
```

**What happens behind the scenes:**
1. Creates backup in `backups/dashboard-YYYYMMDD-HHMMSS/`
2. Builds frontend and validates
3. Stages deployment in container
4. Tests staged deployment
5. Hot-reloads Nginx (no downtime)
6. Runs health check
7. Auto-rollback if anything fails

---

### 3. `rollback-dashboard.sh` (Recovery)
**Use when:** Need to manually rollback to a previous version

**Usage:**
```bash
# List available backups
ls -lth backups/

# Rollback to specific backup
./scripts/rollback-dashboard.sh backups/dashboard-20251212-120000
```

---

## Comparison

| Feature | Simple | Safe |
|---------|--------|------|
| **Deployment Time** | ~30s | ~45s |
| **Downtime** | 1-3s | 0s |
| **Auto Backup** | ❌ | ✅ |
| **Auto Rollback** | ❌ | ✅ |
| **Smoke Tests** | ❌ | ✅ |
| **Complexity** | Low | Medium |

---

## Production Workflow

**For normal deployments:**
```bash
cd ~/petcare_project
git pull origin main
./scripts/deploy-dashboard-safe.sh
```

**If deployment fails:**
```bash
# Safe script auto-rolls back
# Or manually rollback:
./scripts/rollback-dashboard.sh backups/dashboard-YYYYMMDD-HHMMSS
```

**Clean old backups (keep last 5):**
```bash
ls -t backups/ | tail -n +6 | xargs -I {} rm -rf backups/{}
```

---

## Technical Details

### Zero-Downtime Strategy (Safe Script)
- Uses `nginx -s reload` instead of container restart
- Nginx reloads config without dropping connections
- Staging area tested before going live
- Rollback restores previous working version

### Backup Strategy
- Backups stored in `backups/dashboard-TIMESTAMP/`
- Includes all built assets and source files
- Can be restored with rollback script
- Recommended: Keep last 5 backups (cleanup command above)

---

## Troubleshooting

**"Build failed - index.html not found"**
- Check frontend build: `cd frontend && npm run build`
- Verify `src/static/dashboard/index.html` exists

**"Health check failed - HTTP 404"**
- Check nginx logs: `docker compose -f docker-compose.prod.yml logs nginx`
- Verify static files: `docker compose -f docker-compose.prod.yml exec web ls -la /usr/src/app/staticfiles/dashboard/`

**"Containers not running"**
- Start containers: `docker compose -f docker-compose.prod.yml up -d`

---

## Files Modified by Deployment

- `src/static/dashboard/` (built frontend)
- Container: `/usr/src/app/src/static/dashboard/`
- Container: `/usr/src/app/staticfiles/dashboard/` (after collectstatic)
- Nginx config remains unchanged (no reload needed)
