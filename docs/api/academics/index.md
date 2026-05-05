# Academics API Documentation Index

This index maps each academics router to its dedicated documentation file.

Base API prefix: `/api/v1`

---

## Router to Documentation Mapping

| Router | Source File | Documentation File | Endpoint Signatures |
|---|---|---|---:|
| Courses Router | `app/api/routers/academics/courses_router.py` | [courses.md](courses.md) | 7 |
| Groups Router | `app/api/routers/academics/groups_router.py` | [groups.md](groups.md) | 8 |
| Group Directory Router | `app/api/routers/academics/group_directory_router.py` | [group_directory.md](group_directory.md) | 8 |
| Group Lifecycle Router | `app/api/routers/academics/group_lifecycle_router.py` | [group_lifecycle.md](group_lifecycle.md) | 7 |
| Group Details Router | `app/api/routers/academics/group_details_router.py` | [group_details.md](group_details.md) | 5 |
| Group Competitions Router | `app/api/routers/academics/group_competitions_router.py` | [group_competitions.md](group_competitions.md) | 7 |
| Sessions Router | `app/api/routers/academics/sessions_router.py` | [sessions.md](sessions.md) | 8 |

**Total unique endpoint signatures: 50**

---

## Supporting Files Reviewed

Request/public schema references used to build these docs:
- `app/modules/academics/schemas/course_schemas.py`
- `app/modules/academics/schemas/group_schemas.py`
- `app/modules/academics/schemas/group_details_schemas.py`
- `app/modules/academics/schemas/session_schemas.py`
- `app/modules/academics/schemas/team_schemas.py`
- `app/modules/academics/schemas/competition_schemas.py`
- `app/modules/academics/schemas/grouped_schemas.py`
- `app/api/schemas/academics/course.py`
- `app/api/schemas/academics/group.py`
- `app/api/schemas/academics/session.py`
- `app/api/schemas/academics/team.py`
- `app/api/schemas/academics/group_level.py`
- `app/api/schemas/academics/competition.py`
- `app/api/schemas/academics/grouped.py`
- `app/api/schemas/common.py`
- `app/api/dependencies.py`
- `app/api/exceptions.py`

---

## Documentation Structure

The API documentation is organized by router responsibility:

1. **[courses.md](courses.md)** - Course management endpoints
2. **[groups.md](groups.md)** - Main group management (Core CRUD, scheduling, progression)
3. **[group_directory.md](group_directory.md)** - Group listings, search, and grouped-display
3. **[group_lifecycle.md](group_lifecycle.md)** - Level management (complete/cancel) and analytics
4. **[group_details.md](group_details.md)** - Detailed levels, attendance, payments, enrollments
5. **[group_competitions.md](group_competitions.md)** - Teams and competition integration
6. **[sessions.md](sessions.md)** - Session management endpoints
7. **[attendance.md](attendance.md)** - Attendance tracking endpoints

---

## Verification

Coverage checklist:
- [verification-checklist.md](verification-checklist.md)
