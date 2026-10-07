# Data Model: Competition Fee User Input

## Entity Changes

### Team (table: `teams`)

**Removed field**:

| Field | Type | Reason |
|-------|------|--------|
| `fee` | Optional[Decimal] | Replaced by per-student fees on TeamMember.member_share |

**SQLModel before**:
```python
class TeamBase(SQLModel):
    competition_id: int = Field(foreign_key="competitions.id")
    group_id: Optional[int] = Field(default=None, foreign_key="groups.id")
    team_name: str
    coach_id: Optional[int] = Field(default=None, foreign_key="employees.id")
    category: str
    subcategory: Optional[str] = None
    fee: Optional[Decimal] = None  # ← REMOVED
    placement_rank: Optional[int] = None
    placement_label: Optional[str] = None
    notes: Optional[str] = None
```

**SQLModel after**:
```python
class TeamBase(SQLModel):
    competition_id: int = Field(foreign_key="competitions.id")
    group_id: Optional[int] = Field(default=None, foreign_key="groups.id")
    team_name: str
    coach_id: Optional[int] = Field(default=None, foreign_key="employees.id")
    category: str
    subcategory: Optional[str] = None
    placement_rank: Optional[int] = None
    placement_label: Optional[str] = None
    notes: Optional[str] = None
```

### TeamMember (table: `team_members`)

**No changes**. Fields remain:
- `member_share: float` — still set per-student, now from user input instead of auto-calculation
- `fee_paid: bool` — unchanged
- `payment_id: Optional[int]` — unchanged

### Competition (table: `competitions`)

**No changes**. `fee_per_student` remains as UI reference.

---

## Validation Rules (RegisterTeamInput)

| Field | Type | Validation |
|-------|------|------------|
| `student_ids` | `list[int]` | At least 1 student (existing) |
| `student_fees` | `Optional[dict[int, float]]` | Keys must be subset of student_ids (implied — extraneous keys ignored). Values >= 0. |

**Logic** for each student_id in student_ids:
```
member_share = student_fees.get(student_id, 0.0) if student_fees else 0.0
```

## State Transitions

### Team Registration Flow (updated)

```
RegisterTeamInput(student_ids=[1,2], student_fees={1:50})
  │
  ├── For student_id=1: member_share = 50 (from dict)
  ├── For student_id=2: member_share = 0 (missing from dict → default)
  │
  ├── team_repo.add_team_member(db, team.id, 1, member_share=50)
  ├── team_repo.add_team_member(db, team.id, 2, member_share=0)
  │
  └── (no team.fee set — column removed)
```

### Add Member Flow (updated)

```
AddTeamMemberInput(student_id=3, fee=25)
  │
  ├── member_share = 25 (from input fee param)
  ├── (no team.fee / 2 calculation)
  │
  └── team_repo.add_team_member(db, team.id, 3, member_share=25)
```
