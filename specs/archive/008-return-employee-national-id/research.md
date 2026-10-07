# Research: Return Employee National ID

No unknowns to research. All technical context determined by direct codebase inspection.

## Key Findings

### Current Data Flow

```
Employee ORM (has national_id) → EmployeeReadDTO (has national_id: str) → EmployeePublic (missing national_id)
```

- `EmployeeReadDTO.national_id` is typed as `str` (required, non-optional in the DTO)
- `Employee` ORM model stores `national_id: str` (required, non-nullable in DB)
- `EmployeeCreateInput` accepts `national_id: str` (required field)
- The field is simply dropped at the `EmployeePublic` serialization layer

### Files to Modify

| File | Change |
|------|--------|
| `app/api/schemas/hr/employee.py` | Add `national_id: str` to `EmployeePublic` |
| `tests/test_hr.py` | Add `assert "national_id" in data["data"]` to `test_get_employee_success` |

### Files NOT to Modify

- `app/modules/hr/schemas/employee_schemas.py` — `EmployeeReadDTO` already has `national_id: str`
- `app/modules/hr/models/employee_models.py` — ORM already has `national_id`
- `app/modules/hr/repositories/employee_repository.py` — queries return full ORM objects
- `app/modules/hr/services/employee_crud_service.py` — DTO conversion already includes `national_id`
- `app/api/routers/hr_router.py` — no routing logic changes needed
- No database migration needed — column exists

### Decision Record

| Decision | Rationale |
|----------|-----------|
| Add `national_id` to `EmployeePublic` only | Data already flows correctly; only the final Pydantic serialization drops the field |
| Type as `str` (not `Optional[str]`) | `national_id` is required in the DB and `EmployeeReadDTO` — it always has a value |
| No service/repo changes | `EmployeeReadDTO` already has `national_id`; `model_validate` matches by name |
| No migration needed | Column exists in `employees` table |
