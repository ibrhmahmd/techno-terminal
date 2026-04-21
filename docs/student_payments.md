# CRM Student Payments API

API endpoints for retrieving and managing student payment records with receipt integration.

---

## Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/crm/students/{student_id}/payments` | List all payments for a student |
| GET | `/api/v1/finance/payments/{payment_id}` | Get detailed payment information |
| POST | `/api/v1/finance/payments/{payment_id}/send-receipt` | Send receipt to student via WhatsApp/Email |

---

## 1. List Student Payments

**GET** `/api/v1/crm/students/{student_id}/payments`

Retrieve all payment records associated with a specific student, including related receipt and enrollment information.

### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| student_id | integer | Yes | The unique identifier of the student |

### Response (200 OK)

```json
{
  "success": true,
  "data": [
    {
      "id": 12345,
      "student_id": 789,
      "amount": 1500.00,
      "payment_date": "2024-01-15T10:30:00",
      "payment_method": "cash",
      "status": "completed",
      "receipt_id": 9876,
      "receipt_number": "RCP-2024-0001",
      "course_name": "Introduction to Robotics",
      "group_name": "Robotics 101 - Group A",
      "level_number": 1,
      "transaction_type": "payment"
    },
    {
      "id": 12346,
      "student_id": 789,
      "amount": 1200.00,
      "payment_date": "2024-02-01T14:15:00",
      "payment_method": "bank_transfer",
      "status": "completed",
      "receipt_id": 9877,
      "receipt_number": "RCP-2024-0002",
      "course_name": "Advanced Programming",
      "group_name": "Code Masters - Group B",
      "level_number": 2,
      "transaction_type": "payment"
    }
  ],
  "total": 2,
  "skip": 0,
  "limit": 50,
  "message": null
}
```

### Response Schema: PaymentListItem

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Unique payment identifier |
| student_id | integer | Reference to the student |
| amount | decimal(10,2) | Payment amount in local currency |
| payment_date | string (ISO 8601) | Date and time when payment was made |
| payment_method | string | Method used: "cash", "bank_transfer", "credit_card", "debit_card", "online" |
| status | string | Payment status: "completed" (default) |
| receipt_id | integer | Reference to the generated receipt |
| receipt_number | string | Human-readable receipt identifier (e.g., "RCP-2024-0001") |
| course_name | string \| null | Name of the course this payment is for |
| group_name | string \| null | Name of the specific group/enrollment |
| level_number | integer \| null | Course level number |
| transaction_type | string | Type of transaction: "payment", "refund", "adjustment" |

### Error Responses

**404 Not Found** - Student does not exist
```json
{
  "success": false,
  "data": null,
  "message": "Student not found"
}
```

---

## 2. Get Payment Details

**GET** `/api/v1/finance/payments/{payment_id}`

Retrieve comprehensive details about a specific payment, including receipt details, enrollment information, student snapshot, and parent contact information.

### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| payment_id | integer | Yes | The unique identifier of the payment |

### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "id": 12345,
    "student_id": 789,
    "amount": 1500.00,
    "payment_type": "course_level",
    "transaction_type": "payment",
    "discount_amount": 0.00,
    "notes": "Full payment for January session",
    "created_at": "2024-01-15T10:30:00",
    "receipt": {
      "receipt_id": 9876,
      "receipt_number": "RCP-2024-0001",
      "issued_date": "2024-01-15T10:30:00",
      "payment_method": "cash",
      "issued_by": "Admin User",
      "notes": null
    },
    "enrollment": {
      "enrollment_id": 456,
      "group_id": 101,
      "group_name": "Robotics 101 - Group A",
      "course_name": "Introduction to Robotics",
      "level_number": 1,
      "instructor_id": 55,
      "instructor_name": "Dr. Ahmed Hassan"
    },
    "student": {
      "full_name": "Omar Khaled",
      "phone": "+20 123 456 7890"
    },
    "parent": {
      "parent_id": 234,
      "full_name": "Khaled Mohamed",
      "phone": "+20 123 456 7891"
    }
  },
  "message": null
}
```

### Response Schema: PaymentDetailsResponse

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Unique payment identifier |
| student_id | integer | Reference to the student |
| amount | decimal(10,2) | Payment amount |
| payment_type | string \| null | Type of payment: "course_level", "competition", "materials", etc. |
| transaction_type | string | Transaction type: "payment", "refund", "adjustment" |
| discount_amount | decimal(10,2) | Discount applied to this payment |
| notes | string \| null | Optional notes |
| created_at | string (ISO 8601) \| null | When the payment record was created |
| receipt | ReceiptDetails | Receipt information |
| enrollment | EnrollmentInfo | Enrollment, group, course, and instructor details |
| student | StudentSnapshot | Student information at time of payment |
| parent | ParentInfo | Primary parent contact information |

#### ReceiptDetails
| Field | Type | Description |
|-------|------|-------------|
| receipt_id | integer | Reference to the receipt |
| receipt_number | string \| null | Human-readable receipt identifier |
| issued_date | string (ISO 8601) \| null | When the receipt was generated |
| payment_method | string \| null | Method used for payment |
| issued_by | string \| null | Name of user who issued the receipt |
| notes | string \| null | Receipt notes |

#### EnrollmentInfo
| Field | Type | Description |
|-------|------|-------------|
| enrollment_id | integer \| null | Reference to the enrollment record |
| group_id | integer \| null | Group ID |
| group_name | string \| null | Name of the specific group |
| course_name | string \| null | Name of the course |
| level_number | integer \| null | Course level number |
| instructor_id | integer \| null | Instructor's team member ID |
| instructor_name | string \| null | Name of the assigned instructor |

#### StudentSnapshot
| Field | Type | Description |
|-------|------|-------------|
| full_name | string | Student's full name at time of payment |
| phone | string \| null | Contact phone number |

#### ParentInfo
| Field | Type | Description |
|-------|------|-------------|
| parent_id | integer \| null | Parent's unique identifier |
| full_name | string \| null | Parent's full name |
| phone | string \| null | Parent's contact phone |

### Error Responses

**404 Not Found** - Payment does not exist
```json
{
  "success": false,
  "data": null,
  "message": "Payment not found"
}
```

---

## 3. Send Receipt to Student

**POST** `/api/v1/finance/payments/{payment_id}/send-receipt`

Send the receipt PDF to the student's primary parent via WhatsApp or Email. The notification is queued via background tasks for async processing.

### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| payment_id | integer | Yes | The unique identifier of the payment |

### Request Body

```json
{
  "method": "whatsapp"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| method | string | Yes | Delivery method: "whatsapp" or "email" |

### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "success": true,
    "message": "Receipt queued for sending to Khaled Mohamed via whatsapp.",
    "receipt_id": 9876,
    "recipient_contact": "+20 123 456 7891",
    "sent_at": "2024-01-15T10:35:00"
  },
  "message": "Receipt queued for sending to Khaled Mohamed via whatsapp."
}
```

### Response Schema: SendReceiptResponse

| Field | Type | Description |
|-------|------|-------------|
| success | boolean | Whether the send operation was queued successfully |
| message | string | Human-readable result message |
| receipt_id | integer | The receipt ID that was sent |
| recipient_contact | string \| null | Phone or email used for delivery |
| sent_at | string (ISO 8601) | When the send was queued |

### Error Responses

**400 Bad Request** - Invalid method or missing parent/contact info
```json
{
  "success": false,
  "data": {
    "success": false,
    "message": "No parent found for student Omar Khaled.",
    "receipt_id": 9876,
    "recipient_contact": null,
    "sent_at": "2024-01-15T10:35:00"
  },
  "message": "No parent found for student Omar Khaled."
}
```

**404 Not Found** - Payment does not exist
```json
{
  "success": false,
  "data": null,
  "message": "Payment not found"
}
```

**500 Internal Server Error** - Notification service error
```json
{
  "success": false,
  "data": null,
  "message": "Internal server error"
}
```

---

## Related Endpoints

### Download Receipt PDF (Finance API)

**GET** `/api/v1/finance/receipts/{receipt_id}/pdf`

Download the receipt as a PDF file. This endpoint is part of the Finance module but is referenced here for completeness.

**Response**: Binary PDF data with `Content-Type: application/pdf`

---

## Query Parameters (List Endpoint)

The list payments endpoint supports standard pagination:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| skip | integer | 0 | Number of records to skip |
| limit | integer | 50 | Maximum records to return (max: 200) |

---

## Notes

1. **API Organization**: 
   - **CRM Router**: The list endpoint (`/api/v1/crm/students/{student_id}/payments`) is in the CRM router as it's student-centric
   - **Finance Router**: The detail and send-receipt endpoints (`/api/v1/finance/payments/{payment_id}`) are in the Finance router as they are finance operations

2. **Data Structure**: The payment details response uses nested objects:
   - `receipt`: Receipt information including receipt_id, number, date, and issuer
   - `enrollment`: Enrollment, group, course, and instructor details
   - `student`: Student snapshot (name and phone at time of payment)
   - `parent`: Primary parent contact information (resolved from student_parent relationship)

3. **Receipt Sending**: The send endpoint:
   - Validates payment exists and has an associated receipt
   - Resolves the primary parent from student_parent relationship (ordered by `is_primary DESC`)
   - Uses `NotificationService.payment.notify_payment_received()` for delivery
   - Queues the notification via FastAPI BackgroundTasks for async processing
   - Returns the actual contact used (parent phone for WhatsApp)

4. **Sorting**: The list endpoint returns payments sorted by `payment_date` descending (newest first).

5. **Soft Deletes**: All queries filter out soft-deleted payments (`deleted_at IS NULL`).

6. **Null Safety**: Many fields are nullable as payments may not always have enrollments (e.g., competition fees, material purchases).
