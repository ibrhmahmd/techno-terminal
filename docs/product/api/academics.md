# Academics API Documentation

The Academics API documentation has been split by router for accuracy and maintainability.

Base path prefix: `/api/v1`

---

## Split Files

- Courses router docs: [academics/courses.md](academics/courses.md)
- Groups router docs: [academics/groups.md](academics/groups.md)
- Sessions router docs: [academics/sessions.md](academics/sessions.md)

---

## Mapping Index

- Router-to-file mapping: [academics/index.md](academics/index.md)

---

## Verification Checklist

- Endpoint coverage and DTO verification: [academics/verification-checklist.md](academics/verification-checklist.md)

---

## Authentication

All academics endpoints require Bearer authentication:

```http
Authorization: Bearer <access_token>
```

Role guards used:
- `require_any`: any authenticated active user
- `require_admin`: admin/system_admin only

---

## Summary

- Routers documented: `courses.py`, `groups.py`, `sessions.py`
- Total unique endpoint signatures covered: **26**
- Source of truth used: router code + DTO/schema modules + exception/auth dependencies
