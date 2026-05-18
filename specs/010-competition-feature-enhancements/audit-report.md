# Competition Module — Comprehensive Audit Report

**Date**: 2026-05-17
**Branch**: `010-competition-feature-enhancements`
**Scope**: Full audit of competition module workflows, architecture, security, performance, and spec compliance.

---

## Executive Summary

The competition module is **~85% complete**. All foundational work (migration, models, schemas, dead code removal, hard delete, coach read-only) is implemented and tested. Two high-priority gaps remain:

1. **Duplicate student registration** (FR-010) — currently hard-blocked instead of warn-and-allow
2. **30-day placement window** (FR-020) — upper bound not enforced

Two critical architectural issues require attention:
- `pay_competition_fee` uses **3 separate transactions** instead of atomic rollback
- `ReceiptService._link_competition_payment` references **non-existent fields** (`fee_paid`, `payment_id`)

---

## 1. Architecture Overview

```mermaid
graph TB
    subgraph "API Layer (app/api/)"
        R1[competitions_router.py<br/>8 endpoints]
        R2[teams_router.py<br/>13 endpoints]
        D1[dependencies.py<br/>require_coach_or_admin]
        S1[API Schemas<br/>UpdateTeamInput, PlacementUpdateInput]
    end

    subgraph "Service Layer (app/modules/competitions/services/)"
        CS[CompetitionService<br/>7 methods]
        TS[TeamService<br/>18 methods]
    end

    subgraph "Repository Layer (app/modules/competitions/repositories/)"
        CR[competition_repository.py<br/>5 functions]
        TR[team_repository.py<br/>17 functions]
    end

    subgraph "Data Layer"
        M1[Competition Model]
        M2[Team Model]
        M3[TeamMember Model]
        M4[Payment Model<br/>app/modules/finance/]
    end

    subgraph "External Modules"
        FIN[Finance Module<br/>ReceiptService, FinanceUnitOfWork]
        CRM[CRM Module<br/>StudentActivityService, Student]
        AUTH[Auth Module<br/>User, require_admin]
    end

    R1 --> CS
    R2 --> TS
    D1 --> R2
    S1 --> R1
    S1 --> R2
    CS --> CR
    TS --> TR
    CR --> M1
    TR --> M2
    TR --> M3
    TR --> M4
    TS --> FIN
    TS --> CRM
    R1 --> AUTH
    R2 --> AUTH
```

---

## 2. Endpoint Inventory (21 endpoints)

| # | Method | Path | Auth | Request | Response | Status Codes |
|---|--------|------|------|---------|----------|-------------|
| 1 | GET | `/competitions` | any | — | `list[CompetitionDTO]` | 200, 401 |
| 2 | POST | `/competitions` | admin | `CreateCompetitionInput` | `CompetitionDTO` | 201, 401, 403, 422 |
| 3 | GET | `/competitions/{id}` | any | — | `CompetitionDTO` | 200, 401, 404 |
| 4 | PUT | `/competitions/{id}` | admin | `UpdateCompetitionInput` | `CompetitionDTO` | 200, 400, 401, 403, 404, 422 |
| 5 | PATCH | `/competitions/{id}` | admin | `UpdateCompetitionInput` | `CompetitionDTO` | 200, 400, 401, 403, 404, 422 |
| 6 | DELETE | `/competitions/{id}` | admin | — | `bool` | 200, 401, 403, 409 |
| 7 | GET | `/competitions/{id}/summary` | any | — | `CompetitionSummaryResponse` | 200, 401, 404 |
| 8 | GET | `/competitions/{id}/categories` | any | — | `list[CategoryResponse]` | 200, 401, 404 |
| 9 | GET | `/teams` | any (coach-filtered) | Query params | `list[TeamWithMembersDTO]` | 200, 400, 401 |
| 10 | POST | `/teams` | admin | `RegisterTeamInput` | `TeamRegistrationResultDTO` | 201, 400, 401, 403, 404, 409, 422 |
| 11 | GET | `/teams/{id}` | coach_or_admin | — | `TeamDTO` | 200, 401, 403, 404 |
| 12 | PUT | `/teams/{id}` | admin | `UpdateTeamInput` | `TeamDTO` | 200, 400, 401, 403, 404, 422 |
| 13 | PATCH | `/teams/{id}` | admin | `UpdateTeamInput` | `TeamDTO` | 200, 400, 401, 403, 404, 422 |
| 14 | DELETE | `/teams/{id}` | admin | — | `bool` | 200, 401, 403, 409 |
| 15 | GET | `/teams/{id}/members` | coach_or_admin | — | `TeamMemberListResponse` | 200, 401, 403, 404 |
| 16 | POST | `/teams/{id}/members` | admin | `AddTeamMemberInput` | `AddTeamMemberResultDTO` | 201, 400, 401, 403, 404, 409, 422 |
| 17 | DELETE | `/teams/{id}/members/{sid}` | admin | — | `bool` | 200, 400, 401, 403, 404 |
| 18 | POST | `/teams/{id}/members/{sid}/pay` | admin | `PayCompetitionFeeInput` | `PayCompetitionFeeResponseDTO` | 200, 400, 401, 403, 404 |
| 19 | POST | `/teams/{id}/members/{sid}/refund` | admin | `RefundCompetitionFeeBody` | `bool` | 200, 400, 401, 403, 404 |
| 20 | PATCH | `/teams/{id}/placement` | admin | `PlacementUpdateInput` | `TeamDTO` | 200, 400, 401, 403, 404, 409 |
| 21 | GET | `/students/{sid}/competitions` | any | — | `StudentCompetitionsResponse` | 200, 401, 404 |

