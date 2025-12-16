# Development Workflow Guide

## 🎯 Philosophy: Right Tool for the Job

### Development vs Deployment

**Development** (local):
- **Goal**: Fast iteration, hot reload, experimentation
- **Tool**: `Makefile` + `docker-compose.yml`
- **Speed**: Immediate (no validation overhead)

**Deployment** (staging/production):
- **Goal**: Robust, validated, zero-downtime deployment
- **Tool**: `deploy.sh`
- **Speed**: Slower (backups, checks, rollback protection)

## 🚀 Quick Start

### First Time Setup
```bash
make dev              # Start containers
make migrate          # Run migrations
make createsuperuser  # Create admin user
```

Or all at once:
```bash
make quickstart
```

### Daily Development
```bash
# Start working
make dev

# Make code changes (hot reload automatic!)

# Run tests when ready
make test

# Check code quality
make check

# Stop when done
make stop
```

## 📋 Common Commands

### Development Environment
```bash
make dev              # Start dev environment
make dev-build        # Rebuild and start
make stop             # Stop containers
make restart          # Restart containers
make logs             # View all logs
make logs SERVICE=web # View specific service logs
make ps               # Show running containers
make stats            # Show resource usage
```

### Shell Access
```bash
make shell            # Django shell
make bash             # Bash in web container
make zsh              # Zsh in web container (with autocomplete!)
make db-shell         # PostgreSQL shell
```

### Database
```bash
make migrate          # Run migrations
make makemigrations   # Create migrations
make makemigrations APP=pets  # For specific app
make migrate-check    # Check for pending migrations
make createsuperuser  # Create admin user
make db-backup        # Backup database
make db-reset         # Reset database (DANGER!)
```

### Testing
```bash
make test             # Run all tests
make test-cov         # With coverage report
make test-app APP=pets  # Test specific app
```

### Code Quality
```bash
make check            # Run all checks (lint + types + security)
make lint             # Run ruff linter
make lint-fix         # Auto-fix linting issues
make format           # Format code
make typecheck        # Run mypy
make security         # Security checks
```

### Frontend
```bash
make frontend-install # Install npm dependencies
make frontend-build   # Build for production
make frontend-dev     # Run in dev mode
```

### Deployment
```bash
make deploy-staging   # Deploy current branch to staging
make deploy-staging-branch BRANCH=feature/xyz  # Deploy specific branch
make deploy-prod      # Deploy to production (main only)
```

### Cleanup
```bash
make clean            # Clean containers and caches
make deep-clean       # Also remove node_modules, chroma_db
```

## 🎯 Workflows

### Feature Development
```bash
# 1. Create branch
git checkout -b feature/new-feature

# 2. Start dev environment
make dev

# 3. Make changes (hot reload automatic)

# 4. Test regularly
make test

# 5. Check before commit
make check

# 6. Test in staging before merge
make deploy-staging

# 7. Verify at http://localhost:8001

# 8. If good, merge and deploy to prod
git checkout main
git merge feature/new-feature
make deploy-prod
```

### Bug Fix
```bash
# 1. Reproduce bug locally
make dev
make logs SERVICE=web

# 2. Fix and test
make test-app APP=affected_app

# 3. Verify fix
make deploy-staging

# 4. Deploy to prod
git checkout main
make deploy-prod
```

### Database Changes
```bash
# 1. Create migration
make makemigrations APP=pets

# 2. Review migration file

# 3. Test migration
make migrate

# 4. Test in staging
make deploy-staging

# 5. Deploy to prod
make deploy-prod
```

## 🔍 Debugging

### View Logs
```bash
# All services
make logs

# Specific service
make logs SERVICE=web
make logs SERVICE=db
make logs SERVICE=celery_worker
```

### Interactive Debugging
```bash
# Django shell
make shell

# Container bash
make bash

# Database shell
make db-shell
```

### Check Container Status
```bash
make ps              # List containers
make stats           # Resource usage
```

## 💡 Tips & Tricks

### Fast Iteration
```bash
# Don't restart containers for code changes!
# Just edit files, Django auto-reloads
vim src/apps/pets/views.py  # Edit
# Refresh browser → changes applied!
```

### Before Committing
```bash
# Always run checks
make check

# Format code
make format

# Run tests
make test
```

### Database Issues
```bash
# Backup first!
make db-backup

# Then reset if needed
make db-reset
```

### Clean Start
```bash
# Full clean slate
make deep-clean
make dev
make migrate
make createsuperuser
```

## 🆚 Makefile vs deploy.sh

### Use `Makefile` for:
- ✅ Daily development
- ✅ Running tests
- ✅ Code quality checks
- ✅ Database operations
- ✅ Quick iterations

### Use `deploy.sh` for:
- ✅ Staging deployment (test before merge)
- ✅ Production deployment
- ✅ Robust, validated deployments
- ✅ With backups, rollback, health checks

## 🎓 Senior-Level Practices

### ✅ **DO:**
```bash
# Use make for common tasks
make test            # Not: docker compose exec web pytest

# Check before commit
make check

# Test in staging before prod
make deploy-staging

# Keep dev environment clean
make clean  # Weekly
```

### ❌ **DON'T:**
```bash
# Don't use deploy.sh for development
./deploy.sh  # Too slow, too much overhead

# Don't skip tests
git commit -m "fix" && git push  # BAD!

# Don't deploy untested code
git checkout main && ./deploy.sh  # BAD if not tested in staging!
```

## 📊 Command Cheat Sheet

| Task | Command |
|------|---------|
| Start dev | `make dev` |
| Run tests | `make test` |
| Check code | `make check` |
| Format code | `make format` |
| View logs | `make logs` |
| Django shell | `make shell` |
| Run migration | `make migrate` |
| Create migration | `make makemigrations` |
| Deploy staging | `make deploy-staging` |
| Deploy prod | `make deploy-prod` |
| Clean up | `make clean` |
| Help | `make help` |

## 🚨 Emergency Commands

### Containers won't start
```bash
make stop
make clean
make dev-build
```

### Database corrupted
```bash
make db-reset  # DANGER: loses all data!
```

### Out of disk space
```bash
make deep-clean
docker system prune -a --volumes
```

## 📝 Summary

**Development = Speed**
- Use `Makefile` for everything
- Fast iteration with hot reload
- Quick feedback loop

**Deployment = Safety**
- Use `deploy.sh` for staging/production
- Robust with validations
- Backups and rollback

This separation gives you the best of both worlds! 🎯
