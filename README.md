# 🐾 PetCare - Pet Shop Management System

[![Django CI](https://github.com/CFBruna/petcare_project/actions/workflows/ci.yml/badge.svg)](https://github.com/CFBruna/petcare_project/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-94%25-brightgreen)]()
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Django 5.2](https://img.shields.io/badge/django-5.2-green.svg)](https://docs.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Enterprise-grade web application for pet shop management, built with best practices, robust architecture, and production-ready infrastructure on AWS.

**🚀 Live Demo:** [petcare.brunadev.com](http://petcare.brunadev.com) | **📚 API Docs:** [Swagger UI](http://petcare.brunadev.com/api/v1/schema/swagger-ui/)

---

## 🎯 Quick Start

Test the live application deployed on AWS production infrastructure:

### 🔐 Demo Credentials

Email: recrutador@petcare.com  
Password: avaliar123

**Access Points:**
- 🌐 Main Application: [petcare.brunadev.com](http://petcare.brunadev.com)
- 🛠️ Admin Panel: [petcare.brunadev.com/admin](http://petcare.brunadev.com/admin)
- 📖 API Documentation: [Swagger UI](http://petcare.brunadev.com/api/v1/schema/swagger-ui/) | [ReDoc](http://petcare.brunadev.com/api/v1/schema/redoc/)

---

## 🎥 Video Demo

[<img src="https://github.com/user-attachments/assets/71919de7-47a8-465b-83a7-05f1efcfced4" width="100%">](https://youtu.be/hD8qak2FAoQ)

*Click the dashboard cover above to watch demo video.*

---

## 🏭️ Production Architecture (AWS)

This project runs on a modern, scalable cloud infrastructure:

**Infrastructure Components:**
- **Compute:** EC2 instance running containerized application (Docker)
- **Database:** RDS PostgreSQL for reliable, managed data storage
- **Cache & Queue:** ElastiCache Redis for Celery task queue and caching
- **Web Server:** Nginx as reverse proxy and static file server
- **DNS:** Route 53 for domain management
- **Containerization:** Docker & Docker Compose for environment consistency

---

## ✨ Key Features

### 📋 Core Functionality
- **Customer & Pet Management:** Complete registration system for owners and their pets
- **Appointment Scheduling:** Smart booking system with availability checks and service duration
- **Product Catalog:** Manage products, categories, brands, and inventory with batch tracking
- **Promotions Engine:** Manual and automatic promotions based on product expiration dates
- **Point of Sale (POS):** Sales module with automatic inventory updates
- **Dashboard Analytics:** Revenue metrics and appointment overview
- **Scheduled Tasks:** Automated daily sales reports and promotion generation (Celery Beat)

### 🛡️ Technical Highlights
- **94% Test Coverage** with pytest + factory-boy
- **CI/CD Pipeline** with GitHub Actions (lint, type-check, test)
- **Service Layer Architecture** for clean separation of concerns
- **Repository Pattern** for data access abstraction
- **OpenAPI Documentation** with drf-spectacular (Swagger/ReDoc)
- **Asynchronous Tasks** with Celery + Redis
- **Type Safety** with MyPy strict mode
- **Code Quality** enforced by Ruff + pre-commit hooks

---

## 📸 Screenshots

### Dashboard (covers the demo video)
[<img width="100%" alt="Dashboard" src="https://github.com/user-attachments/assets/71919de7-47a8-465b-83a7-05f1efcfced4" />](https://youtu.be/hD8qak2FAoQ)

### API Documentation (Swagger UI)
<img width="100%" alt="Swagger" src="https://github.com/user-attachments/assets/434afee3-6c2a-405c-9df5-0c07f593cdba" />

---

## 🛠️ Tech Stack

**Backend**
- Python 3.12
- Django 5.2
- Django REST Framework 3.16
- Celery 5.4 (task queue)
- Gunicorn (WSGI server)

**Database & Cache**
- PostgreSQL 16
- Redis 7 (Celery broker + cache)

**Infrastructure**
- Docker + Docker Compose
- Nginx (reverse proxy)
- AWS EC2, RDS, ElastiCache, Route 53

**Code Quality & Testing**
- pytest + pytest-django
- factory-boy (test fixtures)
- Ruff (linting)
- MyPy (type checking)
- pre-commit hooks

**API Documentation**
- drf-spectacular (OpenAPI 3.0)

---

## 🚀 Local Development Setup

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Git](https://git-scm.com/)

### Installation Steps

1. **Clone the repository**

```
git clone https://github.com/CFBruna/petcare_project.git
cd petcare_project
```

2. **Set up environment variables**

```
cp .env.example .env
```

> ⚠️ Edit `.env` and fill in required values (especially `SECRET_KEY`)

3. **Build and start containers**

```
docker-compose up --build -d
```

4. **Run database migrations**

```
docker-compose exec web python manage.py migrate
```

5. **Create superuser**

```
docker-compose exec web python manage.py createsuperuser
```

6. **Access the application**
- Admin Panel: `http://127.0.0.1:8000/admin/`
- API Docs: `http://127.0.0.1:8000/api/v1/schema/swagger-ui/`

---

## 🧪 Running Tests

Execute the complete test suite with coverage report:

```
docker-compose exec web pytest --cov
```

With detailed output:

```
docker-compose exec web pytest --cov --cov-report=html -v
```

Run specific test file:

```
docker-compose exec web pytest src/apps/pets/tests.py -v
```

**Coverage Report:** The project maintains **94% test coverage** across all modules.

---

## 📚 API Documentation

The API follows OpenAPI 3.0 specification and provides interactive documentation:

**Local Development:**
- Swagger UI: `http://127.0.0.1:8000/api/v1/schema/swagger-ui/`
- ReDoc: `http://127.0.0.1:8000/api/v1/schema/redoc/`

**Production:**
- Swagger UI: `http://petcare.brunadev.com/api/v1/schema/swagger-ui/`
- ReDoc: `http://petcare.brunadev.com/api/v1/schema/redoc/`

### API Endpoints Overview

| Resource | Endpoint | Methods | Description |
|----------|----------|---------|-------------|
| Customers | `/api/v1/customers/` | GET, POST, PUT, DELETE | Manage pet owners |
| Pets | `/api/v1/pets/` | GET, POST, PUT, DELETE | Manage registered pets |
| Appointments | `/api/v1/appointments/` | GET, POST, PUT, DELETE | Schedule services |
| Products | `/api/v1/products/` | GET, POST, PUT, DELETE | Manage inventory |
| Sales | `/api/v1/sales/` | GET, POST | Process transactions |

---

## 🔄 CI/CD Pipeline

Every push or pull request to `main` triggers an automated pipeline:

1. 📦 Install Dependencies
2. 🔍 Type Check (MyPy)
3. ✨ Lint Code (Ruff)
4. 🧪 Run Tests (pytest) + Coverage Report
5. ✅ Quality Gate: 90%+ coverage required

View workflow: [.github/workflows/ci.yml](.github/workflows/ci.yml)

---

## 📁 Project Structure

    petcare_project/
    ├── src/
    │   ├── apps/
    │   │   ├── accounts/      # Customer & user management
    │   │   ├── pets/          # Pet registration
    │   │   ├── health/        # Health records
    │   │   ├── schedule/      # Appointment system
    │   │   └── store/         # Products, sales, promotions
    │   ├── config/
    │   │   ├── settings/      # Environment-based settings
    │   │   ├── urls.py        # Main URL configuration
    │   │   └── celery.py      # Celery config
    │   └── shared/            # Shared utilities
    ├── .github/workflows/     # CI/CD pipelines
    ├── docker-compose.yml     # Local development
    ├── docker-compose.prod.yml # Production config
    ├── Dockerfile             # Container definition
    └── pytest.ini             # Test configuration

---

## 🌟 Key Learnings & Highlights

This project demonstrates proficiency in:

- ✅ **Clean Architecture:** Service Layer + Repository Pattern for maintainable code
- ✅ **AWS Deployment:** Full production infrastructure with EC2, RDS, ElastiCache
- ✅ **DevOps Practices:** Docker, CI/CD, automated testing, code quality gates
- ✅ **Test-Driven Development:** 94% coverage with unit and integration tests
- ✅ **API Design:** RESTful endpoints with comprehensive OpenAPI documentation
- ✅ **Asynchronous Processing:** Celery for background tasks and scheduled jobs
- ✅ **Type Safety:** MyPy strict mode for better code reliability

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Bruna Menezes**
- GitHub: [@CFBruna](https://github.com/CFBruna)
- LinkedIn: [bruna-c-menezes](https://www.linkedin.com/in/bruna-c-menezes/)
- Email: brunaads.ti@gmail.com

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/CFBruna/petcare_project/issues).

---

**⭐ If you find this project helpful, please give it a star!**