# Bug Fix Plan: Competition Module

**Branch**: `010-competition-feature-enhancements`
**Date**: 2026-05-17
**Source**: `bug-report.md` (8 open bugs identified)

## Summary

Fix 8 open bugs in the competition module, ordered by severity and effort. Two CRITICAL bugs (payment atomicity, ReceiptService crash), two HIGH bugs (duplicate student warning, placement window), two MEDIUM (TOCTOU race, kwargs whitelist), two LOW (dead code).

## Technical Context

**All fixes are in-place edits** — no schema changes, no new endpoints, no API contract changes except B3 (warning in response envelope, which is already documented in contracts/overview.md).

**No migration needed** — all bugs are code-level fixes.

## Constitution Check

| Gate | Status | Notes |
|------|--------|-------|
| §I Router → Service → Repository | ✅ PASS | All fixes stay within existing layer boundaries. |
| §II Module Organization | ✅ PASS | No new files or directories. |
| §III Typed Contracts | ✅ PASS | B3 uses existing `message` field in response envelope. No new DTOs. |
| §IV Response Envelope | ✅ PASS | B3 populates `message` field per existing pattern. |
| §V Auth-Guarded Endpoints | ✅ PASS | B5 refactors auth guard but doesn't weaken it. |
| Dead Code Discipline | ✅ PASS | B7, B8 remove dead code per constitution mandate. |

## Fix Details

### Fix 1: B1 — ReceiptService._link_competition_payment Crash (CRITICAL)

**File**: `app/modules/finance/services/receipt_service.py:359-369`

**Problem**: References `fee_paid` and `payment_id` fields that were removed from `TeamMember` in migration 054.

**Fix**: Replace field assignments with no-op comment. The `team_member_id` FK on `payments` table already links the payment to the team member — no additional field needed on `TeamMember`.

```python
def _link_competition_payment(self, team_member_id: int, payment_id: int) -> None:
    """Internal: Link payment to team member for competition fees.
    
    Note: The payments table has team_member_id FK, so the link is
    already established. No TeamMember fields need updating.
    """
    pass
```

**Risk**: None — currently unreachable from competition module's `pay_competition_fee` (doesn't pass `team_member_id` to `ReceiptLineInput`). Other code paths that DO pass `team_member_id` will no longer crash.

### Fix 2: B4 — 30-Day Placement Window Upper Bound (HIGH)

**File**: `app/modules/competitions/services/team_service.py:367-370`

**Problem**: Only blocks future dates, not dates >30 days past.

**Fix**:
```python
if comp and comp.competition_date:
    days_since = (date.today() - comp.competition_date).days
    if comp.competition_date > date.today():
        raise BusinessRuleError("Cannot set placement for a competition that has not yet occurred.")
    if days_since > 30:
        raise BusinessRuleError(
            "Placement recording window closed. Placements must be recorded "
            "within 30 days of the competition date."
        )
```

**Risk**: Low — adds validation, may block admins who were relying on the missing check.

### Fix 3: B3 — Duplicate Student Warning (HIGH)

**Files**: `app/modules/competitions/services/team_service.py` (register_team, add_team_member_to_existing), `app/api/routers/competitions/teams_router.py` (POST /teams, POST /teams/{id}/members)

**Problem**: Hard-blocks with `ConflictError` instead of warning in response envelope.

**Fix approach**:
1. `register_team()` collects duplicate warnings instead of raising `ConflictError`
2. Returns `(TeamRegistrationResultDTO, warning_message_or_none)`
3. Router checks for warning and populates `message` field
4. Same pattern for `add_team_member_to_existing()`

**Service signature change**:
```python
def register_team(self, cmd: RegisterTeamInput, current_user_id: Optional[int] = None) -> tuple[TeamRegistrationResultDTO, str | None]:
```

**Router change**:
```python
result, warning = svc.register_team(cmd, current_user.id)
return ApiResponse(data=result, message=warning or "Team created successfully.")
```

**Risk**: Medium — changes return type of service method. All callers must be updated. Only one caller exists (teams_router.py).

### Fix 4: B2 — Payment Atomicity (CRITICAL)

