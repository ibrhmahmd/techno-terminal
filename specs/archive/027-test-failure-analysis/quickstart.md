# Quickstart: Test Failure Cleanup Verification

## Run full test suite to see current failures:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -v --tb=short 2>&1 | Select-String "passed|failed|error|FAILED"
```

## Run specific category after cleanup:

```powershell
# HR (out of scope — code fix)
.\.venv\Scripts\python.exe -m pytest tests/test_hr.py -v --tb=short

# Academics Groups
.\.venv\Scripts\python.exe -m pytest tests/test_academics_groups.py -v --tb=short

# Analytics Dashboard (expect 0 failures after deletion)
.\.venv\Scripts\python.exe -m pytest tests/test_analytics_dashboard.py -v --tb=short

# All analytics
.\.venv\Scripts\python.exe -m pytest tests/test_analytics_dashboard.py tests/test_analytics.py tests/test_analytics_academic.py tests/test_analytics_competition.py -v --tb=short

# Notifications
.\.venv\Scripts\python.exe -m pytest tests/test_notifications.py -v --tb=short

# Attendance
.\.venv\Scripts\python.exe -m pytest tests/test_attendance.py -v --tb=short

# Everything except HR (out of scope)
.\.venv\Scripts\python.exe -m pytest tests/ --ignore=tests/test_hr.py -v --tb=short
```

## Expected outcome after cleanup:

- **74 failures resolved** (66 in-scope + 8 already passing)
- **12 HR phone failures remain** (out of scope — code fix)
- **1 G1 attendance failure remains** (out of scope — code fix)
- **1 I4 instructor query failure remains** (out of scope — investigate)
