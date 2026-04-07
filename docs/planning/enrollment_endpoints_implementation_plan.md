# Enrollment Module Endpoints Implementation Plan

## Executive Summary

**Date:** April 3, 2026  
**Module:** Enrollments  
**Current API Endpoints:** 4  
**Service Methods:** 7  
**Missing Endpoints:** 3  
**Target Total:** 7 endpoints

---

## Current State Analysis

### Enrollment Service Methods (7 total)

| Method | Purpose | API Exposed | Endpoint |
|--------|---------|-------------|----------|
| `enroll_student` | Create enrollment | ✅ Yes | `POST /enrollments` |
| `apply_sibling_discount` | Apply discount to enrollment | ❌ **MISSING** | — |
| `transfer_student` | Transfer to new group | ✅ Yes | `POST /enrollments/transfer` |
| `drop_enrollment` | Mark as dropped | ✅ Yes | `DELETE /enrollments/{id}` |
| `complete_enrollment` | Mark as completed | ❌ **MISSING** | — |
| `get_group_roster` | List by group | ❌ **MISSING** | — |
| `get_student_enrollments` | List by student | ✅ Yes | `GET /enrollments/student/{id}` |

### Current API Endpoints (4 total)

1. `POST /enrollments` - Enroll a student
2. `DELETE /enrollments/{id}` - Drop enrollment
3. `POST /enrollments/transfer` - Transfer student
4. `GET /enrollments/student/{student_id}` - Get student history

---

## Missing Endpoints (3)

### 1. Apply Sibling Discount
**Service Method:** `EnrollmentService.apply_sibling_discount(enrollment_id, discount_amount)`  
**Proposed Endpoint:** `POST /enrollments/{enrollment_id}/discount`  
**Purpose:** Apply a discount to an active enrollment (e.g., sibling discount)  
**Use Case:** Enrollments module discount application for family discounts

**Request Schema:** `ApplyDiscountInput`
```python
class ApplyDiscountInput(BaseModel):
    discount_amount: float = 50.0  # Default 50 currency units
```

**Response:** `ApiResponse[EnrollmentPublic]`

**Notes:**
- Only works on active enrollments
- Discount is added to existing `discount_applied` field
- Returns 400 if enrollment not active

---

### 2. Complete Enrollment
**Service Method:** `EnrollmentService.complete_enrollment(enrollment_id)`  
**Proposed Endpoint:** `POST /enrollments/{enrollment_id}/complete`  
**Purpose:** Mark enrollment as completed (level finished)  
**Use Case:** When student finishes all sessions for their level

**Response:** `ApiResponse[EnrollmentPublic]`

**Notes:**
- Changes status from "active" to "completed"
- Preserves enrollment record for history
- Cannot complete already dropped/completed enrollments

---

### 3. Get Group Roster (List Enrollments by Group)
**Service Method:** `EnrollmentService.get_group_roster(group_id, level_number)`  
**Proposed Endpoint:** `GET /enrollments/group/{group_id}`  
**Purpose:** List all active enrollments for a specific group  
**Use Case:** Group management, attendance sheets, roster view

**Query Parameters:**
- `level_number` - integer (optional) - Filter by level

**Response:** `ApiResponse[list[EnrollmentPublic]]`

**Notes:**
- Returns only active enrollments by default
- Optional level_number filter for multi-level groups
- Used by Analytics module (group roster endpoint)

---

## Implementation Phases

### Phase 1: Schemas (15 min)

**Files to modify:**

1. **`app/modules/enrollments/schemas/enrollment_schemas.py`**
   - Add `ApplyDiscountInput`

2. **Update `__init__.py`**
   - `app/modules/enrollments/schemas/__init__.py`

### Phase 2: Router (30 min)

**File:** `app/api/routers/enrollments_router.py`

Add 3 new endpoints:
1. `POST /enrollments/{enrollment_id}/discount`
2. `POST /enrollments/{enrollment_id}/complete`
3. `GET /enrollments/group/{group_id}`

### Phase 3: Documentation Update (20 min)

**File:** `docs/product/api/enrollments.md`
- Add 3 new endpoints
- Add `ApplyDiscountInput` schema
- Update endpoint count from 4 → 7
- Update README.md total from 86 → 89

---

## Detailed Endpoint Specifications

### Endpoint 1: Apply Sibling Discount

```python
@router.post(
    "/enrollments/{enrollment_id}/discount",
    response_model=ApiResponse[EnrollmentPublic],
    summary="Apply sibling discount to enrollment",
)
def apply_discount(
    enrollment_id: int,
    body: ApplyDiscountInput,
    _user: User = Depends(require_admin),
    svc: EnrollmentService = Depends(get_enrollment_service),
):
    enrollment = svc.apply_sibling_discount(enrollment_id, body.discount_amount)
    return ApiResponse(
        data=EnrollmentPublic.model_validate(enrollment),
        message=f"Discount of {body.discount_amount} applied successfully."
    )
```

### Endpoint 2: Complete Enrollment

```python
@router.post(
    "/enrollments/{enrollment_id}/complete",
    response_model=ApiResponse[EnrollmentPublic],
    summary="Mark enrollment as completed",
)
def complete_enrollment(
    enrollment_id: int,
    _user: User = Depends(require_admin),
    svc: EnrollmentService = Depends(get_enrollment_service),
):
    enrollment = svc.complete_enrollment(enrollment_id)
    return ApiResponse(
        data=EnrollmentPublic.model_validate(enrollment),
        message="Enrollment marked as completed."
    )
```

### Endpoint 3: Get Group Roster

```python
@router.get(
    "/enrollments/group/{group_id}",
    response_model=ApiResponse[list[EnrollmentPublic]],
    summary="Get all enrollments for a group (roster)",
)
def get_group_enrollments(
    group_id: int,
    level: int = Query(None, description="Filter by level number"),
    _user: User = Depends(require_any),
    svc: EnrollmentService = Depends(get_enrollment_service),
):
    enrollments = svc.get_group_roster(group_id, level_number=level)
    return ApiResponse(data=[EnrollmentPublic.model_validate(e) for e in enrollments])
```

---

## Testing Commands

```bash
# 1. Apply discount to enrollment
curl -X POST http://localhost:8000/api/v1/enrollments/1/discount \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"discount_amount": 50.0}'

# 2. Complete enrollment
curl -X POST http://localhost:8000/api/v1/enrollments/1/complete \
  -H "Authorization: Bearer $TOKEN"

# 3. Get group roster (all levels)
curl http://localhost:8000/api/v1/enrollments/group/1 \
  -H "Authorization: Bearer $TOKEN"

# 4. Get group roster (specific level)
curl "http://localhost:8000/api/v1/enrollments/group/1?level=2" \
  -H "Authorization: Bearer $TOKEN"
```

---

## File Changes Summary

| File | Action | Lines |
|------|--------|-------|
| `app/modules/enrollments/schemas/enrollment_schemas.py` | Add `ApplyDiscountInput` | +8 |
| `app/modules/enrollments/schemas/__init__.py` | Export new DTO | +1 |
| `app/api/routers/enrollments_router.py` | Add 3 endpoints | +50 |
| `docs/product/api/enrollments.md` | Document new endpoints | +50 |
| `docs/product/api/README.md` | Update counts | +2 |

**Total estimated changes:** ~110 lines across 5 files

---

## Notes

- All service methods already exist - no service layer changes needed
- `get_group_roster` is currently used internally by Analytics module
- Sibling discount endpoint uses existing `apply_sibling_discount` method
- Complete enrollment enables proper enrollment lifecycle management
