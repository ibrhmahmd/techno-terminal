# HR (Human Resources) API Reference

Base path: `/api/v1/hr`

> **Note:** This module has been refactored to follow SOLID principles with a layered architecture (repositories, services, DTOs). See `docs/skills/module_refactoring_guide.md` for details.

---

## 🔐 Authentication
All requests MUST include a Bearer token in the `Authorization` header:
```http
Authorization: Bearer <access_token>
```

---

## Schemas

### EmployeePublic
```json
{
  "id": 1,
  "full_name": "Ahmed Hassan",
  "phone": "01123456789",
  "email": "ahmed@techno.com",
  "job_title": "Senior Robotics Instructor",
  "employment_type": "full_time",
  "is_active": true,
  "hired_at": "2025-01-15T00:00:00"
}
```

### EmployeeListItem
```json
{
  "id": 1,
  "full_name": "Ahmed Hassan",
  "job_title": "Senior Robotics Instructor",
  "employment_type": "full_time",
  "is_active": true
}
```

### EmployeeCreateInput
```json
{
  "full_name": "string (required)",
  "phone": "string (required)",
  "email": "string (optional)",
  "national_id": "string (required)",
  "university": "string (required)",
  "major": "string (required)",
  "is_graduate": "boolean (default: false)",
  "job_title": "string (optional)",
  "employment_type": "string (required) - full_time|part_time|contract",
  "monthly_salary": "number (optional)",
  "contract_percentage": "number (optional)",
  "is_active": "boolean (default: true)"
}
```

### StaffAccountPublic
```json
{
  "id": 1,
  "username": "ahmed.hassan",
  "email": "ahmed@techno.com",
  "employee_id": 1,
  "employee_name": "Ahmed Hassan",
  "job_title": "Senior Robotics Instructor",
  "is_active": true,
  "created_at": "2025-01-15T10:00:00"
}
```

### AttendanceLogInput
```json
{
  "employee_id": "integer (required)",
  "status": "string (required) - present|absent|late|early_departure",
  "check_in": "datetime (optional) - ISO 8601",
  "check_out": "datetime (optional) - ISO 8601",
  "notes": "string (optional)"
}
```

### AttendanceLogOutput
```json
{
  "employee_id": 1,
  "status": "present",
  "logged_at": "2026-04-01T09:00:00",
  "message": "Attendance logged successfully"
}
```

### CreateEmployeeAccountRequest
```json
{
  "email": "string (required)",
  "password": "string (required, min 8 characters)",
  "role": "string (required) - admin|system_admin"
}
```

### EmployeeAccountResponse
```json
{
  "employee_id": 1,
  "user_id": 42,
  "email": "ahmed@techno.com",
  "role": "admin",
  "created_at": "2026-04-29T10:00:00"
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

### Employees

#### 1. List all employees
**GET** `/api/v1/hr/employees`

**Query Parameters:**
- `page` - integer (default: 1, min: 1) - Page number
- `page_size` - integer (default: 20, min: 1, max: 100) - Items per page

**Response (200):** `ApiResponse<list<EmployeeListItem>>`

**Notes:**
- Paginated list of all employees
- Response message includes total count

---

#### 2. Create employee record
**POST** `/api/v1/hr/employees`

**Request Body:** `EmployeeCreateInput`

**Response (201):** `ApiResponse<EmployeePublic>`

**Error Responses:**
- `422` - Validation error
- `409` - Conflict (e.g., duplicate national_id)

**Notes:**
- Creates new employee record
- National ID and university info required for HR compliance
- Sensitive fields (salary, national_id) excluded from public response

---

#### 3. Get employee by ID
**GET** `/api/v1/hr/employees/{employee_id}`

**Path Parameters:**
- `employee_id` - integer (required)

**Response (200):** `ApiResponse<EmployeePublic>`

**Error Response:**
- `404` - Employee not found

---

#### 4. Update employee record
**PUT** `/api/v1/hr/employees/{employee_id}`

**Path Parameters:**
- `employee_id` - integer (required)

**Request Body:** `EmployeeCreateInput`

**Response (200):** `ApiResponse<EmployeePublic>`

**Error Responses:**
- `404` - Employee not found
- `422` - Validation error
- `409` - Conflict (e.g., duplicate national_id)

**Notes:**
- Partial update - only provided fields are updated
- Unset fields in request body are ignored

---

### Staff Accounts

#### 5. List staff accounts
**GET** `/api/v1/hr/staff-accounts`

**Response (200):** `ApiResponse<list<StaffAccountPublic>>`

**Notes:**
- Returns all staff accounts with linked employee info
- Includes username, email, and employee details

---

#### 6. Create user account for employee
**POST** `/api/v1/hr/employees/{employee_id}/create-account`

**Path Parameters:**
- `employee_id` - integer (required) - Employee ID to link account to

**Request Body:** `CreateEmployeeAccountRequest`

**Response (201):** `ApiResponse<EmployeeAccountResponse>`

**Error Responses:**
- `404` - Employee not found
- `409` - Account already exists for employee
- `422` - Validation error

**Notes:**
- Creates a Supabase user account for an existing employee
- Only admin or system_admin roles are allowed
- Links the user account to the employee record

---

### Attendance (Stub)

#### 7. Log employee attendance
**POST** `/api/v1/hr/attendance/log`

**Request Body:** `AttendanceLogInput`

**Response (200):** `ApiResponse<AttendanceLogOutput>`

**Error Response (422):** `HTTPValidationError`

**Notes:**
- Stub endpoint for future HR attendance module
- Currently returns mock response
- Full implementation planned for future release
