# Enrollments API Reference

Base path: `/api/v1/enrollments`

---

## 🔐 Authentication
All requests MUST include a Bearer token in the `Authorization` header:
```http
Authorization: Bearer <access_token>
```

---

## Schemas

### EnrollmentPublic
```json
{
  "id": 1,
  "student_id": 1,
  "group_id": 1,
  "level_number": 1,
  "status": "active",
  "amount_due": 1500.0,
  "discount_applied": 0.0,
  "notes": "First enrollment",
  "enrolled_at": "2026-04-01T10:00:00"
}
```

### EnrollStudentInput
```json
{
  "student_id": "integer (required)",
  "group_id": "integer (required)",
  "amount_due": "number (optional) - calculated from course price if not provided",
  "discount": "number (default: 0) - discount amount applied",
  "notes": "string (optional)",
  "created_by": "integer (optional) - set automatically from current user"
}
```

**Note:** `level_number` is automatically set from the group's current level.

### TransferStudentInput
```json
{
  "from_enrollment_id": "integer (required) - enrollment ID to transfer from",
  "to_group_id": "integer (required) - target group ID",
  "created_by": "integer (optional) - set automatically from current user"
}
```

**Note:** The transfer looks up the source enrollment by ID, then creates a new enrollment in the target group with the same student and balance.

### ApplyDiscountInput
```json
{
  "discount_amount": "number (default: 50.0)"
}
```

### StudentEnrollmentSummaryPublic
```json
{
  "student_id": 1,
  "student_name": "John Doe",
  "enrollment_id": 1,
  "level_number": 1,
  "status": "active",
  "sessions_attended": 3,
  "sessions_total": 5,
  "payment_status": "due",
  "amount_due": 1500.0,
  "discount_applied": 0.0
}
```

### ApiResponse (Envelope)
```json
{
  "success": true,
  "data": {},
  "message": null
}
```

---

## Endpoints

### 1. Enroll a student in a group
**POST** `/api/v1/enrollments`

**Request Body:** `EnrollStudentInput`

**Response (201):** `ApiResponse<EnrollmentPublic>`

**Error Response (422):** `HTTPValidationError`

**Notes:**
- Creates enrollment linking student to group at specified level
- Amount due is calculated from course price
- Returns 409 Conflict if student already enrolled

---

### 2. Drop an enrollment
**DELETE** `/api/v1/enrollments/{enrollment_id}`

**Path Parameters:**
- `enrollment_id` - integer (required)

**Response (200):** `ApiResponse<EnrollmentPublic>`

**Error Response (422):** `HTTPValidationError`

**Notes:**
- Soft delete - marks enrollment as dropped
- Preserves enrollment history
- Cannot drop if balance is outstanding

---

### 3. Transfer a student to a new group
**POST** `/api/v1/enrollments/transfer`

**Request Body:** `TransferStudentInput`

**Response (200):** `ApiResponse<EnrollmentPublic>`

**Error Response (422):** `HTTPValidationError`

**Notes:**
- Transfers student from one group to another
- Maintains enrollment history
- Balance transfers with student

---

### 4. Get student enrollment history
**GET** `/api/v1/enrollments/student/{student_id}`

**Path Parameters:**
- `student_id` - integer (required)

**Response (200):** `ApiResponse<list<EnrollmentPublic>>`

**Error Response (422):** `HTTPValidationError`

**Notes:**
- Returns all enrollments for a student (active and dropped)
- Ordered by enrolled_at descending

---

### 5. Apply sibling discount to enrollment
**POST** `/api/v1/enrollments/{enrollment_id}/discount`

**Path Parameters:**
- `enrollment_id` - integer (required)

**Query Parameters:**
- `discount_amount` - number (optional, default: 50.0)

**Response (200):** `ApiResponse<EnrollmentPublic>`

**Error Response (422):** `HTTPValidationError`

**Notes:**
- Only works on active enrollments
- Discount is added to existing `discount_applied` field
- Used for family/sibling discounts

---

### 6. Get group roster (enrollments by group)
**GET** `/api/v1/enrollments/group/{group_id}/students-summary`

**Path Parameters:**
- `group_id` - integer (required)

**Query Parameters:**
- `level` - integer (optional) - Filter by level number

**Response (200):** `ApiResponse<list<StudentEnrollmentSummaryPublic>>`

**Error Response (422):** `HTTPValidationError`

**Notes:**
- Returns summary of all student enrollments for the group
- Includes attendance counts and payment status
- Optional level filter for multi-level groups
- Useful for attendance sheets and roster views
