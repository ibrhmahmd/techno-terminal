# Enrollment Connection Drop Prevention Plan

## Table Of Contents
1. [Executive Summary](#executive-summary)
2. [Problem Statement And Context](#problem-statement-and-context)
3. [Technical Requirements](#technical-requirements)
4. [Architectural Constraints](#architectural-constraints)
5. [Current-State Findings](#current-state-findings)
6. [Vulnerability Inventory](#vulnerability-inventory)
7. [Target Prevention Architecture](#target-prevention-architecture)
8. [Implementation Plan And Timelines](#implementation-plan-and-timelines)
9. [Resource Allocation](#resource-allocation)
10. [Risk Assessment](#risk-assessment)
11. [Quality Standards And Success Metrics](#quality-standards-and-success-metrics)
12. [Testing Strategy](#testing-strategy)
13. [Monitoring And Alerting](#monitoring-and-alerting)
14. [Rollout And Rollback Plan](#rollout-and-rollback-plan)
15. [Deliverables Checklist](#deliverables-checklist)
16. [Appendix: Detection Rules](#appendix-detection-rules)

## Executive Summary
The `POST /api/v1/enrollments` intermittent `500` is caused by **session lifecycle anti-patterns** that can leave stale database connections in memory and reuse invalid sessions after idle periods. The most severe defect is manual context management in the enrollment service (`__enter__()` without guaranteed `__exit__()`), compounded by additional dependency-injection patterns that return services built from already-exited Unit of Work scopes.

This plan defines a **codebase-wide prevention architecture** to eliminate the root cause category, not only the single endpoint symptom. It includes:
- Standardized request-scoped session ownership.
- Unit of Work lifecycle safety rules.
- Static and runtime detection controls.
- Focused regression and fault-injection testing.
- Monitoring/alerting and staged rollout with rollback guardrails.

## Problem Statement And Context
### Problem Statement
- Endpoint: `POST /api/v1/enrollments`
- Failure mode: intermittent `500 Internal Server Error`
- Error class: `psycopg2.OperationalError`
- Typical signature: *server closed the connection unexpectedly*

### Why This Matters
- Affects high-value enrollment flows and potentially related CRM/finance service paths.
- Erodes user trust due to intermittent behavior (hard to predict/reproduce manually).
- Introduces operational risk under low traffic followed by burst traffic patterns.

### Domain Context
- Backend stack: FastAPI + SQLModel + SQLAlchemy engine pooling + Supabase/Postgres.
- Data-access patterns: mixed `get_session()` context managers + Unit of Work objects.
- Service orchestration crosses modules (enrollments, CRM, academics, notifications, finance).

## Technical Requirements
### Functional Requirements
- Enrollment creation must succeed consistently after idle periods.
- No endpoint should rely on long-lived, unchecked-out DB sessions.
- Existing API contracts and DTO responses must remain backward compatible.

### Non-Functional Requirements
- **Reliability:** eliminate stale session reuse category.
- **Observability:** produce actionable telemetry for connection lifecycle errors.
- **Maintainability:** enforce safe patterns through lint/static checks and code review gates.
- **Performance:** maintain acceptable p95 latency and avoid unnecessary connection churn.

### Security And Compliance Requirements
- Keep transaction boundaries explicit and deterministic.
- Ensure no hidden retry loops that can duplicate writes.
- Preserve auditability through structured logs and traceable remediation history.

## Architectural Constraints
- Must preserve current module layering:
  - `Models -> Schemas -> Repositories -> Services -> Facade/Router`
- Must avoid circular dependencies and high-risk architectural rewrites in one phase.
- Must be deployable incrementally with feature-flag fallback.
- Must align with Supabase connection behavior (PgBouncer idle and transaction characteristics).

## Current-State Findings
### Primary Failure Pattern
- Manual context entry in enrollment path:
  - `uow.__enter__()` used directly and cached.
  - No guaranteed paired `__exit__()` for that specific object lifetime.

### Secondary Systemic Patterns
- Services returned from inside `with UnitOfWork()` blocks in DI factories.
- Non-context-managed session acquisition using `get_session().__enter__()`.
- Long-lived app-level session usage in scheduler startup lifecycle.
- Singleton service instances with mutable internal cached state.

### Net Result
- Invalid/stale session handles can outlive intended scope.
- Increased probability of `OperationalError` after idle windows.
- Reproducibility across endpoints with similar patterns, not just enrollments.

## Vulnerability Inventory
The following inventory prioritizes locations that can reproduce the same bug class.

| Risk Score (1-10) | Vulnerability Pattern | Module Area | Impact Summary |
|---:|---|---|---|
| 10 | Manual `__enter__()` without lifecycle guarantee | Enrollments service | Direct stale-session reuse risk in enrollment writes |
| 10 | `get_session().__enter__()` and `__del__` cleanup reliance | Finance receipt generation | High leak/stale risk under long process uptime |
| 9 | Returning services created inside `with StudentUnitOfWork()` | API DI layer / CRM | Service may hold exited UoW/session references |
| 9 | Returning services created inside `with FinanceUnitOfWork()` | API DI layer / Finance | Same lifecycle mismatch in reporting/balance paths |
| 8 | Long-lived scheduler DB session | App startup/lifespan | Idle-time stale connections in scheduled jobs |
| 7 | Singleton service facades with mutable internals | Module facades | Cross-request state contamination risk |
| 7 | Pool recycle policy mismatch for Supabase behavior | DB connection config | Increased stale checkout probability |

### Representative Pattern Example
```python
# Anti-pattern: manual context entry, no deterministic context exit
uow = StudentUnitOfWork()
uow.__enter__()
self._student_crud_service = StudentCrudService(uow)
```

## Target Prevention Architecture
### Design Principles
1. **Request-scoped ownership:** every request/job gets explicit session scope.
2. **Deterministic cleanup:** no destructor-based DB resource cleanup.
3. **No manual context invocation:** use `with` blocks or `yield` dependencies only.
4. **Retry discipline:** bounded retries only at safe boundaries.
5. **Visibility first:** failures must be measurable and attributable.

### Core Patterns
- **Pattern A:** FastAPI `yield` dependencies for DB-backed services.
- **Pattern B:** UoW created and consumed within operation scope.
- **Pattern C:** Scheduler opens fresh session/UoW per tick/report dispatch.
- **Pattern D:** Stateless services; forbid persistent DB-bound object caches.

### Implementation Standards
- Allowed:
  - `with get_session() as session: ...`
  - `def dep(...): yield service; finally: cleanup`
- Forbidden:
  - `.__enter__()` calls in application business code
  - Returning service instances from inside completed `with UoW()` scopes
  - `__del__` as the primary session close mechanism

## Implementation Plan And Timelines
### Phase 1 (Week 1): Immediate Stabilization
1. Fix enrollment service lifecycle anti-pattern.
2. Fix finance receipt generation session ownership.
3. Refactor highest-risk DI factories to `yield`-managed dependencies.
4. Add targeted integration tests for enrollment idle-gap scenario.

### Phase 2 (Week 2): Platform Hardening
1. Refactor scheduler to per-run session acquisition.
2. Introduce bounded `OperationalError` recovery at safe session boundaries.
3. Add structured logging fields for DB lifecycle failures.
4. Implement static checks in CI for banned patterns.

### Phase 3 (Week 3): Governance And Scale
1. Extend static rules to all modules.
2. Add monitoring dashboards and SLO-based alerts.
3. Execute load + soak + fault-injection validation.
4. Finalize runbook and on-call remediation steps.

### Milestone Timeline
| Milestone | Target Date | Exit Criteria |
|---|---|---|
| M1: Enrollment path stabilized | End Week 1 | No stale-session defect in enrollment regression suite |
| M2: DI and scheduler hardened | End Week 2 | All critical lifecycle anti-patterns removed in core paths |
| M3: Guardrails operational | End Week 3 | CI detection + monitoring + runbook live |

## Resource Allocation
### Team Roles
- **Backend Lead (1):** architecture decisions, critical path implementation, final code reviews.
- **Backend Engineers (2):** refactors, static checks, test implementation.
- **QA/Automation Engineer (1):** integration, fault-injection, soak test execution.
- **DevOps/SRE (0.5):** dashboards, alerts, deploy guardrails, rollback readiness.

### Effort Estimate
| Workstream | Effort (Person-Days) | Owner |
|---|---:|---|
| Enrollment + DI core fixes | 4 | Backend Lead + Engineer |
| Finance/session ownership fixes | 3 | Backend Engineer |
| Static detection + CI integration | 2 | Backend Engineer |
| Testing + fault injection + soak | 3 | QA/Automation |
| Monitoring + alerting + runbook | 2 | DevOps/SRE |
| **Total** | **14** | Cross-functional |

## Risk Assessment
### Top Risks
1. **Regression risk in DI wiring**
   - Probability: Medium
   - Impact: High
   - Mitigation: phased rollout + endpoint contract tests
2. **Hidden duplicate patterns in less-used modules**
   - Probability: High
   - Impact: Medium
   - Mitigation: static scanning + mandatory review checklist
3. **Retry misuse causing duplicate writes**
   - Probability: Low
   - Impact: High
   - Mitigation: retries only at safe boundaries and idempotent operations
4. **Operational blind spots**
   - Probability: Medium
   - Impact: High
   - Mitigation: structured logs + alert thresholds + runbook

### Risk Matrix
| Risk | Likelihood | Impact | Priority | Owner |
|---|---|---|---|---|
| DI lifecycle regressions | Medium | High | P1 | Backend Lead |
| Undiscovered anti-pattern variants | High | Medium | P1 | Backend Team |
| Retry-induced duplication | Low | High | P2 | Backend + QA |
| Missing observability signals | Medium | High | P1 | DevOps/SRE |

## Quality Standards And Success Metrics
### Quality Standards
- No banned lifecycle patterns in merged code.
- All DB session/UoW ownership must be explicit and deterministic.
- All changes validated through unit + integration + fault-injection coverage.
- Rollout protected by feature flags and rollback plan.

### Success Metrics
- **Reliability:** `0` stale-session enrollment failures in controlled idle-gap test runs.
- **Error budget:** `OperationalError` rate reduced by `>= 95%` on affected endpoints.
- **Stability:** `500` response rate on enrolled scope endpoints below agreed SLO.
- **Performance:** p95 endpoint latency regression no worse than `+10%`.
- **Governance:** CI rejects all newly introduced banned patterns.

## Testing Strategy
### Test Layers
1. **Unit tests**
   - Dependency lifecycle tests for open/close semantics.
   - UoW boundary tests for commit/rollback correctness.
2. **Integration tests**
   - Idle-gap enrollment flow (`sleep` or forced connection disposal simulation).
   - CRM/finance endpoint checks using same dependency patterns.
3. **Fault-injection tests**
   - Inject `OperationalError` at first query; verify bounded recovery behavior.
4. **Soak tests**
   - 30-60 minute mixed traffic with idle windows.

### Example Validation Scenario
```text
Given idle period > expected connection timeout window
When POST /api/v1/enrollments is executed
Then request returns 2xx/4xx business outcome (not 500)
And no leaked session indicators are present
And logs include connection lifecycle metadata
```

## Monitoring And Alerting
### Required Telemetry Fields
- `endpoint`
- `error_class`
- `db_operation`
- `retry_attempt`
- `session_scope`
- `pool_state` (where available)

### Alert Policies
- Alert A: `OperationalError` count above threshold per 5-minute window.
- Alert B: `500` rate spike on enrollment/CRM/finance endpoints.
- Alert C: DB pool checkout timeout or saturation indicators.

### Dashboards
- Endpoint error trend by exception class.
- Retry count trend and success-after-retry ratio.
- Latency and throughput on remediated endpoints.

## Rollout And Rollback Plan
### Rollout Strategy
1. Deploy Phase 1 fixes behind feature flag (e.g., `DB_LIFECYCLE_V2`).
2. Canary subset of traffic or non-peak rollout window.
3. Monitor key metrics for 24-48 hours.
4. Promote to full traffic after acceptance criteria pass.

### Rollback Procedure
1. Disable `DB_LIFECYCLE_V2` flag.
2. Revert to previous dependency/session wiring.
3. Keep logging instrumentation enabled for incident analysis.
4. Publish incident summary and corrective action updates.

## Deliverables Checklist
- [ ] Enrollment lifecycle anti-pattern removed.
- [ ] Finance receipt generation session ownership fixed.
- [ ] High-risk DI factories converted to lifecycle-safe `yield` patterns.
- [ ] Scheduler DB session scope refactored per job run.
- [ ] Static detection rules active in CI.
- [ ] Integration and fault-injection test suites green.
- [ ] Monitoring dashboards and alerts active.
- [ ] Rollback runbook approved and shared.

## Appendix: Detection Rules
### Rule Set (Automated)
1. Block direct calls to `.__enter__()` and `.__exit__()` in app business logic.
2. Block `get_session().__enter__()` usage.
3. Detect `with UnitOfWork() as uow: return Service(uow)` anti-pattern.
4. Flag module-level singleton service objects that cache DB lifecycle state.

### Example Rule Intent (Pseudo-Semgrep)
```yaml
rules:
  - id: forbid-manual-context-enter
    pattern: $X.__enter__()
    message: "Use context manager syntax, not manual __enter__() calls."
    severity: ERROR
```

---

**Document Owner:** Backend Architecture Team  
**Last Updated:** 2026-04-19  
**Status:** Draft for stakeholder review

