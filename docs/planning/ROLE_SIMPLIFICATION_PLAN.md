# Role Simplification Implementation Plan

**Date:** 2026-04-02  
**Objective:** Simplify role system from 4 roles to 2 roles: `admin` and `system_admin`  
**Rationale:** Reduce complexity, eliminate unused instructor/receptionist/manager roles

---

## Executive Summary

### Current State (4 Roles)
- **Database:** `admin`, `instructor`, `system_admin` (3 roles - migration 002 has old constraint)
- **Code:** `admin`, `instructor`, `receptionist`, `manager` (4 roles in constants.py)
- **API Guards:** `require_admin`, `require_instructor`, `require_receptionist`, `require_any`

### Target State (2 Roles)
- **Database:** `admin`, `system_admin` (aligned with migration 002)
- **Code:** `admin`, `system_admin` only
- **API Guards:** `require_admin`, `require_any` only

### Impact Assessment
| Factor | Assessment |
|:---|:---|
| **Files to Change** | ~10-15 files |
| **Breaking Changes** | Yes - users with instructor/receptionist/manager roles will become unauthorized |
| **Time Estimate** | 2-3 hours |
| **Risk Level** | Medium - affects authentication across entire API |

---

## Detailed Implementation Plan

### Phase 1: Update Auth Constants (app/modules/auth/constants.py)

**What it will work on:**
Simplify the UserRole enum to only 2 roles.

**The Problem:**
Current code has 4 roles but only 2 are needed. This creates confusion and maintenance overhead.

**Recommended Solution:**
Replace 4-role enum with 2-role enum.

**Files:**
- `app/modules/auth/constants.py`

**Code Changes:**

```python
# BEFORE
class UserRole(str, Enum):
    ADMIN = "admin"
    INSTRUCTOR = "instructor"
    RECEPTIONIST = "receptionist"
    MANAGER = "manager"

# AFTER
class UserRole(str, Enum):
    ADMIN = "admin"
    SYSTEM_ADMIN = "system_admin"
```

---

### Phase 2: Update Dependencies (app/api/dependencies.py)

**What it will work on:**
Simplify role guards to match new 2-role system.

**The Problem:**
Current guards reference roles that will be removed (instructor, receptionist, manager).

**Recommended Solution:**
Keep only 2 guards:
- `require_admin` - for admin + system_admin
- `require_any` - for any authenticated user

**Files:**
- `app/api/dependencies.py` (lines 111-127)

**Code Changes:**

```python
# BEFORE
def _require_roles(*roles: UserRole):
    role_values = {r.value for r in roles}
    async def _guard(user: User = Depends(get_current_user)) -> User:
        if user.role not in role_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {sorted(role_values)}",
            )
        return user
    return _guard

require_admin = _require_roles(UserRole.ADMIN, UserRole.MANAGER)
require_instructor = _require_roles(UserRole.INSTRUCTOR, UserRole.ADMIN, UserRole.MANAGER)
require_receptionist = _require_roles(UserRole.RECEPTIONIST, UserRole.ADMIN, UserRole.MANAGER)
require_any = get_current_user

# AFTER
def _require_roles(*roles: UserRole):
    """
    Factory that returns a FastAPI dependency enforcing one of the given roles.
    """
    role_values = {r.value for r in roles}

    async def _guard(user: User = Depends(get_current_user)) -> User:
        if user.role not in role_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {sorted(role_values)}",
            )
        return user

    return _guard


# Convenience shortcuts — use these directly in router Depends() calls.
# Admin access: both admin and system_admin can access
require_admin = _require_roles(
    UserRole.ADMIN,
    UserRole.SYSTEM_ADMIN,
)

# Any valid, active, authenticated user (no role check, just valid JWT).
require_any = get_current_user


# DEPRECATED: These will be removed - now all use require_admin
# require_instructor = _require_roles(...)  # REMOVED
# require_receptionist = _require_roles(...)  # REMOVED
```

---

### Phase 3: Update Attendance Router (app/api/routers/attendance_router.py)

**What it will work on:**
Replace `require_instructor` with `require_admin` since instructor role is being removed.

**The Problem:**
This is the ONLY router using `require_instructor`. All attendance operations will now require admin access.

**Recommended Solution:**
Change `require_instructor` → `require_admin`.

**Files:**
- `app/api/routers/attendance_router.py`

**Code Changes:**

```python
# BEFORE
from app.api.dependencies import require_instructor, get_attendance_service

@router.get("/attendance/session/{session_id}")
def get_session_attendance(
    session_id: int,
    current_user: User = Depends(require_instructor),  # ← instructor role
    ...
):
    ...

@router.post("/attendance/session/{session_id}/mark")
def mark_attendance(
    session_id: int,
    body: MarkAttendanceRequest,
    current_user: User = Depends(require_instructor),  # ← instructor role
    ...
):
    ...

# AFTER
from app.api.dependencies import require_admin, get_attendance_service

@router.get("/attendance/session/{session_id}")
def get_session_attendance(
    session_id: int,
    current_user: User = Depends(require_admin),  # ← now requires admin
    ...
):
    ...

@router.post("/attendance/session/{session_id}/mark")
def mark_attendance(
    session_id: int,
    body: MarkAttendanceRequest,
    current_user: User = Depends(require_admin),  # ← now requires admin
    ...
):
    ...
```

**Documentation Update:**
Update the docstring at top of file:
```python
"""
Role policy:
  GET  → require_admin (admin, system_admin)
  POST → require_admin
"""
```

---

### Phase 4: Clean Up References in Other Files

