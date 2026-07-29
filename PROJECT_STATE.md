# Project State - AI-Native Enterprise CPQ Platform

## Current Architecture
- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0 (Async), Alembic, Pydantic v2. Domain-Driven Design (DDD) & Clean Architecture (Modular Monolith).
- **Frontend**: Next.js 14+ (App Router), TypeScript, Tailwind CSS, shadcn/ui.
- **Database**: PostgreSQL (normalized, migrations managed via Alembic).

---

## Folder Structure (Planned & Current Setup)
```
/
├── backend/
│   ├── app/
│   │   ├── core/           # Shared database setup, security, config, errors
│   │   ├── domains/        # Domain-driven Modular Monolith layers
│   │   │   ├── auth/       # Auth & RBAC
│   │   │   ├── customer/   # Customer Management
│   │   │   ├── catalog/    # Catalog & Price Books
│   │   │   ├── pricing/    # Pricing Engine
│   │   │   ├── configuration/ # Product Configuration
│   │   │   ├── quotes/     # Quote Builder
│   │   │   ├── approval/   # Approval Workflow
│   │   │   ├── document/   # PDF Generation
│   │   │   ├── email/      # Email Dispatcher
│   │   │   ├── ai/         # Gemini AI Assistant
│   │   │   └── integrations/ # CSV/Excel/Salesforce interfaces
│   │   └── main.py         # Entrypoint
│   ├── alembic/            # Migrations folder
│   ├── alembic.ini
│   └── requirements.txt
├── frontend/               # Next.js Application
└── PROJECT_STATE.md
```

---

## Status of Application Modules
- [x] 1. **Authentication** (Folder/Placeholder created: Yes | Fully implemented: Yes | Forgot & Reset Password: Yes)
- [x] 2. **Customer Management** (Folder/Placeholder created: Yes | Fully implemented: No)
- [x] 3. **Product Catalog** (Folder/Placeholder created: Yes | Fully implemented: No)
- [x] 4. **Pricing Engine** (Folder/Placeholder created: Yes | Fully implemented: No)
- [x] 5. **Product Configuration** (Folder/Placeholder created: Yes | Fully implemented: No)
- [x] 6. **Quote Builder** (Folder/Placeholder created: Yes | Fully implemented: No)
- [x] 7. **Approval Workflow** (Folder/Placeholder created: Yes | Fully implemented: No)
- [x] 8. **PDF Generation** (Folder/Placeholder created: Yes | Fully implemented: No)
- [x] 9. **Email** (Folder/Placeholder created: Yes | Fully implemented: No)
- [x] 10. **AI** (Folder/Placeholder created: Yes | Fully implemented: No)
- [x] 11. **Integrations** (Folder/Placeholder created: Yes | Fully implemented: No)

---

## Architectural Decisions
1. **Modular Monolith**: Run all domains inside a single FastAPI runtime. Ensure clean boundary lines by restricting cross-domain imports to services/repositories (no direct cross-model modifications outside their domains).
2. **Interface Abstraction**: Domain services and repositories inherit from protocols/abstract base classes to support easy testing and replacement.
3. **No Direct Business Logic in Routes**: API routes handle request validation, delegate to services, and format responses.

---

## Dependencies
- **Backend**: `fastapi`, `uvicorn[standard]`, `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `pydantic-settings`, `pydantic[email]`, `pyjwt[crypto]`, `passlib[bcrypt]`, `python-multipart`, `google-genai`
- **Frontend**: Next.js, React, React DOM, Tailwind CSS, lucide-react, clsx, tailwind-merge, @tanstack/react-query, react-hook-form, zod

---

## API Endpoints Map
All API routes are prefixed under `/api/v1` and defined in each domain's `routes.py`:
- **Auth**: `/auth/register` (POST), `/auth/login` (POST), `/auth/me` (GET)
- **Customer**: `/customers/` (GET, POST), `/customers/{customer_id}` (GET, PUT, DELETE), `/customers/{customer_id}/contacts` (POST)
- **Catalog**: `/products` (GET, POST), `/products/{product_id}` (GET), `/categories` (GET, POST), `/price-books` (GET, POST), `/price-books/{price_book_id}/entries` (POST)
- **Pricing**: `/pricing/calculate` (POST), `/pricing/rules` (GET, POST)
- **Configuration**: `/configuration/validate` (POST), `/configuration/rules` (GET, POST)
- **Quotes**: `/quotes/` (GET, POST), `/quotes/{quote_id}` (GET, PUT), `/quotes/{quote_id}/revise` (POST)
- **Approvals**: `/approvals/policies` (GET, POST), `/approvals/submit` (POST), `/approvals/pending` (GET), `/approvals/requests/{request_id}/decide` (POST)
- **Documents**: `/documents/generate` (POST), `/documents/quote/{quote_id}` (GET)
- **Email**: `/emails/send` (POST), `/emails/quote/{quote_id}` (GET)
- **AI**: `/ai/customer-summary` (POST), `/ai/quote-summary` (POST), `/ai/draft-email` (POST), `/ai/recommendations` (POST)
- **Integrations**: `/integrations/import/preview` (POST), `/integrations/salesforce/connect` (POST), `/integrations/salesforce/sync-quote/{quote_id}` (POST), `/integrations/logs` (GET)
