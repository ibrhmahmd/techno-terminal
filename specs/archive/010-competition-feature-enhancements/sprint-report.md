# Sprint Report: Competition Module Enhancements (010)

**Date**: 2026-05-17
**Branch**: `010-competition-feature-enhancements`
**Migration**: `054_competition_hard_delete_and_payment_model.sql`

---

## 1. Executive Summary

The competition module was refactored across **6 dimensions**:

| Dimension | Before | After |
|-----------|--------|-------|
| **Delete model** | Soft delete (`deleted_at`/`deleted_by`) on Competition + Team | Hard delete — permanent removal from database |
| **Fee tracking** | Single boolean `fee_paid` + single `payment_id` per team member | Enrollment-style `amount_due` + `amount_paid` with partial payment support |
| **Team info** | No project metadata | `project_name` + `project_description` on every team |
| **Group linkage** | `GroupCompetitionParticipation` table linking groups → teams → competitions | `group_id` on teams is a one-time student pre-fill source only; participation table dropped |
| **Access control** | All reads open to `require_any` | Coaches can read their own teams only; admins retain full access |
| **Dead code** | 7 files (competition slice, router, schemas, tests) | All removed — zero remaining references |

**Stats**: 42 files changed, 893 insertions, 1,744 deletions.

---

## 2. Database Schema Changes

### 2.1 Competition Table

```
BEFORE                                  AFTER
┌────────────────────────────┐         ┌────────────────────────────┐
│ competitions               │         │ competitions               │
├────────────────────────────┤         ├────────────────────────────┤
│ PK id              INT     │         │ PK id              INT     │
│    name            VARCHAR │         │    name            VARCHAR │
│    edition         VARCHAR │    →    │    edition         VARCHAR │
│    edition_year    INT     │         │    edition_year    INT     │
│    competition_date DATE   │         │    competition_date DATE   │
│    location        VARCHAR │         │    location        VARCHAR │
│    notes           TEXT    │         │    notes           TEXT    │
│    fee_per_student DECIMAL │         │    fee_per_student DECIMAL │
│    created_at      TIMESTMP│         │    created_at      TIMESTMP│
│ X  deleted_at      TIMESTMP│         └────────────────────────────┘
│ X  deleted_by      INT     │
└────────────────────────────┘
  DROPPED: deleted_at, deleted_by
```

**Impact**: `DELETE FROM competitions WHERE id = :id` — blocked if any teams reference this competition (business rule enforced at service layer).

### 2.2 Team Table

```
BEFORE                                  AFTER
┌────────────────────────────┐         ┌────────────────────────────┐
│ teams                      │         │ teams                      │
├────────────────────────────┤         ├────────────────────────────┤
│ PK id              INT     │         │ PK id              INT     │
│ FK competition_id  INT     │         │ FK competition_id  INT     │
│    team_name       VARCHAR │         │    team_name       VARCHAR │
│    category        CITEXT  │         │    category        CITEXT  │
│    subcategory     CITEXT  │    →    │    subcategory     CITEXT  │
│ FK group_id        INT?    │         │ FK group_id        INT?    │
│ FK coach_id        INT?    │         │ FK coach_id        INT?    │
│    placement_rank  INT?    │         │    placement_rank  INT?    │
│    placement_label VARCHAR │         │    placement_label VARCHAR │
│    notes           TEXT    │         │    notes           TEXT    │
│    created_at      TIMESTMP│         │    created_at      TIMESTMP│
│ X  deleted_at      TIMESTMP│         │ +  project_name    VARCHAR │
│ X  deleted_by      INT     │         │ +  project_description TEXT│
└────────────────────────────┘         └────────────────────────────┘
  DROPPED: deleted_at, deleted_by        ADDED: project_name, project_description
```

### 2.3 TeamMember Table

```
BEFORE                                  AFTER
┌────────────────────────────┐         ┌────────────────────────────┐
│ team_members               │         │ team_members               │
├────────────────────────────┤         ├────────────────────────────┤
│ PK id              INT     │         │ PK id              INT     │
│ FK team_id         INT     │         │ FK team_id         INT     │
│ FK student_id      INT     │         │ FK student_id      INT     │
│ X  member_share    DECIMAL │    →    │ +  amount_due      DECIMAL │
│ X  fee_paid        BOOLEAN │         │ +  amount_paid     DECIMAL │
│ X  payment_id      INT?    │         └────────────────────────────┘
└────────────────────────────┘
  DROPPED: member_share, fee_paid, payment_id
  ADDED: amount_due (DECIMAL 10,2), amount_paid (DECIMAL 10,2)
```