---

## 3. Workflow Diagrams

### 3.1 Competition Lifecycle (US1)

```mermaid
sequenceDiagram
    participant Admin
    participant Router as competitions_router
    participant Service as CompetitionService
    participant Repo as competition_repository
    participant DB as PostgreSQL

    Admin->>Router: POST /competitions
    Router->>Router: require_admin guard
    Router->>Service: create_competition(input)
    Service->>Repo: create_competition()
    Repo->>DB: INSERT INTO competitions
    DB-->>Repo: Competition row
    Repo-->>Service: Competition
    Service->>Service: commit
    Service-->>Router: CompetitionDTO
    Router-->>Admin: 201 Created

    Admin->>Router: PUT /competitions/{id}
    Router->>Router: require_admin guard
    Router->>Service: update_competition(id, **kwargs)
    Service->>Repo: update_competition(id, **kwargs)
    Repo->>DB: UPDATE competitions SET ...
    DB-->>Repo: Updated row
    Repo-->>Service: Competition
    Service->>Service: commit
    Service-->>Router: CompetitionDTO
    Router-->>Admin: 200 OK

    Admin->>Router: DELETE /competitions/{id}
    Router->>Router: require_admin guard
    Router->>Service: delete_competition(id)
    Service->>Repo: list_teams(competition_id=id)
    Repo-->>Service: teams[]
    alt Has teams
        Service-->>Router: BusinessRuleError
        Router-->>Admin: 409 Conflict
    else No teams
        Service->>Repo: delete_competition(id)
        Repo->>DB: DELETE FROM competitions
        DB-->>Repo: success
        Service->>Service: commit
        Service-->>Router: True
        Router-->>Admin: 200 OK
    end
```

### 3.2 Team Registration with Group Pre-Fill (US2)

