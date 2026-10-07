# Feature Specification: Payment Method Mapping

**Feature Branch**: `029-payment-method-mapping`  
**Created**: 2026-06-10  
**Status**: Draft  
**Input**: User description: "investigate the payment options cause the frontend allows these: Cash (payments icon), E-Wallet (account_balance_wallet icon), instaPay (bolt icon), Other (more_horiz icon)"

## Clarifications

### Session 2026-06-10

- Q: What exact string values does the frontend send for each payment method (icon names, display labels, coded values)? → A: Expect any format — icon names (`"payments"`, `"account_balance_wallet"`, `"bolt"`, `"more_horiz"`), display labels (`"Cash"`, `"E-Wallet"`, `"instaPay"`, `"Other"`), lowercase labels, or coded values. The system must normalize all of them to canonical backend values.
- Q: What are the canonical backend storage values for the new methods? → A: Simple lowercase codes — `"cash"`, `"ewallet"`, `"instapay"`, `"other"`. Keep existing `"card"`, `"transfer"`, `"online"` unchanged.
- Q: Where should the normalization mapping live? → A: Dedicated mapping dictionary in `app/shared/constants.py` + `@field_validator` on `CreateReceiptRequest.method`.
- Q: Keep `Literal` type or switch to `Enum` for `PaymentMethod`? → A: Keep `Literal` — expand the existing type alias with new values.
- Q: Should existing methods (`"card"`, `"transfer"`, `"online"`) also get case normalization? → A: Yes — include all methods in the normalization mapping for consistency.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Accept All Frontend Payment Methods (Priority: P1)

As a staff user creating a receipt, I want to select any payment method offered by the frontend (Cash, E-Wallet, instaPay, Other) and have the receipt created successfully without errors.

**Why this priority**: The currently reported bug blocks receipt creation when users select E-Wallet, instaPay, or Other — only Cash works. This is a direct production blocker for payment processing.

**Independent Test**: Can be fully tested by sending POST /api/v1/finance/receipts with each payment method value and confirming 201 success.

**Acceptance Scenarios**:

1. **Given** a staff user creates a receipt with payment method set to the value the frontend sends for "Cash", **When** the request is submitted, **Then** the receipt is created with status 201 and the payment method is recorded correctly.
2. **Given** a staff user creates a receipt with payment method set to the value the frontend sends for "E-Wallet", **When** the request is submitted, **Then** the receipt is created with status 201 and the payment method is recorded as a normalized value.
3. **Given** a staff user creates a receipt with payment method set to the value the frontend sends for "instaPay", **When** the request is submitted, **Then** the receipt is created with status 201 and the payment method is recorded as a normalized value.
4. **Given** a staff user creates a receipt with payment method set to the value the frontend sends for "Other", **When** the request is submitted, **Then** the receipt is created with status 201 and the payment method is recorded as a normalized value.

---

### User Story 2 - Normalize Payment Method Values Consistently (Priority: P1)

As a backend developer, I want payment methods to be stored consistently so that reports and queries can aggregate by payment method without case or label variations.

**Why this priority**: Without consistent normalization, the same payment method could be stored as "E-Wallet", "e_wallet", "ewallet" — breaking financial reports.

**Independent Test**: Can be tested by sending the same payment method with different casing/labels and verifying the stored value is normalized.

**Acceptance Scenarios**:

1. **Given** the backend receives a payment method value, **When** it is stored, **Then** it is normalized to a canonical lowercase form (e.g., `"e_wallet"`, `"instapay"`, `"cash"`, `"other"`).
2. **Given** existing receipts with old payment methods (`"card"`, `"transfer"`, `"online"`), **When** the system reads them, **Then** they are still displayed correctly and the old values are not invalidated.

---

### User Story 3 - Flexible Input Mapping (Priority: P2)

As a backend developer, I want the payment method input to be flexible enough to accept any format the frontend sends (icon names, display labels, labels with different casing, or coded values) so that frontend changes don't require backend updates.

**Why this priority**: Since we confirmed the system must expect any format, building a flexible normalization mapping is more valuable than just investigating what the frontend sends today.

**Independent Test**: Test by sending each semantic payment method in all known formats (icon name, display label, lowercase, coded) and confirming they all map to the same canonical stored value.