**Payment status is now derived, not stored**:

| Condition | Derived Status |
|-----------|---------------|
| `amount_paid >= amount_due AND amount_paid > 0` | Fully paid |
| `amount_paid > 0 AND amount_paid < amount_due` | Partially paid |
| `amount_paid = 0 AND amount_due > 0` | Unpaid |
| `amount_due = 0` | No fee required |

### 2.4 Payment Table

```
BEFORE                                  AFTER
┌────────────────────────────┐         ┌────────────────────────────┐
│ payments                   │         │ payments                   │
├────────────────────────────┤         ├────────────────────────────┤
│ PK id              INT     │         │ PK id              INT     │
│ FK receipt_id      INT     │         │ FK receipt_id      INT     │
│ FK student_id      INT     │         │ FK student_id      INT     │
│ FK enrollment_id   INT?    │    →    │ FK enrollment_id   INT?    │
│    amount          DECIMAL │         │ FK team_member_id  INT?    │ ← NEW
│    ... other fields        │         │    amount          DECIMAL │
└────────────────────────────┘         │    ... other fields        │
                                       └────────────────────────────┘
  ADDED: team_member_id (FK → team_members.id)
  Mirrors the existing enrollment_id pattern for linking payments to entities.
```

### 2.5 Dropped: GroupCompetitionParticipation

```
DROPPED TABLE
┌────────────────────────────────────────┐
│ group_competition_participation        │
├────────────────────────────────────────┤
│ PK id                          INT     │
│ FK group_id                    INT     │
│ FK team_id                     INT     │
│ FK competition_id              INT     │
│    entered_at                  TIMESTMP│
│    left_at                     TIMESTMP│
│    is_active                   BOOLEAN │
│    final_placement             INT?    │
│    notes                       TEXT    │
└────────────────────────────────────────┘

The group_id on teams remains as a one-time student pre-fill source.
No lifecycle tracking persists after team creation.
```

---

## 3. API Contract Changes

### 3.1 Removed Endpoints (6 total)

| Method | Path | Reason |
|--------|------|--------|
| `GET` | `/api/v1/competitions/deleted` | No soft delete |
| `POST` | `/api/v1/competitions/{id}/restore` | No soft delete |
| `GET` | `/api/v1/teams/deleted` | No soft delete |
| `POST` | `/api/v1/teams/{id}/restore` | No soft delete |
| `GET` | `/api/v1/academics/groups/{gid}/competitions` | Table dropped |
| `POST` | `/api/v1/academics/groups/{gid}/competitions/{cid}/register` | Table dropped |
| `PATCH` | `/api/v1/academics/groups/{gid}/competitions/{pid}/complete` | Table dropped |
| `DELETE` | `/api/v1/academics/groups/{gid}/competitions/{pid}` | Table dropped |
| `GET` | `/api/v1/academics/groups/{gid}/teams` | Table dropped |
| `POST` | `/api/v1/academics/groups/{gid}/teams/{tid}/link` | Table dropped |
| `GET` | `/api/v1/academics/groups/{gid}/competitions/analytics` | Table dropped |

### 3.2 Modified Endpoints

#### `GET /api/v1/competitions`

```diff
- Query param: include_deleted (bool, default false)
+ No query params — returns all competitions
```

#### `DELETE /api/v1/competitions/{id}`

```diff
- Summary: "Soft delete competition"
+ Summary: "Hard delete competition"
- Body: { deleted_by: user_id }  (implicit via auth)
+ No body — permanent deletion
```

#### `DELETE /api/v1/teams/{id}`

```diff
- Summary: "Soft delete team"
+ Summary: "Hard delete team"
- Check: if any member.fee_paid → block
+ Check: if any member.amount_paid > 0 → block
```

#### `POST /api/v1/teams`

```diff
  Request body:
    competition_id: int
    team_name: str
    category: str
    subcategory?: str
+   project_name?: string     ← NEW
+   project_description?: string  ← NEW
    student_ids: int[]
    student_fees?: { student_id: float }
    coach_id?: int
    group_id?: int
    notes?: string
```

