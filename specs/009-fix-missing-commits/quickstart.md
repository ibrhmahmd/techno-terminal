# Quickstart: Fix Missing Commits

## Verification Steps

### 1. Run existing tests to establish baseline

```bash
pytest tests/test_academics_courses.py -v --tb=short
pytest tests/test_academics_enrollments.py -v --tb=short 2>/dev/null || echo "No enrollment test file yet"
pytest tests/test_competitions.py -v --tb=short 2>/dev/null || echo "No competition test file yet"
```

### 2. Verify each fix manually

For each affected method, confirm:
- Service file has `session.commit()` after repo writes
- Service file has `session.refresh()` if the entity is returned
- No schema changes, no migration files

### 3. Run persistence verification

```bash
# After fixes are applied, each new test should:
# 1. POST to create resource → assert 201
# 2. GET the resource → assert it exists with correct data
pytest tests/ -v -k "persists" --tb=short
```

### Expected pass criteria

| Test | Expected |
|------|----------|
| `test_course_create_persists` | ✅ |
| `test_enroll_student_persists` | ✅ |
| `test_enroll_drop_persists` | ✅ |
| `test_enroll_transfer_persists` | ✅ |
| `test_competition_create_persists` | ✅ |
| `test_team_register_persists` | ✅ |
