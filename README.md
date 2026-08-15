# AI-Native Enterprise CPQ Platform

A production-quality, modular monolith Configure, Price, Quote platform with Google Gemini AI-powered workflows and Salesforce CRM integration.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 (Async), Pydantic v2 |
| Database | PostgreSQL 16 |
| Migrations | Alembic |
| Authentication | JWT (HS256) + bcrypt |
| Frontend | Next.js 16, TypeScript, Tailwind CSS |
| State Management | TanStack Query |
| Forms | React Hook Form + Zod |
| AI | Google Gemini API |

---

## Prerequisites

- Python 3.12+
- Node.js 18+
- Docker Desktop (for PostgreSQL) — or a local PostgreSQL 16 installation

---

## Local Development Setup

> A fresh developer can reproduce the complete environment in ~5 minutes without receiving any database dump.

### 1. Clone and configure environment

```bash
git clone https://github.com/your-org/cpq-pricing.git
cd cpq-pricing

# Copy the environment template and fill in your values
cp .env.example backend/.env
nano backend/.env     # set DATABASE_URL and JWT_SECRET at minimum
```

### 2. Start PostgreSQL

```bash
# Option A — Docker (recommended)
docker compose up -d db
# Wait ~5 seconds, then verify:
docker compose ps

# Option B — Local PostgreSQL 16
# Create the database manually:
#   createdb cpq_db
```

### 3. Install Python dependencies

```bash
pip install -r backend/requirements.txt
```

### 4. Run database migrations

```bash
cd backend
python -m alembic upgrade head
cd ..
```

This creates all tables from scratch. No manual SQL required.

### 5. Seed the development environment

```bash
python scripts/seed_dev.py
```

This idempotently creates:
- All permissions and roles (Administrator, Sales Manager, Sales Rep, Executive, Viewer)
- Four development user accounts (one per role)
- Product categories and 14 DEV-* catalog products
- 3 development customers

Running it multiple times is safe — it will never duplicate records.

#### Development Login Credentials

| Role | Email | Password |
|---|---|---|
| Administrator | admin@cpq.local | DevAdmin@2025! |
| Sales Manager | manager@cpq.local | DevManager@2025! |
| Sales Representative | rep@cpq.local | DevRep@2025! |
| Executive | executive@cpq.local | DevExec@2025! |

> **Security**: These credentials are for local development only. Never reuse them in staging or production.

### 6. Start the backend API

```bash
python backend/run.py
```

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health check**: http://localhost:8000/health

### 7. Install and start the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:3000

---


## Project Structure

```
/
├── backend/
│   ├── app/
│   │   ├── core/              # Config, DB, security, exceptions
│   │   └── domains/           # 11 business domains (DDD)
│   │       ├── auth/
│   │       ├── customer/
│   │       ├── catalog/
│   │       ├── pricing/
│   │       ├── configuration/
│   │       ├── quotes/
│   │       ├── approval/
│   │       ├── document/
│   │       ├── email/
│   │       ├── ai/
│   │       └── integrations/
│   ├── alembic/               # Database migrations
│   ├── .env                   # Environment variables (not committed)
│   ├── .env.example           # Template for .env
│   ├── requirements.txt
│   └── run.py                 # Dev server entrypoint
├── frontend/                  # Next.js application
├── docker-compose.yml
├── Makefile
└── PROJECT_STATE.md           # Living implementation tracker
```

---

## API Overview

All endpoints are prefixed under `/api/v1`. Visit `/docs` for the full interactive Swagger UI.

| Domain | Example Endpoints |
|---|---|
| Auth | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` |
| Customers | `GET /customers`, `POST /customers`, `POST /customers/{id}/contacts` |
| Catalog | `GET /products`, `POST /price-books`, `POST /price-books/{id}/entries` |
| Pricing | `POST /pricing/calculate`, `POST /pricing/rules` |
| Configuration | `POST /configuration/validate`, `POST /configuration/rules` |
| Quotes | `POST /quotes`, `POST /quotes/{id}/revise` |
| Approvals | `POST /approvals/submit`, `POST /approvals/requests/{id}/decide` |
| Documents | `POST /documents/generate` |
| Email | `POST /emails/send` |
| AI Copilot | `POST /ai/customer-summary`, `POST /ai/draft-email` |
| Integrations | `POST /integrations/import/preview`, `POST /integrations/salesforce/connect` |

---

## Development Principles

- **No business logic in routes** — routes delegate to services only
- **Domain isolation** — cross-domain communication via service/repository interfaces only
- **Type safety** — Pydantic v2 schemas on all inputs and outputs
- **Async first** — SQLAlchemy async engine, async FastAPI handlers throughout
- **Centralized error handling** — all exceptions caught at app level, consistent JSON format
