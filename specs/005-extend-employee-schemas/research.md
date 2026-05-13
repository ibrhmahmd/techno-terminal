# Research: Extend Employee Schemas

No unknowns to research. All technical context was determined by direct codebase inspection:

## Key Findings

### Current Data Flow

```
Employee ORM → EmployeeReadDTO (all fields) → EmployeePublic (selective) / EmployeeListItem (selective)
```

- `EmployeeReadDTO` already includes: `university`, `major`, `is_graduate`, `monthly_salary`, `contract_percentage`, `phone`, `email`
- `Employee` ORM model stores all these fields
- `EmployeeCreateInput` accepts all these fields during create/update
- The loss happens at the API schema layer (`app/api/schemas/hr/employee.py`)

### Files to Modify

| File | Change |
|------|--------|
| `app/api/schemas/hr/employee.py` | Add 5 fields to `EmployeePublic`, 2 fields to `EmployeeListItem` |
| `tests/test_hr.py` | Update assertions to expect new fields in responses |

### Files NOT to Modify

- `app/modules/hr/schemas/employee_schemas.py` — `EmployeeReadDTO` already complete
- `app/modules/hr/models/employee_models.py` — ORM already has all fields
- `app/modules/hr/repositories/employee_repository.py` — queries return full ORM objects
- `app/modules/hr/services/employee_crud_service.py` — DTO conversion already includes all fields
- `app/api/routers/hr_router.py` — no routing logic changes needed
- No database migration needed — all columns exist

### Test Impact

Current tests in `tests/test_hr.py::test_get_employee_success` assert:
```python
assert "id" in data["data"]
assert "full_name" in data["data"]
```

These will still pass. The new fields will appear in responses but existing assertions remain valid. New tests should verify the 7 added fields are present.

### Decision Record

| Decision | Rationale |
|----------|-----------|
| Modify API schemas only | Data already flows correctly; only the final Pydantic serialization drops fields |
| No service/repo changes | `EmployeeReadDTO` already has all fields; `model_validate` matches by name |
| No migration needed | All columns exist in `employees` table |
| Backward compatible | All new fields are `Optional` / have defaults |
