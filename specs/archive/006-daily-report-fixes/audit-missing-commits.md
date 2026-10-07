# Audit Report: Missing `session.commit()` in Service Write Methods

**Date**: 2026-05-14  
**Scope**: All `app/modules/` service files using `get_session()` for write operations  
**Pattern**: `get_session()` context manager — callers **must** `session.commit()` before exit  
**Risk**: Data silently lost — API returns 2xx but DB transaction rolled back

---

## Root Cause Analysis

### `get_session()` contract (app/db/connection.py:35-46)

```python
@contextmanager
def get_session():
    with Session(get_engine(), expire_on_commit=False) as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
```

On **normal** exit, `Session.__exit__` calls `Session.close()`, which rolls back any uncommitted transaction. The docstring states: *"Caller is responsible for commit."* Services that do NOT call `session.commit()` silently lose all writes.

### Two DI patterns causing confusion

| Pattern | Services | Session owner | Commit responsibility |
|---------|----------|---------------|-----------------------|
| **UoW-based** | CRM, Finance, HR | `get_db()` Depends or `UnitOfWork.__exit__` | Auto-committed ✅ |
| **Stateless** | Academics, Competitions, Enrollments, Attendance, Analytics | Self-opened via `get_session()` | **Service's responsibility** — often forgotten ❌ |

The **UoW pattern** handles commit automatically, so developers in CRM/Finance/HR never think about it. The **stateless pattern** requires the service to call `session.commit()` — and many don't.

### Why tests don't catch it

Tests like `test_create_course_success` only verify:
- HTTP status code (201)
- Response body (contains the flushed-but-uncommitted object with ID)

They never call `GET` afterward to verify the data actually persisted. The 201 response looks correct even though the data is silently rolled back.

---

## Affected Services

### BUG CONFIRMED ❌ — Missing `session.commit()`

#### 1. Enrollment Service — 5 methods
**File**: `app/modules/enrollments/services/enrollment_service.py`

| Method | Line | Writes | Severity |
|--------|------|--------|----------|
| `enroll_student` | 62 | Creates enrollment, activates WAITING student | **CRITICAL** |
| `apply_sibling_discount` | 131 | Updates discount_applied | Medium |
| `transfer_student` | 152 | Updates old status → "transferred", creates new enrollment | **CRITICAL** |
| `drop_enrollment` | 210 | Updates status → "dropped" | Medium |
| `complete_enrollment` | 252 | Updates status → "completed" | Medium |

#### 2. Team Service — 7 methods
**File**: `app/modules/competitions/services/team_service.py`

| Method | Line | Writes | Severity |
|--------|------|--------|----------|
| `register_team` | 74 | Creates team + members + group participation | **CRITICAL** |
| `update_team` | 312 | Updates team fields | Medium |
| `delete_team` | 318 | Soft deletes team | Medium |
| `restore_team` | 330 | Restores team | Medium |
| `update_placement` | 350 | Updates placement, syncs participation | High |
| `add_team_member_to_existing` | 405 | Adds team member | Medium |
| `remove_team_member` | 446 | Removes team member | Medium |

Note: `pay_competition_fee()` (line 488) uses `FinanceUnitOfWork` for the receipt (committed ✅), but its `get_session()` block at line 534 for `mark_fee_paid()` is **NOT committed** ❌.  
Only `unmark_team_fee_for_payment()` (line 572) correctly calls `db.commit()` ✅.

#### 3. Competition Service — 4 methods
**File**: `app/modules/competitions/services/competition_service.py`

| Method | Line | Writes | Severity |
|--------|------|--------|----------|
| `create_competition` | 31 | Creates competition | **CRITICAL** |
| `update_competition` | 56 | Updates competition fields | Medium |
| `delete_competition` | 61 | Soft deletes competition | Medium |
| `restore_competition` | 72 | Restores competition | Medium |

#### 4. Course Service — FIXED ✅
**File**: `app/modules/academics/course/service.py`
- `add_new_course()` — FIXED (added commit + refresh at lines 32-33)
- `update_course_price()` — FIXED (added commit + refresh at lines 43-44)

### CLEAN ✅ — Correctly call `session.commit()`

| Service | File | Methods with commits |
|---------|------|---------------------|
| Academics Session | `session/service.py` | `add_extra_session`, `cancel_session`, `substitute_instructor` |
| Academics Group Core | `group/core/service.py` | `schedule_group`, `archive_group`, `update_group`, `delete_group` |
| Academics Group Lifecycle | `group/lifecycle/service.py` | Progress level, cancel level logic |
| Academics Group Level | `group/level/service.py` | Level CRUD |
| Academics Group Competition | `group/competition/service.py` | Competition participation CRUD |
| Academics Group Details | `group/details/service.py` | Group enrichment |
| Auth | `auth/services/auth_service.py` | User creation, upsert |
| Attendance | `attendance/services/attendance_service.py` | Mark attendance |

### UoW-based (commit managed by UnitOfWork) ✅

| Module | UoW Class | Auto-commit |
|--------|-----------|-------------|
| CRM | `StudentUnitOfWork` | ✅ `__exit__` calls `commit()` on success |
| HR | `HRUnitOfWork` | ✅ `__exit__` calls `commit()` on success |
| Finance | `FinanceUnitOfWork` | ✅ `__exit__` calls `commit()` on success |

---

## Summary

| Module | Write methods | Missing commit | Fix status |
|--------|:------------:|:--------------:|:----------:|
| Academics Course | 3 | 0 | ✅ FIXED |
| Enrollments | 5 | 5 | ❌ NEEDS FIX |
| Competitions — Teams | 9 | 7 | ❌ NEEDS FIX |
| Competitions — Competition | 4 | 4 | ❌ NEEDS FIX |
| **Totals** | **21** | **16** | |

**16 write methods across 3 service files** return 2xx success but silently discard all data.

---

## Recommended Fix

For each affected method, add before the `return` statement:

```python
session.commit()
session.refresh(entity)  # if entity is returned
```

Example fix pattern:

```python
# BEFORE (broken)
with get_session() as session:
    entity = repo.create(session, data)
    return EntityDTO.model_validate(entity)

# AFTER (fixed)
with get_session() as session:
    entity = repo.create(session, data)
    session.commit()
    session.refresh(entity)
    return EntityDTO.model_validate(entity)
```

### Test improvement

Every creation/update test should add a `GET` verification step:

```python
# AFTER the POST:
response = client.post("/api/v1/...", json=payload, headers=admin_headers)
assert response.status_code == 201

# ADD: Verify it actually persisted
get_resp = client.get(f"/api/v1/.../{response.json()['data']['id']}", headers=admin_headers)
assert get_resp.status_code == 200
assert get_resp.json()["data"]["name"] == payload["name"]
```
