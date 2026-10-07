# Feature Specification: Extend Employee Schemas

**Feature Branch**: `005-extend-employee-schemas`
**Created**: 2026-05-12
**Status**: Draft
**Input**: User description: Redesign Employee Cards & Detail Dialog

## User Scenarios & Testing

### User Story 1 - View Complete Employee Details (Priority: P1)

An admin opens an employee's detail page and sees all relevant information including academic background (university, major, graduation status) and financial details (monthly salary, contract percentage) without needing to navigate elsewhere.

**Why this priority**: This is the primary ask — the detail dialog must show all employee data. Without it, users have no way to see academic/financial info through the API.

**Independent Test**: Can be fully tested by calling the employee detail endpoint and verifying all 5 new fields (university, major, is_graduate, monthly_salary, contract_percentage) are present in the response for an employee that has them populated.

**Acceptance Scenarios**:

1. **Given** an employee record with university, major, is_graduate, monthly_salary, and contract_percentage stored, **When** a user requests that employee's details, **Then** all five fields are present and populated with correct values in the response
2. **Given** an employee record where some of these fields are null, **When** a user requests that employee's details, **Then** those fields return null (not absent from response)
3. **Given** an employee record with no optional fields populated, **When** a user requests that employee's details, **Then** all five fields return null with no errors

---

### User Story 2 - Browse Employees With Contact Info (Priority: P1)

An admin browsing the employee list sees phone number and email address on each employee card, allowing quick contact without opening each employee's detail dialog.

**Why this priority**: The explicit rationale given is to avoid forcing users to open detail dialogs just to find contact information. This is a direct UX improvement.

**Independent Test**: Can be fully tested by calling the employee list endpoint and verifying phone and email fields are present in every item in the response.

**Acceptance Scenarios**:

1. **Given** multiple employee records with phone and email populated, **When** a user requests the employee list, **Then** every list item includes phone and email fields with correct values
2. **Given** an employee with null phone and/or email, **When** the list endpoint returns, **Then** those fields appear as null (not absent)

---

### Edge Cases

- What happens when monthly_salary or contract_percentage are zero? They should return as 0 (not null)
- What happens when an employee has no stored university/major? These should return as null
- How does the system handle very long university names or majors? They should be returned in full without truncation
- Are existing frontend integrations broken by new fields? No — new optional fields are backward-compatible

## Requirements

### Functional Requirements

- **FR-001**: The employee detail endpoint MUST return `university` as an optional string field
- **FR-002**: The employee detail endpoint MUST return `major` as an optional string field
- **FR-003**: The employee detail endpoint MUST return `is_graduate` as an optional boolean field
- **FR-004**: The employee detail endpoint MUST return `monthly_salary` as an optional numeric field
- **FR-005**: The employee detail endpoint MUST return `contract_percentage` as an optional numeric field
- **FR-006**: The employee list endpoint MUST return `phone` as an optional string field for each item
- **FR-007**: The employee list endpoint MUST return `email` as an optional string field for each item
- **FR-008**: All new fields MUST be null when the underlying data is not stored (backward compatibility)
- **FR-009**: All existing fields on both endpoints MUST continue to work unchanged

### Key Entities

- **Employee**: Staff member record with identity info (full_name, phone, email, national_id), employment details (job_title, employment_type, is_active, hired_at), academic background (university, major, is_graduate), and financial arrangement (monthly_salary, contract_percentage)
- **EmployeeListItem**: Summary representation of an employee used in list views, containing identity and employment info plus contact details (phone, email)

## Success Criteria

### Measurable Outcomes

- **SC-001**: Users can view all employee academic and financial data through the detail endpoint without additional API calls
- **SC-002**: Users can identify contact information (phone, email) from employee list cards without opening individual detail dialogs
- **SC-003**: Existing integrations consuming the employee endpoints continue to function without modification (all new fields are optional)
- **SC-004**: No database migration or schema change is required — all fields already exist in the data store

## Assumptions

- All seven new fields already exist in the database on the employee record and are populated during create/update — no new data storage is needed
- Existing frontends ignore unknown JSON fields, making this backward-compatible
- The phone and email fields on the list endpoint need only be selected in the existing query — no new query logic is needed
- academic and financial fields (university, major, is_graduate, monthly_salary, contract_percentage) need only be selected in the detail endpoint query — no new data access logic is needed
- No database migration or schema change is required
