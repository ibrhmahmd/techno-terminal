# Academics Module - Missing Endpoints Implementation Plan

## Development Standards & Patterns

Based on existing codebase:
- **Routers**: Split by entity into `app/api/routers/academics/{entity}.py`
- **Public Schemas**: `app/api/schemas/academics/{entity}.py` - Pydantic models with `from_attributes=True`
- **Input DTOs**: `app/modules/academics/schemas/{entity}_schemas.py` - validation with `@field_validator`
- **Dependencies**: Use `require_admin` for mutations, `require_any` for reads
- **Service Factories**: Already exist in `app/api/dependencies.py`
- **Response Pattern**: `ApiResponse[T]` for single items, `PaginatedResponse[T]` for lists

---

## Missing Endpoints Overview

| Priority | Endpoint | Service Method | Router File |
|----------|----------|----------------|-------------|
| 1 | `PATCH /academics/courses/{id}/price` | `update_course_price()` | `courses.py` |
| 2 | `GET /academics/courses/stats` | `get_all_course_stats()` | `courses.py` |
| 3 | `GET /academics/courses/{id}/stats` | `get_course_stats()` | `courses.py` |
| 4 | `GET /academics/courses/{id}/groups` | `get_groups_by_course()` | `courses.py` |
| 5 | `DELETE /academics/groups/{id}` | `delete_group()` | `groups.py` |
| 6 | `GET /academics/groups/enriched` | `get_all_active_groups_enriched()` | `groups.py` |
| 7 | `POST /academics/groups/{id}/generate-sessions` | `generate_level_sessions()` | `groups.py` |

---

## Phase 1: Schemas & DTOs

### 1.1 Update `app/api/schemas/academics/course.py`

Add new public-facing DTOs:

```python
class CourseStatsPublic(BaseModel):
    """Public course statistics from v_course_stats view."""
    course_id: int
    course_name: str
    total_groups: int
    active_groups: int
    total_students_ever: int
    active_students: int

    model_config = {"from_attributes": True}


class UpdateCoursePriceInput(BaseModel):
    """Input for updating course price."""
    new_price: float
```

### 1.2 Update `app/api/schemas/academics/group.py`

Add new public-facing DTOs (most likely already has GroupPublic and GroupListItem):

```python
class EnrichedGroupPublic(BaseModel):
    """Group with joined instructor and course names for display."""
    id: int
    name: str
    course_id: int
    course_name: str
    instructor_id: Optional[int]
    instructor_name: Optional[str]
    level_number: int
    max_capacity: Optional[int]
    default_day: Optional[str]
    default_time_start: Optional[str]
    default_time_end: Optional[str]
    is_active: bool

    model_config = {"from_attributes": True}
```

### 1.3 Update `app/modules/academics/schemas/course_schemas.py`

Add input DTO with validation:

```python
class UpdateCoursePriceInput(BaseModel):
    """Input for CourseService.update_course_price()."""
    new_price: float

    @field_validator("new_price")
    @classmethod
    def price_positive(cls, v: float) -> float:
        validate_positive_amount(v, field="new price")
        return v
```

### 1.4 Update `app/modules/academics/schemas/group_schemas.py`

Add input DTO for generating sessions:

```python
class GenerateLevelSessionsRequest(BaseModel):
    """Input for manual level session generation."""
    level_number: int
    start_date: Optional[date] = None
```

---

## Phase 2: Router Implementations

### 2.1 Update `app/api/routers/academics/courses.py`

Add 4 new endpoints to existing file:

