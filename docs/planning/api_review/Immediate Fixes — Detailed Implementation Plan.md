

## Immediate Fixes — Detailed Implementation Plan

---

### **Fix 1: B6 — Error Envelope Format Mismatch**

**What it fixes:** Exception handlers emit wrong JSON structure that doesn't match [ErrorResponse](cci:2://file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/api/schemas/common.py:49:0-60:47) schema

**Problem:** 
- Current: `{"detail": "...", "error_type": "..."}`
- Schema expects: `{"success": false, "error": "...", "message": "..."}`
- OpenAPI docs don't match actual responses

**Files to modify:**
- [app/api/exceptions.py](cci:7://file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/api/exceptions.py:0:0-0:0)

**Code changes:**

```python
# BEFORE (lines 15-48):
@app.exception_handler(NotFoundError)
async def not_found_exception_handler(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": exc.message, "error_type": "NotFoundError"},
    )

# AFTER:
@app.exception_handler(NotFoundError)
async def not_found_exception_handler(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=404,
        content={"success": False, "error": "NotFoundError", "message": exc.message},
    )
```

Apply same pattern to all 5 handlers (`ValidationError`, `BusinessRuleError`, `ConflictError`, `AuthError`).

---

### **Fix 2: S1 — Remove AUTH_DEBUG Logging**

**What it fixes:** Security risk from debug logs leaking tokens/UIDs at ERROR level

**Problem:** 
- `logger.error("AUTH_DEBUG: ...")` statements in [get_current_user()](cci:1://file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/api/dependencies.py:46:0-83:15)
- Pollutes monitoring/alarming
- Leaks sensitive token prefixes

**Files to modify:**
- [app/api/dependencies.py](cci:7://file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/api/dependencies.py:0:0-0:0)

**Code changes:**

```python
# BEFORE (lines 68-72):
except Exception as e:
    logger.error("AUTH_DEBUG: Supabase JWT validation failed: %s", type(e).__name__)
    raise credentials_exception

# AFTER:
except Exception as e:
    logger.warning("Supabase JWT validation failed: %s", type(e).__name__)
    raise credentials_exception
```

Also remove any other `AUTH_DEBUG` prefixed logs if found.

---

### **Fix 3: B2 — Stop Mutating Input DTOs**

**What it fixes:** Anti-pattern mutating request body DTOs — crashes if frozen, couples layers

**Problem:**
- `body.created_by = current_user.id` mutates input directly
- Same in [transfer_student](cci:1://file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/api/routers/enrollments_router.py:67:0-83:5) (line 78)
- Breaks if `EnrollStudentInput` has `frozen=True`

**Files to modify:**
- [app/api/routers/enrollments_router.py](cci:7://file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/api/routers/enrollments_router.py:0:0-0:0)

**Code changes — Option A (model_copy):**

```python
# BEFORE (lines 31-46):
def enroll_student(
    body: EnrollStudentInput,
    current_user: User = Depends(require_admin),
    svc: EnrollmentService = Depends(get_enrollment_service),
):
    body.created_by = current_user.id
    enrollment, capacity_exceeded = svc.enroll_student(body)
    ...

# AFTER:
def enroll_student(
    body: EnrollStudentInput,
    current_user: User = Depends(require_admin),
    svc: EnrollmentService = Depends(get_enrollment_service),
):
    enrollment_data = body.model_copy(update={"created_by": current_user.id})
    enrollment, capacity_exceeded = svc.enroll_student(enrollment_data)
    ...
```

```python
# BEFORE transfer_student (lines 73-84):
def transfer_student(...):
    body.created_by = current_user.id
    new_enr = svc.transfer_student(body)
    ...

# AFTER:
def transfer_student(...):
    transfer_data = body.model_copy(update={"created_by": current_user.id})
    new_enr = svc.transfer_student(transfer_data)
    ...
```

---

### **Fix 4: B4 — Validate group_id Path vs Body**

**What it fixes:** URL path `group_id` ignored — body could specify different group, misleading API

**Problem:**
- `@router.post("/academics/groups/{group_id}/sessions")` declares path param
- But [svc.add_extra_session(body)](cci:1://file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/api/routers/academics_router.py:201:0-217:5) doesn't use it
- Body could have different `group_id` than URL

**Files to modify:**
- [app/api/routers/academics_router.py](cci:7://file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/api/routers/academics_router.py:0:0-0:0)

**Code changes — Option A (inject from path, remove from body):**

```python
# BEFORE (lines 201-218):
@router.post("/academics/groups/{group_id}/sessions")
def add_extra_session(
    group_id: int,
    body: AddExtraSessionInput,
    _user: User = Depends(require_admin),
    svc: SessionService = Depends(get_session_service),
):
    session = svc.add_extra_session(body)
    ...

# AFTER:
@router.post("/academics/groups/{group_id}/sessions")
def add_extra_session(
    group_id: int,
    body: AddExtraSessionInput,
    _user: User = Depends(require_admin),
    svc: SessionService = Depends(get_session_service),
):
    # Validate path matches body, or inject from path
    if hasattr(body, 'group_id') and body.group_id != group_id:
        raise HTTPException(
            status_code=422,
            detail=f"Path group_id ({group_id}) does not match body group_id ({body.group_id})"
        )
    # Or: override body with path param
    session_data = body.model_copy(update={"group_id": group_id})
    session = svc.add_extra_session(session_data)
    ...
```

**Alternative:** If `AddExtraSessionInput` shouldn't have `group_id`, remove it from the schema entirely and always use path param.

---

### **Fix 5: S4 — Stub Endpoint Returns Fake Success**

**What it fixes:** Misleading API that pretends to register teams but does nothing

**Problem:**
- `POST /competitions/register` returns fake success response
- API consumers think registration worked
- Should return `501 Not Implemented` or be removed

**Files to modify:**
- [app/api/routers/competitions_router.py](cci:7://file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/api/routers/competitions_router.py:0:0-0:0)

**Code changes — Option A (return 501):**

```python
# BEFORE (lines 42-56):
@router.post(
    "/competitions/register",
    response_model=ApiResponse[Any],
    summary="Register a team for a competition (Stub)",
)
def register_team(body: RegisterTeamInputStub, _user: User = Depends(require_admin)):
    return ApiResponse(
        data={"status": "queued", "team": body.team_name},
        message="Team registration stub.",
    )

# AFTER:
from fastapi import HTTPException

@router.post(
    "/competitions/register",
    status_code=501,
    summary="Register a team for a competition (Not Implemented)",
)
def register_team(body: RegisterTeamInputStub, _user: User = Depends(require_admin)):
    raise HTTPException(
        status_code=501,
        detail="Team registration endpoint not yet implemented. Use Streamlit UI for team registration."
    )
```

**Option B:** Comment out the endpoint entirely with `# TODO: Implement in post-launch sprint`.

---

### **Fix 6: Q4 — Verify HTTPBearer auto_error Setting**

**What it fixes:** Debug change `auto_error=False` may still be present

**Problem:**
- Was changed to `False` during debugging
- Should be `True` for automatic 401 on missing auth

**Files to check:**
- [app/api/dependencies.py](cci:7://file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/api/dependencies.py:0:0-0:0) (line 38)

**Current status:** Already `auto_error=True` in latest code — **no fix needed**, just verify.

If found `False`:

```python
# BEFORE:
http_bearer = HTTPBearer(auto_error=False)

# AFTER:
http_bearer = HTTPBearer(auto_error=True)
```

---

## Summary Table

| Fix | File(s) | Lines | Effort |
|:---|:--------|:------|:-------|
| **B6** | [app/api/exceptions.py](cci:7://file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/api/exceptions.py:0:0-0:0) | 15-48 | 15 min |
| **S1** | [app/api/dependencies.py](cci:7://file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/api/dependencies.py:0:0-0:0) | ~71 | 5 min |
| **B2** | [app/api/routers/enrollments_router.py](cci:7://file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/api/routers/enrollments_router.py:0:0-0:0) | 36, 78 | 10 min |
| **B4** | [app/api/routers/academics_router.py](cci:7://file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/api/routers/academics_router.py:0:0-0:0) | 208-214 | 10 min |
| **S4** | [app/api/routers/competitions_router.py](cci:7://file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/api/routers/competitions_router.py:0:0-0:0) | 42-56 | 5 min |
| **Q4** | [app/api/dependencies.py](cci:7://file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/api/dependencies.py:0:0-0:0) | 38 | Verify only |

**Total estimated time: ~45 minutes**

---