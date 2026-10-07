# Data Model: Payment Method Mapping

**Branch**: `029-payment-method-mapping`
**Date**: 2026-06-10

## Entity: PaymentMethod (Type Alias)

**File**: `app/shared/constants.py`

### Current (Before)

```python
PaymentMethod: TypeAlias = Literal["cash", "card", "transfer", "online"]
PAYMENT_METHODS: list[PaymentMethod] = ["cash", "card", "transfer", "online"]
```

### After (Fix)

```python
PaymentMethod: TypeAlias = Literal[
    "cash", "card", "transfer", "online",
    "ewallet", "instapay", "other",
]
PAYMENT_METHODS: list[PaymentMethod] = [
    "cash", "card", "transfer", "online",
    "ewallet", "instapay", "other",
]
```

### New: PAYMENT_METHOD_MAP

```python
PAYMENT_METHOD_MAP: dict[str, str] = {
    # Cash variants
    "cash": "cash",
    "payments": "cash",
    # Card (keep existing)
    "card": "card",
    # Transfer (keep existing)
    "transfer": "transfer",
    # Online (keep existing)
    "online": "online",
    # E-Wallet variants
    "ewallet": "ewallet",
    "e_wallet": "ewallet",
    "e-wallet": "ewallet",
    "account_balance_wallet": "ewallet",
    # instaPay variants
    "instapay": "instapay",
    "insta_pay": "instapay",
    "insta-pay": "instapay",
    "bolt": "instapay",
    # Other variants
    "other": "other",
    "more_horiz": "other",
}
```

## Entity: Receipt

**File**: `app/modules/finance/models/receipt.py`

| Field | Type | Current | After Fix |
|-------|------|---------|-----------|
| `payment_method` | `Optional[PaymentMethod]` | `Literal["cash","card","transfer","online"]` | `Literal[..., "ewallet","instapay","other"]` |

No structural change — the Literal type is expanded, but the column stays `String`.

## Entity: CreateReceiptRequest (API DTO)

**File**: `app/api/schemas/finance/receipt.py`

| Field | Type | Default | Fix |
|-------|------|---------|-----|
| `method` | `str` | `"cash"` | Add `@field_validator("method", mode="before")` that lowercases and maps via `PAYMENT_METHOD_MAP` |

## Normalization Flow

```
Request: {"method": "bolt", ...}
  → @field_validator (mode="before")
    → .lower() → "bolt"
    → PAYMENT_METHOD_MAP["bolt"] → "instapay"
    → Returns "instapay"
  → CreateReceiptRequest.method = "instapay"
  → CreateReceiptServiceDTO.payment_method = "instapay"
  → Receipt.payment_method = "instapay" ✅
```

```
Request: {"method": "UNKNOWN", ...}
  → @field_validator (mode="before")
    → .lower() → "unknown"
    → PAYMENT_METHOD_MAP["unknown"] → KeyError (or None)
    → Returns "unknown" as-is (let Literal validation handle it)
  → CreateReceiptRequest.method = "unknown"
  → Pydantic validates "unknown" against Literal → ❌ 422 ValidationError
```
