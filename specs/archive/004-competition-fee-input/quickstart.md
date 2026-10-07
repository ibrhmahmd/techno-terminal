# Quickstart: Competition Fee User Input

## Implementation Order

### Step 1: Schema changes
1. Create `db/migrations/050_remove_team_fee_column.sql`
2. Update `db/schema/07_tables_competitions.sql` — remove `fee` column from teams table

### Step 2: Model changes
3. `app/modules/competitions/models/team_models.py` — remove `fee` field from `TeamBase`

### Step 3: Schema/DTO changes
4. `app/modules/competitions/schemas/team_schemas.py`:
   - Add `student_fees: Optional[dict[int, float]] = None` to `RegisterTeamInput`
   - Add `fee: float = 0.0` to `AddTeamMemberInput`
   - Remove `fee: Optional[float]` from `TeamDTO`

### Step 4: Router changes
5. `app/api/routers/competitions/teams_router.py`:
   - Remove `fee: Optional[Decimal]` from `UpdateTeamInput`
   - Keep `AddTeamMemberInput` as-is (it has the new `fee` field from step 3)
6. `app/api/routers/competitions/competitions_router.py`:
   - Remove `fee_per_student: Optional[Decimal]` from `UpdateCompetitionInput`

### Step 5: Service changes
7. `app/modules/competitions/services/team_service.py`:
   - In `register_team()`: replace auto-split with per-student lookup from `cmd.student_fees`
   - In `add_team_member_to_existing()`: add `fee: float = 0.0` param, remove `team.fee / 2`, use param directly as `member_share`

### Step 6: Tests
8. `tests/test_competitions.py`: update test bodies to remove `fee` references, add `student_fees` test cases

## Key files

| File | Change type |
|------|-------------|
| `db/migrations/050_remove_team_fee_column.sql` | New |
| `db/schema/07_tables_competitions.sql` | Edit |
| `app/modules/competitions/models/team_models.py` | Edit |
| `app/modules/competitions/schemas/team_schemas.py` | Edit |
| `app/api/routers/competitions/teams_router.py` | Edit |
| `app/api/routers/competitions/competitions_router.py` | Edit |
| `app/modules/competitions/services/team_service.py` | Edit |
| `tests/test_competitions.py` | Edit |

## Verification

```bash
pytest tests/test_competitions.py -v
pytest tests/test_analytics_competition.py -v  # confirm no regression
pytest tests/test_finance.py -v -k "unpaid"    # confirm no regression
```