```python
# After existing imports, add:
from app.api.schemas.academics.course import CourseStatsPublic
from app.modules.academics.schemas import UpdateCoursePriceInput
from app.api.schemas.academics.group import EnrichedGroupPublic

# ───────────────────────────────────────────────────────────────────────────────
# Endpoint 1: Update Course Price
# ───────────────────────────────────────────────────────────────────────────────
@router.patch(
    "/academics/courses/{course_id}/price",
    response_model=ApiResponse[CoursePublic],
    summary="Update course price per level",
)
def update_course_price(
    course_id: int,
    body: UpdateCoursePriceInput,
    _user: User = Depends(require_admin),
    svc: CourseService = Depends(get_course_service),
):
    course = svc.update_course_price(course_id, body.new_price)
    return ApiResponse(
        data=CoursePublic.model_validate(course),
        message="Course price updated successfully."
    )

# ───────────────────────────────────────────────────────────────────────────────
# Endpoint 2: Get All Course Stats
# ───────────────────────────────────────────────────────────────────────────────
@router.get(
    "/academics/courses/stats",
    response_model=ApiResponse[list[CourseStatsPublic]],
    summary="Get aggregate stats for all courses",
)
def list_course_stats(
    _user: User = Depends(require_any),
    svc: CourseService = Depends(get_course_service),
):
    stats = svc.get_all_course_stats()
    return ApiResponse(data=[CourseStatsPublic.model_validate(s) for s in stats])

# ───────────────────────────────────────────────────────────────────────────────
# Endpoint 3: Get Single Course Stats
# ───────────────────────────────────────────────────────────────────────────────
@router.get(
    "/academics/courses/{course_id}/stats",
    response_model=ApiResponse[CourseStatsPublic],
    summary="Get aggregate stats for a single course",
)
def get_course_stats(
    course_id: int,
    _user: User = Depends(require_any),
    svc: CourseService = Depends(get_course_service),
):
    stats = svc.get_course_stats(course_id)
    if not stats:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Course {course_id} not found")
    return ApiResponse(data=CourseStatsPublic.model_validate(stats))

# ───────────────────────────────────────────────────────────────────────────────
# Endpoint 4: Get Groups by Course
# ───────────────────────────────────────────────────────────────────────────────
@router.get(
    "/academics/courses/{course_id}/groups",
    response_model=ApiResponse[list[EnrichedGroupPublic]],
    summary="Get all groups for a specific course",
)
def list_course_groups(
    course_id: int,
    _user: User = Depends(require_any),
    group_svc: GroupService = Depends(get_group_service),
):
    groups = group_svc.get_groups_by_course(course_id)
    # Need to enrich with names - either enhance service or do here
    return ApiResponse(data=[EnrichedGroupPublic.model_validate(g) for g in groups])
```

### 2.2 Update `app/api/routers/academics/groups.py`

Add 2 new endpoints to existing file:

```python
# After existing imports, add:
from app.modules.academics.schemas import GenerateLevelSessionsRequest

# ───────────────────────────────────────────────────────────────────────────────
# Endpoint 5: Delete Group (Soft Delete)
# ───────────────────────────────────────────────────────────────────────────────
@router.delete(
    "/academics/groups/{group_id}",
    response_model=ApiResponse[GroupPublic],
    summary="Soft delete a group (set inactive)",
)
def delete_group(
    group_id: int,
    _user: User = Depends(require_admin),
    svc: GroupService = Depends(get_group_service),
):
    group = svc.delete_group(group_id)
    return ApiResponse(
        data=GroupPublic.model_validate(group),
        message="Group archived successfully."
    )

# ───────────────────────────────────────────────────────────────────────────────
# Endpoint 6: Get Enriched Groups (All Active with Names)
# ───────────────────────────────────────────────────────────────────────────────
@router.get(
    "/academics/groups/enriched",
    response_model=ApiResponse[list[EnrichedGroupPublic]],
    summary="Get all active groups with instructor and course names",
)
def list_enriched_groups(
    _user: User = Depends(require_any),
    svc: GroupService = Depends(get_group_service),
):
    groups = svc.get_all_active_groups_enriched()
    return ApiResponse(data=[EnrichedGroupPublic.model_validate(g) for g in groups])

# ───────────────────────────────────────────────────────────────────────────────
# Endpoint 7: Generate Level Sessions (Manual Trigger)
# ───────────────────────────────────────────────────────────────────────────────
@router.post(
    "/academics/groups/{group_id}/generate-sessions",
    response_model=ApiResponse[list[SessionPublic]],
    status_code=201,
    summary="Generate sessions for a specific level",
)
def generate_level_sessions(
    group_id: int,
    body: GenerateLevelSessionsRequest,
    _user: User = Depends(require_admin),
    svc: SessionService = Depends(get_session_service),
):
    from app.modules.academics.schemas import GenerateLevelSessionsInput
    data = GenerateLevelSessionsInput(
        group_id=group_id,
        level_number=body.level_number,
        start_date=body.start_date or date.today()
    )
    sessions = svc.generate_level_sessions(data)
    return ApiResponse(
        data=[SessionPublic.model_validate(s) for s in sessions],
        message=f"Generated {len(sessions)} sessions for level {body.level_number}."
    )
```

---

## Phase 3: Schema Registration

### 3.1 Update `app/api/schemas/academics/__init__.py`

```python
from .course import CoursePublic, CourseStatsPublic, UpdateCoursePriceInput
from .group import GroupPublic, GroupListItem, EnrichedGroupPublic
from .session import SessionPublic

__all__ = [
    "CoursePublic",
    "CourseStatsPublic",
    "UpdateCoursePriceInput",
    "GroupPublic",
    "GroupListItem",
    "EnrichedGroupPublic",
    "SessionPublic",
]
```

### 3.2 Update `app/modules/academics/schemas/__init__.py`

