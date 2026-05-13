# Quickstart: Extend Employee Schemas

## Implementation Order

### Step 1: Update `EmployeePublic` (detail endpoint)

**File**: `app/api/schemas/hr/employee.py`

Add these 5 fields to the `EmployeePublic` class (after `has_account`):

```python
university: Optional[str] = None
major: Optional[str] = None
is_graduate: Optional[bool] = None
monthly_salary: Optional[float] = None
contract_percentage: Optional[float] = None
```

### Step 2: Update `EmployeeListItem` (list endpoint)

**File**: `app/api/schemas/hr/employee.py`

Add these 2 fields to the `EmployeeListItem` class (after `is_active`):

```python
phone: Optional[str] = None
email: Optional[str] = None
```

### Step 3: Update tests

**File**: `tests/test_hr.py`

- Add assertions in `test_get_employee_success` to verify new `EmployeePublic` fields are present
- Add assertions in `test_list_employees_success` to verify new `EmployeeListItem` fields are present

### Step 4: Verify

```bash
pytest tests/test_hr.py -v
```

## Files Changed

| File | Change Type |
|------|-------------|
| `app/api/schemas/hr/employee.py` | 🔧 Modified — 5+2 field additions |
| `tests/test_hr.py` | 🔧 Modified — test assertions |
