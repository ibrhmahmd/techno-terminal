# Data Model: Extend Employee Schemas

## Employee (detail — `EmployeePublic`)

**File**: `app/api/schemas/hr/employee.py`

### Current Fields

| Field | Type | Required |
|-------|------|----------|
| id | int | Yes |
| full_name | str | Yes |
| phone | str | Yes |
| email | str \| None | No |
| national_id | str \| None | No |
| job_title | str \| None | No |
| employment_type | str | Yes |
| is_active | bool | Yes |
| hired_at | datetime \| None | No |
| has_account | bool | No (default False) |

### Fields to Add

| Field | Type | Required | Source |
|-------|------|----------|--------|
| university | str \| None | No | `EmployeeReadDTO.university` |
| major | str \| None | No | `EmployeeReadDTO.major` |
| is_graduate | bool \| None | No | `EmployeeReadDTO.is_graduate` |
| monthly_salary | float \| None | No | `EmployeeReadDTO.monthly_salary` |
| contract_percentage | float \| None | No | `EmployeeReadDTO.contract_percentage` |

### Validation Rules

- All new fields are optional — `None` when not stored
- `monthly_salary` should use `Optional[float]` (matches ORM model type)
- `contract_percentage` should use `Optional[float]` (0–100 range, but stored as-is)
- `is_graduate` should use `Optional[bool]` (None = unknown, False = not graduated, True = graduated)

---

## EmployeeListItem (list — card view)

**File**: `app/api/schemas/hr/employee.py`

### Current Fields

| Field | Type | Required |
|-------|------|----------|
| id | int | Yes |
| full_name | str | Yes |
| job_title | str \| None | No |
| employment_type | str | Yes |
| is_active | bool | Yes |

### Fields to Add

| Field | Type | Required | Source |
|-------|------|----------|--------|
| phone | str \| None | No | `EmployeeReadDTO.phone` |
| email | str \| None | No | `EmployeeReadDTO.email` |

### Validation Rules

- `phone` is `Optional[str]` — always populated in practice but nullable for safety
- `email` is `Optional[str]` — employees may not have an email on file

---

## Data Flow

```
DB "employees" table
  → Employee (SQLModel ORM)
    → EmployeeReadDTO (model_validate) — all fields
      → EmployeePublic (model_validate) — currently drops: university, major, is_graduate, monthly_salary, contract_percentage
      → EmployeeListItem (model_validate) — currently drops: phone, email
```

**No changes** to DB, ORM, internal DTOs, services, or repositories.
