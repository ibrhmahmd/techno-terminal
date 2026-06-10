# Data Model: CI Seed Data

**Branch**: `030-test-coverage-ci`
**Date**: 2026-06-10

## Overview

The seed data fixture creates minimum viable records that satisfy all FK constraints across the 16 database tables. Records are created using SQLModel models in `tests/seed_data.py`.

## Entity Relationship Chain

```
users (1)
  ├── employees (1) — linked via user_id
  ├── receipts (1) — received_by
  └── notifications (?) — sent_by

courses (1)
  ├── groups (1) — course_id
  │   ├── sessions (2) — group_id
  │   │   └── attendance (2) — session_id + student_id
  │   ├── enrollments (1) — group_id + student_id
  │   └── level_history (1) — group_id + student_id

students (2)
  ├── student_parents (1) — student_id + parent_id
  ├── enrollments (1) — student_id
  ├── attendance (2) — student_id
  └── receipts (1) — via payments

parents (1)
  └── student_parents (1)

competitions (1)
  └── competition_categories (1)
      └── teams (1)
          └── team_members (1) — student_id

receipts (1)
  └── payments (1) — receipt_id
```

## Minimum Required Records

| Entity | Count | Key Fields |
|--------|-------|------------|
| `users` | 1 | `email`, `supabase_uid`, `role=admin` |
| `employees` | 1 | `user_id`, `full_name`, `role` |
| `parents` | 1 | `full_name`, `phone` |
| `students` | 2 | `full_name`, `date_of_birth`, `status=active` |
| `student_parents` | 1 | `student_id`, `parent_id`, `relationship` |
| `courses` | 1 | `name`, `category`, `academic_year` |
| `groups` | 1 | `name`, `course_id`, `status=active` |
| `sessions` | 2 | `group_id`, `session_date`, `day_of_week` |
| `enrollments` | 1 | `student_id`, `group_id`, `status=active` |
| `attendance` | 2 | `session_id`, `student_id`, `status=present` |
| `receipts` | 1 | `payment_method=cash`, `received_by=user_id` |
| `payments` | 1 | `receipt_id`, `amount`, `type=charge`, `status=completed` |
| `competitions` | 1 | `name`, `status=upcoming` |
| `competition_categories` | 1 | `competition_id`, `name` |
| `teams` | 1 | `competition_category_id`, `name` |
| `team_members` | 1 | `team_id`, `student_id` |

## Idempotency Strategy

```python
# tests/seed_data.py
def seed_database(session: Session) -> dict[str, Any]:
    \"\"\"Create seed records, return mapping of created entities by name.\"\"\"
    # Clear existing data in dependency order (children first)
    for table in REVERSE_ORDER_TABLES:
        session.exec(text(f"DELETE FROM {table} CASCADE"))

    # Create records
    user = User(email="admin@test.com", ...)
    session.add(user)
    session.flush()

    student1 = Student(full_name="Ahmed Ali", ...)
    session.add(student1)
    session.flush()
    # ...

    return {"user": user, "student1": student1, ...}
```

## Transaction Isolation

```python
# In conftest.py
@pytest.fixture(scope="module")
def seeded_session():
    \"\"\"Session with seed data, rolled back after module completes.\"\"\"
    with get_session() as session:
        seed_database(session)
        yield session
        session.rollback()  # Discard all test modifications
```