**Acceptance Scenarios**:

1. **Given** a frontend sends `"payments"`, `"Cash"`, `"cash"`, or `"cash"`, **When** the receipt is created, **Then** the stored payment method is the canonical value for Cash.
2. **Given** a frontend sends `"account_balance_wallet"`, `"E-Wallet"`, `"e-wallet"`, or `"ewallet"`, **When** the receipt is created, **Then** the stored payment method is the canonical value for E-Wallet.
3. **Given** a frontend sends `"bolt"`, `"instaPay"`, `"instapay"`, or `"insta_pay"`, **When** the receipt is created, **Then** the stored payment method is the canonical value for instaPay.
4. **Given** a frontend sends `"more_horiz"`, `"Other"`, or `"other"`, **When** the receipt is created, **Then** the stored payment method is the canonical value for Other.

---

### Edge Cases

- What happens when an existing receipt with `"card"`, `"transfer"`, or `"online"` (current backend-only values) is displayed? Existing data must not break.
- What happens when the payment method field is empty or missing? The system should default to `"cash"`.
- What happens when an unsupported value is sent (e.g., typo like `"instapy"`)? The system should return a clear 422 validation error.
- What happens if the frontend sends Material Icon names instead of display labels (e.g., `"bolt"` instead of `"instaPay"`)? The system must map both to the same canonical backend value.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST accept all payment methods the frontend sends, including at minimum: Cash, E-Wallet, instaPay, and Other.
- **FR-002**: The system MUST normalize payment method values to consistent canonical form before storage, regardless of input format (icon name, display label, lowercase label, coded value).
- **FR-003**: The system MUST NOT break existing receipts that use `"card"`, `"transfer"`, or `"online"` as payment methods.
- **FR-004**: The system MUST default the payment method to `"cash"` when no method is provided.
- **FR-005**: The system MUST return a clear 422 validation error for truly invalid/unrecognized payment method values.
- **FR-006**: The system MUST define a mapping from all known frontend input formats to canonical backend storage values.
- **FR-007**: The payment_method field on the Receipt model MUST accept the expanded set of methods without Pydantic/SQLModel validation failures.
- **FR-008**: The backend `PaymentMethod` type alias and `PAYMENT_METHODS` list in `app/shared/constants.py` MUST be updated to include the new methods.

### Key Entities *(include if feature involves data)*

- **PaymentMethod** (`app/shared/constants.py`): A `Literal` type alias currently defining `["cash", "card", "transfer", "online"]`. This must be expanded to include `"ewallet"`, `"instapay"`, `"other"`.
- **Receipt** (`app/modules/finance/models/receipt.py`): The database model that stores `payment_method` as an optional string typed to `PaymentMethod`.
- **CreateReceiptRequest** (`app/api/schemas/finance/receipt.py`): The API input DTO where `method: str = "cash"` accepts the payment method from the frontend.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of receipt creation requests with each frontend payment method return 201 during acceptance testing.
- **SC-002**: All payment methods are stored in consistent lowercase form — verified via database query.
- **SC-003**: Zero existing receipts with `"card"`, `"transfer"`, or `"online"` methods are affected.
- **SC-004**: The exact frontend values are documented in the investigation findings.
- **SC-005**: All existing finance tests continue to pass (no regressions).

## Assumptions

- The frontend sends the payment method as a string in the `method` field of the receipt creation request body.
- The current backend values (`"cash"`, `"card"`, `"transfer"`, `"online"`) are a subset of what the frontend offers — the frontend's full set includes at least Cash, E-Wallet, instaPay, and Other.
- The system must accept any format the frontend sends — icon names (`"bolt"`), display labels (`"instaPay"`), lowercase labels (`"instapay"`), or coded values — and normalize to canonical backend values.
- Canonical storage values: `"cash"`, `"ewallet"`, `"instapay"`, `"other"` (new) + `"card"`, `"transfer"`, `"online"` (existing).
- Since the system is format-agnostic, US3 is no longer an investigation task but a flexible mapping implementation task.
- Existing payment methods `"card"`, `"transfer"`, `"online"` should remain valid after the change.
- The fix approach will follow the same pattern as the student status fix: expand the allowed values and add normalization.
