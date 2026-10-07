# Data Model: Competition Module Enhancements

## Entity Changes

### Competition (Table: `competitions`)

**Before** (soft-delete):
```
id, name, edition, edition_year, competition_date, location, notes, 
fee_per_student, created_at, deleted_at, deleted_by
```

**After** (hard delete):
```
id, name, edition, edition_year, competition_date, location, notes, 
fee_per_student, created_at
```

- **Removed**: `deleted_at`, `deleted_by`
- **Delete behavior**: `DELETE FROM competitions WHERE id = :id` (blocked if any teams reference this competition)

### Team (Table: `teams`)

**Before** (soft-delete, no project fields):
```
id, competition_id, group_id, team_name, coach_id, category, subcategory,
placement_rank, placement_label, notes, created_at, deleted_at, deleted_by
```

**After** (hard delete, with project tracking):
```
id, competition_id, group_id, team_name, coach_id, category, subcategory,
placement_rank, placement_label, project_name, project_description, notes, created_at
```

- **Added**: `project_name VARCHAR(500)`, `project_description TEXT`
- **Removed**: `deleted_at`, `deleted_by`
- **Delete behavior**: `DELETE FROM teams WHERE id = :id` (blocked if any member has `amount_paid > 0`)

### TeamMember (Table: `team_members`)

**Before** (boolean fee, single payment):
```
id, team_id, student_id, member_share, fee_paid, payment_id
```

**After** (enrollment-style fee tracking):
```
id, team_id, student_id, amount_due DECIMAL(10,2) DEFAULT 0.00, 
amount_paid DECIMAL(10,2) DEFAULT 0.00
```

- **Added**: `amount_due` (replaces `member_share` semantics as the fee due), `amount_paid` (running total)
- **Removed**: `fee_paid` (derived: `amount_paid >= amount_due`), `payment_id` (single payment — no longer applicable)
- **Payment status derived**:
  - `amount_paid >= amount_due` → fully paid
  - `amount_paid > 0 AND amount_paid < amount_due` → partially paid
  - `amount_paid = 0 AND amount_due > 0` → unpaid
  - `amount_due = 0` → no fee required

### Payment (Table: `payments`)

**Before**:
```
id, receipt_id, student_id, enrollment_id, amount, transaction_type, 
payment_type, original_payment_id, discount_amount, notes, created_at, metadata,
deleted_at, deleted_by
```

**After**:
```
id, receipt_id, student_id, enrollment_id, team_member_id, amount, transaction_type, 
payment_type, original_payment_id, discount_amount, notes, created_at, metadata,
deleted_at, deleted_by
```

- **Added**: `team_member_id INTEGER REFERENCES team_members(id)` — mirrors `enrollment_id` for linking competition fee payments

### Removed: GroupCompetitionParticipation (Table: `group_competition_participation`)

**Dropped entirely**. The `group_id` on `teams` table remains as a student roster pre-fill source only — no participation lifecycle tracking. The placement sync that updated `final_placement` on this table is removed.

## Entity Relationship Diagram (After)

```
┌──────────────────┐       ┌──────────────────┐
│   Competition    │       │     Employee     │
├──────────────────┤       │   (Coach/Owner)  │
│ PK id            │       ├──────────────────┤
│    name          │       │ PK id            │
│    edition_year  │       └──────────────────┘
│    fee_per_stud  │              │
│    competition_  │       ┌──────────────────┐
│    date          │       │    Student       │
│    location      │       ├──────────────────┤
└────────┬─────────┘       │ PK id            │
         │                 └────────┬─────────┘
         │ 1:N                      │
         ▼                          │ N:M
┌──────────────────┐               │
│      Team        │               │
├──────────────────┤               │
│ PK id            │               │
│ FK competition_id│               │
│    team_name     │               │
│    category      │               │
│    subcategory   │               │
│    project_name  │               │
│    project_desc  │               │
│ FK group_id opt  │ (source only) │
│ FK coach_id opt  │               │
│    placement_rnk │               │
│    placement_lbl │               │
└────────┬─────────┘               │
         │ 1:N                     │
         ▼                         │
┌──────────────────┐               │
│   TeamMember     │               │
├──────────────────┤               │
│ PK id            │               │
│ FK team_id       │               │
│ FK student_id    ├───────────────┘
│    amount_due    │
│    amount_paid   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│    Payment       │
├──────────────────┤
│ PK id            │
│ FK team_member_id│ (NEW)
│ FK receipt_id    │
│ FK student_id    │
│    amount        │
│    payment_type  │
└──────────────────┘
```