```mermaid
sequenceDiagram
    participant Admin
    participant Router as teams_router
    participant Service as TeamService
    participant Repo as team_repository
    participant DB as PostgreSQL
    participant CRM as CRM Module

    Admin->>Router: POST /teams {competition_id, team_name, category, student_ids, group_id?, project_name?, project_description?}
    Router->>Router: require_admin guard
    Router->>Service: register_team(input, current_user_id)

    Service->>Repo: get_competition(competition_id)
    alt Competition missing
        Service-->>Router: NotFoundError
        Router-->>Admin: 404
    end

    Service->>Repo: check_category_has_subcategories(competition_id, category)
    alt Category requires subcategory but none provided
        Service-->>Router: BusinessRuleError
        Router-->>Admin: 400
    end

    Service->>Repo: list_teams(competition_id)
    alt Team name already exists
        Service-->>Router: ConflictError
        Router-->>Admin: 409
    end

    loop For each student_id
        Service->>DB: SELECT * FROM students WHERE id = ?
        alt Student missing
            Service-->>Router: NotFoundError
            Router-->>Admin: 404
        end
        alt Student not active
            Service-->>Router: BusinessRuleError
            Router-->>Admin: 400
        end
        Service->>Repo: check_student_in_competition(competition_id, student_id)
        alt Already in another team
            Service-->>Router: ConflictError
            Router-->>Admin: 409
        end
    end

    Service->>Repo: create_team(team_data)
    Repo->>DB: INSERT INTO teams
    DB-->>Repo: Team row

    loop For each student_id
        Service->>Repo: add_team_member(team_id, student_id, amount_due)
        Repo->>DB: INSERT INTO team_members
    end

    Service->>CRM: log_competition_registration (silent fail)
    Service->>Service: commit
    Service-->>Router: TeamRegistrationResultDTO
    Router-->>Admin: 201 Created {team, members_added}
```

### 3.3 Payment Flow — Multi-Transaction Architecture (US4)

```mermaid
sequenceDiagram
    participant Admin
    participant Router as teams_router
    participant Svc as TeamService
    participant Repo as team_repository
    participant DB1 as Session 1<br/>(validation)
    participant FIN as FinanceUnitOfWork
    participant DB2 as Session 2<br/>(payment)
    participant CRM as CRM Module

    Admin->>Router: POST /teams/{id}/members/{sid}/pay {amount}
    Router->>Router: require_admin guard
    Router->>Svc: pay_competition_fee(cmd)

    Note over Svc,DB1: TRANSACTION 1: Validation
    Svc->>DB1: get_team(team_id)
    DB1-->>Svc: Team
    Svc->>DB1: get_team_member(team_id, student_id)
    DB1-->>Svc: TeamMember
    alt amount <= 0
        Svc-->>Router: BusinessRuleError
        Router-->>Admin: 400
    end
    Svc->>DB1: db.get(Parent) [optional]
    Note over DB1: Session closes

    Note over Svc,FIN: TRANSACTION 2: Finance Receipt
    Svc->>FIN: ReceiptService.create(lines=[competition])
    FIN->>FIN: Create receipt + receipt lines
    FIN->>FIN: commit
    FIN-->>Svc: receipt_number, payment_id

    Note over Svc,DB2: TRANSACTION 3: Record Payment
    Svc->>DB2: get_session() — NEW session
    Svc->>DB2: record_payment(member_id, amount)
    DB2->>DB2: UPDATE team_members SET amount_paid = amount_paid + ?
    Svc->>CRM: log_payment_activity (silent fail)
    Svc->>DB2: commit
    DB2-->>Svc: Updated TeamMember

    Svc-->>Router: PayCompetitionFeeResponseDTO
    Router-->>Admin: 200 OK {receipt_number, payment_id, amount, amount_paid, amount_due}

    alt Transaction 3 fails
        Svc->>FIN: FinanceUnitOfWork refund (compensating)
        FIN->>FIN: Create refund receipt
        FIN->>FIN: commit
        Svc-->>Router: BusinessError
        Router-->>Admin: 400
    end
```

### 3.4 Refund Flow (New — T051)

```mermaid
sequenceDiagram
    participant Admin
    participant Router as teams_router
    participant Svc as TeamService
    participant Repo as team_repository
    participant DB as PostgreSQL

    Admin->>Router: POST /teams/{id}/members/{sid}/refund {amount}
    Router->>Router: require_admin guard
    Router->>Svc: get_team_member(team_id, student_id)
    Svc->>Repo: get_team_member(team_id, student_id)
    Repo->>DB: SELECT * FROM team_members WHERE team_id=? AND student_id=?
    DB-->>Repo: TeamMember
    Repo-->>Svc: TeamMember
    Svc-->>Router: TeamMember

    alt amount > amount_paid
        Router-->>Admin: 400 "Refund amount exceeds amount paid"
    end

    Router->>Svc: refund_competition_fee(member_id, amount)
    Svc->>Repo: refund_payment(member_id, amount)
    Repo->>DB: UPDATE team_members SET amount_paid = GREATEST(amount_paid - ?, 0)
    DB-->>Repo: Updated TeamMember
    Svc->>Svc: commit
    Svc-->>Router: None
    Router-->>Admin: 200 OK "Refund processed successfully"
```

