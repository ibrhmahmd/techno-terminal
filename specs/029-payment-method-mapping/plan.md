# Implementation Plan: Payment Method Mapping

**Branch**: `029-payment-method-mapping` | **Date**: 2026-06-10 | **Spec**: `specs/029-payment-method-mapping/spec.md`
**Input**: Feature specification from `specs/029-payment-method-mapping/spec.md`

## Summary

Expand the backend `PaymentMethod` literal type (currently `["cash", "card", "transfer", "online"]`) to include `"ewallet"`, `"instapay"`, `"other"`. Add a normalization mapping dictionary in `app/shared/constants.py` that maps all frontend input formats (icon names, display labels, lowercase labels, coded values) to canonical values. Wire a `@field_validator` on `CreateReceiptRequest.method` that normalizes the input before storage.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: FastAPI, Pydantic v2, SQLModel, PostgreSQL
**Storage**: PostgreSQL (payment_method stored as string in `receipts` table)
**Testing**: pytest (with mock auth tokens)
**Target Platform**: Linux server (Leapcell, uvicorn/gunicorn)
**Project Type**: Web service (FastAPI backend)
**Performance Goals**: N/A — simple mapping, no performance concern
**Constraints**: Must not break existing receipts with `"card"`, `"transfer"`, `"online"`
**Scale/Scope**: Single field normalization on one endpoint: POST /api/v1/finance/receipts

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

### Post-Design Re-check (Phase 1 Complete)

- ✅ **Gate 1 — Layer Separation**: `PAYMENT_METHOD_MAP` lives in `constants.py` (shared layer), validator on API DTO, model unchanged. No violations.
- ✅ **Gate 2 — Typed Contracts**: `PaymentMethod` Literal expanded with new values. Mapping dict is config data, not a return type.
- ✅ **Gate 3 — Exception Mapping**: 422 for invalid methods, 201 for success. Unchanged.
- ✅ **Gate 4 — Dead Code**: No dead code.

**Overall: ✅ ALL GATES PASS**

### Gate 1 — Layer Separation (§I)
- ✅ **PASS**: Mapping dict in `constants.py` (shared layer), `@field_validator` on API DTO (`app/api/schemas/finance/receipt.py`), Receipt model uses the expanded Literal. No layer mixing.

### Gate 2 — Typed Contracts (§III)
- ✅ **PASS**: `PaymentMethod` remains a typed `Literal`. The mapping dict is a plain `dict[str, str]` which is acceptable for configuration data. `CreateReceiptRequest.method` stays `str` with validator.

### Gate 3 — Exception Mapping (§IV)
- ✅ **PASS**: Invalid values produce `RequestValidationError` → 422 with standard envelope. No change to exception handling.

### Gate 4 — Dead Code (§Dead Code)
- ✅ **PASS**: No dead code involved. The old `Literal` values are expanded, not replaced.

**Overall: ✅ GATE PASSED** — No violations.

## Project Structure

### Documentation (this feature)

```text
specs/029-payment-method-mapping/
├── plan.md              # This file
├── spec.md              # Feature specification (with clarifications)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output — PaymentMethod entity mapping
├── quickstart.md        # Phase 1 output — reproduction steps
├── contracts/           # Phase 1 output — API contract for method field
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
# Backend monorepo — files relevant to this fix
app/
├── shared/
│   └── constants.py                # PAYMENT_METHOD_MAP + expanded PAYMENT_METHODS
├── api/
│   └── schemas/finance/
│       └── receipt.py              # @field_validator on CreateReceiptRequest.method
├── modules/finance/
│   └── models/
│       └── receipt.py              # Uses PaymentMethod literal (no code change)

tests/
└── test_finance.py                 # New tests for payment method normalization
```

**Structure Decision**: Single backend monorepo. Two files changed + one new mapping + tests.

## Complexity Tracking

*No constitution violations to justify. Table omitted.*
