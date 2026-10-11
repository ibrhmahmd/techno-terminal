---
status: accepted
---

# A service may call a sibling service only through the shared Unit of Work

Legacy services built their collaborators themselves, for example `self.level_svc = level_svc or GroupLevelService()`. Each default-constructed collaborator could open its own session, so one use case ran in several transactions and the commit point was invisible (ADR-0001). The old refactoring guide answered by forbidding service-to-service calls inside a module, which pushed business rules down into repositories and helpers. We decided that a use-case service may call another service of the same module, provided it passes the same injected `UnitOfWork`, so the call stays inside one transaction. Services never construct their own dependencies or open sessions: the module's `api/deps.py` factories, or the non-HTTP entry point (`with unit_of_work() as uow:`), build the object graph. Calls across modules still go through facades in module order (ADR-0003), and a workflow writing to several modules lives in the highest one (ADR-0006).

## Considered Options

- **Services never call services**: rejected. Shared logic drifts into repositories (which must hold no business rules) or into ad-hoc helpers.
- **A separate use-case layer above services**: rejected. It adds a sixth layer to every module for a problem the shared Unit of Work already solves.
