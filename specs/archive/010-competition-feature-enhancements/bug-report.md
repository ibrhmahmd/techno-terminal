# Competition Module — Bug Report

**Date**: 2026-05-17
**Branch**: `010-competition-feature-enhancements`
**Source**: Comprehensive audit report (`audit-report.md`)

---

## Bug Inventory (10 bugs, 4 resolved)

| # | Severity | Bug | Status | Location |
|---|----------|-----|--------|----------|
| B1 | **CRITICAL** | `ReceiptService._link_competition_payment` references non-existent fields | 🔴 OPEN | `receipt_service.py:367-368` |
| B2 | **CRITICAL** | `pay_competition_fee` uses 3 separate transactions — not atomic | 🔴 OPEN | `team_service.py:497-577` |
| B3 | **HIGH** | Duplicate student registration hard-blocks instead of warning | 🔴 OPEN | `team_service.py:101-108`, `team_service.py:414-420` |
| B4 | **HIGH** | 30-day placement window upper bound not enforced | 🔴 OPEN | `team_service.py:368` |
| B5 | **MEDIUM** | `require_coach_or_admin` TOCTOU race condition | 🔴 OPEN | `dependencies.py:334` |
| B6 | **MEDIUM** | `**kwargs` in update methods allows arbitrary field setting | 🔴 OPEN | `competition_service.py:58`, `team_service.py:328` |
| B7 | **LOW** | `get_teams_by_student()` is dead code | 🔴 OPEN | `team_repository.py:120-127` |
| B8 | **LOW** | `create_team()` accepts dead `fee` parameter | 🔴 OPEN | `team_repository.py:21, 35` |
| B9 | **RESOLVED** | N+1 queries in `get_competition_summary` (602 → 1) | ✅ FIXED | `competition_service.py:104-166` |
| B10 | **RESOLVED** | N+1 queries in 3 other service methods (144 → 3) | ✅ FIXED | `team_service.py` |

---

## Open Bugs (Detailed)

### B1: `ReceiptService._link_competition_payment` References Non-Existent Fields

**Severity**: CRITICAL
**Location**: `app/modules/finance/services/receipt_service.py:367-368`

```python
def _link_competition_payment(self, team_member_id: int, payment_id: int) -> None:
    team_member = self._uow._session.get(TeamMember, team_member_id)
    if team_member:
        team_member.fee_paid = True        # ❌ fee_paid does not exist
        team_member.payment_id = payment_id  # ❌ payment_id does not exist
        self._uow._session.add(team_member)
```

**Root Cause**: Migration 054 removed `fee_paid` and `payment_id` from `TeamMember` model, replaced by `amount_due`/`amount_paid`. The finance module's `_link_competition_payment` was not updated.

**When it fires**: Any competition payment processed through the standard finance receipt flow (i.e., when `ReceiptLineInput` includes `team_member_id`). The competition module's `pay_competition_fee` avoids this by NOT passing `team_member_id` to `ReceiptLineInput`, so this code path is currently unreachable from the competition module. However, if any other code path creates a competition receipt with `team_member_id`, it will crash with `AttributeError`.

**Impact**: Runtime crash (`AttributeError`) on any competition payment through the finance module's standard flow.

**Fix**:
```python
def _link_competition_payment(self, team_member_id: int, payment_id: int) -> None:
    team_member = self._uow._session.get(TeamMember, team_member_id)
    if team_member:
        # amount_paid is managed by the competition module's record_payment()
        # No need to update it here — the receipt already links via payment.team_member_id
        pass
```

---

### B2: `pay_competition_fee` Uses 3 Separate Transactions — Not Atomic

**Severity**: CRITICAL
**Location**: `app/modules/competitions/services/team_service.py:497-577`

**Current flow**:
```
Transaction 1: Validation (get_team, get_team_member, get_parent) → session closes
Transaction 2: FinanceUnitOfWork.create() → receipt committed
Transaction 3: get_session() → record_payment() → commit
  └─ On failure: FinanceUnitOfWork.refund() → compensating rollback
```

**Problem**: Three independent transactions create windows where:
1. Between T1 and T2: team/member state could change (another payment, team deletion) — TOCTOU race
2. Between T2 and T3: receipt exists in finance but `amount_paid` is not updated — inconsistent state
3. If T3 fails: compensating refund is issued, but the refund itself can fail — orphan receipt + double charge