#### `POST /api/v1/teams/{id}/members`

```diff
  Request body:
    student_id: int
-   fee: float
+   amount_due: float         ← RENAMED
```

#### `POST /api/v1/teams/{id}/members/{student_id}/pay`

```diff
  BEFORE (query params):
    parent_id?: int (query param)

  AFTER (request body):
    amount: float              ← NEW — payment amount for partial payments
    parent_id?: int            ← MOVED to body
```

#### `GET /api/v1/teams`

```diff
  BEFORE: Any authenticated user sees all teams
+ AFTER:  Coaches see only teams where coach_id matches their employee_id
          Admins see all teams (unchanged)
```

#### `GET /api/v1/teams/{id}` and `GET /api/v1/teams/{id}/members`

```diff
- Auth: require_any (any authenticated user)
+ Auth: require_coach_or_admin (admin OR team's coach)
```

### 3.3 DTO Changes

#### TeamMemberDTO

```diff
  {
    id: int,
    team_id: int,
    student_id: int,
-   member_share: float,
-   fee_paid: bool,
-   payment_id: int?,
+   amount_due: float,
+   amount_paid: float,
  }
```

#### TeamMemberRosterDTO

```diff
  {
    team_member_id: int,
    team_id: int,
    team_name: str,
    student_id: int,
    student_name: str,
-   member_share: float,
-   fee_paid: bool,
-   payment_id: int?,
+   amount_due: float,
+   amount_paid: float,
  }
```

#### PayCompetitionFeeResponseDTO

```diff
  {
    receipt_number: str,
    payment_id: int,
    amount: float,
+   amount_paid: float,    ← NEW — running total after this payment
+   amount_due: float,     ← NEW — for context
  }
```

#### TeamDTO

```diff
  {
    id: int,
    competition_id: int,
    category: str,
    subcategory?: str,
    group_id?: int,
    team_name: str,
    coach_id?: int,
+   project_name?: string,          ← NEW
+   project_description?: string,   ← NEW
    placement_rank?: int,
    placement_label?: str,
    notes?: str,
    created_at: datetime,
  }
```

#### RegisterTeamInput

```diff
  {
    competition_id: int,
    team_name: str,
    category: str,
    subcategory?: str,
+   project_name?: string,          ← NEW
+   project_description?: string,   ← NEW
    student_ids: int[],
    student_fees?: { student_id: float },
    coach_id?: int,
    group_id?: int,
    notes?: str,
  }
```

---

## 4. New Workflows

### 4.1 Competition Hard Delete

```
┌──────────┐     DELETE /competitions/{id}      ┌─────────────────────────────────┐
│  Admin   │ ──────────────────────────────────► │  CompetitionService             │
│          │                                     │  delete_competition(id)         │
│          │                                     │                                 │
│          │                                     │  1. List teams for competition  │
│          │                                     │  2. If teams exist → 409 error  │
│          │                                     │  3. Hard delete (db.delete)     │
│          │                                     │  4. Commit                      │
│          │                                     └─────────────────────────────────┘
│          │ ◄──────────────────────────────────
│  200 OK  │   { success: true, data: true }
│          │
│          │   OR
│          │
│  409     │   { success: false, error: "BusinessRuleError",
│          │     message: "Cannot delete competition that has teams..." }
└──────────┘
```

**Key difference from before**: No `deleted_at` timestamp set. The row is physically removed from the database. No restore endpoint exists.

### 4.2 Team Registration with Project Info

```
┌──────────┐     POST /teams                          ┌──────────────────────────────────┐
│  Admin   │ ────────────────────────────────────────► │  TeamService                     │
│          │  {                                       │  register_team(cmd)              │
│          │    competition_id: 1,                    │                                  │
│          │    team_name: "RoboCup Alpha",           │  1. Validate competition exists  │
│          │    category: "Robotics",                 │  2. Validate category/subcategory│
│          │    subcategory: "Autonomous",            │  3. Validate team name unique    │
│          │    project_name: "Line Follower v2",     │  4. Validate students active     │
│          │    project_description: "...",           │  5. Check no student in 2 teams  │
│          │    student_ids: [10, 20, 30],            │  6. CREATE team (with project)   │
│          │    student_fees: {10: 50, 20: 50},       │  7. FOR each student:            │
│          │    group_id: 5,                          │     CREATE team_member           │
│          │    coach_id: 3,                          │     (amount_due from student_fees│
│          │  }                                       │      or 0)                       │
│          │                                          │  8. Log activity for each student│
│          │                                          │  9. Commit                       │
│          │                                          │                                  │
│          │                                          │  NOTE: No GroupCompetitionPartic.│
│          │                                          │  created (table dropped)         │
│          │                                          └──────────────────────────────────┘
│          │ ◄───────────────────────────────────────
│  201     │   { team: {..., project_name: "Line Follower v2"},
│          │     members_added: 3 }
└──────────┘
```

