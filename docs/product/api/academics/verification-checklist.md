# Academics API Verification Checklist

Verification target:
- Router implementations in `app/api/routers/academics`
- DTOs/schemas in `app/modules/academics/schemas` and `app/api/schemas/academics`

Status legend:
- `[x]` documented and cross-checked against source

---

## Courses Router Coverage (`courses.py`)

- [x] `GET /api/v1/academics/courses` -> documented in `academics/courses.md`
- [x] `POST /api/v1/academics/courses` -> documented in `academics/courses.md`
- [x] `GET /api/v1/academics/courses/{course_id}` -> documented in `academics/courses.md`
- [x] `DELETE /api/v1/academics/courses/{course_id}` -> documented in `academics/courses.md`
- [x] `PATCH /api/v1/academics/courses/{course_id}` -> documented in `academics/courses.md`
- [x] `PATCH /api/v1/academics/courses/{course_id}/price` -> documented in `academics/courses.md`
- [x] `GET /api/v1/academics/courses/stats` -> documented in `academics/courses.md`
- [x] `GET /api/v1/academics/courses/{course_id}/stats` -> documented in `academics/courses.md`
- [x] `GET /api/v1/academics/courses/{course_id}/groups` -> documented in `academics/courses.md`

---

## Groups Router Coverage (`groups.py`)

- [x] `GET /api/v1/academics/groups` -> documented in `academics/groups.md`
- [x] `GET /api/v1/academics/groups/enriched` -> documented in `academics/groups.md`
- [x] `GET /api/v1/academics/groups/{group_id}` -> documented in `academics/groups.md`
- [x] `GET /api/v1/academics/groups/{group_id}/enriched` -> documented in `academics/groups.md`
- [x] `POST /api/v1/academics/groups` -> documented in `academics/groups.md`
- [x] `PATCH /api/v1/academics/groups/{group_id}` -> documented in `academics/groups.md`
- [x] `GET /api/v1/academics/groups/{group_id}/sessions` -> documented in `academics/groups.md`
- [x] `POST /api/v1/academics/groups/{group_id}/progress-level` -> documented in `academics/groups.md`
- [x] `DELETE /api/v1/academics/groups/{group_id}` -> documented in `academics/groups.md`
- [x] `POST /api/v1/academics/groups/{group_id}/generate-sessions` -> documented in `academics/groups.md`

Code observation:
- [x] duplicate route registration exists for `GET /academics/groups/{group_id}/enriched`; documented once as one unique signature.

---

## Sessions Router Coverage (`sessions.py`)

- [x] `GET /api/v1/academics/sessions/daily-schedule` -> documented in `academics/sessions.md`
- [x] `POST /api/v1/academics/groups/{group_id}/sessions` -> documented in `academics/sessions.md`
- [x] `GET /api/v1/academics/sessions/{session_id}` -> documented in `academics/sessions.md`
- [x] `PATCH /api/v1/academics/sessions/{session_id}` -> documented in `academics/sessions.md`
- [x] `DELETE /api/v1/academics/sessions/{session_id}` -> documented in `academics/sessions.md`
- [x] `POST /api/v1/academics/sessions/{session_id}/cancel` -> documented in `academics/sessions.md`
- [x] `POST /api/v1/academics/sessions/{session_id}/substitute` -> documented in `academics/sessions.md`

---

## DTO and Payload Verification

- [x] `AddNewCourseInput` fields and validators reflected
- [x] `UpdateCourseDTO` optional fields and conditional validators reflected
- [x] `UpdateCoursePriceInput` (`new_price > 0`) reflected
- [x] `ScheduleGroupInput` weekday literal and time-window validators reflected
- [x] `UpdateGroupDTO` optional fields reflected
- [x] `GenerateLevelSessionsRequest` reflected
- [x] `AddExtraSessionInput` reflected
- [x] `UpdateSessionDTO` reflected
- [x] `SubstituteInstructorRequest` corrected to `instructor_id` based on router code
- [x] `ApiResponse` and `PaginatedResponse` envelopes reflected

---

## Error Mapping Verification

- [x] `401/403` auth/role errors included for protected endpoints
- [x] `422` validation errors included (Pydantic + custom validation)
- [x] `404` included where router/service can raise not-found
- [x] `409` included where service may raise conflict/business-rule errors

---

## Final Coverage Result

- [x] All **26 unique academics endpoint signatures** in code are documented.
