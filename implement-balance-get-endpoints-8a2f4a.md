# Implement Balance GET Endpoints (Phase 1)

Implement two balance endpoints: `GET /students/{id}/balance` and `GET /balance/unpaid-enrollments`, while deferring `POST /students/{id}/balance/adjust` pending clarification on adjustment recording method.

---

## Clarifying Question for Adjust Endpoint

**Endpoint:** `POST /students/{student_id}/balance/adjust`

**Question:** How should balance adjustments be recorded in the database?

**Option A: Payment Line with transaction_type="adjustment"**
- Add a synthetic payment line with negative or positive amount
- Fits existing payment/receipt model
- Existing views (v_enrollment_balance) will automatically include it
- Less explicit audit trail

**Option B: Separate balance_adjustments table**
- Create dedicated table for manual adjustments
- Cleaner audit trail with reason, adjusted_by, timestamp
- Need to update views to include adjustments
- More complex but better for compliance

**Option C: Both (recommended for audit)**
- Record in balance_adjustments for audit trail
- Create synthetic payment line for balance calculation consistency
- Most work but most robust

**Please confirm which approach before implementing the adjust endpoint.**

---

## Phase 1: Implement These Two Endpoints

### 1. GET /students/{student_id}/balance

**Router:** `app/api/routers/finance/finance_router.py`

**Implementation Steps:**
1. Add `get_balance_service` dependency (already exists)
2. Create endpoint calling `balance_service.get_student_balances(student_id)`
3. Aggregate enrollment balances into summary response
4. Return StudentBalanceResponse with enrollments array

**Code Pattern:**
```python
@router.get(
    "/students/{student_id}/balance",
    response_model=ApiResponse[StudentBalanceResponse],
    summary="Get student balance summary",
)
def get_student_balance(
    student_id: int,
    _user: User = Depends(require_any),
    service: BalanceService = Depends(get_balance_service),
):
    enrollments = service.get_student_balances(student_id)
    # Aggregate into summary
    total_due = sum(e.amount_due for e in enrollments)
    total_paid = sum(e.amount_paid for e in enrollments)
    ...
```

**New Schema Required:** `app/api/schemas/finance/balance.py`
```python
class StudentBalanceResponse(BaseModel):
    student_id: int
    total_amount_due: float
    total_discounts: float
    total_paid: float
    net_balance: float
    enrollments: list[EnrollmentBalanceResponse]
```

---

### 2. GET /balance/unpaid-enrollments

**Router:** `app/api/routers/finance/finance_router.py`

**Implementation Steps:**
1. Verify `v_unpaid_enrollments` view exists in database
2. Add repository method `get_unpaid_enrollments(group_id, skip, limit)`
3. Add service method `get_unpaid_enrollments()`
4. Create endpoint with pagination

**Repository Addition:** `app/modules/finance/repositories/payment_repository.py`
```python
def get_unpaid_enrollments(
    self, group_id: Optional[int], skip: int, limit: int
) -> tuple[list[UnpaidEnrollmentItem], int]:
    """Get unpaid enrollments from v_unpaid_enrollments view."""
    # Query view with optional group filter
    # Return items + total count for pagination
```

**Endpoint Pattern:**
```python
@router.get(
    "/balance/unpaid-enrollments",
    response_model=PaginatedResponse[UnpaidEnrollmentItem],
    summary="List unpaid enrollments",
)
def get_unpaid_enrollments(
    group_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _user: User = Depends(require_any),
    service: BalanceService = Depends(get_balance_service),
):
    items, total = service.get_unpaid_enrollments(group_id, skip, limit)
    return PaginatedResponse(data=items, total=total, skip=skip, limit=limit)
```

**Check First:** Does `v_unpaid_enrollments` view exist in database?

---

## Files to Modify

| File | Changes |
|------|---------|
| `app/api/routers/finance/finance_router.py` | Add 2 new endpoints |
| `app/api/schemas/finance/balance.py` | Add `StudentBalanceResponse` schema |
| `app/api/schemas/finance/__init__.py` | Export new schema |
| `app/modules/finance/services/balance_service.py` | Add `get_student_balance_summary()`, `get_unpaid_enrollments()` |
| `app/modules/finance/interfaces/services/Ibalance_service.py` | Add protocol methods |
| `app/modules/finance/repositories/payment_repository.py` | Add `get_unpaid_enrollments()` |
| `app/modules/finance/interfaces/repositories/Ipayment_repository.py` | Add protocol method |
| `app/api/dependencies.py` | Add `get_balance_service` if not exists |

---

## Documentation Cleanup

After implementation, update (don't delete yet):
- `docs/api/students/finance.md` - Update first 2 endpoints as implemented
- `docs/product/api/finance/balance.md` - Update first 2 endpoints as implemented

Delete sections for unimplemented endpoints:
- `GET /students/{id}/balance/enrollments/{id}`
- `GET /students/{id}/credit`
- `POST /students/{id}/balance/enrollments/{id}/apply-credit`
- `POST /balance/allocations/{id}/reverse`

---

## Implementation Order

1. Add schemas
2. Add repository method (check view exists first)
3. Add service methods
4. Add endpoints
5. Test both endpoints
6. Update documentation

---

## Risk Check

- ✅ `BalanceService` already has `get_student_balances()` - low risk
- ⚠️ `v_unpaid_enrollments` view existence unknown - check first
- ✅ Both are read-only operations - no data mutation risk