**Spec requirement (FR-023)**: "Fee payment operations MUST be atomic — if receipt creation or fee status update fails, the entire operation MUST roll back with no orphan data."

**Impact**: Orphan receipts, potential double-charging, inconsistent state between finance and competition modules.

**Fix options**:

**Option A — Single transaction** (preferred if finance module supports it):
```python
def pay_competition_fee(self, cmd: PayCompetitionFeeInput) -> PayCompetitionFeeResponseDTO:
    with get_session() as db:
        # All in one transaction
        team = team_repo.get_team(db, cmd.team_id)
        member = team_repo.get_team_member(db, cmd.team_id, cmd.student_id)
        # Validate...
        # Create receipt via direct DB insert (not FinanceUnitOfWork)
        # record_payment(db, member.id, amount)
        # _log_payment_activity(db, ...)
        db.commit()  # Single atomic commit
```

**Option B — Saga pattern** (if finance module must remain separate):
- Idempotent compensation: track operation state, retry refund on failure
- Add `payment_status` field to track pending/confirmed/failed

---

### B3: Duplicate Student Registration Hard-Blocks Instead of Warning

**Severity**: HIGH
**Location**: `app/modules/competitions/services/team_service.py:101-108`, `team_service.py:414-420`

**Spec requirement (FR-010)**: "The system MUST warn an admin when attempting to register a student in a second team for the same competition, but allow the registration after explicit confirmation."

**Current behavior**:
```python
# register_team() line 101-108:
already_enrolled = team_repo.check_student_in_competition(db, cmd.competition_id, sid)
if already_enrolled:
    raise ConflictError(
        f"Student '{s.full_name}' is already enrolled in another team "
        f"for this competition."
    )  # ← Hard block

# add_team_member_to_existing() line 414-420:
already_enrolled = team_repo.check_student_in_competition(db, team.competition_id, student_id)
if already_enrolled:
    raise ConflictError(
        "Student is already enrolled in another team for this competition."
    )  # ← Hard block
```

**Expected behavior**: Return `(result, warning_message)` and populate the response envelope's `message` field.

**Fix**:
```python
# In register_team():
duplicates = []
for sid in cmd.student_ids:
    if team_repo.check_student_in_competition(db, cmd.competition_id, sid):
        s = db.get(Student, sid)
        duplicates.append(f"Student '{s.full_name}' is already in another team.")

# After creating team:
warning = "; ".join(duplicates) if duplicates else None
return TeamRegistrationResultDTO(team=..., members_added=...), warning

# In router:
result, warning = svc.register_team(cmd, current_user.id)
return ApiResponse(data=result, message=warning or "Team created successfully.")
```

---

### B4: 30-Day Placement Window Upper Bound Not Enforced

**Severity**: HIGH
**Location**: `app/modules/competitions/services/team_service.py:368`

**Spec requirement (FR-020)**: "Placements MUST be blocked for competitions whose date is in the future OR more than 30 days past the competition date."

**Current behavior**:
```python
if comp and comp.competition_date and comp.competition_date > date.today():
    raise BusinessRuleError("Cannot set placement before competition date.")
# ← Missing: upper bound check
```

**Expected behavior**:
```python
if comp and comp.competition_date:
    if comp.competition_date > date.today():
        raise BusinessRuleError("Cannot set placement before competition date.")
    if (date.today() - comp.competition_date).days > 30:
        raise BusinessRuleError(
            "Placement recording window closed. Placements must be recorded "
            "within 30 days of the competition date."
        )
```

**Impact**: Admins can record placements indefinitely after a competition, violating the 30-day window business rule.

---

### B5: `require_coach_or_admin` TOCTOU Race Condition

**Severity**: MEDIUM
**Location**: `app/api/dependencies.py:334`

```python
async def require_coach_or_admin(team_id: int, current_user: User = Depends(require_any)) -> User:
    if current_user.is_admin:
        return current_user
    with get_session() as db:          # ← Opens SEPARATE session
        team = db.get(Team, team_id)    # ← Team could be deleted here
        if team and current_user.employee_id and team.coach_id == current_user.employee_id:
            return current_user
    raise HTTPException(status_code=403, detail="Access denied.")
```

**Problem**: The auth guard opens its own DB session to fetch the team. Between the auth check and the service call, the team could be deleted by another request. The service would then get a 404, but the auth check already passed.

