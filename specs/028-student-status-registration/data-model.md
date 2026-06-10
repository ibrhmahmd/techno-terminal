# Data Model Analysis: Student Status

**Branch**: `028-student-status-registration`  
**Date**: 2026-06-10

## Entity: Student

### Relevant Fields

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `status` | `StudentStatus` (enum) | `StudentBase.status` in `app/modules/crm/models/student_models.py:34` | Default: `StudentStatus.WAITING`; stored as `String` in PG |
| `waiting_since` | `Optional[datetime]` | `Student.waiting_since` (line 49) | Set when status becomes `WAITING` |
| `waiting_priority` | `Optional[int]` | `Student.waiting_priority` (line 50) | 1 = highest |
| `waiting_notes` | `Optional[str]` | `Student.waiting_notes` (line 51) | Free-text |

### StudentStatus Enum

**File**: `app/modules/crm/models/student_models.py:19`

```python
class StudentStatus(str, Enum):
    ACTIVE = "active"
    WAITING = "waiting"
    INACTIVE = "inactive"
```

This is a `str, Enum` — all comparisons and storage use lowercase strings. Pydantic v2 validates incoming JSON against the **exact string values**. No case normalization.

### Validation Flow (Current)

```
Request JSON status field (str or None)
  → Pydantic RegisterStudentDTO.status (Optional[StudentStatus])
    → If None → service defaults to StudentStatus.WAITING
    → If str → case-sensitive enum match against {"active","waiting","inactive"}
      → Match → stored as-is (lowercase)
      → No Match → RequestValidationError → 422 response
```

### Validation Flow (After Fix)

```
Request JSON status field (str or None)
  → @field_validator("status", mode="before") on RegisterStudentDTO
    → If str → .lower() before type validation
    → If None → pass through
  → Pydantic RegisterStudentDTO.status (Optional[StudentStatus])
    → If None → service defaults to StudentStatus.WAITING
    → If str → case-insensitive match (already lowercased)
      → Match → stored as lowercase
      → No Match → RequestValidationError → 422 response
```

### State Transitions

```
                 ┌──────────┐
                 │  waiting │
                 └────┬─────┘
                      │ enroll
                      ▼
                 ┌──────────┐     leave     ┌──────────┐
                 │  active  │ ────────────→ │ inactive │
                 └──────────┘               └──────────┘
                      │                           │
                      │ re-enroll                 │ re-register
                      └───────────────────────────┘
```

Note: During initial registration, any of the three statuses can be set directly. No transition restrictions at creation time.

## Related DTOs

| DTO | Location | Status Field | After Fix |
|-----|----------|-------------|-----------|
| `RegisterStudentDTO` | `app/modules/crm/schemas/student_schemas.py:11` | `Optional[StudentStatus] = None` | Add `@field_validator("status", mode="before")` with `.lower()` |
| `UpdateStudentDTO` | `app/modules/crm/schemas/student_schemas.py:34` | `Optional[StudentStatus] = None` | Consider adding same validator (out of this scope) |
| `UpdateStudentStatusDTO` | `app/modules/crm/schemas/student_schemas.py:42` | `StudentStatus` (required) | Consider adding same validator (out of this scope) |
| `StudentResponseDTO` | `app/modules/crm/schemas/student_schemas.py:50` | `status: str` | Read-only output, no change needed |
| `StudentPublic` | `app/api/schemas/crm/student.py:12` | `status: str` | Read-only output, no change needed |
