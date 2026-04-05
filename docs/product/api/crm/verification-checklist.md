# CRM API Verification Checklist

Verification target:
- Router implementations in `app/api/routers/crm`
- DTOs/schemas in `app/modules/crm/schemas` and `app/api/schemas/crm`

Status legend:
- `[x]` documented and cross-checked against source

---

## Parents Router Coverage (`parents.py`)

- [x] `GET /api/v1/crm/parents` -> documented in `crm/parents.md`
- [x] `GET /api/v1/crm/parents/{parent_id}` -> documented in `crm/parents.md`
- [x] `POST /api/v1/crm/parents` -> documented in `crm/parents.md`
- [x] `PATCH /api/v1/crm/parents/{parent_id}` -> documented in `crm/parents.md`
- [x] `POST /api/v1/crm/parents/find-or-create` -> documented in `crm/parents.md`
- [x] `GET /api/v1/crm/parents/{parent_id}/students` -> documented in `crm/parents.md`
- [x] `DELETE /api/v1/crm/parents/{parent_id}` -> documented in `crm/parents.md`

---

## Students Router Coverage (`students.py`)

- [x] `GET /api/v1/crm/students` -> documented in `crm/students.md`
- [x] `GET /api/v1/crm/students/{student_id}` -> documented in `crm/students.md`
- [x] `POST /api/v1/crm/students` -> documented in `crm/students.md`
- [x] `PATCH /api/v1/crm/students/{student_id}` -> documented in `crm/students.md`
- [x] `GET /api/v1/crm/students/{student_id}/parents` -> documented in `crm/students.md`
- [x] `GET /api/v1/crm/students/{student_id}/siblings` -> documented in `crm/students.md`
- [x] `DELETE /api/v1/crm/students/{student_id}` -> documented in `crm/students.md`

---

## DTO and Payload Verification

- [x] `RegisterParentInput` required fields and phone normalization rules reflected
- [x] `UpdateParentDTO` optional field behavior reflected
- [x] `FindOrCreateParentInput` + `FindOrCreateParentResponse` reflected
- [x] `RegisterStudentDTO` + `RegisterStudentCommandDTO` reflected
- [x] `UpdateStudentDTO` reflected
- [x] `ParentPublic`, `ParentListItem`, `StudentPublic`, `StudentListItem`, `SiblingInfo` reflected
- [x] `ApiResponse` and `PaginatedResponse` envelopes reflected

---

## Error Mapping Verification

- [x] `401/403` auth/role errors included for protected endpoints
- [x] `422` request/validation errors included
- [x] `404` included where not-found checks are present
- [x] `409` included for parent duplicate phone conflict

---

## Final Coverage Result

- [x] All **14 unique CRM endpoint signatures** in code are documented.
