# CRM API Documentation

The CRM API documentation has been split by router for accuracy and maintainability.

Base path prefix: `/api/v1`  
Router prefix: `/crm`

---

## Split Files

- Parents router docs: [crm/parents.md](crm/parents.md)
- Students router docs: [crm/students.md](crm/students.md)

---

## Mapping Index

- Router-to-file mapping: [crm/index.md](crm/index.md)

---

## Verification Checklist

- Endpoint coverage and DTO verification: [crm/verification-checklist.md](crm/verification-checklist.md)

---

## Authentication

All CRM endpoints require Bearer authentication:

```http
Authorization: Bearer <access_token>
```

Role guards used:
- `require_any`: any authenticated active user
- `require_admin`: admin/system_admin only

---

## Summary

- Routers documented: `parents.py`, `students.py`
- Total unique endpoint signatures covered: **14**
- Source of truth used: router code + DTO/schema modules + exception/auth dependencies
