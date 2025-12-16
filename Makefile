.PHONY: help dev dev-build stop restart logs shell test migrate makemigrations createsuperuser collectstatic check lint format clean deploy-staging deploy-prod

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m

help: ## Show this help message
	@printf "$(BLUE)PetCare Development Commands$(NC)\n"
	@echo "=============================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

# Development Environment
dev: ## Start development environment
	@printf "$(BLUE)Starting development environment...$(NC)\n"
	docker compose up -d
	@printf "$(GREEN)✓ Development server running at http://localhost:8000$(NC)\n"

dev-build: ## Build and start development environment
	@printf "$(BLUE)Building and starting development...$(NC)\n"
	docker compose up -d --build
	@printf "$(GREEN)✓ Development server running at http://localhost:8000$(NC)\n"

dev-integrated: ## Build frontend, start dev, and integrate (Zero Config Start)
	@printf "$(BLUE)Building frontend integration...$(NC)\n"
	@$(MAKE) frontend-install
	@$(MAKE) frontend-build
	@printf "$(BLUE)Starting containers...$(NC)\n"
	@$(MAKE) dev
	@printf "$(BLUE)Collecting static files...$(NC)\n"
	@# Wait for container to be ready before running exec
	@sleep 5
	@$(MAKE) collectstatic
	@printf "$(GREEN)✓ Integrated environment ready! Access Admin at http://localhost:8000/admin/$(NC)\n"

stop: ## Stop all containers
	@printf "$(YELLOW)Stopping containers...$(NC)\n"
	docker compose down
	@printf "$(GREEN)✓ Containers stopped$(NC)\n"

restart: ## Restart development environment
	@printf "$(BLUE)Restarting...$(NC)\n"
	docker compose restart
	@printf "$(GREEN)✓ Containers restarted$(NC)\n"

logs: ## Show logs (Usage: make logs SERVICE=web)
	@if [ -z "$(SERVICE)" ]; then \
		docker compose logs -f; \
	else \
		docker compose logs -f $(SERVICE); \
	fi

# Shell Access
shell: ## Open Django shell
	docker compose exec web python manage.py shell

bash: ## Open bash shell in web container
	docker compose exec web bash

zsh: ## Open zsh shell in web container (with autocomplete!)
	docker compose exec web zsh

db-shell: ## Open PostgreSQL shell
	docker compose exec db psql -U $$POSTGRES_USER -d $$POSTGRES_DB

# Database Management
migrate: ## Run database migrations
	@printf "$(BLUE)Running migrations...$(NC)\n"
	docker compose exec web python manage.py migrate
	@printf "$(GREEN)✓ Migrations complete$(NC)\n"

makemigrations: ## Create new migrations (Usage: make makemigrations APP=pets)
	@if [ -z "$(APP)" ]; then \
		docker compose exec web python manage.py makemigrations; \
	else \
		docker compose exec web python manage.py makemigrations $(APP); \
	fi

migrate-check: ## Check for missing migrations
	docker compose exec web python manage.py makemigrations --check --dry-run

createsuperuser: ## Create Django superuser
	docker compose exec web python manage.py createsuperuser

# Testing
test: ## Run all tests
	@printf "$(BLUE)Running tests...$(NC)\n"
	docker compose exec web uv run pytest
	@printf "$(GREEN)✓ Tests complete$(NC)\n"

test-cov: ## Run tests with coverage report
	@printf "$(BLUE)Running tests with coverage...$(NC)\n"
	docker compose exec web uv run pytest --cov --cov-report=term-missing
	@printf "$(GREEN)✓ Coverage report generated$(NC)\n"

test-app: ## Run tests for specific app (Usage: make test-app APP=pets)
	@if [ -z "$(APP)" ]; then \
		echo "$(YELLOW)Usage: make test-app APP=pets$(NC)"; \
	else \
		docker compose exec web uv run pytest src/apps/$(APP)/tests/; \
	fi

# Code Quality
check: ## Run all checks (lint + types + security)
	@printf "$(BLUE)Running all checks...$(NC)\n"
	@$(MAKE) lint
	@$(MAKE) typecheck
	@$(MAKE) security
	@printf "$(GREEN)✓ All checks passed$(NC)\n"

precommit: ## Auto-fix and run all checks (format + lint-fix + test + types + security)
	@printf "$(BLUE)Running pre-commit checks with auto-fixes...$(NC)\n"
	@$(MAKE) format
	@$(MAKE) lint-fix
	@$(MAKE) test
	@$(MAKE) typecheck
	@$(MAKE) security
	@printf "$(GREEN)✓ All pre-commit checks passed - ready to commit!$(NC)\n"

ci: ## Simulate CI/CD checks (format-check + lint + test + types + security)
	@printf "$(BLUE)Simulating CI/CD pipeline...$(NC)\n"
	@printf "$(BLUE)1/5: Format check...$(NC)\n"
	@docker compose exec web uv run ruff format --check .
	@printf "$(BLUE)2/5: Linting...$(NC)\n"
	@docker compose exec web uv run ruff check .
	@printf "$(BLUE)3/5: Tests...$(NC)\n"
	@docker compose exec web uv run pytest
	@printf "$(BLUE)4/5: Type checking...$(NC)\n"
	@docker compose exec web uv run mypy .
	@printf "$(BLUE)5/5: Security...$(NC)\n"
	@docker compose exec web uv run bandit -c pyproject.toml -r .
	@printf "$(GREEN)✓ All CI checks passed!$(NC)\n"