**Impact**: Minor — results in a 404 instead of 403, which is acceptable. Not a security vulnerability since the service layer re-validates.

**Fix**: Pass the team lookup into the service layer and do the coach check there using the same session.

---

### B6: `**kwargs` in Update Methods Allows Arbitrary Field Setting

**Severity**: MEDIUM
**Location**: `app/modules/competitions/services/competition_service.py:58`, `team_service.py:328`

```python
def update_competition(self, competition_id: int, **kwargs) -> CompetitionDTO | None:
    with get_session() as db:
        c = comp_repo.update_competition(db, competition_id, **kwargs)
        # ...
```

```python
def update_team(self, team_id: int, **kwargs) -> TeamDTO | None:
    with get_session() as db:
        team = team_repo.update_team(db, team_id, **kwargs)
        # ...
```

**Problem**: The repository functions use `setattr()` for each key in `kwargs`. If a caller passes `id`, `created_at`, or any unexpected field, it will be set on the model.

**Mitigation**: The API layer filters inputs via Pydantic schemas (`UpdateCompetitionInput`, `UpdateTeamInput`), so external callers cannot pass arbitrary keys. However, the service methods are callable directly from other code and accept arbitrary keys.

**Fix**: Add field whitelist in repository:
```python
ALLOWED_TEAM_UPDATES = {"team_name", "category", "subcategory", "project_name",
                        "project_description", "group_id", "coach_id", "notes"}

def update_team(db: Session, team_id: int, **kwargs) -> Team | None:
    t = db.get(Team, team_id)
    if t:
        for k, v in kwargs.items():
            if k in ALLOWED_TEAM_UPDATES:
                setattr(t, k, v)
        db.add(t)
        db.flush()
    return t
```

---

### B7: `get_teams_by_student()` Is Dead Code

**Severity**: LOW
**Location**: `app/modules/competitions/repositories/team_repository.py:120-127`

```python
def get_teams_by_student(db: Session, student_id: int) -> list[Team]:
    stmt = select(Team).join(TeamMember).where(TeamMember.student_id == student_id)
    return list(db.exec(stmt).all())
```

**Problem**: No service method or endpoint calls this function. Replaced by `list_student_memberships_enriched()` (T103).

**Fix**: Delete the function.

---

### B8: `create_team()` Accepts Dead `fee` Parameter

**Severity**: LOW
**Location**: `app/modules/competitions/repositories/team_repository.py:21, 35`

```python
def create_team(
    db: Session,
    ...
    fee: Optional[Decimal] = None,  # ← Dead parameter
    ...
) -> Team:
    t = Team(
        ...
        fee=fee,  # ← Team model has no 'fee' field — will raise AttributeError
        ...
    )
```

**Problem**: The `Team` model has no `fee` field. If `fee` is passed (non-None), this will raise `AttributeError` at runtime. Currently, no caller passes `fee`, so it defaults to `None` and the `setattr` silently ignores it.

**Fix**: Remove the `fee` parameter from `create_team()`.

---

## Resolved Bugs

### B9: N+1 Queries in `get_competition_summary` — FIXED ✅

**Before**: 602 queries for 100 teams × 5 members
**After**: 1 query via `get_competition_summary_data()` batch function
**Fixed in**: `competition_service.py:104-166`, `competition_repository.py:69-110`

### B10: N+1 Queries in 3 Other Service Methods — FIXED ✅

| Method | Before | After |
|--------|--------|-------|
| `get_teams_with_members` | 101 | 1 |
| `list_team_members` | 22 | 1 |
| `get_student_competitions` | 21 | 1 |

**Fixed in**: `team_service.py` (4 methods refactored), `team_repository.py` (3 batch functions added)

---

## Priority Order for Fixes

| Priority | Bug | Effort | Risk |
|----------|-----|--------|------|
| 1 | B1: `_link_competition_payment` crash | 5 min | None — currently unreachable |
| 2 | B4: 30-day placement window | 5 min | Low — adds validation |
| 3 | B3: Duplicate student warning | 30 min | Medium — changes API behavior |
| 4 | B2: Payment atomicity | 2 hours | High — restructures payment flow |
| 5 | B6: `**kwargs` whitelist | 15 min | Low — adds field filtering |
| 6 | B5: TOCTOU race | 30 min | Low — refactors auth guard |
| 7 | B7: Dead code removal | 2 min | None |
| 8 | B8: Dead `fee` parameter | 2 min | None |
