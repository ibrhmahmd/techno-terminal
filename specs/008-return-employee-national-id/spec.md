# Feature Specification: Return Employee National ID

**Feature Branch**: `008-return-employee-national-id`
**Created**: 2026-05-13
**Status**: Draft
**Input**: User description: Return required data from employee endpoint per backend-fixes.md

## User Scenarios & Testing

### User Story 1 - View Employee National ID (Priority: P1)

An admin viewing an employee's detail page sees the national ID number alongside other employee data, enabling identity verification without switching systems.

**Why this priority**: The national ID is a required piece of employee data that must be accessible through the detail endpoint. Without it, admins cannot verify employee identity from the API.

**Independent Test**: Can be fully tested by calling the employee detail endpoint and verifying `national_id` is present in the response (either as a string or null).

**Acceptance Scenarios**:

1. **Given** an employee record with a stored national ID, **When** a user requests that employee's details, **Then** the `national_id` field is present with the correct string value
2. **Given** an employee record where national_id is null, **When** a user requests that employee's details, **Then** `national_id` returns null (not absent from response)
3. **Given** an employee record retrieved via the detail endpoint, **When** inspecting the response, **Then** all previously available fields (full_name, phone, email, etc.) continue to work unchanged

---

### Edge Cases

- What happens when national_id is null? It should return as null (not omitted from the response)
- What happens to existing frontend integrations? Adding an optional nullable field is backward-compatible
- Does adding national_id change security posture? The field is already stored in the database and available through create/update flows — exposing it via the read endpoint is a business decision

## Requirements

### Functional Requirements

- **FR-001**: The employee detail endpoint MUST return `national_id` as an optional string field
- **FR-002**: `national_id` MUST be null when no value is stored for the employee
- **FR-003**: All existing fields on the employee detail endpoint MUST continue to be returned unchanged
- **FR-004**: `has_account` field (already returned) requires no changes

### Key Entities

- **Employee**: Staff member record currently exposing id, full_name, phone, email, job_title, employment_type, is_active, hired_at, has_account, university, major, is_graduate, monthly_salary, contract_percentage — now also returning national_id as an optional field

## Success Criteria

### Measurable Outcomes

- **SC-001**: Users can view the employee's national ID through the detail endpoint without additional API calls or UI navigation
- **SC-002**: Existing integrations continue to function — no breaking changes to the response schema
- **SC-003**: All existing test assertions pass without modification

## Assumptions

- The `national_id` field already exists in the database on the employee record and is already captured during employee create/update — no new data storage is needed
- The `EmployeeReadDTO` internal DTO already carries `national_id` — only the API-facing `EmployeePublic` schema needs to include it
- The `has_account` field is already returned correctly and needs no backend change (per backend-fixes.md)
- No database migration or schema change is required
