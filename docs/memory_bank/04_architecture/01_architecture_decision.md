# Architectural Pattern Comparison — Techno Kids Web Application

## The Question

Which architectural pattern should we use to organize the Python codebase?

The patterns evaluated are:

1. **Layered (N-Tier)** — organize by technical layer
2. **Vertical Slice** — organize by feature
3. **Module-per-Feature (Monolith with internal modules)** — organize by business domain
4. **Clean Architecture / Hexagonal** — organize by dependency direction

---

## Overview of Patterns

### 1. Layered (N-Tier) Architecture

Organize code by its technical role across the entire application.

```
src/
├── models/          # All 16 SQLModel table definitions
├── repositories/    # All database queries for all tables
├── services/        # All business logic for all features
└── ui/              # All Streamlit pages
```

**How a feature works:**
A single "Enroll Student" feature touches `models/enrollment.py`, `repositories/enrollment_repo.py`, `services/enrollment_service.py`, and `ui/pages/enroll_student.py`.

**Pros:**

- Familiar to most developers — easy to explain the structure
- Clear separation of "database stuff" vs "logic stuff" vs "UI stuff"

**Cons for this project:**

- When building the Enrollment feature, you jump between 4 different folders
- `services/` grows to 20+ files covering completely unrelated domains (Finance and CRM in the same folder)
- Coupling within a layer becomes invisible — `enrollment_service.py` might import from `guardian_service.py` in ways that are hard to track

**Verdict for Techno Kids:** Works fine at small scale, but starts to hide complexity as the project grows.

---

### 2. Vertical Slice Architecture

Organize code by *feature*. Each feature is a self-contained folder.

```
src/
├── features/
│   ├── student_registration/
│   │   ├── models.py
│   │   ├── repo.py
│   │   ├── service.py
│   │   └── page.py
│   ├── attendance/
│   │   ├── models.py     (reuses db models from shared/)
│   │   ├── repo.py
│   │   ├── service.py
│   │   └── page.py
│   └── finance/
│       ├── ...
└── shared/
    ├── db.py             # Database connection
    └── db_models.py      # All 16 SQLModel table definitions
```

**How a feature works:**
To build "Mark Attendance", you only ever open `features/attendance/`. Everything that feature needs is in one place.

**Pros:**

