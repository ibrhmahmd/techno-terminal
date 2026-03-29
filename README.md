# Techno Terminal — CRM & Operations System

Internal admin system for Techno Terminal / Techno Future KFS tech education center.

## Stack

- **UI:** Streamlit (MVP delivery layer)
- **Core:** Python N-Tier (modules: crm, academics, enrollments, attendance, finance, competitions)
- **DB:** PostgreSQL 15+
- **ORM:** SQLModel

## Project Structure

```
app/
├── modules/        # Core business logic (service + repository + models per domain)
├── ui/             # Streamlit delivery layer
├── api/            # Future FastAPI delivery layer
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
   python run_app.py
   ```

## Development Phases

| Phase | Status | Description |
|---|---|---|
| Phase 1 | 🔄 In Progress | Core Foundation & Security (Auth, DB, UI Shell) |
| Phase 2 | ⏳ Pending | CRM Core (Parents, Students, Courses, Groups) |
| Phase 3 | ⏳ Pending | Daily Operations (Enrollments, Sessions, Attendance) |
| Phase 4 | ⏳ Pending | Financial Ledger (Receipts, Payments, Balances) |
| Phase 5 | ⏳ Pending | Competitions & Teams |
| Phase 6 | ⏳ Pending | Reporting & Analytics |
