# Unified Deployment Architecture

## 🎯 **The Senior Principle: ONE Script, Multiple Environments**

### ✅ **Why ONE deployment script?**

```bash
# CORRECT (Senior Level):
./deploy.sh              # Production
./deploy.sh --staging    # Staging

# ✅ Same script = Same process = Same guarantees
```

```bash
# WRONG (Junior mistake):
./deploy.sh          # Production script
./deploy-staging.sh  # Different staging script

# ❌ Different scripts = Different bugs = False confidence
```

## 🏗️ The Problem Solved

### ❌ **Old Approach (Two Scripts):**
```
deploy.sh          → production logic
deploy-staging.sh  → staging logic (DIFFERENT!)
```

**Issues:**
- ❌ Staging deploys successfully, production fails (script bug)
- ❌ Production deploys successfully, staging fails (drift)
- ❌ Maintain two codebases (DRY violation)
- ❌ "Worked in staging!" doesn't mean "Will work in prod!"

### ✅ **New Approach (One Script, Two Modes):**
```
deploy.sh                        → production mode
deploy.sh --staging              → staging mode
deploy.sh --staging feature/xyz  → staging mode (specific branch)
```

**Benefits:**
- ✅ **Identical deployment process** for staging and production
- ✅ **Same validation logic** - if staging passes, prod WILL pass
- ✅ **One script to maintain** - DRY principle
- ✅ **True parity** - staging tests the EXACT deployment process

## 📋 Usage

### Production Deployment
```bash
# Must be on main branch
git checkout main
git pull origin main

# Deploy to production
./deploy.sh

# Accesses: https://petcare.brunadev.com
```

### Staging Deployment

#### Deploy Current Branch
```bash
# On your feature branch
git checkout feature/ai-product-intelligence

# Deploy to staging (current branch)
./deploy.sh --staging

# Accesses: http://localhost:8001
```

#### Deploy Specific Branch
```bash
# From any branch, deploy another specific branch
./deploy.sh --staging feature/new-feature

# Automatically checks out and deploys feature/new-feature
# Accesses: http://localhost:8001
```

## 🔍 What's Different Between Modes?

### Production Mode (`./deploy.sh`)
- ✅ Branch: `main` (enforced)
- ✅ Compose: `docker-compose.prod.yml`
- ✅ URL: https://petcare.brunadev.com
- ✅ Port: 80/443
- ✅ Database: `postgres_data` volume

### Staging Mode (`./deploy.sh --staging`)
- ✅ Branch: Any (current or specified)
- ✅ Compose: `docker-compose.prod.yml` + `docker-compose.staging-override.yml`
- ✅ URL: http://localhost:8001
- ✅ Port: 8001
- ✅ Database: `postgres_data_staging` volume

### What's IDENTICAL? (The Important Part!)
- ✅ **Deployment steps** - Build → Test → Deploy → Migrate → Verify
- ✅ **Docker images** - Same Dockerfile, same build process
- ✅ **Environment config** - Same .env requirements
- ✅ **Validation logic** - Same health checks
- ✅ **Rollback mechanism** - Same error handling
- ✅ **Frontend build** - Same npm build process

## 🚀 Complete Workflow Example

```bash
# 1. Create feature branch
git checkout -b feature/new-ai-feature

# 2. Develop and commit
git add .
git commit -m "feat(ai): add new AI feature"
git push origin feature/new-ai-feature

# 3. Test in staging with EXACT production deployment process
./deploy.sh --staging

# 4. Verify at http://localhost:8001
curl http://localhost:8001/api/v1/status/
# Test UI, API, everything

# 5. If passes, staging deployment succeeded = production will succeed!
#    Clean up staging
docker compose -f docker-compose.prod.yml -f docker-compose.staging-override.yml down -v

# 6. Merge to main
git checkout main
git merge feature/new-ai-feature
git push origin main

# 7. Deploy to production with SAME script
./deploy.sh

# ✅ Confidence: Same script worked in staging, will work in production!
```

## 📊 Comparison Matrix

| Aspect | Production | Staging | Dev |
|--------|------------|---------|-----|
| **Script** | `./deploy.sh` | `./deploy.sh --staging` | `docker compose up` |
| **Branch** | `main` only | Any branch | Any branch |
| **Compose File** | `docker-compose.prod.yml` | `docker-compose.prod.yml` + override | `docker-compose.yml` |
| **Port** | 80/443 | 8001 | 8000 |
| **URL** | petcare.brunadev.com | localhost:8001 | localhost:8000 |
| **Database** | `postgres_data` | `postgres_data_staging` | `postgres_data` (dev) |
| **Process** | ✅ **IDENTICAL** | ✅ **IDENTICAL** | Different (dev mode) |
| **Parity** | Production | ✅ **=Production** | ❌ Dev only |

## 🎯 The Guarantee

```
If staging deployment succeeds → production deployment will succeed
```

**Why?**
- Same script → Same steps → Same process
- Same Docker configs → Same images → Same runtime
- Same validations → Same health checks → Same rollback

**The only differences are intentional and isolated:**
- Port number (to avoid conflicts)
- Volume names (to avoid data conflicts)
- Container names (to avoid naming conflicts)

Everything else is **100% identical**.

## 💡 Best Practices

### ✅ **DO:**
```bash
# Always test in staging first
./deploy.sh --staging feature/my-feature
# Verify it works
# Then merge and deploy to production
./deploy.sh
```

### ❌ **DON'T:**
```bash
# Skip staging and deploy directly to production
git checkout main
git merge feature/untested-feature  # ❌ BAD!
./deploy.sh  # ❌ RISKY!
```

### ✅ **DO:**
```bash
# Use staging for every PR
1. Create feature branch
2. ./deploy.sh --staging  # Test with production process
3. Share http://localhost:8001 for review
4. If passes, merge confidently
```

### ❌ **DON'T:**
```bash
# Trust "works on my machine" without staging
docker compose up  # ❌ Different from production!
# Looks good
git push  # ❌ No production-like testing!
```

## 🔧 Technical Implementation

### Script Logic
```bash
if [ "$STAGING_MODE" = true ]; then
    # Staging-specific settings
    COMPOSE_OVERRIDE="docker-compose.staging-override.yml"
    STAGING_WEB_PORT="8001"
    TARGET_BRANCH="<any-branch>"
else
    # Production settings
    COMPOSE_OVERRIDE=""  # No override
    TARGET_BRANCH="main"  # Enforce main
fi

# ALL OTHER LOGIC IS IDENTICAL
# Build, test, deploy, migrate, verify - SAME CODE PATH
```

### Docker Compose Usage
```bash
# In production mode:
docker compose -f docker-compose.prod.yml up -d

# In staging mode:
docker compose -f docker-compose.prod.yml -f docker-compose.staging-override.yml up -d

# Same base (docker-compose.prod.yml)
# Staging just adds minimal overrides (port, names, volumes)
```

## 📝 Summary

**Key Insight:**
> Staging should test the DEPLOYMENT PROCESS, not just the code.

**The Rule:**
```
ONE script + environment flag = Production Parity
TWO scripts = Config drift = False confidence
```

**Senior Level Practice:**
- ✅ One deployment script with modes
- ✅ Staging tests exact production process
- ✅ If staging succeeds, prod will succeed
- ✅ DRY principle applied to deployments
- ✅ Industry standard for professional teams

## 🎓 Learning Point

This is the difference between junior and senior deployment strategies:

**Junior:** "Let me create a staging script similar to production"
**Senior:** "Let me ensure staging tests the EXACT production deployment"

The second approach is what this implementation provides. ✅