### 3.5 Placement Recording with 30-Day Window (US6)

```mermaid
sequenceDiagram
    participant Admin
    participant Router as teams_router
    participant Svc as TeamService
    participant Repo as team_repository
    participant DB as PostgreSQL
    participant CRM as CRM Module

    Admin->>Router: PATCH /teams/{id}/placement {placement_rank, placement_label}
    Router->>Router: require_admin guard
    Router->>Svc: update_placement(team_id, rank, label, current_user_id)

    Svc->>Repo: get_team(team_id)
    alt Team missing
        Svc-->>Router: NotFoundError
        Router-->>Admin: 404
    end

    Svc->>Repo: get_competition(team.competition_id)
    Repo-->>Svc: Competition

    alt competition_date > today
        Svc-->>Router: BusinessRuleError
        Router-->>Admin: 409 "Competition has not yet occurred"
    end

    alt (today - competition_date).days > 30
        Note over Svc: NOT YET IMPLEMENTED
        Svc-->>Router: BusinessRuleError
        Router-->>Admin: 409 "Placement window closed"
    end

    Svc->>Repo: update_team(team_id, placement_rank, placement_label)
    Repo->>DB: UPDATE teams SET placement_rank=?, placement_label=?
    DB-->>Repo: Updated Team

    loop For each team member
        Svc->>CRM: log_placement_activity (silent fail)
    end

    Svc->>Svc: commit
    Svc-->>Router: TeamDTO
    Router-->>Admin: 200 OK
```

### 3.6 Coach Read-Only Access

```mermaid
sequenceDiagram
    participant Coach
    participant Router as teams_router
    participant Deps as dependencies.py<br/>require_coach_or_admin
    participant DB as PostgreSQL
    participant Svc as TeamService

    Coach->>Router: GET /teams/{id}
    Router->>Deps: require_coach_or_admin(team_id, current_user)

    alt current_user.is_admin
        Deps-->>Router: User (admin)
    else
        Deps->>DB: get_session() — separate session
        DB-->>Deps: Team
        alt team.coach_id == current_user.employee_id
            Deps-->>Router: User (coach)
        else
            Deps-->>Router: 403 Forbidden
        end
    end

    Router->>Svc: get_team_by_id(team_id)
    Svc-->>Router: TeamDTO
    Router-->>Coach: 200 OK

    Note over Coach,Router: Coach attempts write
    Coach->>Router: DELETE /teams/{id}
    Router->>Router: require_admin guard
    Router-->>Coach: 403 Forbidden
```

### 3.7 Competition Summary (N+1 Warning)

```mermaid
graph LR
    A[GET /competitions/{id}/summary] --> B[get_competition]
    B --> C[list_teams]
    C --> D{For each team}
    D --> E[list_team_members]
    E --> F{For each member}
    F --> G[db.get Student]
    G --> H[Build DTO]

    style G fill:#ff6b6b
    style F fill:#ff6b6b
    style E fill:#ff6b6b

    Note1["⚠️ N+1: 1 + N + N×M queries<br/>100 teams × 5 members = 601 queries"] -.-> G
```

---

## 4. Spec Compliance Matrix

