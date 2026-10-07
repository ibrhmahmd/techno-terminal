# Data Model: Unified Student Listing DTO

**Feature**: 031-unified-student-listing-dto  
**Date**: 2026-06-10

---

## New Schema: `StudentListingDTO` (API Boundary)

**File**: `app/api/schemas/crm/student.py`  
**Layer**: API boundary — replaces `StudentListItem` as the response model for all five listing endpoints.

```python
class StudentListingDTO(BaseModel):
    """
    Unified student card representation returned by all listing endpoints.
    All five GET /crm/students/* endpoints use this as their item type.
    """
    # Core identity (always present)
    id: int
    full_name: str
    status: str                          # 'active' | 'waiting' | 'inactive'

    # Contact
    phone: Optional[str] = None

    # Demographics
    date_of_birth: Optional[date] = None
    age: Optional[int] = None            # Computed from date_of_birth; null when DOB unknown
    gender: Optional[str] = None         # 'male' | 'female' | null

    # Enrollment display
    current_group_name: Optional[str] = None   # Most recent active enrollment's group

    # Financial indicator
    has_unpaid_balance: bool = False     # See two-tier definition in spec FR-008

    model_config = ConfigDict(from_attributes=True)

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def convert_datetime_to_date(cls, v):
        if isinstance(v, datetime):
            return v.date()
        return v
```

**Replaces**: `StudentListItem` (in same file). `StudentListItem` must be audited for other callers and deleted if unused after migration.

---

## Modified Schema: `StudentFilterItemDTO` (Service Layer)

**File**: `app/modules/crm/interfaces/dtos/student_filter_result_dto.py`

| Field | Before | After | Notes |
|---|---|---|---|
| `enrollment_count` | `int = 0` | `current_enrollment_count: int = 0` | Rename only |
| `unpaid_balance` | `Optional[float] = None` | `has_unpaid_balance: bool = False` | Type change: float → bool |
| `date_of_birth` | absent | `Optional[date] = None` | New field |

The filter-specific context fields (`instructor_id`, `instructor_name`, `group_default_day`, `enrolled_courses`) are **preserved** as extras beyond the unified core.

---

## Modified Schema: `StudentSummaryDTO` (Service Layer — Grouped Endpoint)

**File**: `app/modules/crm/interfaces/dtos/student_summary_dto.py`

| Field | Before | After | Notes |
|---|---|---|---|
| `has_unpaid_balance` | absent | `bool = False` | New field — populated by `get_all_enriched()` |

`age` is NOT added here — computed in the router/service layer post-query.

---

## Modified Input DTO: `StudentFilterDTO` (Service Layer — Filter Endpoint)

**File**: `app/modules/crm/interfaces/dtos/student_filter_dto.py`

| Field | Before | After | Notes |
|---|---|---|---|
| `has_unpaid_balance` | `Optional[bool]` | `has_any_outstanding_balance: Optional[bool]` | Rename only — semantics preserved (all-enrollment scope) |

---

## Data Flow per Endpoint

### 1. `GET /crm/students` (paginated list)

```
Router → SearchService.list_all_paginated() [new enriched variant]
       → Raw SQL: students + LEFT JOIN enrollments + LEFT JOIN groups
                  + EXISTS(v_unpaid_enrollments) subquery
       → List[StudentListingDTO] (age computed in Python)
```

**Current**: `list_all()` returns `List[Student]` (bare ORM, no JOINs).  
**After**: New enriched paginated query returns data mapped directly to `StudentListingDTO`.

### 2. `GET /crm/students?q=` (search)

```
Router → SearchService.search(query) [extend existing]
       → Raw SQL: existing search + age computation added in Python
       → List[StudentListingDTO]
```

**Current**: Returns `List[Student]`. `StudentListItem` mapped in router.  
**After**: Returns `List[StudentListingDTO]` directly.

### 3. `GET /crm/students/grouped`

```
Router → SearchService.get_grouped()
       → StudentRepository.get_all_enriched() [add has_unpaid_balance to SQL]
       → Python grouping + pagination
       → StudentGroupedResultDTO (buckets contain StudentSummaryDTO with has_unpaid_balance)
       → Router maps StudentSummaryDTO → StudentListingDTO (adds age computation)
```

### 4. `GET /crm/students/filter`

```
Router → SearchService.filter_students(StudentFilterDTO with has_any_outstanding_balance)
       → CTE SQL: existing logic, field rename only
       → StudentFilterResultDTO containing StudentFilterItemDTO (date_of_birth added, fields renamed)
       → Router maps StudentFilterItemDTO → StudentListingDTO
```

### 5. `GET /crm/students/waiting-list`

```
Router → SearchService.get_waiting_list() [extend]
       → Raw SQL: existing query + EXISTS(v_enrollment_balance) subquery
       → List[StudentResponseDTO with has_unpaid_balance + age]
       → Router maps → StudentListingDTO (preserving waiting_since, waiting_priority, waiting_notes as extras)
```

**Note**: The waiting-list endpoint returns a superset — `StudentListingDTO` fields plus the waiting-specific fields. The response model remains `ApiResponse[list[StudentResponseDTO]]` or is updated to a new extended DTO. See contracts/ for the API contract decision.

---

## State Transitions

No state transitions — this is a read-only DTO unification. No mutations to student records.

---

## Validation Rules

| Field | Rule |
|---|---|
| `age` | Computed via `StudentValidator.compute_age(date_of_birth)`. Must be `None` when `date_of_birth` is `None`. Must be non-negative. |
| `has_unpaid_balance` | Non-nullable boolean. Default `False`. Never `None`. |
| `current_group_name` | `None` when student has no active enrollment. |
| `date_of_birth` | Stored as `datetime` in DB, serialized as `date` (YYYY-MM-DD) via `field_validator`. |