### 4.3 Partial Payment Flow (Multi-Payment)

```
┌──────────┐     POST /teams/{id}/members/{sid}/pay     ┌──────────────────────────────────┐
│  Admin   │ ─────────────────────────────────────────► │  TeamService                     │
│          │  {                                         │  pay_competition_fee(cmd)        │
│          │    amount: 20.0,    ← NEW: partial amount  │                                  │
│          │    parent_id: 5,                           │  1. Validate team + member exist │
│          │  }                                         │  2. Validate amount > 0          │
│          │                                            │  3. Create receipt (Finance UoW) │
│          │                                            │     payment_type = "competition" │
│          │                                            │  4. record_payment(member_id,    │
│          │                                            │                   amount)        │
│          │                                            │     → amount_paid += amount      │
│          │                                            │  5. Log payment activity         │
│          │                                            │  6. Commit                       │
│          │                                            │                                  │
│          │                                            │  ON FAILURE:                     │
│          │                                            │  → Refund payment atomically     │
│          │                                            │  → Raise BusinessRuleError       │
│          │                                            └──────────────────────────────────┘
│          │ ◄─────────────────────────────────────────
│  200     │   { receipt_number: "REC-2026-0042",
│          │     payment_id: 99,
│          │     amount: 20.0,
│          │     amount_paid: 20.0,    ← running total
│          │     amount_due: 50.0 }    ← for context
└──────────┘

  PAYMENT PROGRESSION (amount_due = 50):

  Payment 1: amount=20  →  amount_paid=20  →  Status: PARTIAL
  Payment 2: amount=20  →  amount_paid=40  →  Status: PARTIAL
  Payment 3: amount=10  →  amount_paid=50  →  Status: PAID
  Payment 4: amount=5   →  amount_paid=55  →  Status: PAID (overpayment tracked)
```

### 4.4 Refund Flow

```
┌──────────────────────────────────┐
│  Finance Module (RefundService)  │
│                                  │
│  1. Create refund payment        │
│     (transaction_type = "refund")│
│  2. Call _unlink_competition_    │
│     payment(original_payment_id) │
│                                  │
│  3. Lookup Payment by ID         │
│  4. If payment.team_member_id:   │
│     → Get TeamMember by ID       │
│     → amount_paid -= payment_amt │
│     → (min 0.0)                  │
│  5. Commit                       │
└──────────────────────────────────┘

  BEFORE (old model):
    Set fee_paid = False, payment_id = None
    (binary — all or nothing)

  AFTER (new model):
    Decrement amount_paid by refund amount
    (supports partial refunds)
```

### 4.5 Coach Read-Only Access

```
┌──────────┐     GET /teams/{id}                  ┌──────────────────────────────────┐
│  Coach   │ ────────────────────────────────────► │  require_coach_or_admin          │
│  (emp:3) │                                       │  dependency                      │
│          │                                       │                                  │
│          │                                       │  1. If user.is_admin → ALLOW     │
│          │                                       │  2. Lookup Team by id            │
│          │                                       │  3. If team.coach_id ==          │
│          │                                       │     user.employee_id → ALLOW     │
│          │                                       │  4. Else → 403 Forbidden         │
│          │                                       └──────────────────────────────────┘
│          │ ◄───────────────────────────────────
│  200 OK  │   { team: { id: 1, coach_id: 3, ... } }
│          │
│          │
│  Coach tries: DELETE /teams/{id}
│          │ ────────────────────────────────────► │  require_admin                   │
│          │                                       │  → 403 Forbidden (not admin)     │
└──────────┘

  WRITE ENDPOINTS (all require_admin):
    POST /teams, PUT/PATCH /teams/{id}, DELETE /teams/{id}
    POST /teams/{id}/members, DELETE /teams/{id}/members/{sid}
    POST /teams/{id}/members/{sid}/pay
    PATCH /teams/{id}/placement

  READ ENDPOINTS (require_coach_or_admin):
    GET /teams (coaches see only their teams, admins see all)
    GET /teams/{id}
    GET /teams/{id}/members
    GET /students/{sid}/competitions
```

