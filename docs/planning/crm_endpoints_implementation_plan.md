# CRM Module Endpoints Implementation Plan

## Executive Summary

**Date:** April 3, 2026  
**Module:** CRM (Customer Relationship Management)  
**Current API Endpoints:** 9  
**Service Methods:** 16  
**Missing Endpoints:** 3  
**Target Total:** 12 endpoints

---

## Current State Analysis

### Parent Service Methods (7 total)

| Method | Purpose | API Exposed | Endpoint |
|--------|---------|-------------|----------|
| `get_parent_by_id` | Get single parent | ✅ Yes | `GET /crm/parents/{id}` |
| `register_parent` | Create new parent | ✅ Yes | `POST /crm/parents` |
| `find_or_create_parent` | Find existing or create | ❌ **MISSING** | — |
| `update_parent` | Update parent fields | ✅ Yes | `PATCH /crm/parents/{id}` |
| `search_parents` | Search by name/phone | ✅ Yes | `GET /crm/parents?q=` |
| `list_all_parents` | Paginated list | ✅ Yes | `GET /crm/parents` |
| `count_parents` | Total count | ✅ Internal | — |

### Student Service Methods (9 total)

| Method | Purpose | API Exposed | Endpoint |
|--------|---------|-------------|----------|
| `register_student` | Create + link parent | ✅ Yes | `POST /crm/students` |
| `get_student_by_id` | Get single student | ✅ Yes | `GET /crm/students/{id}` |
| `get_student_parents` | Get linked parents | ✅ Yes | `GET /crm/students/{id}/parents` |
| `search_students` | Search by name/phone | ✅ Yes | `GET /crm/students?q=` |
| `list_all_students` | Paginated list | ✅ Yes | `GET /crm/students` |
| `count_students` | Total count | ✅ Internal | — |
| `update_student` | Update student fields | ✅ Yes | `PATCH /crm/students/{id}` |
| `find_siblings` | Find student siblings | ❌ **MISSING** | — |
| `get_parent_students` | Get parent's students | ❌ **MISSING** | — |
| `delete_student` | Soft delete | ✅ Yes | `DELETE /crm/students/{id}` |

---

## Missing Endpoints (3)

### 1. Find or Create Parent
**Service Method:** `ParentService.find_or_create_parent()`  
**Proposed Endpoint:** `POST /crm/parents/find-or-create`  
**Purpose:** Check if parent exists by phone, return existing OR create new
**Use Case:** Student registration workflow - prevents duplicate parent entries

**Request Schema:** `FindOrCreateParentInput`
```python
class FindOrCreateParentInput(BaseModel):
    full_name: str
    phone_primary: str
    phone_secondary: Optional[str] = None
    email: Optional[str] = None
    relation: Optional[str] = None
    notes: Optional[str] = None
```

**Response Schema:** `ParentPublic` + `created` flag
```python
class FindOrCreateParentResponse(BaseModel):
    data: ParentPublic
    created: bool  # True if new, False if existing
    message: Optional[str] = None
```

---

### 2. Find Student Siblings
**Service Method:** `StudentService.find_siblings(student_id)`  
**Proposed Endpoint:** `GET /crm/students/{student_id}/siblings`  
**Purpose:** Return all siblings of a student (same parent)
**Use Case:** Sibling discount detection, family view

**Response:** `ApiResponse[list[SiblingInfo]]`
```python
class SiblingInfo(BaseModel):
    student_id: int
    full_name: str
    age: Optional[int] = None
    parent_id: int
    parent_name: str
```

---

### 3. Get Students by Parent
**Service Method:** `StudentService.get_parent_students(parent_id)`  
**Proposed Endpoint:** `GET /crm/parents/{parent_id}/students`  
**Purpose:** Return all students linked to a parent
**Use Case:** Parent detail view, family dashboard

**Response:** `ApiResponse[list[StudentPublic]]`

---

## Implementation Phases

### Phase 1: Schemas (30 min)

**Files to modify:**

1. **`app/api/schemas/crm/parent.py`**
   - Add `FindOrCreateParentInput`
   - Add `FindOrCreateParentResponse`

2. **`app/modules/crm/schemas/parent_schemas.py`**
   - Add `FindOrCreateParentInput` (internal DTO)

3. **`app/api/schemas/crm/student.py`**
   - Add `SiblingInfo` for sibling endpoint response