**File**: `app/modules/competitions/services/team_service.py:491-577`

**Problem**: 3 separate transactions. If T3 fails after T2 commits, orphan receipt exists.

**Fix approach**: Single transaction using `get_session()` for the entire operation. The finance receipt creation must happen within the same session.

**Option A — Direct DB insert for receipt** (if FinanceUnitOfWork can accept an existing session):
```python
with get_session() as db:
    # Validate
    team = team_repo.get_team(db, cmd.team_id)
    member = team_repo.get_team_member(db, cmd.team_id, cmd.student_id)
    # Validate amount > 0
    
    # Create receipt within same session
    with FinanceUnitOfWork(session=db) as uow:
        service = ReceiptService(uow)
        result = service.create(lines=[...], ...)
        payment_id = result.payment_ids[0]
    
    # Record payment in same session
    team_repo.record_payment(db, member.id, amount)
    self._log_payment_activity(db, ...)
    db.commit()  # Single atomic commit
```

**Risk**: High — requires `FinanceUnitOfWork` to accept an existing session. If it doesn't support this, need Option B (saga pattern with idempotent compensation).

### Fix 5: B6 — **kwargs Whitelist (MEDIUM)

**Files**: `app/modules/competitions/repositories/competition_repository.py:update_competition`, `app/modules/competitions/repositories/team_repository.py:update_team`

**Fix**: Add field whitelists to repository functions.

```python
ALLOWED_COMPETITION_UPDATES = {"name", "edition", "edition_year", "competition_date", "location", "notes", "fee_per_student"}

def update_competition(db: Session, competition_id: int, **kwargs) -> Competition | None:
    c = db.get(Competition, competition_id)
    if c:
        for k, v in kwargs.items():
            if k in ALLOWED_COMPETITION_UPDATES:
                setattr(c, k, v)
        db.add(c)
        db.flush()
    return c
```

**Risk**: Low — adds field filtering. API layer already filters via Pydantic, so this is defense-in-depth.

### Fix 6: B5 — TOCTOU Race in require_coach_or_admin (MEDIUM)

**File**: `app/api/dependencies.py:327-338`

**Fix**: Move coach check into service layer, use same session as the service call.

```python
# In team_service.py:
def get_team_for_user(self, team_id: int, current_user: User) -> Team | None:
    with get_session() as db:
        team = team_repo.get_team(db, team_id)
        if not team:
            return None
        if current_user.is_admin:
            return team
        if current_user.employee_id and team.coach_id == current_user.employee_id:
            return team
        return None  # Not authorized
```

**Router change**:
```python
def get_team(team_id: int, current_user: User = Depends(require_any), svc: TeamService = Depends(get_team_service)):
    team = svc.get_team_for_user(team_id, current_user)
    if not team:
        raise HTTPException(status_code=404 if team is None else 403, detail="...")
    return ApiResponse(data=TeamDTO.model_validate(team))
```

**Risk**: Low — refactors auth check into service layer. Same security posture, no race condition.

### Fix 7: B7 — Dead Code Removal (LOW)

**File**: `app/modules/competitions/repositories/team_repository.py:120-127`

**Fix**: Delete `get_teams_by_student()` function.

**Risk**: None.

### Fix 8: B8 — Dead `fee` Parameter (LOW)

**File**: `app/modules/competitions/repositories/team_repository.py:21, 35`

**Fix**: Remove `fee: Optional[Decimal] = None` parameter from `create_team()`.

**Risk**: None — no caller passes this parameter.

## Execution Order

| Phase | Bugs | Effort |
|-------|------|--------|
| Phase 1: Quick fixes | B1, B4, B7, B8 | 15 min total |
| Phase 2: Medium fixes | B6, B5 | 45 min total |
| Phase 3: High fixes | B3 | 30 min |
| Phase 4: Critical fix | B2 | 2 hours |

## Testing Strategy

After each phase:
1. Run `pytest tests/test_competitions.py -v` — all 22 tests pass
2. Run `py -c "import app.api.main"` — app imports cleanly
3. Manual smoke test for changed behavior (B3 warning, B4 placement window)
