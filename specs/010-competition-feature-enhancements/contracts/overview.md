# API Contracts: Competition Module Enhancements

## Contract Changes Summary

### New/Modified DTOs (Module Schemas — `app/modules/competitions/schemas/`)

#### TeamMemberDTO (updated)
```python
class TeamMemberDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    team_id: int
    student_id: int
    amount_due: float = 0.0
    amount_paid: float = 0.0
    # REMOVED: fee_paid, payment_id
```

#### RegisterTeamInput (updated)
```python
class RegisterTeamInput(BaseModel):
    competition_id: int
    team_name: str
    category: str
    subcategory: Optional[str] = None
    project_name: Optional[str] = None  # NEW
    project_description: Optional[str] = None  # NEW
    student_ids: list[int]
    student_fees: Optional[dict[int, float]] = None
    coach_id: Optional[int] = None
    group_id: Optional[int] = None
    notes: Optional[str] = None
```

#### PayCompetitionFeeInput (updated)
```python
class PayCompetitionFeeInput(BaseModel):
    team_id: int
    student_id: int
    amount: float  # NEW — the payment amount (supports partial)
    parent_id: Optional[int] = None
    received_by_user_id: Optional[int] = None
```

#### PayCompetitionFeeResponseDTO (updated)
```python
class PayCompetitionFeeResponseDTO(BaseModel):
    receipt_number: str
    payment_id: int
    amount: float
    amount_paid: float  # NEW — new running total
    amount_due: float  # NEW — for context
```

#### TeamMemberRosterDTO (updated)
```python
class TeamMemberRosterDTO(BaseModel):
    team_member_id: int
    team_id: int
    team_name: str
    student_id: int
    student_name: str
    amount_due: float = 0.0  # was member_share
    amount_paid: float = 0.0  # NEW
    # REMOVED: fee_paid, payment_id
```

#### AddTeamMemberInput (updated)
```python
class AddTeamMemberInput(BaseModel):
    student_id: int
    amount_due: float = 0.0  # was "fee"
```

### New/Modified DTOs (API Schemas — `app/api/schemas/competitions/`)

#### UpdateTeamInput (updated)
```python
class UpdateTeamInput(BaseModel):
    team_name: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[str] = Field(None, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    project_name: Optional[str] = Field(None, max_length=500)  # NEW
    project_description: Optional[str] = Field(None, max_length=5000)  # NEW
    group_id: Optional[int] = None
    coach_id: Optional[int] = None
    notes: Optional[str] = Field(None, max_length=1000)
```

#### PayCompetitionFeeInput (API — new)
```python
class PayCompetitionFeeBody(BaseModel):
    amount: float = Field(..., gt=0, description="Payment amount (supports partial)")
    parent_id: Optional[int] = None
```

### Service Method Contracts

#### `TeamService.pay_competition_fee()`
```
Input:  team_id, student_id, amount, parent_id?, received_by_user_id?
Output: PayCompetitionFeeResponseDTO {receipt_number, payment_id, amount, amount_paid, amount_due}
Flow:   Validate -> Create receipt (FinanceUnitOfWork) -> Update amount_paid -> Log activity -> Commit
        On failure: rollback entire operation, no orphan data
```

#### `TeamService.register_team()`
```
Input:  RegisterTeamInput (with new project_name, project_description)
Output: TeamRegistrationResultDTO {team, members_added}
Note:   No longer creates GroupCompetitionParticipation
```

#### `TeamService.add_team_member_to_existing()`
```
Input:  team_id, student_id, amount_due (was "fee"), current_user_id?
Output: AddTeamMemberResultDTO
```

### Removed Service Methods

| Method | Reason |
|--------|--------|
| `CompetitionService.restore_competition()` | Hard delete — no restore |
| `CompetitionService.list_deleted_competitions()` | No soft delete |
| `TeamService.restore_team()` | Hard delete — no restore |
| `TeamService.list_deleted_teams()` | No soft delete |
| `TeamService.unmark_team_fee_for_payment()` | No single payment_id — refund uses team_member_id on payment row |
| `TeamService._log_placement_activity()` → GroupCompetitionParticipation sync | Table dropped |

### Removed Repository Functions

| Function | File |
|----------|------|
| `restore_competition()` | `competition_repository.py` |
| `list_deleted_competitions()` | `competition_repository.py` |
| `restore_team()` | `team_repository.py` |
| `list_deleted_teams()` | `team_repository.py` |
| `get_members_by_payment_id()` | `team_repository.py` (no single payment_id) |
| `mark_fee_paid()` | `team_repository.py` (replaced by `record_payment()`) |

### New Repository Functions

| Function | Purpose |
|----------|---------|
| `record_payment(db, team_member_id, amount)` | Adds payment to `amount_paid` on TeamMember |
| `refund_payment(db, team_member_id, amount)` | Subtracts from `amount_paid` on TeamMember |
| `hard_delete_team(db, team_id)` | `DELETE FROM teams WHERE id = :id` |
| `hard_delete_competition(db, competition_id)` | `DELETE FROM competitions WHERE id = :id` |

### Coach Read-Only Guard (New Dependency)

```python
# Inline check in router or new Depends():
def require_team_access(
    team_id: int,
    current_user: User = Depends(require_any),
    svc: TeamService = Depends(get_team_service),
) -> User:
    team = svc.get_team_by_id(team_id)
    if current_user.is_admin:
        return current_user
    if team and current_user.employee and current_user.employee.id == team.coach_id:
        return current_user
    raise HTTPException(status_code=403, detail="Access denied")
```
