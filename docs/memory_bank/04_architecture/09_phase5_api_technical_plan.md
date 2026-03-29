# Phase 5: API Layer Integration

**Execution roadmap (sprints, acceptance, current vs planned):** [phase5_api_execution_roadmap_2026.md](../../reviews/phase5_api_execution_roadmap_2026.md)

This document serves as the architectural blueprint for converting the Techno Terminal backend from a direct-consumption Streamlit application into a highly scalable, stateless REST API using **FastAPI**.

## 1. Context & Motivation
Phases A-D successfully decoupled the monolithic Streamlit logic into strict Domain-Driven `models.py`, `repository.py`, and `service.py` layers. However, parsing heavy state and complex UI logic within Streamlit natively reached its scale ceiling. To support future SaaS clients (Flutter, React, Mobile), the backend must provide a unified JSON interface.

## 2. API Architecture (FastAPI)

### 2.1 The Bootloader (`run_api.py` vs CLI)
- A new Git branch `feature/api-layer` has been created.
- For local development, `run_api.py` operates a programmatic Uvicorn wrapper on port 8000.
- For production, pure CLI Uvicorn commands with multi-worker scaling will be utilized instead of the synchronous `run_api.py`.

### 2.2 Framework & Libraries
- `fastapi` (Routing & Dependency Injection)
- `uvicorn` (Asynchronous ASGI server)
- `python-jose` (Available for JWT utilities; **primary tokens are issued by Supabase**, not a local signing route)
- `pydantic` v2 (Native serialization)

### 2.3 Dependency Injection (DI) & Stateful Mechanics
Stateless REST operations demand that the backend does not "remember" sessions.
Instead, a global `get_current_user()` dependency will intercept `Bearer JWT` tokens on the `Authorization` header on *every single request*. It will decrypt the token, verify the identity against the database, and inject the `User` object directly into the executing route. This ensures concurrent multi-threading safely isolates requests without global state collisions.

## 3. Pre-Requisite: Schema Isolation (DTOs)
**CRITICAL**: The current `app.modules.*.models.py` files primarily define `SQLModel(table=True)` classes.

Routing these raw database tables directly to endpoints creates severe vulnerabilities:
1. **Mass Assignment**: `Student(id: Optional[int])` allows malicious clients to pass `{"id": 1}` mapping over existing rows during POST creation.
2. **Data Leakage**: Returning a `User` raw object via GET leaks `password_hash` strings to the client.

Before routing begins, the module models **must** be refactored using the SQLModel split-inheritance pattern:
- `EntityBase(SQLModel)`: Shared properties
- `Entity(EntityBase, table=True)`: Internal database model
- `EntityCreate(EntityBase)`: POST payload model ensuring no ID mapping
- `EntityRead(EntityBase)`: GET payload model exposing only safe data

We have chosen **Option A: Shared DTOs** for development speed, meaning these Create/Read schemas will reside natively inside the backend modules (e.g., `app.modules.crm.crm_models.py`) and be directly imported by the API.

## 4. Execution Roadmap (The Map Sequence)

1.  **Phase 5.1: Scaffold & Auth** *(largely implemented)*
    - Create `app/api/main.py` configuring CORS to `["*"]` (dev).
    - Create `app/api/dependencies.py` providing `get_db` and `get_current_user`.
    - Create `app/api/exceptions.py` mapping domain errors to HTTP status codes.
    - **Auth:** validate **Supabase-issued** Bearer JWTs and expose **`GET /api/v1/auth/me`** returning a safe **`UserPublic`** DTO — *not* a local `POST /auth/token` issuer (see execution roadmap §3).
2.  **Phase 5.2: CRM Endpoints**
    - `POST /guardians`, `GET /students`.
3.  **Phase 5.3: Academic Endpoints**
    - `POST /groups`, `POST /sessions`, `PUT /attendance`.
4.  **Phase 5.4: Transaction Endpoints**
    - `POST /enrollments` (leveraging strict enrollment business logic).
    - `POST /receipts` (Financial aggregations).
5.  **Phase 5.5: Analytics**
    - BI data streams for client-side Dashboards.
