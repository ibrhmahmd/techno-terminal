# Research: Student Status Registration Bug

**Branch**: `028-student-status-registration`  
**Date**: 2026-06-10  
**Status**: Complete

## Bug Reproduction Hypothesis

### Code Path Analysis

The POST `/api/v1/crm/students` endpoint accepts a JSON body deserialized into `RegisterStudentCommandDTO`, which wraps `RegisterStudentDTO` under `student_data`.

**Key code path for status field:**

```
Request JSON
  → RegisterStudentCommandDTO (Pydantic model)
    → student_data: RegisterStudentDTO (Pydantic model)
      → status: Optional[StudentStatus] = None
        → StudentStatus = str, Enum with values: "active", "waiting", "inactive"
```

**Pydantic v2 behavior for `str, Enum` fields:**
- Case-sensitive by default. `"Waiting"` ≠ `"waiting"` → raises `RequestValidationError`
- The error is caught by `pydantic_validation_handler` in `app/api/exceptions.py` → returns 422 with `"error": "ValidationError"`

**Service layer (`StudentCrudService.register_student`):**
- If `status` is `None`, defaults to `StudentStatus.WAITING`
- If `status` is a valid `StudentStatus` enum member, uses it directly
- No additional validation or rejection of any enum value

### Root Cause Analysis

There are **two possible causes** for the reported "not found" behavior:

#### Cause A: Case sensitivity mismatch (most likely)

The frontend sends the status as `"Waiting"` (capitalized from a dropdown/toggle UI) or some other casing variation. Pydantic's `str, Enum` validation is case-sensitive, so `"Waiting"` fails validation and returns a 422 error. The frontend displays this as "not found" (either by interpreting the 422 as a generic error or by showing the error message from validation details).

**Evidence:**
- The `StudentStatus` enum values are all lowercase: `"active"`, `"waiting"`, `"inactive"`
- Pydantic v2 does not normalize string inputs for `str, Enum` fields
- The frontend dropdown may display "Waiting" (capitalized) but send the capitalized value
- The `test_create_student_success` test does NOT pass `status` — it relies on the default

#### Cause B: The frontend sends a status value not in the enum

Possible values the frontend might send include: `"Waiting"`, `"wait"`, `"pending"`, or a status ID. Any value outside `{"active", "waiting", "inactive"}` would fail Pydantic enum validation → 422.

#### Why "active" works:

- If "active" is sent as `"active"` (lowercase), it matches the enum → passes validation
- If the frontend hardcodes "active" in the dropdown but sends user-selected values for other options, only "active" works correctly

### Decision

- **Decision**: Add `@field_validator("status", mode="before")` to `RegisterStudentDTO` to lowercase the input string before enum validation. This is the simplest fix that handles all case variations (Cause A) and also provides a clear error path for truly invalid values (Cause B).
- **Rationale**: Normalization is more resilient than requiring exact casing from the frontend. Pydantic's `mode="before"` validator runs before the type/field validation, so we can convert `str` values to lowercase before the enum check.
- **Alternatives considered**:
  1. Case-insensitive enum class — more complex implementation, non-standard pattern
  2. Strict case-sensitive — pushes the fix to the frontend (out of scope)
  3. Accept any casing and store as-is — would break consistency with existing data

### Reproduction Test Design

A targeted pytest in the existing `tests/test_crm.py` pattern:

```python
def test_create_student_with_waiting_status(self, client, mock_admin_headers, override_auth):
    """POST /crm/students with status="waiting" must succeed."""
    unique_name = f"Waiting Student {uuid.uuid4().hex[:8]}"
    
    response = client.post(
        "/api/v1/crm/students",
        headers=mock_admin_headers,
        json={
            "student_data": {
                "full_name": unique_name,
                "date_of_birth": "2010-01-01",
                "gender": "male",
                "phone": "+201000000001",
                "status": "waiting"
            },
            "parent_id": None,
            "relationship": None,
            "created_by_user_id": None
        }
    )
    
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["data"]["status"] == "waiting"
```

Additional variant tests:
- `test_create_student_with_waiting_status_capitalized` — sends `"Waiting"` → expects 201 after fix
- `test_create_student_with_active_status_explicit` — sends `"active"` → expects 201
- `test_create_student_with_inactive_status` — sends `"inactive"` → expects 201
- `test_create_student_defaults_to_waiting` — omits status → expects 201 + status="waiting"

## Fix Confirmation

### Root Cause (Confirmed)

**Cause A: Case sensitivity mismatch** — ✅ Confirmed.

Sending `"Waiting"` (capitalized) to POST /api/v1/crm/students returns a **422 ValidationError** because Pydantic's `str, Enum` validation is case-sensitive and `"Waiting" ≠ "waiting"`.

The frontend receives this 422 error and displays it as a "not found" message.

### Fix Applied

A `@field_validator("status", mode="before")` was added to `RegisterStudentDTO` in `app/modules/crm/schemas/student_schemas.py` that lowercases the input string before enum validation.

### Verification Results (All Passing)

| Test | Input | Expected | Result |
|------|-------|----------|--------|
| `test_create_student_with_waiting_status_lowercase` | `"waiting"` | 201 | ✅ PASS |
| `test_create_student_with_waiting_status_capitalized` | `"Waiting"` | 201 | ✅ PASS |
| `test_create_student_with_waiting_status_uppercase` | `"WAITING"` | 201 | ✅ PASS |
| `test_create_student_defaults_to_waiting` | (omitted) | 201 → `"waiting"` | ✅ PASS |
| `test_create_student_explicit_null_status` | `null` | 201 → `"waiting"` | ✅ PASS |
| `test_create_student_with_active_status` | `"active"` | 201 → `"active"` | ✅ PASS |
| `test_create_student_with_inactive_status` | `"inactive"` | 201 → `"inactive"` | ✅ PASS |
| `test_create_student_invalid_status_returns_422` | `"invalid_value"` | 422 | ✅ PASS |
| `test_create_student_empty_status_returns_422` | `""` | 422 | ✅ PASS |
| `test_create_student_success` (existing) | (no status) | 201 | ✅ PASS |

Full CRM suite: **26/26 passed** — no regressions.

## References

- `app/modules/crm/models/student_models.py:19` — `StudentStatus` enum definition
- `app/modules/crm/schemas/student_schemas.py:25` — `RegisterStudentDTO.status` field
- `app/modules/crm/services/student_crud_service.py:61` — Status defaulting logic
- `app/api/exceptions.py:49` — `pydantic_validation_handler` error format
- `tests/test_crm.py:69` — Existing `test_create_student_success` pattern
