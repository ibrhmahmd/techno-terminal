# Quickstart: Return Employee National ID

## Implementation Order

### Step 1: Update `EmployeePublic`

**File**: `app/api/schemas/hr/employee.py`

Add `national_id` field to the `EmployeePublic` class (after `contract_percentage`):

```python
national_id: str
```

Also update the docstring to remove the exclusion note.

### Step 2: Update tests

**File**: `tests/test_hr.py`

Add assertion in `test_get_employee_success` to verify `national_id` is present in the response.

### Step 3: Verify

```bash
pytest tests/test_hr.py::TestEmployeesRead -v
```

## Files Changed

| File | Change Type |
|------|-------------|
| `app/api/schemas/hr/employee.py` | 🔧 Modified — add `national_id` field to `EmployeePublic` |
| `tests/test_hr.py` | 🔧 Modified — test assertion for `national_id` |
