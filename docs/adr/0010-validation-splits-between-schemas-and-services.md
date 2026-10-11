---
status: accepted
---

# Validation splits by kind: format on schemas, business rules in services

Validation lived in three places: Pydantic validators on schemas (built on `app/shared/validators`), service code, and crm's `validators/` package, whose `StudentValidator` is imported by a router, a service and a repository. A repository importing a validator puts rules where ADR-0002 allows none, and `validators/` is a layer outside the module template. We decided that format and shape checks (phone format, positive amounts, non-empty strings) are Pydantic validators on the schema that receives the input, and checks that need the database or business state (uniqueness, allowed status transitions) live in services. Repositories validate nothing, and there is no `validators/` layer. Shared format helpers stay in `app/shared/validators`.

## Consequences

- crm's `validators/` package is split and deleted, and `search_repository.py` stops importing it (#76).
- Migrating modules apply the same split as part of their flatten ticket.
