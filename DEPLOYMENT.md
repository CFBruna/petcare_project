# Production Deployment

This README explains how to deploy the PetCare application to production using the unified deployment scripts.

## 🚀 Quick Start

### For normal deployments:
```bash
./deploy.sh
```

That's it! The script handles everything with automatic testing and rollback.

### If something goes wrong:
```bash
./rollback.sh backups/deployment-YYYYMMDD-HHMMSS
```

---

## 📋 Scripts Overview

### 1. `deploy.sh` - **Production-Grade Deployment** ⭐

**Complete blue-green deployment with:**
- ✅ Automatic backup before deployment
- ✅ Build and test BEFORE applying
- ✅ Dashboard + Application deployment
- ✅ Database migrations
- ✅ Zero-downtime nginx reload
- ✅ **Automatic rollback if tests fail**
- ✅ Health checks (API + Dashboard)
- ✅ ~10s downtime (container restart only)

**What it deploys:**
- Django application (rebuild containers)
- TypeScript/React dashboard
- Static files
- Database migrations
- Nginx configuration

**Safety features:**
- Creates backup in `backups/deployment-TIMESTAMP/`
- Tests new version before applying
- Rolls back automatically on failure
- Validates health before confirming success
- Keeps last 5 backups automatically

---

### 2. `rollback.sh` - **Manual Recovery**

**Use when:** You need to manually revert to a previous deployment

**Features:**
- Restores complete system state
- Includes dashboard, containers, static files
- Confirmation prompt for safety
- Health checks after rollback

---

## 📊 Deployment Process

### What Happens (10 Steps):

```
1. ✅ Pre-flight checks (main branch, git pull)
2. 💾 Create full backup (dashboard + containers)
3. 📦 Build TypeScript dashboard
4. 🏗️  Build Docker images (not deployed yet)
5. 🧪 Test build in staging
6. 🚀 Deploy with minimal downtime
7. 📋 Run database migrations
8. 📊 Deploy dashboard assets
9. ✅ Verify all containers running
10. 🏥 Health checks (API + Dashboard)
```

**If any step fails → Automatic rollback**

---

## 🎯 Usage Examples

### Normal Workflow:

```bash
# 1. SSH into Azure VM
ssh -i ~/.ssh/vm-petcare-prod_key.pem petcare-azure-key@20.157.194.30

# 2. Navigate to project
cd ~/petcare_project

# 3. Ensure you're on main
git checkout main

# 4. Deploy!
./deploy.sh
```

### Disaster Recovery:

```bash
# List available backups
ls -lth backups/

# Rollback to specific version
./rollback.sh backups/deployment-20251212-140000

# Verify system is healthy
docker compose -f docker-compose.prod.yml ps
curl -I https://petcare.brunadev.com/api/v1/status/
curl -I https://petcare.brunadev.com/dashboard/
```

### Cleanup Old Backups:

```bash
# Keep only last 5 backups manually
ls -1dt backups/deployment-* | tail -n +6 | xargs rm -rf
```
*(deploy.sh does this automatically)*

---

## 🛡️ Safety & Best Practices

### Before Deployment:

1. ✅ **Test locally first**
   ```bash
   docker compose up --build
   npm run build
   ```

2. ✅ **Ensure main branch**
   ```bash
   git status
   # Should show: "On branch main"
   ```

3. ✅ **Check current system health**
   ```bash
   curl -I https://petcare.brunadev.com/api/v1/status/
   # Should return: HTTP/2 200
   ```

### During Deployment:

- Monitor the output - script provides detailed logging
- Don't interrupt the script (Ctrl+C) during deployment
- If error occurs, automatic rollback will trigger

### After Deployment:

1. **Verify health checks passed**
   - API: HTTP 200
   - Dashboard: HTTP 200
   - All containers running

2. **Test critical features**
   - Login at https://petcare.brunadev.com
   - Check dashboard at https://petcare.brunadev.com/dashboard
   - Test API at https://petcare.brunadev.com/api/v1/schema/swagger-ui/

3. **Monitor logs** (first 10 minutes)
   ```bash
   docker compose -f docker-compose.prod.yml logs -f --tail=100
   ```

---

## 🔧 Troubleshooting

### "Deployment aborted. Current branch: X (must be 'main')"
```bash
git checkout main
git pull origin main
```

### "Docker build failed! Keeping current version online."
```bash
# Check for syntax errors in Dockerfile or docker-compose.prod.yml
docker compose -f docker-compose.prod.yml build web
```

### "Health check failed after 15 attempts"
```bash
# Check application logs
docker compose -f docker-compose.prod.yml logs web

# Check nginx logs
docker compose -f docker-compose.prod.yml logs nginx

# Manual rollback
./rollback.sh backups/deployment-LATEST
```

### Dashboard returns 404 after deployment
```bash
# Verify static files were collected
docker compose -f docker-compose.prod.yml exec web ls -la /usr/src/app/staticfiles/dashboard/

# Re-collect static files
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Reload nginx
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

---

## 📁 Scripts Directory

Additional dashboard-specific scripts are in `scripts/`:

- `deploy-dashboard.sh` - Quick dashboard-only deploy (simple)
- `deploy-dashboard-safe.sh` - Safe dashboard deploy with backup
- `rollback-dashboard.sh` - Dashboard-only rollback

**Recommendation:** Use root `deploy.sh` for production. Use `scripts/` for dashboard-only quick updates.

---

## 🎓 Technical Details

### Blue-Green Deployment Strategy:

1. **Blue (Current):** Production currently running
2. **Green (New):** Build and test new version
3. **Verification:** Test green version is healthy
4. **Switch:** Deploy green version
5. **Fallback:** If green fails, keep blue running (rollback)

### Zero-Downtime Approach:

- Uses `docker compose up -d` (rolling restart)
- Nginx reloads config (`nginx -s reload`) instead of restart
- Containers restart sequentially, not all at once
- Health checks ensure services are ready

### Backup Structure:

```
backups/
└── deployment-20251212-140530/
    ├── dashboard/          # Frontend build
    │   ├── index.html
    │   └── assets/
    └── docker-compose.yml  # Container config
```

---

## 📞 Support

**If deployment fails repeatedly:**

1. Check GitHub Actions CI/CD for test failures
2. Test locally with `docker compose up --build`
3. Review recent commits for breaking changes
4. Consider deploying a known-good commit:
   ```bash
   git checkout <commit-hash>
   ./deploy.sh
   ```

---

**Last Updated:** 2025-12-12  
**Production Deployment Version:** 2.0 (Unified Blue-Green)