### 4.6 Team Hard Delete

```
┌──────────┐     DELETE /teams/{id}               ┌──────────────────────────────────┐
│  Admin   │ ────────────────────────────────────► │  TeamService                     │
│          │                                       │  delete_team(id)                 │
│          │                                       │                                  │
│          │                                       │  1. List team members            │
│          │                                       │  2. FOR each member:             │
│          │                                       │     IF member.amount_paid > 0    │
│          │                                       │        → 409 BusinessRuleError   │
│          │                                       │  3. Hard delete team (db.delete) │
│          │                                       │  4. Commit                       │
│          │                                       └──────────────────────────────────┘
│          │ ◄───────────────────────────────────
│  200 OK  │   { success: true, data: true }
│          │
│          │   OR (if any member has paid):
│  409     │   { success: false, error: "BusinessRuleError",
│          │     message: "Cannot delete team with members who have paid fees." }
└──────────┘
```

---

## 5. Service Layer Changes

### 5.1 CompetitionService

| Method | Before | After |
|--------|--------|-------|
| `list_competitions()` | `list_competitions(include_deleted=False)` | `list_competitions()` — no filter |
| `delete_competition()` | Sets `deleted_at`, takes `deleted_by` | `db.delete()` — hard delete |
| `restore_competition()` | Restores `deleted_at = NULL` | **REMOVED** |
| `list_deleted_competitions()` | Lists soft-deleted | **REMOVED** |

### 5.2 TeamService

| Method | Before | After |
|--------|--------|-------|
| `register_team()` | Creates `GroupCompetitionParticipation` if `group_id` set | No participation created; passes `project_name`/`project_description` |
| `delete_team()` | Sets `deleted_at`; checks `m.fee_paid` | `db.delete()`; checks `m.amount_paid > 0` |
| `restore_team()` | Restores `deleted_at = NULL` | **REMOVED** |
| `list_deleted_teams()` | Lists soft-deleted | **REMOVED** |
| `remove_team_member()` | Checks `member.fee_paid` | Checks `member.amount_paid > 0` |
| `add_team_member_to_existing()` | Parameter `fee` | Parameter `amount_due` |
| `list_team_members()` | Returns `member_share`, `fee_paid`, `payment_id` | Returns `amount_due`, `amount_paid` |
| `pay_competition_fee()` | Creates receipt, calls `mark_fee_paid(payment_id)` | Creates receipt, calls `record_payment(member_id, amount)` |
| `unmark_team_fee_for_payment()` | Sets `fee_paid=False`, `payment_id=None` | **REMOVED** — replaced by `refund_competition_fee()` |
| `update_placement()` | Syncs to `GroupCompetitionParticipation` | No sync (table dropped) |
| `list_teams_for_coach()` | **N/A** | NEW — filters by `coach_id` |

### 5.3 Repository Layer

| Function | Before | After |
|----------|--------|-------|
| `delete_competition()` | Sets `deleted_at`, `deleted_by` | `db.delete(c)` |
| `restore_competition()` | Sets `deleted_at = NULL` | **REMOVED** |
| `list_deleted_competitions()` | `WHERE deleted_at IS NOT NULL` | **REMOVED** |
| `list_competitions()` | `WHERE deleted_at IS NULL` (optional) | No filter |
| `delete_team()` | Sets `deleted_at`, `deleted_by` | `db.delete(t)` |
| `restore_team()` | Sets `deleted_at = NULL` | **REMOVED** |
| `list_deleted_teams()` | `WHERE deleted_at IS NOT NULL` | **REMOVED** |
| `list_teams()` | `WHERE deleted_at IS NULL` (optional) | No filter |
| `get_team()` | Checks `deleted_at` | Direct `db.get()` |
| `create_team()` | No project fields | Accepts `project_name`, `project_description` |
| `add_team_member()` | `member_share`, `fee_paid=False` | `amount_due`, `amount_paid=0.0` |
| `mark_fee_paid()` | Sets `fee_paid=True`, `payment_id` | **REMOVED** |
| `get_members_by_payment_id()` | `WHERE payment_id = :id` | **REMOVED** |
| `record_payment()` | **N/A** | NEW — `amount_paid += amount` |
| `refund_payment()` | **N/A** | NEW — `amount_paid -= amount` (min 0) |

