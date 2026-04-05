# CRM API Split Documentation Index

This index maps each CRM router to its dedicated documentation file.

Base API prefix: `/api/v1`

---

## Router to Documentation Mapping

| Router | Source File | Documentation File | Endpoint Signatures |
|---|---|---|---:|
| Parents Router | `app/api/routers/crm/parents.py` | [parents.md](parents.md) | 7 |
| Students Router | `app/api/routers/crm/students.py` | [students.md](students.md) | 14 |

**Total unique endpoint signatures: 21**

---

## Supporting Files Reviewed

- `app/modules/crm/schemas/parent_schemas.py`
- `app/modules/crm/schemas/student_schemas.py`
- `app/api/schemas/crm/parent.py`
- `app/api/schemas/crm/student.py`
- `app/api/schemas/common.py`
- `app/api/dependencies.py`
- `app/api/exceptions.py`

---

## Verification

Coverage checklist:
- [verification-checklist.md](verification-checklist.md)
