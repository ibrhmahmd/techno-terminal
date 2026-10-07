# Data Model: Return Employee National ID

## Employee (detail — `EmployeePublic`)

**File**: `app/api/schemas/hr/employee.py`

### Current Fields

| Field | Type | Required |
|-------|------|----------|
| id | int | Yes |
| full_name | str | Yes |
| phone | str | Yes |
| email | str \| None | No |
| job_title | str \| None | No |
| employment_type | str | Yes |
| is_active | bool | Yes |
| hired_at | datetime \| None | No |
| has_account | bool | No |
| university | str \| None | No |
| major | str \| None | No |
| is_graduate | bool \| None | No |
| monthly_salary | float \| None | No |
| contract_percentage | float \| None | No |

### Field to Add

| Field | Type | Required | Source |
|-------|------|----------|--------|
| national_id | str | Yes | `EmployeeReadDTO.national_id` |

### Validation Rules

- `national_id` is `str` — always populated, exists in DB as NOT NULL
- No new validation needed — already validated on create/update
- backward-compatible: existing consumers ignore unknown fields

---

## Data Flow

```
DB "employees" table (national_id column)
  → Employee (SQLModel ORM, national_id: str)
    → EmployeeReadDTO (model_validate, national_id: str)
      → EmployeePublic (model_validate) — currently drops national_id
```

**No changes** to DB, ORM, internal DTOs, services, or repositories.