## State Derivation (No Explicit Status Fields)

| Concept | Derivation |
|---------|------------|
| Fee paid | `amount_paid >= amount_due` AND `amount_paid > 0` |
| Partial payment | `amount_paid > 0` AND `amount_paid < amount_due` |
| Unpaid | `amount_paid = 0` AND `amount_due > 0` |
| No fee required | `amount_due = 0` |
| Placed | `placement_rank IS NOT NULL` |
| Competition past | `competition_date < today` |
| Competition ongoing | `competition_date = today` |
| Competition upcoming | `competition_date > today` |

## Key Model (SQLModel)

### Team (After)
```python
class TeamBase(SQLModel):
    competition_id: int = Field(foreign_key="competitions.id")
    group_id: Optional[int] = Field(default=None, foreign_key="groups.id")
    team_name: str
    coach_id: Optional[int] = Field(default=None, foreign_key="employees.id")
    category: str
    subcategory: Optional[str] = None
    project_name: Optional[str] = None
    project_description: Optional[str] = None
    placement_rank: Optional[int] = None
    placement_label: Optional[str] = None
    notes: Optional[str] = None

class Team(TeamBase, table=True):
    __tablename__ = "teams"
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = None
```

### TeamMember (After)
```python
class TeamMemberBase(SQLModel):
    team_id: int = Field(foreign_key="teams.id")
    student_id: int = Field(foreign_key="students.id")
    amount_due: float = Field(default=0.0)
    amount_paid: float = Field(default=0.0)

class TeamMember(TeamMemberBase, table=True):
    __tablename__ = "team_members"
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
```

### Competition (After)
```python
class CompetitionBase(SQLModel):
    name: str
    edition: Optional[str] = None
    edition_year: int
    competition_date: Optional[date] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    fee_per_student: float = Field(default=0.0)

class Competition(CompetitionBase, table=True):
    __tablename__ = "competitions"
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = None
```

## Migration SQL (`054_competition_hard_delete_and_payment_model.sql`)

```sql
-- Phase 1: Drop group_competition_participation table
DROP TABLE IF EXISTS group_competition_participation CASCADE;

-- Phase 2: Add project tracking columns to teams
ALTER TABLE teams ADD COLUMN project_name VARCHAR(500);
ALTER TABLE teams ADD COLUMN project_description TEXT;

-- Phase 3: Migrate team_members to enrollment-style fee model
ALTER TABLE team_members ADD COLUMN amount_due DECIMAL(10,2) DEFAULT 0.00;
ALTER TABLE team_members ADD COLUMN amount_paid DECIMAL(10,2) DEFAULT 0.00;
-- Migrate existing data: member_share -> amount_due
UPDATE team_members SET amount_due = member_share;
-- If fee_paid, set amount_paid = amount_due (assume fully paid)
UPDATE team_members SET amount_paid = amount_due WHERE fee_paid = TRUE;
ALTER TABLE team_members DROP COLUMN member_share;
ALTER TABLE team_members DROP COLUMN fee_paid;
ALTER TABLE team_members DROP COLUMN payment_id;

-- Phase 4: Add team_member_id to payments table
ALTER TABLE payments ADD COLUMN team_member_id INTEGER REFERENCES team_members(id);

-- Phase 5: Remove soft delete from competitions
ALTER TABLE competitions DROP COLUMN IF EXISTS deleted_at;
ALTER TABLE competitions DROP COLUMN IF EXISTS deleted_by;

-- Phase 6: Remove soft delete from teams
ALTER TABLE teams DROP COLUMN IF EXISTS deleted_at;
ALTER TABLE teams DROP COLUMN IF EXISTS deleted_by;
```
