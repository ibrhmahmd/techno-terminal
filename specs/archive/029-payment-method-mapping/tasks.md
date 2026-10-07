---

description: "Task list for Payment Method Mapping feature"
---

# Tasks: Payment Method Mapping

**Input**: Design documents from `specs/029-payment-method-mapping/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Single backend monorepo
- `app/` at repository root
- `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Read and understand existing files before making changes

- [x] T001 Read `app/shared/constants.py` — understand current `PaymentMethod` Literal, `PAYMENT_METHODS` list
- [x] T002 Read `app/api/schemas/finance/receipt.py` — understand `CreateReceiptRequest.method` field
- [x] T003 Read `app/modules/finance/models/receipt.py` — understand `Receipt.payment_method` field
- [x] T004 Read `tests/test_finance.py` — understand existing test patterns and fixtures

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Expand the PaymentMethod type and payment methods list — required before any user story can work

**⚠ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Expand `PaymentMethod` Literal in `app/shared/constants.py` — add `"ewallet"`, `"instapay"`, `"other"` to the Literal type alias
- [x] T006 Expand `PAYMENT_METHODS` list in `app/shared/constants.py` — add `"ewallet"`, `"instapay"`, `"other"` to the list

**Checkpoint**: Foundation ready — PaymentMethod now accepts 7 values instead of 4

---

## Phase 3: User Story 1 — Accept All Frontend Payment Methods (Priority: P1) 🎯 MVP

**Goal**: Staff users can create receipts with Cash, E-Wallet, instaPay, or Other without getting a "not found" error.

**Independent Test**: Send POST /api/v1/finance/receipts with each payment method and confirm 201 success.

### Implementation for User Story 1

- [x] T007 [P] [US1] Add `PAYMENT_METHOD_MAP` dictionary in `app/shared/constants.py` mapping all known frontend input formats (lowercased) to canonical backend values — per `data-model.md`
- [x] T008 [US1] Add `@field_validator("method", mode="before")` on `CreateReceiptRequest` in `app/api/schemas/finance/receipt.py` — lowercases input, looks up in `PAYMENT_METHOD_MAP`, returns canonical value or passes through for Literal validation
- [x] T009 [US1] Verify existing `"cash"`, `"card"`, `"transfer"`, `"online"` values still work when the validator returns them unchanged
- [x] T010 [US1] Verify default value `"cash"` (when method is omitted) works correctly — no KeyError from map lookup

**Checkpoint**: User Story 1 complete — receipt creation succeeds for Cash, E-Wallet, instaPay, and Other display label values.

---

## Phase 4: User Story 2 — Normalize Payment Method Values Consistently (Priority: P1)

**Goal**: All payment methods are stored in canonical form and existing receipts with old methods are unaffected.

**Independent Test**: Send the same payment method with different casing and verify stored value is always canonical.

### Implementation for User Story 2

- [x] T011 [P] [US2] Write test for lowercase normalization: send `"cash"`, `"Cash"`, `"CASH"` → all store as `"cash"`
- [x] T012 [P] [US2] Write test for E-Wallet normalization: send `"ewallet"`, `"e_wallet"`, `"e-wallet"`, `"E-Wallet"` → all store as `"ewallet"`
- [x] T013 [P] [US2] Write test for instaPay normalization: send `"instapay"`, `"insta_pay"`, `"insta-pay"`, `"instaPay"` → all store as `"instapay"`
- [x] T014 [P] [US2] Write test for Other normalization: send `"other"`, `"Other"` → all store as `"other"`
- [x] T015 [P] [US2] Write test for existing methods backward compatibility: send `"card"`, `"Card"`, `"transfer"`, `"Transfer"`, `"online"`, `"Online"` → all store as canonical values
- [x] T016 [US2] Write test for missing method → defaults to `"cash"`

**Checkpoint**: User Story 2 complete — normalization verified with tests, existing methods work.

---

## Phase 5: User Story 3 — Flexible Input Mapping (Priority: P2)

