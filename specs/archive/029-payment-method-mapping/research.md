# Research: Payment Method Mapping

**Branch**: `029-payment-method-mapping`
**Date**: 2026-06-10
**Status**: Complete

## Root Cause Analysis

### Current State

**Backend** (`app/shared/constants.py`):
```python
PaymentMethod = Literal["cash", "card", "transfer", "online"]
PAYMENT_METHODS = ["cash", "card", "transfer", "online"]
```

**Frontend UI offers**: Cash, E-Wallet, instaPay, Other (with Material Icons)

**Code path**:
1. `CreateReceiptRequest.method: str = "cash"` — accepts any string at API level
2. `CreateReceiptServiceDTO.payment_method: str` — passes through
3. `Receipt.payment_method: Optional[PaymentMethod]` — `Literal["cash","card","transfer","online"]`
4. When saving, SQLModel/Pydantic validates against the Literal → rejects values outside the set

### What the Frontend May Send

| Payment Method | Icon Name | Display Label | Lowercase Label | Canonical (new) |
|---------------|-----------|---------------|-----------------|-----------------|
| Cash | `"payments"` | `"Cash"` | `"cash"` | `"cash"` |
| E-Wallet | `"account_balance_wallet"` | `"E-Wallet"` | `"e-wallet"` | `"ewallet"` |
| instaPay | `"bolt"` | `"instaPay"` | `"instapay"` | `"instapay"` |
| Other | `"more_horiz"` | `"Other"` | `"other"` | `"other"` |

### Existing Backend Values (Keep)

- `"cash"` — already matches canonical
- `"card"` — keep as-is
- `"transfer"` — keep as-is
- `"online"` — keep as-is

### Fix Approach

Same pattern as the student status bug (028):

1. **Expand `PAYMENT_METHODS`** list in `app/shared/constants.py` to include all 7 values
2. **Expand `PaymentMethod` Literal** to include `"ewallet"`, `"instapay"`, `"other"`
3. **Add `PAYMENT_METHOD_MAP`** dict mapping all known frontend input formats → canonical values
4. **Add `@field_validator("method", mode="before")`** on `CreateReceiptRequest` that:
   - Lowercases the input
   - Looks up in `PAYMENT_METHOD_MAP`
   - Returns canonical value if found
   - Returns the value as-is if not found (let Literal validation catch truly invalid values)

### Decision

- **Decision**: Mapping dict in `constants.py` + `@field_validator` on `CreateReceiptRequest`
- **Rationale**: Keeps mapping logic centralized and testable. The validator stays thin (just lookups).
- **Alternatives considered**:
  1. Service-layer normalization — less discoverable, harder to test
  2. Model-level normalization — too late, data already failed validation
  3. Frontend-only fix — out of scope, backend should be resilient

## References

- `app/shared/constants.py:20` — `PaymentMethod` Literal definition
- `app/shared/constants.py:21` — `PAYMENT_METHODS` list
- `app/api/schemas/finance/receipt.py:89` — `CreateReceiptRequest.method` field
- `app/modules/finance/models/receipt.py:22` — `Receipt.payment_method` field
