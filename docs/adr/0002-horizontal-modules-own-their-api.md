---
status: accepted
---

# Every module has horizontal layers and owns its HTTP API

Modules had four different internal shapes:
- vertical "D+" slices (academics, enrollments)
- horizontal layers (most modules)
- flat files (tasks)
- an analytics module with no models

Their HTTP code also lived apart from them in `app/api/routers` and `app/api/schemas`. We standardise on one shape, `app/modules/<name>/` containing:

| Folder | Contents |
|---|---|
| `api/` | routers, HTTP request/response schemas, the module's service factories |
| `services/` | business logic |
| `repositories/` | classes constructed with a session |
| `schemas/` | service DTOs |
| `models/` | ORM models |

`__init__.py` is the module's public facade. Inside a module, imports point downward only: `api → services → repositories → models`. Services never import `api` (the old Two-Layer Schema Rule, now scoped per module). `app/api/` keeps only shared HTTP code: the app factory and router registry, middleware, exception handlers, auth and role guards, the response envelope and `get_uow`. Horizontal layers won because most modules already used them, so one template is predictable for both agents and humans. The slice split added folders without adding depth, and its interfaces were never referenced.
