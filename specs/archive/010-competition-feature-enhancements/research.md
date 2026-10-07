# Research: Competition Module Enhancements

## Current State

### Competition Model (`competition_models.py`)
- **Fields**: `id`, `name`, `edition`, `edition_year`, `competition_date`, `location`, `notes`, `fee_per_student`, `created_at`, `deleted_at`, `deleted_by`
- Soft-delete with `deleted_at` + `deleted_by` columns

### Team Model (`team_models.py`)
- **Fields**: `id`, `competition_id`, `group_id`, `team_name`, `coach_id`, `category`, `subcategory`, `placement_rank`, `placement_label`, `notes`, `created_at`, `deleted_at`, `deleted_by`
- Soft-delete with `deleted_at` + `deleted_by` columns

### TeamMember Model (`team_models.py`)
- **Fields**: `id`, `team_id`, `student_id`, `member_share` (float), `fee_paid` (bool), `payment_id` (FK to payments.id)

### GroupCompetitionParticipation (`group_level_models.py`)
- Independent table in academics module — links groups to teams to competitions
- Has `group_id`, `team_id`, `competition_id`, `is_active`, `final_placement`, `entered_at`, `left_at`

### Payment Model
- Uses Finance module: `ReceiptService.create()` with `payment_type="competition"`
- `PayCompetitionFeeInput` → creates receipt with lines → gets `payment_id` → calls `mark_fee_paid()`
- Refund path: `unmark_team_fee_for_payment()` sets `fee_paid=False`, `payment_id=None`
- **Problem**: Current model supports only ONE payment per team member (single `payment_id`). No partial payments.

### Services
- `CompetitionService`: CRUD + summary + categories + soft-delete management
- `TeamService`: team registration, members CRUD, payment, placement, activity logging

## Key Research Findings

### 1. Enrollment Payment Pattern (Target)
The enrollments module tracks fees differently:
- `Enrollment.amount_due` on the enrollment record itself
- `amount_paid` is computed via SQL view summing payments linked by `enrollment_id` on `payments` table
- Multiple payments per enrollment supported naturally
- `Payments` table already has `enrollment_id` FK for this purpose

**Adoption**: Add `team_member_id` FK to `payments` table, add `amount_due` + `amount_paid` to `TeamMember`, drop `fee_paid` boolean and `payment_id`. Compute payment status as `amount_paid >= amount_due`.

### 2. Hard Delete Implications
Current soft-delete pattern uses `deleted_at` + `deleted_by` on Competition and Team.

**Removal**:
- Drop both columns from `competitions` and `teams` tables (migration `054`)
- Remove all repository functions: `delete_competition` (replace with hard delete), `restore_competition`, `list_deleted_competitions`, `restore_team`, `list_deleted_teams`
- Update `list_competitions` / `list_teams` — remove `include_deleted` flag and `deleted_at IS NULL` filters
- Remove restore endpoints from routers
- Remove `/competitions/deleted` and `/teams/deleted` endpoints
- Cascade hard delete: delete team members first, then team, then remove participation records (for competition: block if any teams exist — already implemented)

### 3. Group as Student Source
Current code already supports `group_id` on Team model and auto-creates `GroupCompetitionParticipation` in `register_team()`.
**Change**: Remove `GroupCompetitionParticipation` auto-creation from `register_team()`. The group serves as a student roster pre-fill source ONLY — not a continuing participation link. Drop the `GroupCompetitionParticipation` table entirely (migration).

### 4. Coach Read-Only Access
New concept — coaches (employees linked via `team.coach_id`) can read their own teams but not modify.
**Implementation**: Add a `require_coach_or_admin` guard in `dependencies.py` or an inline check in the router. Check `current_user.employee.id == team.coach_id`.

### 5. Subcategory Filtering
Already supported by `list_teams(competition_id, category, subcategory)` — both `category` and `subcategory` query params work. No structural change needed; just verify the existing router handles it (it does — line 48-58 in teams_router.py).

### 6. Payment Atomicity
Current `pay_competition_fee()` already has a try/except with refund rollback. The new multi-payment model needs to maintain this with the added `amount_paid += payment_amount` update. Keep same pattern: create receipt → update amount_paid → commit both atomically.

### 7. State Derivation
No explicit status field needed:
- **Payment status**: `amount_paid >= amount_due` → "paid", `amount_paid > 0` → "partial", else "unpaid"
- **Placement status**: `placement_rank IS NOT NULL` → placed
- **Competition status**: derive from `competition_date` vs today

