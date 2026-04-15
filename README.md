# Techno Terminal

## Stack

- **UI:** Streamlit (MVP delivery layer), React + Vite + TypeScript (Complete)
- **Core:** Python N-Tier (10 modules: crm, academics, enrollments, attendance, finance, competitions, hr, analytics, auth, shared)
- **DB:** PostgreSQL 15+ (30 tables, 12 views, 21 migrations)
- **ORM:** SQLModel
- **API:** FastAPI with 85+ endpoints across 15 routers (100% Complete)
- **Auth:** Supabase JWT with role-based access control
- **Deployment:** Leapcell with Gunicorn + Uvicorn workers

## Project Structure

```
app/
├── modules/        # Core business logic (10 modules: service + repository + models)
├── ui/             # Streamlit delivery layer
├── api/            # FastAPI delivery layer (15 routers, 85+ endpoints)
└── db/             # Shared DB engine and session factory

db/
└── schema.sql      # PostgreSQL schema definition

docs/
└── memory_bank/    # Architecture decisions, phase plans, business requirements
```

## Setup

1. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and fill in your `DATABASE_URL`.

3. Create the PostgreSQL database and run the schema:

   ```bash
   psql -U postgres -c "CREATE DATABASE techno_kids;"
   psql -U postgres -d techno_kids -f db/schema.sql
   ```

4. Run the application:

   ```bash
   # UI (Streamlit)
   python run_ui.py
   
   # API (FastAPI)
   python run_api.py
   # or: uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## Development Phases

| Phase | Status | Description |
|---|---|---|
| Phase 1 | ✅ Complete | Core Foundation & Security (Auth, DB, UI Shell) |
| Phase 2 | ✅ Complete | CRM Core (Parents, Students, Courses, Groups) |
| Phase 3 | ✅ Complete | Daily Operations (Enrollments, Sessions, Attendance) |
| Phase 4 | ✅ Complete | Financial Ledger (Receipts, Payments, Balances, Triggers) |
| Phase 5 | ✅ Complete | Competitions & Teams |
| Phase 6 | ✅ Complete | Reporting & Analytics (Academic, Financial, BI) |
| Frontend | ✅ Complete | React + Vite + TypeScript + TanStack Query |
| Deployment | ✅ Complete | Leapcell with health checks and monitoring |

## Live Deployment

**API Base URL:** https://techno-terminal-ibrhmahmd2165-00zb1kxm.leapcell.dev/api/v1

**Health Check:** https://techno-terminal-ibrhmahmd2165-00zb1kxm.leapcell.dev/health

## Architecture Highlights

### Design Patterns
- **Repository Pattern:** Pure data access functions
- **Service Layer:** Business logic encapsulation with DI
- **Dependency Injection:** FastAPI `Depends()` for all dependencies
- **DTO Pattern:** Pydantic models for all API I/O
- **Factory Pattern:** Service instantiation per request
- **Strategy Pattern:** Balance calculation algorithms

### Database Features
- **30 Tables** (16 core + 14 history/tracking) with proper relationships and check constraints
- **12 Views** for complex aggregations
- **21 Migrations** with sequential versioning
- **Triggers** for automated balance calculation
- **Hybrid Schema:** `schema.sql` + `migrations/*.sql`