---

## 6. Dead Code Removed

| File | Type | Reason |
|------|------|--------|
| `app/modules/academics/group/competition/` (5 files) | Slice | `GroupCompetitionParticipation` table dropped |
| `app/api/routers/academics/group_competitions_router.py` | Router | 7 endpoints for dropped table |
| `app/api/schemas/academics/competition.py` | Schema | DTOs for dropped router |
| `app/api/schemas/academics/team.py` | Schema | `TeamPublic` for dropped router |
| `tests/test_academics_competitions.py` | Test | 414 lines of dead tests |

**Dead code audit result**: ZERO remaining references to `GroupCompetitionParticipation`, `fee_paid`, `payment_id` (competitions context), `member_share`, `restore_*`, `list_deleted_*`, `deleted_at` (competitions context) across the entire codebase.

---

## 7. Migration Summary (054)

```sql
-- Phase 1: Drop group_competition_participation table
DROP TABLE IF EXISTS group_competition_participation CASCADE;

-- Phase 2: Add project tracking to teams
ALTER TABLE teams ADD COLUMN project_name VARCHAR(500);
ALTER TABLE teams ADD COLUMN project_description TEXT;

-- Phase 3: Migrate team_members fee model
ALTER TABLE team_members ADD COLUMN amount_due DECIMAL(10,2) DEFAULT 0.00;
ALTER TABLE team_members ADD COLUMN amount_paid DECIMAL(10,2) DEFAULT 0.00;
UPDATE team_members SET amount_due = member_share WHERE amount_due = 0;
UPDATE team_members SET amount_paid = amount_due WHERE fee_paid = TRUE AND amount_paid = 0;
ALTER TABLE team_members DROP COLUMN member_share;
ALTER TABLE team_members DROP COLUMN fee_paid;
ALTER TABLE team_members DROP COLUMN payment_id;

-- Phase 4: Add team_member_id to payments
ALTER TABLE payments ADD COLUMN team_member_id INTEGER REFERENCES team_members(id);

-- Phase 5: Remove soft delete from competitions
ALTER TABLE competitions DROP COLUMN IF EXISTS deleted_at;
ALTER TABLE competitions DROP COLUMN IF EXISTS deleted_by;

-- Phase 6: Remove soft delete from teams
ALTER TABLE teams DROP COLUMN IF EXISTS deleted_at;
ALTER TABLE teams DROP COLUMN IF EXISTS deleted_by;
```

**Data migration**: Existing `member_share` values migrate to `amount_due`. Existing `fee_paid = TRUE` records get `amount_paid = amount_due` (fully paid). All other records get `amount_paid = 0`.

---

## 8. Risk & Rollback

| Risk | Mitigation |
|------|-----------|
| Migration drops `GroupCompetitionParticipation` | `CASCADE` ensures dependent objects are cleaned; data is unrecoverable after migration |
| `amount_paid` derivation may differ from old `fee_paid` | Migration sets `amount_paid = amount_due` for all previously `fee_paid = TRUE` records — equivalent state |
| Refund logic changes from boolean to decrement | `_unlink_competition_payment` now uses `team_member_id` on payment row — more precise than previous `payment_id` scan |
| Coach guard may block legitimate reads | Admins bypass the guard entirely; only non-admin coaches are affected |

**Rollback**: Not recommended. Migration 054 drops tables and columns. A rollback would require restoring from a pre-migration database backup.

---

## 9. Pending Items

| Task | Status | Notes |
|------|--------|-------|
| T002: Apply migration 054 to Supabase | ⏳ Pending | Must run before deployment |
| T064: `pytest tests/test_competitions.py -v` | ⏳ Pending | Test suite needs execution |
| T065: `pytest tests/test_academics_competitions.py -v` | ⏳ Complete | File deleted — no tests to run |
| T066: Full test suite `pytest tests/ -v` | ⏳ Pending | Integration validation |
| T069: Quickstart validation | ⏳ Pending | Manual smoke test of 4 integration scenarios |
