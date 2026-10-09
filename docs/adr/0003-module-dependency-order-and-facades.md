---
status: accepted
---

# Modules form a fixed dependency order and talk only through facades

Every module imported almost every other one:
- crm ↔ enrollments ↔ finance ↔ academics depended on each other in a cycle.
- notifications imported seven modules.
- 221 imports sat inside functions to dodge circular-import errors.
- Services reached into other modules' repositories and UoWs.

We fixed an order derived from the foreign-key graph (a table's module sits above the modules its FKs point at). A module may import only modules below it, and only from their `__init__.py` facade (plus models, see ADR-0004):

```
analytics          (top: read-only)
notifications
tasks
finance
competitions
attendance
enrollments
academics
crm
hr
auth               (bottom: identity, see ADR-0005)
--- platform: app/shared, app/core, app/db ---
```

The rules are import-linter contracts that run inside pytest, because the repo has no CI. A contract is report-only until its module is migrated, then it enforces.

## Consequences

- Imports inside functions that exist to dodge cycles are removed as each module migrates; a cycle that appears is a design error to fix, not to hide.
- `enrollment_level_history` moves from academics to enrollments. Its FKs point at enrollments and students, so it belongs to enrollments. It is a Python move only, with no schema change.
