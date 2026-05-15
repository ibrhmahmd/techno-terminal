# Enrollment API Contracts

**Note**: Contracts are unchanged — only backend persistence behavior is fixed.

## POST /api/v1/enrollments

**Request**: `EnrollStudentInput` (student_id, group_id, amount_due, discount, notes, created_by)  
**Response**: `ApiResponse[EnrollmentPublic]` — 201 on success  
**Auth**: `require_admin`

## PATCH /api/v1/enrollments/{id}/drop

**Request**: `{ performed_by, reason? }`  
**Response**: `ApiResponse[EnrollmentPublic]` — 200 on success  
**Auth**: `require_admin`

## POST /api/v1/enrollments/transfer

**Request**: `TransferStudentInput` (from_enrollment_id, to_group_id, created_by)  
**Response**: `ApiResponse[EnrollmentPublic]` — 200 on success  
**Auth**: `require_admin`

## PATCH /api/v1/enrollments/{id}/complete

**Request**: `{ performed_by }`  
**Response**: `ApiResponse[EnrollmentPublic]` — 200 on success  
**Auth**: `require_admin`

## PATCH /api/v1/enrollments/{id}/sibling-discount

**Request**: `{ discount_amount }`  
**Response**: `ApiResponse[EnrollmentPublic]` — 200 on success  
**Auth**: `require_admin`
