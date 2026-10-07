# Research: Missing Session Commit Bug Pattern

**Phase**: Phase 0 — Research & Analysis  
**Date**: 2026-05-14  
**Input**: Code audit of `app/modules/` service layer

---

## Decision 1: Fix pattern — add `session.commit()` + `session.refresh()`

**Rationale**: Minimal change (1-2 lines per method), zero schema changes, zero API contract changes. The session already has a transaction open (`.flush()` was called), so `.commit()` just finalizes it — no additional DB roundtrips beyond the commit itself.

**Alternatives considered**:
- Refactor to UoW pattern across all 3 services — safer long-term but higher risk under production timeline
- Change `get_session()` to auto-commit — would break read-only methods and audit utils that expect rollback on exceptions

---

## Decision 2: Connection pool increase (temporary)

**Rationale**: Each enrollment request opens 3+ sessions. At 5+5=10 pool connections, 4 concurrent requests exhaust the pool. Temporarily increase to `pool_size=10, max_overflow=5` (total 15) to reduce `pool_timeout=30` stalls.

**Rollback plan**: After services are refactored to UoW pattern (1 session per request), revert to original 5+5.

---

## Decision 3: Persistence-verification tests

**Rationale**: Existing tests only check HTTP response codes and body shapes. A subsequent GET call within the same test verifies the data actually committed and survives a new session lookup.

**Test pattern**:
```python
# Step 1: Create via POST
response = client.post("/api/v1/enrollments", json=payload, headers=admin_headers)
assert response.status_code == 201
created_id = response.json()["data"]["id"]

# Step 2: Verify via GET
get_resp = client.get(f"/api/v1/enrollments/{created_id}", headers=admin_headers)
assert get_resp.status_code == 200
assert get_resp.json()["data"]["id"] == created_id
```