### 8. Student Activity Logging
Three activity points already implemented:
- Registration: `_log_team_registration_activity()`
- Payment: `_log_payment_activity()`
- Placement: `_log_placement_activity()`

These can be reused with minor field updates (amount, not fee_paid boolean).

## Migration Plan (054)

### New Migration: `054_competition_hard_delete_and_payment_model.sql`

```sql
-- 1. Drop GroupCompetitionParticipation table
DROP TABLE IF EXISTS group_competition_participation CASCADE;

-- 2. Add project_name, project_description to teams
ALTER TABLE teams ADD COLUMN project_name VARCHAR(500);
ALTER TABLE teams ADD COLUMN project_description TEXT;

-- 3. Replace fee model on team_members
ALTER TABLE team_members ADD COLUMN amount_due DECIMAL(10,2) DEFAULT 0.00;
ALTER TABLE team_members ADD COLUMN amount_paid DECIMAL(10,2) DEFAULT 0.00;
ALTER TABLE team_members DROP COLUMN fee_paid;
ALTER TABLE team_members DROP COLUMN payment_id;

-- 4. Add team_member_id to payments table (like enrollment_id)
ALTER TABLE payments ADD COLUMN team_member_id INTEGER REFERENCES team_members(id);

-- 5. Remove soft delete columns from competitions
ALTER TABLE competitions DROP COLUMN deleted_at;
ALTER TABLE competitions DROP COLUMN deleted_by;

-- 6. Remove soft delete columns from teams
ALTER TABLE teams DROP COLUMN deleted_at;
ALTER TABLE teams DROP COLUMN deleted_by;
```

## Affected Files

### Models
- `app/modules/competitions/models/team_models.py` — add project_name, project_description, amount_due, amount_paid; remove fee_paid, payment_id
- `app/modules/competitions/models/competition_models.py` — remove deleted_at, deleted_by
- `app/modules/finance/models/payment.py` — add team_member_id FK

### Schemas (Module)
- `app/modules/competitions/schemas/team_schemas.py` — update TeamMemberDTO, RegisterTeamInput, TeamMemberRosterDTO, PayCompetitionFeeInput, PayCompetitionFeeResponseDTO; remove `fee_paid`, `payment_id`; add `amount_due`, `amount_paid`, `project_name`, `project_description`

### Schemas (API)
- `app/api/schemas/competitions/team_schemas.py` — update UpdateTeamInput with project_name, project_description, amount_due

### Repositories
- `app/modules/competitions/repositories/competition_repository.py` — hard delete, remove restore/list_deleted
- `app/modules/competitions/repositories/team_repository.py` — hard delete, remove restore/list_deleted, update mark_fee_paid -> record_payment, add refund_payment

### Services
- `app/modules/competitions/services/competition_service.py` — hard delete, remove restore/list_deleted
- `app/modules/competitions/services/team_service.py` — update payment flow for multi-payment, remove GroupCompetitionParticipation auto-creation, update placement sync

### Routers
- `app/api/routers/competitions/competitions_router.py` — remove restore endpoint, remove deleted list endpoint, hard delete
- `app/api/routers/competitions/teams_router.py` — remove restore endpoint, remove deleted list endpoint, hard delete, add coach read-only, update payment endpoint
- Remove `group_competitions_router.py` registration from main.py (line 112-116)

### Dependencies
- `app/api/dependencies.py` — possibly add `require_coach_or_admin` guard

### Tests
- `tests/test_competitions.py` — update for hard delete, new payment model
- `tests/test_academics_competitions.py` — update/remove for GroupCompetitionParticipation removal

### Academics Module
- `app/modules/academics/models/group_level_models.py` — remove GroupCompetitionParticipation model
- `app/modules/academics/group/competition/` — remove entire slice (service, repository, interface)
- `app/modules/academics/group/analytics/repository.py` — update query that joins against GroupCompetitionParticipation
- `app/modules/academics/models/__init__.py` — update exports

## Unchanged
- Competition CRUD endpoints (except hard delete)
- Team CRUD endpoints (except hard delete, project fields, payment model)
- Authentication/authorization framework
- Response envelope pattern
- Finance module ReceiptService
- Activity logging pattern
- Stateless service pattern (competitions is not UoW-based)