```python
from .course_schemas import (
    AddNewCourseInput,
    UpdateCourseDTO,
    CourseStatsDTO,
    UpdateCoursePriceInput,  # NEW
)
from .group_schemas import (
    ScheduleGroupInput,
    UpdateGroupDTO,
    EnrichedGroupDTO,
    WeekDay,
    GenerateLevelSessionsRequest,  # NEW
)
from .session_schemas import (
    AddExtraSessionInput,
    GenerateLevelSessionsInput,
    UpdateSessionDTO,
)

__all__ = [
    # Course
    "AddNewCourseInput",
    "UpdateCourseDTO",
    "CourseStatsDTO",
    "UpdateCoursePriceInput",
    # Group
    "ScheduleGroupInput",
    "UpdateGroupDTO",
    "EnrichedGroupDTO",
    "WeekDay",
    "GenerateLevelSessionsRequest",
    # Session
    "AddExtraSessionInput",
    "GenerateLevelSessionsInput",
    "UpdateSessionDTO",
]
```

---

## Phase 4: Service Layer Verification

### 4.1 Verify Service Methods Exist

All service methods are already implemented:
- ✅ `CourseService.update_course_price()` - Line 31-38
- ✅ `CourseService.get_all_course_stats()` - Line 58-65
- ✅ `CourseService.get_course_stats()` - Line 67-74
- ✅ `GroupService.get_groups_by_course()` - Line 63-65
- ✅ `GroupService.delete_group()` - Line 99-113
- ✅ `GroupService.get_all_active_groups_enriched()` - Line 71-74
- ✅ `SessionService.generate_level_sessions()` - Line 20-53

No changes needed to service layer - only router exposure.

---

## Phase 5: Testing & Documentation

### 5.1 Test Endpoints

Test each endpoint after implementation:

```bash
# Course price update
curl -X PATCH http://localhost:8000/api/v1/academics/courses/1/price \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"new_price": 2000}'

# Course stats (all)
curl http://localhost:8000/api/v1/academics/courses/stats \
  -H "Authorization: Bearer $TOKEN"

# Course stats (single)
curl http://localhost:8000/api/v1/academics/courses/1/stats \
  -H "Authorization: Bearer $TOKEN"

# Groups by course
curl http://localhost:8000/api/v1/academics/courses/1/groups \
  -H "Authorization: Bearer $TOKEN"

# Delete group (soft)
curl -X DELETE http://localhost:8000/api/v1/academics/groups/1 \
  -H "Authorization: Bearer $TOKEN"

# Enriched groups
curl http://localhost:8000/api/v1/academics/groups/enriched \
  -H "Authorization: Bearer $TOKEN"

# Generate sessions
curl -X POST http://localhost:8000/api/v1/academics/groups/1/generate-sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"level_number": 2, "start_date": "2026-05-01"}'
```

### 5.2 Update API Documentation

Update `docs/product/api/academics.md` with new endpoints:

```markdown
### Course Price Management

#### Update course price
**PATCH** `/api/v1/academics/courses/{course_id}/price`

**Request Body:** `UpdateCoursePriceInput`
```json
{
  "new_price": 2000.00
}
```

**Response (200):** `ApiResponse<CoursePublic>`
```

---

## File Change Summary

| File | Action | Lines Added |
|------|--------|-------------|
| `app/api/schemas/academics/course.py` | Add `CourseStatsPublic`, `UpdateCoursePriceInput` | ~25 |
| `app/api/schemas/academics/group.py` | Add `EnrichedGroupPublic` | ~20 |
| `app/api/schemas/academics/__init__.py` | Export new schemas | ~5 |
| `app/modules/academics/schemas/course_schemas.py` | Add `UpdateCoursePriceInput` | ~15 |
| `app/modules/academics/schemas/group_schemas.py` | Add `GenerateLevelSessionsRequest` | ~10 |
| `app/modules/academics/schemas/__init__.py` | Re-export new DTOs | ~5 |
| `app/api/routers/academics/courses.py` | Add 4 endpoints | ~80 |
| `app/api/routers/academics/groups.py` | Add 3 endpoints | ~60 |
| `docs/product/api/academics.md` | Document new endpoints | ~100 |

**Total Lines Added:** ~320
**Files Modified:** 9
**No New Files Created**

---

## Implementation Order Recommendation

1. **Schemas First** - Add all DTOs and public models (Phase 1)
2. **Routers Second** - Add endpoints one by one, test as you go (Phase 2)
3. **Exports Third** - Update `__init__.py` files (Phase 3)
4. **Test Fourth** - Run test curls against running API (Phase 5)
5. **Document Fifth** - Update academics.md reference (Phase 5)

Each endpoint is independent - can implement in any order or parallelize.