4. **Update `__init__.py` files**
   - `app/api/schemas/crm/__init__.py`
   - `app/modules/crm/schemas/__init__.py`

### Phase 2: Routers (45 min)

**Files to modify:**

1. **`app/api/routers/crm/parents.py`**
   - Add `POST /crm/parents/find-or-create`
   - Add `GET /crm/parents/{parent_id}/students`

2. **`app/api/routers/crm/students.py`**
   - Add `GET /crm/students/{student_id}/siblings`

### Phase 3: Dependencies Check (15 min)

- Verify `get_parent_service` and `get_student_service` are available in `app/api/dependencies.py`
- No new dependencies needed

### Phase 4: Documentation Update (20 min)

**File:** `docs/product/api/crm.md`
- Add 3 new endpoints
- Update endpoint count from 9 → 12
- Update README.md count from 83 → 86

---

## Detailed Endpoint Specifications

### Endpoint 1: Find or Create Parent

```python
@router.post(
    "/parents/find-or-create",
    response_model=FindOrCreateParentResponse,
    status_code=201,
    summary="Find existing parent by phone or create new",
)
def find_or_create_parent(
    body: FindOrCreateParentInput,
    _user: User = Depends(require_admin),
    svc: ParentService = Depends(get_parent_service),
):
    parent, created = svc.find_or_create_parent(body)
    message = "Parent created." if created else "Existing parent found."
    return FindOrCreateParentResponse(
        data=ParentPublic.model_validate(parent),
        created=created,
        message=message,
    )
```

### Endpoint 2: Get Student Siblings

```python
@router.get(
    "/students/{student_id}/siblings",
    response_model=ApiResponse[list[SiblingInfo]],
    summary="Get all siblings of a student (same parent)",
)
def get_student_siblings(
    student_id: int,
    _user: User = Depends(require_any),
    svc: StudentService = Depends(get_student_service),
):
    siblings = svc.find_siblings(student_id)
    return ApiResponse(data=[SiblingInfo.model_validate(s) for s in siblings])
```

### Endpoint 3: Get Parent's Students

```python
@router.get(
    "/parents/{parent_id}/students",
    response_model=ApiResponse[list[StudentPublic]],
    summary="Get all students linked to a parent",
)
def get_parent_students(
    parent_id: int,
    _user: User = Depends(require_any),
    svc: StudentService = Depends(get_student_service),
):
    students = svc.get_parent_students(parent_id)
    return ApiResponse(data=[StudentPublic.model_validate(s) for s in students])
```

---

## Testing Commands

```bash
# 1. Find or Create Parent (new)
curl -X POST http://localhost:8000/api/v1/crm/parents/find-or-create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Ahmed Hassan",
    "phone_primary": "+201234567890",
    "email": "ahmed@example.com",
    "relation": "Father"
  }'

# 2. Get Student Siblings (new)
curl http://localhost:8000/api/v1/crm/students/1/siblings \
  -H "Authorization: Bearer $TOKEN"

# 3. Get Parent's Students (new)
curl http://localhost:8000/api/v1/crm/parents/1/students \
  -H "Authorization: Bearer $TOKEN"
```

---

## File Changes Summary

| File | Action | Lines |
|------|--------|-------|
| `app/api/schemas/crm/parent.py` | Add schemas | +30 |
| `app/modules/crm/schemas/parent_schemas.py` | Add DTO | +15 |
| `app/api/schemas/crm/student.py` | Add SiblingInfo | +15 |
| `app/api/schemas/crm/__init__.py` | Export new schemas | +3 |
| `app/modules/crm/schemas/__init__.py` | Export new DTO | +2 |
| `app/api/routers/crm/parents.py` | Add 2 endpoints | +45 |
| `app/api/routers/crm/students.py` | Add 1 endpoint | +20 |
| `docs/product/api/crm.md` | Document new endpoints | +60 |
| `docs/product/api/README.md` | Update counts | +2 |

**Total estimated changes:** ~190 lines across 9 files

---

## Notes

- All service methods already exist - no service layer changes needed
- Authentication follows existing pattern (`require_admin` for writes, `require_any` for reads)
- No database schema changes required
- All 3 endpoints follow REST conventions
- Sibling endpoint could be used by enrollment to auto-apply sibling discounts
