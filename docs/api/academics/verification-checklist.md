# Academics API Verification Checklist

Verification target:
- Router implementations in `app/api/routers/academics`
- DTOs/schemas in `app/modules/academics/schemas` and `app/api/schemas/academics`

Status legend:
- `[x]` documented and cross-checked against source

---

## Courses Router Coverage (`courses_router.py`)

- [x] `GET /api/v1/academics/courses` -> documented in `academics/courses.md`
- [x] `POST /api/v1/academics/courses` -> documented in `academics/courses.md`
- [x] `GET /api/v1/academics/courses/{course_id}/stats` -> documented in `academics/courses.md`
- [x] `GET /api/v1/academics/courses/{course_id}/groups` -> documented in `academics/courses.md`
- [x] `GET /api/v1/academics/courses/{course_id}` -> documented in `academics/courses.md`
- [x] `PATCH /api/v1/academics/courses/{course_id}` -> documented in `academics/courses.md`
- [x] `DELETE /api/v1/academics/courses/{course_id}` -> documented in `academics/courses.md`

**Total: 7 endpoints**

---

## Groups Router Coverage (`groups_router.py`)

- [x] `GET /api/v1/academics/groups` -> documented in `academics/groups.md`
- [x] `GET /api/v1/academics/groups/enriched` -> documented in `academics/groups.md`
- [x] `GET /api/v1/academics/groups/grouped` -> documented in `academics/groups.md`
- [x] `GET /api/v1/academics/groups/course/{course_id}` -> documented in `academics/groups.md`
- [x] `GET /api/v1/academics/groups/archived` -> documented in `academics/groups.md`
- [x] `GET /api/v1/academics/groups/{group_id}` -> documented in `academics/groups.md`
- [x] `GET /api/v1/academics/groups/{group_id}/enriched` -> documented in `academics/groups.md`
- [x] `POST /api/v1/academics/groups` -> documented in `academics/groups.md`
- [x] `PATCH /api/v1/academics/groups/{group_id}` -> documented in `academics/groups.md`
- [x] `GET /api/v1/academics/groups/{group_id}/sessions` -> documented in `academics/groups.md`
- [x] `DELETE /api/v1/academics/groups/{group_id}` -> documented in `academics/groups.md`
- [x] `POST /api/v1/academics/groups/{group_id}/generate-sessions` -> documented in `academics/groups.md`
- [x] `POST /api/v1/academics/groups/{group_id}/progress-level` -> documented in `academics/groups.md`
- [x] `GET /api/v1/academics/groups/search` -> documented in `academics/groups.md`
- [x] `GET /api/v1/academics/groups/by-type/{group_type}` -> documented in `academics/groups.md`
- [x] `GET /api/v1/academics/groups/by-course/{course_id}` -> documented in `academics/groups.md`

**Total: 16 endpoints**

**Note:** The `POST /api/v1/academics/groups/{group_id}/schedule-level` endpoint has been removed. Use `progress-level` with `auto_migrate_enrollments: false` and `complete_current_level: false` for equivalent functionality.

---

## Group Lifecycle Router Coverage (`group_lifecycle_router.py`)

- [x] `GET /api/v1/academics/groups/{group_id}/history` -> documented in `academics/group_lifecycle.md`
- [x] `GET /api/v1/academics/groups/{group_id}/levels` -> documented in `academics/group_lifecycle.md`
- [x] `GET /api/v1/academics/groups/{group_id}/levels/{level_number}` -> documented in `academics/group_lifecycle.md`
- [x] `POST /api/v1/academics/groups/{group_id}/levels/{level_number}/complete` -> documented in `academics/group_lifecycle.md`
- [x] `POST /api/v1/academics/groups/{group_id}/levels/{level_number}/cancel` -> documented in `academics/group_lifecycle.md`
- [x] `GET /api/v1/academics/groups/{group_id}/courses/history` -> documented in `academics/group_lifecycle.md`
- [x] `GET /api/v1/academics/groups/{group_id}/enrollments/history` -> documented in `academics/group_lifecycle.md`
- [x] `GET /api/v1/academics/groups/{group_id}/levels/analytics` -> documented in `academics/group_lifecycle.md`
- [x] `GET /api/v1/academics/groups/{group_id}/enrollments/analytics` -> documented in `academics/group_lifecycle.md`
- [x] `GET /api/v1/academics/groups/{group_id}/instructors/analytics` -> documented in `academics/group_lifecycle.md`
- [x] `GET /api/v1/academics/groups/{group_id}/enrollment-history` (alias) -> documented in `academics/group_lifecycle.md`
- [x] `GET /api/v1/academics/groups/{group_id}/instructor-history` (alias) -> documented in `academics/group_lifecycle.md`

**Total: 12 endpoints (10 unique + 2 aliases)**

---

## Group Competitions Router Coverage (`group_competitions_router.py`)

- [x] `GET /api/v1/academics/groups/{group_id}/competitions` -> documented in `academics/group_competitions.md`
- [x] `GET /api/v1/academics/groups/{group_id}/teams` -> documented in `academics/group_competitions.md`
- [x] `POST /api/v1/academics/groups/{group_id}/teams/{team_id}/link` -> documented in `academics/group_competitions.md`
- [x] `POST /api/v1/academics/groups/{group_id}/competitions/{competition_id}/register` -> documented in `academics/group_competitions.md`
- [x] `PATCH /api/v1/academics/groups/{group_id}/competitions/{participation_id}/complete` -> documented in `academics/group_competitions.md`
- [x] `DELETE /api/v1/academics/groups/{group_id}/competitions/{participation_id}` -> documented in `academics/group_competitions.md`
- [x] `GET /api/v1/academics/groups/{group_id}/competitions/analytics` -> documented in `academics/group_competitions.md`

**Total: 7 endpoints**

---

## Sessions Router Coverage (`sessions_router.py`)

- [x] `GET /api/v1/academics/sessions/daily-schedule` -> documented in `academics/sessions.md`
- [x] `POST /api/v1/academics/groups/{group_id}/sessions` -> documented in `academics/sessions.md`
- [x] `GET /api/v1/academics/sessions/{session_id}` -> documented in `academics/sessions.md`
- [x] `PATCH /api/v1/academics/sessions/{session_id}` -> documented in `academics/sessions.md`
- [x] `DELETE /api/v1/academics/sessions/{session_id}` -> documented in `academics/sessions.md`
- [x] `POST /api/v1/academics/sessions/{session_id}/cancel` -> documented in `academics/sessions.md`
- [x] `POST /api/v1/academics/sessions/{session_id}/reactivate` -> documented in `academics/sessions.md`
- [x] `POST /api/v1/academics/sessions/{session_id}/substitute` -> documented in `academics/sessions.md`

**Total: 8 endpoints**

---

## Summary

| Router | Endpoints | Status |
|--------|-----------|--------|
| Courses | 7 | Complete |
| Groups | 17 | Complete |
| Group Lifecycle | 12 (10+2 aliases) | Complete |
| Group Competitions | 7 | Complete |
| Sessions | 8 | Complete |
| **Total** | **51** | **Complete** |

Last verified: 2026-04-07