**What it will work on:**
Remove or update references to INSTRUCTOR, RECEPTIONIST, MANAGER constants throughout codebase.

**Files to Check:**

| File | Action | Notes |
|:---|:---|:---|
| `app/api/routers/enrollments_router.py` | No change | Uses `require_admin`, `require_any` only ✅ |
| `app/api/routers/finance_router.py` | No change | Uses `require_admin`, `require_any` only ✅ |
| `app/api/routers/hr_router.py` | No change | Uses `require_admin` only ✅ |
| `app/api/routers/auth_router.py` | No change | Uses `get_current_user` only ✅ |
| `app/api/routers/analytics/*.py` | Check | Likely uses `require_admin` ✅ |
| `app/api/routers/academics/*.py` | Check | Likely uses `require_admin` ✅ |
| `app/api/routers/crm/*.py` | No change | Uses `require_admin`, `require_any` ✅ |
| `app/api/routers/competitions_router.py` | No change | Uses `require_any`, `require_admin` ✅ |

**Files with Legacy References (needs cleanup):**

These files may have references to old roles but don't use them for API guards. They can be cleaned up later as they're mostly UI or internal code:

- `app/ui/components/attendance_grid.py` - May reference instructor concept
- `app/ui/components/group_overview.py` - May reference instructor concept  
- `app/modules/academics/models/group_models.py` - Has `instructor_id` field (keep this - it's employee reference, not role)
- `app/modules/hr/hr_service.py` - May have instructor references

**Important:** The `instructor_id` fields in database tables refer to **employees who are instructors**, not **user roles**. These should NOT be changed - they're foreign keys to the employees table.

---

### Phase 5: Database Migration (if needed)

**What it will work on:**
Update database role constraint to match new 2-role system.

**Current State Check:**
Migration 002 already has:
```sql
CHECK (role IN ('admin', 'instructor', 'system_admin'))
```

But `schema.sql` v3.3 header says:
```sql
-- v3.3: users — Supabase auth (supabase_uid), roles admin/instructor/system_admin
```

**Recommended Solution:**
Option A - Update schema.sql to remove instructor:
```sql
-- v3.4: users — Supabase auth (supabase_uid), roles admin/system_admin
ALTER TABLE users
    ADD CONSTRAINT users_role_check CHECK (
        role IN ('admin', 'system_admin')
    );
```

Option B - Keep DB flexible (recommended for safety):
Keep database constraint allowing `admin`, `instructor`, `system_admin` but code only uses `admin`/`system_admin`. This allows backward compatibility during transition.

**Recommended:** Option B - Don't change DB constraint. The code simplification is sufficient.

**Migration for existing users (if any have instructor/receptionist/manager):**
```sql
-- If any users have old roles, migrate them to admin
UPDATE users 
SET role = 'admin' 
WHERE role IN ('instructor', 'receptionist', 'manager');
```

---

## Files Requiring Changes

| Priority | File | Change Type | Lines |
|:---:|:---|:---|:---:|
| 1 | `app/modules/auth/constants.py` | Modify enum | 9-14 |
| 2 | `app/api/dependencies.py` | Simplify guards | 111-127 |
| 3 | `app/api/routers/attendance_router.py` | Change import & usage | 22, 51, 72 |
| 4 | `docs/planning/BACKLOG.md` | Update documentation | Role references |
| 5 | `docs/MEMORY_BANK.md` | Update documentation | Role references |

---

## Effort & Time Estimation

| Task | Time | Notes |
|:---|:---:|:---|
| Change auth constants | 10 min | Simple enum change |
| Update dependencies.py | 15 min | Remove 2 guards |
| Update attendance_router.py | 10 min | Change imports |
| Test API endpoints | 30 min | Verify auth still works |
| Update documentation | 15 min | BACKLOG.md, MEMORY_BANK.md |
| **Total** | **~1.5 hours** | |

---

## Breaking Changes & Risks

### Breaking Changes

| Scenario | Impact |
|:---|:---|
| Users with `instructor` role | Will get 403 Forbidden on attendance endpoints |
| Users with `receptionist` role | Already not used in API - no impact |
| Users with `manager` role | Already not used in API - no impact |

### Risk Mitigation

**Before deploying:**
1. Check if any users have `instructor`, `receptionist`, or `manager` roles:
   ```sql
   SELECT role, COUNT(*) FROM users GROUP BY role;
   ```

2. If users exist with old roles, migrate them:
   ```sql
   UPDATE users SET role = 'admin' WHERE role IN ('instructor', 'receptionist', 'manager');
   ```

3. Test with existing admin/system_admin users

### Rollback Plan

If issues occur:
1. Revert `app/modules/auth/constants.py`
2. Revert `app/api/dependencies.py`
3. Revert `app/api/routers/attendance_router.py`

All changes are in 3 files - easy rollback.

---

## Testing Checklist

- [ ] `GET /api/v1/attendance/session/{id}` works with admin JWT
- [ ] `POST /api/v1/attendance/session/{id}/mark` works with admin JWT
- [ ] `GET /api/v1/auth/me` returns correct role
- [ ] Swagger UI shows correct auth requirements
- [ ] Old instructor JWTs get 403 (expected)
- [ ] All other endpoints unchanged

---

## Decision Required

**Before proceeding, confirm:**

1. ✅ Are you okay with attendance endpoints requiring admin access (no instructor-only access)?
2. ✅ Should we migrate any existing instructor/receptionist/manager users to admin role?
3. ✅ Do you want to proceed with this simplification?

**Alternative:** Keep 3 roles (admin, system_admin, instructor) if instructors need separate access level.
