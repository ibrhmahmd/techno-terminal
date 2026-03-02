# Database Session Management — Discussion & Decision

## The Core Concepts

### Engine vs Session vs Connection

```
Engine (singleton, created once at startup)
  └── Connection Pool (maintains N open TCP connections to PostgreSQL)
        └── Session (unit-of-work, borrows a connection when needed)
              └── Transaction (begins on first query, ends on commit/rollback)
```

- **Engine:** Created once. Holds the pool. Costs ~50ms to create (TCP handshake × pool_size).
- **Connection:** A real TCP socket to PostgreSQL. Expensive to create (handshake), cheap to reuse via pool.
- **Session:** A Python object tracking state (identity map, pending changes). Lightweight. Many can exist simultaneously, each borrowing a connection from the pool when active.
- **Transaction:** Begins automatically on the first query inside a session. All reads/writes inside are atomic. Committed or rolled back when the session closes.

---

## Three Lifecycle Approaches (Detailed)

### Approach A: Per-Operation (Recommended)

```python
@contextmanager
def get_session():
    with Session(get_engine()) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise

# In service:
def create_student(data: StudentCreate) -> Student:
    with get_session() as session:              # borrows connection
        student = repo.create_student(session, data)
    return student                             # connection returned to pool here
```

**Lifecycle per call:**

1. `with get_session()` → borrows a connection from the pool (< 1ms if pool not exhausted)
2. Transaction begins implicitly on first SQL statement
3. Repo functions execute SQL, ORM loads objects into session identity map
4. `session.commit()` → flushes all pending changes, commits transaction to DB, releases connection back to pool
5. On exception: `session.rollback()` → rolls back transaction, still releases connection

**Performance characteristics:**

- One connection borrowed per service call
- Connection held for the duration of the service function (typically 1–50ms)
- Pool immediately reuses the connection for the next caller

**Multi-operation atomicity:**

```python
# One session, two repo calls — all or nothing
def enroll_student(student_id, group_id, amount):
    with get_session() as session:
        enrollment = repo.create_enrollment(session, student_id, group_id, amount)
        repo.create_audit_log(session, action="enrollment", ref_id=enrollment.id)
    # Both committed together, or both rolled back if either fails
```

✅ This is the correct approach. The context manager guarantees cleanup even on exception.

---

### Approach B: One Session Per Streamlit Re-run (Anti-pattern)

```python
# WRONG — do not do this
session = Session(engine)  # created at module level or page top

def create_student(data):
    student = repo.create_student(session, data)
    session.commit()
    # session never closed → connection never returned to pool
```

**Problems:**

- Streamlit re-runs import the module each time in some configurations — session may be re-created but previous one not closed
- If user navigates away mid-operation, the session hangs open
- After N page views, the pool is exhausted (`QueuePool limit exceeded` errors)
- Uncommitted changes from a failed operation pollute the next re-run

❌ This approach causes connection leaks in production.

---

### Approach C: Scoped/Thread-Local Sessions

```python
from sqlalchemy.orm import scoped_session, sessionmaker

ScopedSession = scoped_session(sessionmaker(bind=engine))

def create_student(data):
    session = ScopedSession()     # returns the session for this thread
    student = repo.create_student(session, data)
    session.commit()
    ScopedSession.remove()        # MUST call this explicitly
```

**How it works:** SQLAlchemy maintains one session per thread in a thread-local registry. The session persists for the lifetime of the thread unless explicitly removed.

**In Streamlit:** Each user is typically served by one thread. But since Streamlit re-uses threads across users in its thread pool, a session from User A could leak into User B if `ScopedSession.remove()` is not always called.

**In FastAPI:** Works correctly with proper dependency injection — FastAPI ensures `remove()` is called after each request.

⚠️ Over-complex for Streamlit. Correct for FastAPI — but we'll set that up when building the API layer.

---

## Recommended Configuration

```python
# app/db/connection.py

import os
from contextlib import contextmanager
from sqlmodel import create_engine, Session

_engine = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            os.environ["DATABASE_URL"],
            pool_size=5,         # Persistent connections kept alive
            max_overflow=5,      # Extra connections under burst (max 10 total)
            pool_timeout=30,     # Seconds to wait for a connection before error
            pool_pre_ping=True,  # Test connection health before use
            pool_recycle=1800,   # Recycle connections every 30 min (avoid stale TCP)
            echo=False,          # Set True during development to log all SQL
        )
    return _engine

@contextmanager
def get_session():
    with Session(get_engine()) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
```

---

## Pool Sizing Rationale

| Setting | Value | Reasoning |
|---|---|---|
| `pool_size` | 5 | Supports 5 simultaneous admin DB operations |
| `max_overflow` | 5 | Handles bursts (e.g., batch attendance marking + payment entry simultaneously) |
| `pool_timeout` | 30 | 30s wait before erroring — prevents silent hangs |
| `pool_pre_ping` | True | PostgreSQL drops idle connections after `tcp_keepalives_idle` — pre-ping prevents `OperationalError` on stale connections |
| `pool_recycle` | 1800 | Connections older than 30 min are replaced; prevents issues with PostgreSQL's `idle_in_transaction_session_timeout` |

---

## When a Session Should NOT Auto-Commit

The context manager always commits on exit. However, some service operations need explicit control:

```python
# Multi-step operation where intermediate state should not be visible
def transfer_enrollment(from_id, to_group_id):
    with get_session() as session:
        old = repo.get_enrollment(session, from_id)
        repo.update_status(session, from_id, "transferred")    # step 1
        new = repo.create_enrollment(session, to_group_id)    # step 2
        # BOTH steps committed together at end of `with` block
        # If step 2 fails, step 1 is rolled back too
    return new
```

This is the key strength of the per-operation context manager — multi-step operations inside one `with get_session()` block are automatically atomic.

---

## Future: FastAPI Session Management

When the API layer is built, FastAPI uses dependency injection for sessions:

```python
# api/deps.py
from app.db.connection import get_session

def db_session():
    """FastAPI dependency — provides a session per request."""
    with get_session() as session:
        yield session

# api/routes/students.py
@router.post("/students")
def create(data: StudentCreate, session = Depends(db_session)):
    return student_service.create_student(data)
```

The `modules/` services will need a small adaptation at that point: accept an optional `session` parameter so the FastAPI route can pass in the request-scoped session. For now, Streamlit services open their own sessions internally.

---

## Summary

| Decision | Choice | Reason |
|---|---|---|
| Session lifecycle | Per-operation context manager | Safe for Streamlit re-runs, no leaks |
| Pool size | 5 + 5 overflow | Appropriate for 5–10 concurrent admins |
| Pool health | `pool_pre_ping=True` + `pool_recycle=1800` | Prevents stale connection errors in production |
| Multi-step atomicity | Single `with get_session()` block per logical operation | All steps commit or roll back together |
| FastAPI future | `Depends(db_session)` wrapping the same context manager | Zero code change in `modules/` |