lint: ## Run ruff linter
	@printf "$(BLUE)Running ruff...$(NC)\n"
	docker compose exec web uv run ruff check .
	@printf "$(GREEN)✓ Linting complete$(NC)\n"

lint-fix: ## Run ruff with auto-fix
	@printf "$(BLUE)Running ruff with auto-fix...$(NC)\n"
	docker compose exec web uv run ruff check --fix .
	@printf "$(GREEN)✓ Auto-fixes applied$(NC)\n"

format: ## Format code with ruff
	@printf "$(BLUE)Formatting code...$(NC)\n"
	docker compose exec web uv run ruff format .
	@printf "$(GREEN)✓ Code formatted$(NC)\n"

typecheck: ## Run mypy type checker
	@printf "$(BLUE)Running mypy...$(NC)\n"
	docker compose exec web uv run mypy .
	@printf "$(GREEN)✓ Type checking complete$(NC)\n"

security: ## Run security checks (bandit + safety)
	@printf "$(BLUE)Running security checks...$(NC)\n"
	docker compose exec web uv run bandit -c pyproject.toml -r .
	docker compose exec web uv run safety check
	@printf "$(GREEN)✓ Security checks complete$(NC)\n"

# Static Files
collectstatic: ## Collect static files
	docker compose exec web python manage.py collectstatic --noinput

# Frontend
frontend-install: ## Install frontend dependencies
	@printf "$(BLUE)Installing frontend dependencies...$(NC)\n"
	cd frontend && npm install
	@printf "$(GREEN)✓ Frontend dependencies installed$(NC)\n"

frontend-build: ## Build frontend for production
	@printf "$(BLUE)Building frontend...$(NC)\n"
	cd frontend && npm run build
	cd frontend && npx vite build --config vite.admin.config.ts
	@printf "$(GREEN)✓ Frontend built$(NC)\n"

frontend-dev: ## Run frontend in dev mode
	cd frontend && npm run dev

# Deployment
deploy-staging: ## Deploy to staging (any branch)
	@printf "$(BLUE)Deploying to staging...$(NC)\n"
	./deploy.sh --staging
	@printf "$(GREEN)✓ Staging deployment complete$(NC)\n"

deploy-staging-branch: ## Deploy specific branch to staging (Usage: make deploy-staging-branch BRANCH=feature/xyz)
	@if [ -z "$(BRANCH)" ]; then \
		echo "$(YELLOW)Usage: make deploy-staging-branch BRANCH=feature/xyz$(NC)"; \
	else \
		./deploy.sh --staging $(BRANCH); \
	fi

deploy-prod: ## Deploy to production (main branch only)
	@printf "$(BLUE)Deploying to production...$(NC)\n"
	./deploy.sh
	@printf "$(GREEN)✓ Production deployment complete$(NC)\n"

# Cleanup
clean: ## Clean up containers, volumes, and build artifacts
	@printf "$(YELLOW)Cleaning up...$(NC)\n"
	docker compose down -v
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -r {} + 2>/dev/null || true
	@printf "$(GREEN)✓ Cleanup complete$(NC)\n"

deep-clean: clean ## Deep clean (including node_modules and chroma_db)
	@printf "$(YELLOW)Deep cleaning...$(NC)\n"
	rm -rf frontend/node_modules
	rm -rf chroma_db
	rm -rf staticfiles
	@printf "$(GREEN)✓ Deep clean complete$(NC)\n"

# Database Utilities
db-reset: ## Reset database (DANGER: drops all data!)
	@printf "$(YELLOW)WARNING: This will delete ALL data!$(NC)\n"
	@read -p "Are you sure? (y/N): " confirm; \
	if [ "$$confirm" = "y" ]; then \
		docker compose down -v; \
		docker compose up -d db; \
		sleep 5; \
		docker compose up -d; \
		sleep 5; \
		docker compose exec web python manage.py migrate; \
		echo "$(GREEN)✓ Database reset complete$(NC)"; \
	else \
		echo "$(BLUE)Cancelled$(NC)"; \
	fi

db-backup: ## Backup database
	@printf "$(BLUE)Backing up database...$(NC)\n"
	mkdir -p backups
	docker compose exec -T db pg_dump -U $$POSTGRES_USER $$POSTGRES_DB > backups/db-backup-$$(date +%Y%m%d-%H%M%S).sql
	@printf "$(GREEN)✓ Database backed up to backups/$(NC)\n"

# Monitoring
ps: ## Show running containers
	docker compose ps

stats: ## Show container resource usage
	docker compose stats

# Quick Start
quickstart: dev migrate createsuperuser ## Quick start: build, migrate, create superuser
	@printf "$(GREEN)✓ Quickstart complete!$(NC)\n"
	@printf "$(BLUE)Access: http://localhost:8000/admin/$(NC)\n"