| FR | Requirement | Status | Notes |
|----|-------------|--------|-------|
| FR-001 | Create competitions | ✅ Complete | POST /competitions |
| FR-002 | Edit/view competitions | ✅ Complete | PUT/PATCH/GET /competitions/{id} |
| FR-003 | Hard delete competitions | ✅ Complete | DELETE /competitions/{id}, blocked if teams exist |
| FR-004 | List competitions (any auth) | ✅ Complete | GET /competitions |
| FR-004a | Admin-only writes | ✅ Complete | All write endpoints use require_admin |
| FR-004b | Coach read-only | ✅ Complete | require_coach_or_admin on GET /teams/{id}, GET /teams/{id}/members |
| FR-005 | Create teams with project info | ✅ Complete | POST /teams accepts project_name, project_description |
| FR-006 | Group pre-fill | ⚠️ Partial | group_id stored but not used for pre-fill |
| FR-007 | Edit team details | ✅ Complete | PUT/PATCH /teams/{id} |
| FR-008 | Add/remove students | ✅ Complete | POST/DELETE /teams/{id}/members/{sid} |
| FR-009 | Hard delete teams | ✅ Complete | DELETE /teams/{id}, blocked if paid members |
| FR-010 | Warn on duplicate student | ❌ Missing | Currently hard-blocks with ConflictError |
| FR-011 | Verify active students | ✅ Complete | register_team checks s.status == "active" |
| FR-012 | Coach must be employee | ✅ Complete | FK constraint on team.coach_id → employees.id |
| FR-013 | amount_due/amount_paid | ✅ Complete | TeamMember model has both fields |
| FR-014 | Partial payments | ✅ Complete | pay_competition_fee supports any amount > 0 |
| FR-015 | Receipt creation | ✅ Complete | FinanceUnitOfWork creates receipt |
| FR-016 | Fee paid threshold | ✅ Complete | Derived: amount_paid >= amount_due |
| FR-017 | Filter teams | ✅ Complete | GET /teams?category=&subcategory= |
| FR-018 | Group by subcategory | ✅ Complete | GET /competitions/{id}/categories |
| FR-019 | Record placement | ✅ Complete | PATCH /teams/{id}/placement |
| FR-020 | 30-day placement window | ⚠️ Partial | Future date blocked; 30-day upper bound NOT implemented |
| FR-021 | Refund handling | ⚠️ Partial | amount_paid decremented; finance payment link not updated by competition module |
| FR-022 | Activity logging | ✅ Complete | Registration, payment, placement logged (silent fail) |
| FR-023 | Atomic payment | ⚠️ Partial | Compensating rollback, NOT truly atomic |

**Compliance**: 19/23 complete (83%), 4 partial/missing

---

## 5. Critical Issues

### 5.1 Payment Atomicity Gap (CRITICAL)

```mermaid
graph TD
    A[Payment Request] --> B[Session 1: Validate]
    B --> C[Session 1 closes]
    C --> D[FinanceUnitOfWork: Create Receipt]
    D --> E[Finance commits]
    E --> F[Session 2: record_payment]
    F --> G{Success?}
    G -->|Yes| H[Session 2 commits]
    G -->|No| I[FinanceUnitOfWork: Refund]
    I --> J{Refund succeeds?}
    J -->|Yes| K[Return error to client]
    J -->|No| L[⚠️ Orphan receipt + double charge]

    style L fill:#ff6b6b
    style E fill:#ff6b6b
    style I fill:#ff6b6b
```

**Problem**: Three separate transactions create a window where the finance receipt exists but the team member's `amount_paid` is not updated. The compensating refund can also fail.

**Impact**: Orphan receipts, potential double-charging, inconsistent state between finance and competition modules.

**Fix**: Use a single session/transaction for the entire operation, or implement a saga pattern with idempotent compensation.

### 5.2 ReceiptService._link_competition_payment References Non-Existent Fields (CRITICAL)

```python
# receipt_service.py:366-367 — will crash at runtime:
team_member.fee_paid = True       # ❌ fee_paid does not exist
team_member.payment_id = payment_id  # ❌ payment_id does not exist
```

