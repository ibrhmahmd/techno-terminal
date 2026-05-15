# Backend Fixes

**Date**: 2026-05-13

## 1. `national_id` missing from `GET /hr/employees/:id`

The response for `GET /hr/employees/:id` does not include `national_id` at all, even though the backend `EmployeePublic` Pydantic model declares it as `national_id: str | None = None`.

The detail endpoint query or response serializer is not selecting/returning this field.

**Fix**: Ensure the query selects `national_id` from the database and the response includes it (nullable).

**Expected**:
```json
{
  "national_id": "1234567890"  // or null
}
```

## 2. `has_account` is already returned — type it as `bool`

The response already includes `has_account: false`, but our frontend `EmployeePublic` type doesn't have it.

**Fix**: No backend change needed — this field is already being returned correctly. Frontend type will be updated to include it.

---

## Current `GET /hr/employees/:id` Response (for reference)

```json
{
  "id": 3,
  "full_name": "Ibrahim Ahmed",
  "phone": "01008520964",
  "email": "ibrahim.ahmd.net@gmail.com",
  "job_title": "instructor",
  "employment_type": "contract",
  "is_active": true,
  "hired_at": null,
  "national_id": null,         // <-- should be here
  "has_account": false,
  "university": "KFS",
  "major": "computer science",
  "is_graduate": true,
  "monthly_salary": 0,
  "contract_percentage": 25
}
```