**Goal**: The system accepts any format the frontend sends (icon names, display labels, lowercase, coded values) and normalizes to canonical.

**Independent Test**: Send each payment method in all known format variants and confirm they all map to the same canonical stored value.

### Implementation for User Story 3

- [x] T017 [P] [US3] Write test for icon name mapping — send `"payments"` → stores as `"cash"`, `"account_balance_wallet"` → stores as `"ewallet"`, `"bolt"` → stores as `"instapay"`, `"more_horiz"` → stores as `"other"`
- [x] T018 [P] [US3] Write test for edge case: invalid method `"cryptocurrency"` → 422 ValidationError
- [x] T019 [P] [US3] Write test for edge case: invalid method `"instapy"` (typo) → 422 ValidationError
- [x] T020 [US3] Run full test suite for finance module to verify zero regressions: `pytest tests/test_finance.py -v`

**Checkpoint**: User Story 3 complete — all known frontend formats accepted and normalized.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and documentation

- [x] T021 [P] Run `pytest tests/test_finance.py -v` — confirm all 32 finance tests pass
- [ ] T022 Run manual validation per `specs/029-payment-method-mapping/quickstart.md` using cURL commands
- [ ] T023 Update `specs/029-payment-method-mapping/contracts/create-receipt-api.md` if behavior changes during implementation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — just reading files
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2 — can proceed independently of other stories
- **User Story 2 (Phase 4)**: Depends on Phase 2 + US1 — tests validate behavior already implemented in US1
- **User Story 3 (Phase 5)**: Depends on Phase 2 + US1 — extends mapping with icon names
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 — core fix (mapping + validator). No dependency on other stories.
- **User Story 2 (P1)**: Tests for normalization — logically tests US1 behavior but can be written after US1 is implemented.
- **User Story 3 (P2)**: Extends mapping with icon names — builds on the infrastructure from US1.

### Within Each User Story

- Models/services come before tests (for US1 implementation)
- Tests are written alongside implementation (US2, US3 primarily add tests)

### Parallel Opportunities

- T007 and T008 can run in parallel (different files: `constants.py` vs `receipt.py`)
- All US2 test tasks (T011–T016) can run in parallel — each tests a different method
- All US3 test tasks (T017–T019) can run in parallel — each tests different input formats

---

## Parallel Example: User Story 1

```bash
# T007 and T008 are independent:
Task: "Add PAYMENT_METHOD_MAP in app/shared/constants.py"
Task: "Add field_validator in app/api/schemas/finance/receipt.py"
```

## Parallel Example: User Story 2

```bash
# All tests are independent (different methods):
Task: "Test cash normalization in tests/test_finance.py"
Task: "Test ewallet normalization in tests/test_finance.py"
Task: "Test instapay normalization in tests/test_finance.py"
Task: "Test other normalization in tests/test_finance.py"
Task: "Test existing methods backward compat in tests/test_finance.py"
Task: "Test missing method default in tests/test_finance.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (read existing code)
2. Complete Phase 2: Foundational (expand PaymentMethod type)
3. Complete Phase 3: User Story 1 (mapping + validator + verify)
4. **STOP and VALIDATE**: Test US1 independently — receipt creation with all payment methods succeeds
5. Deploy if ready — the bug fix alone is valuable

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → **DEPLOY (MVP!)** — fixes the production bug
3. Add User Story 2 → Test independently → DEPLOY — adds normalization test coverage
4. Add User Story 3 → Test independently → DEPLOY — adds icon name acceptance
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Developer reads all setup files in Phase 1
2. Developer completes Phase 2 (Foundational)
3. Developer implements US1 (core fix)
4. Same or second developer writes US2 tests in parallel
5. Third developer writes US3 edge case tests

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- The `Receipt.payment_method` field (`app/modules/finance/models/receipt.py`) references `PaymentMethod` Literal — no code change needed there, the type expansion in `constants.py` automatically flows through