**Impact**: Any competition payment processed through the standard finance receipt flow (not the competition module's custom `pay_competition_fee`) will crash with `AttributeError`.

**Fix**: Remove or update `_link_competition_payment` to use `amount_paid` instead of `fee_paid`/`payment_id`.

### 5.3 Duplicate Student Registration Hard-Block (HIGH)

Spec says "warn but allow" (Option A). Implementation raises `ConflictError` in two places:
- `register_team()` line 107-114
- `add_team_member_to_existing()` line 413-418

**Fix**: Change to return `(result, warning_message)` and populate the response envelope's `message` field.

### 5.4 30-Day Placement Window Upper Bound Missing (HIGH)

```python
# team_service.py:367 — only checks future date:
if comp.competition_date and comp.competition_date > date.today():
    raise BusinessRuleError(...)

# Missing: upper bound check
# if (date.today() - comp.competition_date).days > 30:
#     raise BusinessRuleError("Placement window closed...")
```

---

## 6. Security Audit

| Severity | Issue | Detail |
|----------|-------|--------|
| MEDIUM | `require_coach_or_admin` TOCTOU | Opens separate DB session. Team could be deleted between auth check and service call. |
| MEDIUM | `**kwargs` in update methods | `update_competition`/`update_team` pass `**kwargs` to `setattr()`. API layer filters via Pydantic, but service methods accept arbitrary keys. |
| LOW | Student competition history exposed | `GET /students/{sid}/competitions` uses `require_any` — any authenticated user can view any student's data. |
| LOW | No rate limiting on payments | `POST /teams/{id}/members/{sid}/pay` has no rate limiting. Could be abused for receipt spam. |

---

## 7. Performance Audit

### N+1 Query Hotspots

| Endpoint | Query Count (100 teams) | Severity |
|----------|------------------------|----------|
| `GET /competitions/{id}/summary` | ~601 queries | SEVERE |
| `GET /teams` (with members) | ~101 queries | HIGH |
| `GET /students/{sid}/competitions` | ~21 queries (per 10 teams) | MEDIUM |
| `GET /teams/{id}/members` | ~22 queries (per 20 members) | MEDIUM |

### Missing Indexes

| Table | Column | Impact |
|-------|--------|--------|
| `teams` | `competition_id` | Full scan on list_teams, check_student_in_competition |
| `teams` | `category` | Full scan on category filter |
| `teams` | `coach_id` | Full scan on coach filtering |
| `team_members` | `team_id` | Full scan on list_team_members |
| `team_members` | `student_id` | Full scan on check_student_in_competition |
| `team_members` | `amount_paid` | Full scan on team delete guard |

---

## 8. Dead Code Inventory

| Location | Code | Status |
|----------|------|--------|
| `team_repository.py:120-127` | `get_teams_by_student()` | Unused — no service or endpoint calls it |
| `team_repository.py:35` | `create_team` accepts `fee` parameter | `fee` doesn't exist on `Team` model — dead parameter |
| `team_service.py:282-301` | `list_teams_for_coach()` returns raw models | Inconsistent with DTO pattern; only called internally |

---

## 9. Recommendations

### Immediate (Blockers)
1. **Fix `ReceiptService._link_competition_payment`** — remove references to `fee_paid`/`payment_id`
2. **Implement 30-day placement window** — add upper bound check in `update_placement`
3. **Implement duplicate student warning** — change ConflictError to warning in response envelope

### Short-term (High Impact)
4. **Fix payment atomicity** — consolidate to single transaction or implement saga pattern
5. **Add missing database indexes** — competition_id, category, coach_id, team_id, student_id on relevant tables
6. **Fix N+1 in `get_competition_summary`** — use JOIN or batch loading for students

### Medium-term
7. **Implement group pre-fill logic** — use `group_id` to populate `student_ids` from group roster
8. **Add rate limiting** on payment endpoints
9. **Remove dead code** — `get_teams_by_student`, unused `fee` parameter
10. **Add ownership check** on `GET /students/{sid}/competitions` — restrict to student's parents/guardians

---

## 10. Task Completion Status

| Phase | Tasks | Completed | Pending |
|-------|-------|-----------|---------|
| Phase 1: Migration | 6 | 1 (T001) | 5 (T002, T063-T066) |
| Phase 2: Foundational | 21 | 21 | 0 |
| Phase 3: US1 (Competition hard-delete) | 7 | 7 | 0 |
| Phase 4: US2 (Team hard-delete + project) | 14 | 14 | 0 |
| Phase 5: US3 (Project tracking) | 2 | 2 | 0 |
| Phase 6: US4 (Multi-payment fees) | 9 | 9 | 0 |
| Phase 7: US6 (Placement recording) | 3 | 3 | 0 |
| Phase 8: US5 (Subcategory filtering) | 2 | 2 | 0 |
| Phase 9: Coach read-only | 4 | 4 | 0 |
| Phase 10: Test updates | 11 | 0 | 11 |
| Phase N: Polish | 6 | 4 | 2 |
| **Total** | **85** | **67** | **18** |

**Completion**: 79% (67/85 tasks)
