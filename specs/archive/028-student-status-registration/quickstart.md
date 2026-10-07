# Quickstart: Reproducing the Student Status Bug

## Prerequisites

- Python 3.10+ with virtual environment activated
- Dependencies installed: `pip install -e .`
- `.env` file with `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, etc. (use `.env.test` for CI-safe values)
- Database schema applied: `psql "$DATABASE_URL" -f db/schema.sql`
- A test JWT token: `python scripts/get_test_jwt.py` (or use mock tokens in tests)

## Running the Investigation Test

```bash
# Run the specific reproduction test
pytest tests/test_crm.py::TestStudentsCreate::test_create_student_with_waiting_status -v

# Run all CRM tests
pytest tests/test_crm.py -v

# Run with coverage
pytest tests/test_crm.py -v --cov=app/modules/crm --cov-report=term-missing
```

## Manual Reproduction via cURL

```bash
# Test 1: POST with status="waiting" (should succeed after fix)
curl -X POST http://localhost:8000/api/v1/crm/students \
  -H "Authorization: Bearer $(python scripts/get_test_jwt.py)" \
  -H "Content-Type: application/json" \
  -d '{
    "student_data": {
      "full_name": "Test Waiting Student",
      "date_of_birth": "2010-01-01",
      "gender": "male",
      "status": "waiting"
    },
    "parent_id": null,
    "relationship": null,
    "created_by_user_id": null
  }'

# Test 2: POST with status="Waiting" (capitalized — should succeed after fix)
curl -X POST http://localhost:8000/api/v1/crm/students \
  -H "Authorization: Bearer $(python scripts/get_test_jwt.py)" \
  -H "Content-Type: application/json" \
  -d '{
    "student_data": {
      "full_name": "Test Capitalized Waiting",
      "date_of_birth": "2010-01-01",
      "gender": "male",
      "status": "Waiting"
    },
    "parent_id": null,
    "relationship": null,
    "created_by_user_id": null
  }'

# Test 3: POST without status (should default to "waiting")
curl -X POST http://localhost:8000/api/v1/crm/students \
  -H "Authorization: Bearer $(python scripts/get_test_jwt.py)" \
  -H "Content-Type: application/json" \
  -d '{
    "student_data": {
      "full_name": "Test Default Status",
      "date_of_birth": "2010-01-01",
      "gender": "female",
      "status": null
    },
    "parent_id": null,
    "relationship": null,
    "created_by_user_id": null
  }'

# Test 4: POST with invalid status (should return 422)
curl -X POST http://localhost:8000/api/v1/crm/students \
  -H "Authorization: Bearer $(python scripts/get_test_jwt.py)" \
  -H "Content-Type: application/json" \
  -d '{
    "student_data": {
      "full_name": "Test Invalid Status",
      "date_of_birth": "2010-01-01",
      "status": "invalid_status"
    },
    "parent_id": null,
    "relationship": null,
    "created_by_user_id": null
  }'
```

## Final Status (After Fix Applied)

All scenarios below were verified with the `@field_validator("status", mode="before")` fix in place.

| Scenario | Status Code | Response Status Field | Result |
|----------|-------------|----------------------|--------|
| `status="waiting"` | 201 | `"waiting"` | ✅ PASS |
| `status="Waiting"` (capitalized) | 201 | `"waiting"` | ✅ PASS |
| `status="WAITING"` (uppercase) | 201 | `"waiting"` | ✅ PASS |
| `status="active"` | 201 | `"active"` | ✅ PASS |
| `status="inactive"` | 201 | `"inactive"` | ✅ PASS |
| `status=null` (omitted) | 201 | `"waiting"` | ✅ PASS |
| `status="invalid"` | 422 | (error) | ✅ PASS |
| `status=""` (empty) | 422 | (error) | ✅ PASS |

## Expected Behavior (Design Reference)

| Scenario | Status Code | Response Status Field |
|----------|-------------|----------------------|
| `status="waiting"` | 201 | `"waiting"` |
| `status="Waiting"` (capitalized) | 201 | `"waiting"` |
| `status="WAITING"` (uppercase) | 201 | `"waiting"` |
| `status="active"` | 201 | `"active"` |
| `status="inactive"` | 201 | `"inactive"` |
| `status=null` (omitted) | 201 | `"waiting"` |
| `status="invalid"` | 422 | — |

## Current Bug Behavior (Before Fix)

| Scenario | Status Code | Error |
|----------|-------------|-------|
| `status="waiting"` (lowercase) | 201 | ✅ Works |
| `status="Waiting"` (capitalized) | 422 🐛 | `ValidationError` — frontend displays as "not found" |
| `status="WAITING"` (uppercase) | 422 🐛 | `ValidationError` — frontend displays as "not found" |
| `status="active"` | 201 | ✅ Works |
| `status=null` | 201 | ✅ Works (defaults to waiting) |