- Excellent for complex features — you see all logic for that feature in one folder
- Adding a new feature is easy (add a folder, don't touch others)
- Very clean when features are truly independent

**Cons for this project:**

- Techno Kids features are *not* truly independent: Attendance depends on Enrollments which depends on Students which depends on Guardians. A vertical slice structure would duplicate code or require heavy imports between feature folders, breaking the isolation benefit.
- 16 tables imply ~12 features — that is manageable, but the `shared/` folder (where re-used domain models live) grows and becomes a second "flat layer", partially defeating the purpose.

**Verdict for Techno Kids:** Vertical Slice shines when features are loosely coupled (e.g., e-commerce: Cart, Checkout, Orders are independent). For a tightly-coupled CRM like this, it adds indirection without much benefit.

---

### 3. Module-per-Feature (Domain Modules) 🏆 *Best Fit*

Organize code by **business domain**, where each domain is a Python package containing models, a repository, and a service. The UI layer is separate.

```
src/
├── modules/
│   ├── crm/              # Guardians + Students (same domain)
│   │   ├── models.py
│   │   ├── repository.py
│   │   └── service.py
│   ├── academics/        # Courses + Groups + Sessions
│   │   ├── models.py
│   │   ├── repository.py
│   │   └── service.py
│   ├── enrollments/
│   │   ├── models.py
│   │   ├── repository.py
│   │   └── service.py
│   ├── attendance/
│   │   ├── models.py
│   │   ├── repository.py
│   │   └── service.py
│   ├── finance/          # Receipts + Payments + Balances
│   │   ├── models.py
│   │   ├── repository.py
│   │   └── service.py
│   └── competitions/     # Competitions + Teams + Members
│       ├── models.py
│       ├── repository.py
│       └── service.py
├── ui/
│   ├── main.py           # Streamlit sidebar + routing
│   └── pages/            # 1 page per domain module
└── db/
    ├── connection.py     # Shared DB session factory
    └── base.py           # SQLModel shared Base
```

**How a feature works:**
"Process a Payment" is entirely in `modules/finance/`. It imports `modules/enrollments/` to validate the enrollment exists. Dependencies between modules are explicit and intentional, just like importing a Python package.

**Pros for this project:**

- Perfectly matches the 6 business domains we already defined in the Development Strategy
- Each module has exactly 3 files: `models`, `repository`, `service`. Simple, predictable, consistent.
- Dependencies between domains are explicit and easy to reason about (Finance imports from Enrollments; Enrollments imports from CRM)
- Streamlit UI just imports `from modules.finance.service import process_payment` — completely direct and readable
- When a FastAPI layer is added later, `api/routes/finance.py` just imports the same service
- No ceremony: no interfaces, no dependency injection containers, no abstract base classes

**Cons:**

- A module's `repo.py` may need 15-20 query functions if the domain is large. This is manageable but worth monitoring.

**Verdict for Techno Kids:** ✅ This is the right pattern. It matches our 6-phase roadmap exactly, keeps the code predictable and simple, and scales cleanly to a future API layer.

---

### 4. Clean Architecture / Hexagonal

Organizes code around "ports" (interfaces) and "adapters" (implementations), with a purely abstract core that doesn't depend on any framework.

```
src/
├── domain/           # Pure Python entities, zero dependencies
├── application/      # Use cases, pure business logic
├── infrastructure/   # DB adapters, SQLAlchemy implementations
└── presentation/     # Streamlit / FastAPI adapters
```

**Pros:**

- Theoretically perfect separation: the domain has zero knowledge of SQLAlchemy or Streamlit
- Extremely testable in isolation

**Cons for this project:**

- Massive overhead for a small team: requires abstract Interfaces (Protocols in Python), Dependency Injection, and careful "inversion of control"
- The overhead of defining interfaces for 16 DB repositories is not justified
- For a PostgreSQL-centered application like this, the "DB Adapter" is unlikely to ever be swapped for a different database, nullifying the primary benefit
- Builds complex code structures that require significantly more time to write and understand

**Verdict for Techno Kids:** Over-engineered. The cognitive overhead is not justified at this stage and contradicts the "simple and direct" philosophy.

---

## Side-by-Side Comparison

| Criterion | Layered | Vertical Slice | Module-per-Feature | Clean Architecture |
|---|---|---|---|---|
| **Simplicity** | ✅ High | ✅ High | ✅ High | ❌ Low |
| **Navigability** | ⚠️ Medium | ✅ High | ✅ High | ⚠️ Medium |
| **Fits tightly coupled entities** | ✅ Yes | ❌ No | ✅ Yes | ✅ Yes |
| **Reflects business domains** | ❌ No | ⚠️ Partially | ✅ Yes | ✅ Yes |
| **Easy to add future API** | ⚠️ Workable | ✅ Yes | ✅ Yes | ✅ Yes |
| **Predictable file structure** | ✅ Yes | ⚠️ Varies | ✅ Yes (3 files/module) | ❌ No |
| **Boilerplate overhead** | Low | Low | Low | **High** |
| **Right size for this project** | ✅ Yes | ⚠️ Marginal | ✅ Yes | ❌ No |

---

## Recommendation: Module-per-Feature

The **Module-per-Feature** approach is the best fit. It gives us:

- A simple, predictable structure (every module has `models.py`, `repository.py`, `service.py`)
- Natural alignment with our 6 business domains (CRM, Academics, Enrollments, Attendance, Finance, Competitions)
- Clean import semantics (`from modules.finance.service import process_payment`)
- Zero framework-specific coupling in the service layer — the FastAPI layer later is trivial to add

The directory structure this implies is already reflected in the SDLC Architecture document and the 6-phase Development Strategy.
