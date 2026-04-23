# Group Details API Specification

**Version:** 1.0.0  
**Last Updated:** April 23, 2026  
**Base URL:** `/api/v1`  
**Status:** Ready for Backend Development

---

## 1. Overview

This API specification defines all endpoints required for the redesigned Group Details page. The new structure implements **on-demand loading** with a consolidated initial endpoint for fast page load, followed by tab-specific endpoints that load only when accessed.

### Architecture Principles
- **Initial Load:** Single consolidated endpoint returns essential data
- **Tab Loading:** On-demand endpoints for secondary data (Levels, Payments, Students, History)
- **Lookup Table Pattern:** Deduplicate shared data (students, instructors) using lookup tables
- **Grouped Data:** Financial and enrollment data grouped by level for easier UI rendering

---

## 2. Authentication & Authorization

### Required Headers

| Header | Value | Required |
|--------|-------|----------|
| `Authorization` | `Bearer {jwt_token}` | Yes |
| `Content-Type` | `application/json` | Yes |

### Authorization
- **Minimum Role:** `instructor` (for viewing group details)
- **Mutation Role:** `admin` (for edit/delete/archive operations)
- Group ownership checks apply for non-admin instructors

---

## 3. Endpoint Specifications

### 3.1 GET /academics/groups/{group_id}/dashboard

**Purpose:** Consolidated endpoint for initial page load. Returns all essential data for the Overview tab and Group Info Card.

#### Request

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `group_id` | `integer` | Yes | Group identifier |

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `include_current_attendance` | `boolean` | No | `true` | Include current level attendance grid data |

#### Response Schema

```typescript
interface GroupDashboardResponse {
  // Group basic information
  group: {
    id: number
    name: string
    status: 'active' | 'inactive' | 'archived'
    max_capacity: number
    notes: string | null
    created_at: string  // ISO 8601
    
    // Schedule information
    default_day: string | null       // e.g., "Saturday"
    default_time_start: string | null  // HH:MM format
    default_time_end: string | null    // HH:MM format
    
    // Aggregated stats
    total_students_ever: number
    total_revenue: number           // Total collected across all levels
    average_attendance_rate: number // 0.0 - 1.0
  }
  
  // Current level details (for Group Info Card)
  current_level: {
    level_number: number
    course_id: number
    course_name: string
    instructor_id: number
    instructor_name: string
    start_date: string  // ISO 8601
    sessions_planned: number
    sessions_completed: number
    student_count: number           // Current active enrollments
    
    // Level pricing
    price_override: number | null
    monthly_fee: number            // From pricing snapshot
    session_fee: number
    currency: string               // e.g., "EGP"
  }
  
  // Levels summary
  total_levels: number
  completed_levels: number
  cancelled_levels: number
  
  // Overview stats for dashboard cards
  overview: {
    current_month_revenue: number
    students_dropped_this_level: number
    students_completed_this_level: number
    attendance_rate_this_level: number
  }
  
  // Current level attendance (for default Attendance tab)
  current_level_attendance: {
    level_dates: {
      start_date: string
      end_date: string | null
    }
    roster: {
      student_id: number
      student_name: string
      enrollment_id: number
      billing_status: 'paid' | 'due'
    }[]
    sessions: {
      session_id: number
      session_number: number
      date: string
      time_start: string
      time_end: string
      status: 'scheduled' | 'completed' | 'cancelled'
      is_extra_session: boolean
      attendance: Record<string, 'present' | 'absent' | 'excused' | 'late' | null>  // student_id -> status
    }[]
  } | null  // null if include_current_attendance=false
  
  // Metadata
  generated_at: string  // ISO 8601
  cache_ttl: number     // seconds (300 = 5 minutes)
}
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "group": {
      "id": 123,
      "name": "Robotics Alpha",
      "status": "active",
      "max_capacity": 15,
      "notes": "Advanced robotics group",
      "created_at": "2024-01-15T10:00:00Z",
      "default_day": "Saturday",
      "default_time_start": "14:00",
      "default_time_end": "16:00",
      "total_students_ever": 45,
      "total_revenue": 85000.00,
      "average_attendance_rate": 0.87
    },
    "current_level": {
      "level_number": 3,
      "course_id": 5,
      "course_name": "Advanced Robotics",
      "instructor_id": 12,
      "instructor_name": "Ahmed Hassan",
      "start_date": "2025-01-15",
      "sessions_planned": 12,
      "sessions_completed": 8,
      "student_count": 12,
      "price_override": null,
      "monthly_fee": 600.00,
      "session_fee": 50.00,
      "currency": "EGP"
    },
    "total_levels": 3,
    "completed_levels": 2,
    "cancelled_levels": 0,
    "overview": {
      "current_month_revenue": 7200.00,
      "students_dropped_this_level": 1,
      "students_completed_this_level": 0,
      "attendance_rate_this_level": 0.92
    },
    "current_level_attendance": {
      "level_dates": {
        "start_date": "2025-01-15",
        "end_date": null
      },
      "roster": [
        {
          "student_id": 1001,
          "student_name": "Omar Khaled",
          "enrollment_id": 5001,
          "billing_status": "paid"
        }
      ],
      "sessions": [
        {
          "session_id": 2001,
          "session_number": 1,
          "date": "2025-01-15",
          "time_start": "14:00",
          "time_end": "16:00",
          "status": "completed",
          "is_extra_session": false,
          "attendance": {
            "1001": "present",
            "1002": "absent"
          }
        }
      ]
    },
    "generated_at": "2026-04-23T07:45:00Z",
    "cache_ttl": 300
  },
  "message": "Group dashboard loaded successfully"
}
```

---

### 3.2 GET /academics/groups/{group_id}/attendance

**Purpose:** Retrieve attendance data for a specific level (used when switching levels in Attendance tab).

#### Request

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `group_id` | `integer` | Yes | Group identifier |

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `level_number` | `integer` | Yes | - | Target level number |

#### Response Schema

```typescript
interface GroupAttendanceResponse {
  group_id: number
  level_number: number
  level_dates: {
    start_date: string
    end_date: string | null
  }
  
  // Lookup table: student_id -> student info
  students: Record<string, {
    student_id: number
    student_name: string
    enrollment_id: number
    billing_status: 'paid' | 'due'
    joined_at: string  // When enrolled in this level
    dropped_at: string | null
  }>
  
  // All sessions for this level
  sessions: {
    session_id: number
    session_number: number
    date: string
    time_start: string
    time_end: string
    status: 'scheduled' | 'completed' | 'cancelled'
    is_extra_session: boolean
    
    // Attendance map: student_id -> status
    attendance: Record<string, 'present' | 'absent' | 'excused' | 'late' | null>
    
    // Session metadata
    notes: string | null
    completed_at: string | null
  }[]
  
  generated_at: string
  cache_ttl: number
}
```

---

### 3.3 GET /academics/groups/{group_id}/levels/detailed

**Purpose:** Retrieve all levels with detailed information including payment summaries for the Levels tab.

#### Request

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `group_id` | `integer` | Yes | Group identifier |

#### Response Schema

```typescript
interface GroupLevelsDetailedResponse {
  group_id: number
  
  // Lookup table: course_id -> course info
  courses: Record<string, {
    course_id: number
    course_name: string
    description: string | null
  }>
  
  // Lookup table: instructor_id -> instructor info
  instructors: Record<string, {
    instructor_id: number
    instructor_name: string
  }>
  
  // Levels ordered by level_number ASC
  levels: {
    level_number: number
    course_id: number  // Reference to courses lookup
    instructor_id: number  // Reference to instructors lookup
    status: 'active' | 'completed' | 'cancelled'
    
    // Dates
    start_date: string
    end_date: string | null
    created_at: string
    
    // Sessions
    sessions_count: number
    sessions_completed: number
    sessions_cancelled: number
    
    // Students
    students_enrolled: number
    students_completed: number
    students_dropped: number
    students_active: number  // Currently active in this level
    
    // Pricing snapshot at level creation
    pricing_snapshot: {
      monthly_fee: number
      session_fee: number
      currency: string
    }
    
    // Payment summary for this level
    payment_summary: {
      total_expected: number        // Based on enrolled students × fees
      total_collected: number
      total_due: number
      collection_rate: number     // 0.0 - 1.0
      paid_students_count: number
      unpaid_students_count: number
      partially_paid_count: number
    }
    
    // Analytics
    completion_rate: number       // sessions_completed / sessions_count
    average_attendance: number    // 0.0 - 1.0
  }[]
  
  // Group-level payment summary across all levels
  summary: {
    total_expected_all_levels: number
    total_collected_all_levels: number
    total_due_all_levels: number
    overall_collection_rate: number
  }
  
  generated_at: string
  cache_ttl: number
}
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "group_id": 123,
    "courses": {
      "4": {
        "course_id": 4,
        "course_name": "Intro to Robotics",
        "description": "Beginner robotics fundamentals"
      },
      "5": {
        "course_id": 5,
        "course_name": "Advanced Robotics",
        "description": "Complex builds and programming"
      }
    },
    "instructors": {
      "11": {
        "instructor_id": 11,
        "instructor_name": "Sarah Kim"
      },
      "12": {
        "instructor_id": 12,
        "instructor_name": "Ahmed Hassan"
      }
    },
    "levels": [
      {
        "level_number": 1,
        "course_id": 4,
        "instructor_id": 11,
        "status": "completed",
        "start_date": "2024-06-01",
        "end_date": "2024-09-01",
        "created_at": "2024-06-01T10:00:00Z",
        "sessions_count": 12,
        "sessions_completed": 12,
        "sessions_cancelled": 0,
        "students_enrolled": 15,
        "students_completed": 14,
        "students_dropped": 1,
        "students_active": 0,
        "pricing_snapshot": {
          "monthly_fee": 500.00,
          "session_fee": 45.00,
          "currency": "EGP"
        },
        "payment_summary": {
          "total_expected": 7500.00,
          "total_collected": 7200.00,
          "total_due": 300.00,
          "collection_rate": 0.96,
          "paid_students_count": 14,
          "unpaid_students_count": 0,
          "partially_paid_count": 1
        },
        "completion_rate": 1.0,
        "average_attendance": 0.91
      },
      {
        "level_number": 2,
        "course_id": 4,
        "instructor_id": 11,
        "status": "completed",
        "start_date": "2024-09-15",
        "end_date": "2024-12-15",
        "created_at": "2024-09-15T10:00:00Z",
        "sessions_count": 12,
        "sessions_completed": 12,
        "sessions_cancelled": 0,
        "students_enrolled": 14,
        "students_completed": 13,
        "students_dropped": 1,
        "students_active": 0,
        "pricing_snapshot": {
          "monthly_fee": 550.00,
          "session_fee": 50.00,
          "currency": "EGP"
        },
        "payment_summary": {
          "total_expected": 7700.00,
          "total_collected": 7150.00,
          "total_due": 550.00,
          "collection_rate": 0.93,
          "paid_students_count": 13,
          "unpaid_students_count": 1,
          "partially_paid_count": 0
        },
        "completion_rate": 1.0,
        "average_attendance": 0.89
      },
      {
        "level_number": 3,
        "course_id": 5,
        "instructor_id": 12,
        "status": "active",
        "start_date": "2025-01-15",
        "end_date": null,
        "created_at": "2025-01-15T10:00:00Z",
        "sessions_count": 12,
        "sessions_completed": 8,
        "sessions_cancelled": 0,
        "students_enrolled": 12,
        "students_completed": 0,
        "students_dropped": 1,
        "students_active": 11,
        "pricing_snapshot": {
          "monthly_fee": 600.00,
          "session_fee": 55.00,
          "currency": "EGP"
        },
        "payment_summary": {
          "total_expected": 7200.00,
          "total_collected": 6600.00,
          "total_due": 600.00,
          "collection_rate": 0.92,
          "paid_students_count": 11,
          "unpaid_students_count": 1,
          "partially_paid_count": 0
        },
        "completion_rate": 0.67,
        "average_attendance": 0.92
      }
    ],
    "summary": {
      "total_expected_all_levels": 22400.00,
      "total_collected_all_levels": 20950.00,
      "total_due_all_levels": 1450.00,
      "overall_collection_rate": 0.935
    },
    "generated_at": "2026-04-23T07:50:00Z",
    "cache_ttl": 300
  },
  "message": "Group levels loaded successfully"
}
```

---

### 3.4 GET /finance/groups/{group_id}/payments

**Purpose:** Retrieve all payments for the group, grouped by level with payment summaries for the Payments tab.

#### Request

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `group_id` | `integer` | Yes | Group identifier |

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `include_details` | `boolean` | No | `true` | Include individual payment records per level |
| `status` | `string` | No | `all` | Filter: `all`, `paid`, `due`, `partial` |

#### Response Schema

```typescript
interface GroupPaymentsResponse {
  group_id: number
  group_name: string
  
  // Group-level financial summary
  summary: {
    total_expected_all_levels: number
    total_collected_all_levels: number
    total_due_all_levels: number
    total_discounts_all_levels: number
    collection_rate: number  // 0.0 - 1.0
    
    // Counts
    total_payments_count: number
    completed_payments_count: number
    pending_payments_count: number
    failed_payments_count: number
    refunded_payments_count: number
  }
  
  // Payments grouped by level
  by_level: {
    level_number: number
    level_status: 'active' | 'completed' | 'cancelled'
    course_name: string
    
    // Level financial summary
    expected: number
    collected: number
    due: number
    discounts: number
    collection_rate: number
    
    // Student payment status counts
    total_students: number
    paid_count: number
    unpaid_count: number
    partial_count: number
    
    // Individual payment records (if include_details=true)
    payments: {
      payment_id: number
      student_id: number
      student_name: string
      enrollment_id: number
      
      // Payment details
      amount: number
      discount_amount: number
      net_amount: number  // amount - discount
      payment_date: string
      payment_method: 'cash' | 'card' | 'bank_transfer' | 'wallet' | 'other'
      status: 'completed' | 'pending' | 'failed' | 'refunded'
      transaction_type: 'payment' | 'refund' | 'adjustment'
      
      // Receipt info
      receipt_id: number | null
      receipt_number: string | null
      
      // Metadata
      recorded_by: string | null  // Admin who recorded payment
      notes: string | null
      created_at: string
    }[] | null  // null if include_details=false
  }[]
  
  // Lookup table for reference
  students: Record<string, {
    student_id: number
    student_name: string
    phone: string | null
  }>
  
  generated_at: string
  cache_ttl: number
}
```

---

### 3.5 GET /academics/groups/{group_id}/enrollments/all

**Purpose:** Retrieve ALL enrollments for the group (across all levels, both current and historical) for the Students tab.

#### Request

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `group_id` | `integer` | Yes | Group identifier |

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `include_dropped` | `boolean` | No | `true` | Include dropped/completed enrollments |
| `level_number` | `integer` | No | - | Filter to specific level |

#### Response Schema

```typescript
interface GroupEnrollmentsAllResponse {
  group_id: number
  group_name: string
  
  // Lookup table: student_id -> student details
  students: Record<string, {
    student_id: number
    student_name: string
    phone: string | null
    parent_name: string | null
    parent_phone: string | null
  }>
  
  // Enrollments grouped by level
  grouped_by_level: {
    level_number: number
    level_status: 'active' | 'completed' | 'cancelled'
    course_name: string
    instructor_name: string
    level_dates: {
      start_date: string
      end_date: string | null
    }
    
    // Enrollments in this level
    enrollments: {
      enrollment_id: number
      student_id: number  // Reference to students lookup
      
      // Enrollment status
      status: 'active' | 'completed' | 'dropped'
      enrolled_at: string
      dropped_at: string | null
      completed_at: string | null
      
      // Attendance stats
      sessions_attended: number
      sessions_total: number
      attendance_rate: number  // 0.0 - 1.0
      
      // Payment status
      payment_status: 'paid' | 'due' | 'partial' | 'not_paid'
      amount_due: number
      amount_paid: number
      discount_applied: number
      
      // Actions available
      actions: {
        can_transfer: boolean    // Can transfer to another group
        can_drop: boolean        // Can drop (if active)
        can_view_payment: boolean
      }
    }[]
    
    // Level summary
    summary: {
      total_enrollments: number
      active_count: number
      completed_count: number
      dropped_count: number
      paid_count: number
      unpaid_count: number
    }
  }[]
  
  // Group-level stats
  stats: {
    total_students_ever: number
    unique_students: number  // Students who enrolled in multiple levels counted once
    current_active: number
    dropped_total: number
    completed_total: number
  }
  
  // Global actions
  actions: {
    can_enroll_new: boolean
    can_transfer_students: boolean
    available_groups_for_transfer: {
      group_id: number
      group_name: string
      course_name: string
      available_slots: number
    }[] | null
  }
  
  generated_at: string
  cache_ttl: number
}
```

---

### 3.6 GET /academics/groups/{group_id}/lifecycle-summary

**Purpose:** Retrieve comprehensive group lifecycle history for the History tab.

#### Request

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `group_id` | `integer` | Yes | Group identifier |

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `include_competitions` | `boolean` | No | `true` | Include competition history |

#### Response Schema

```typescript
interface GroupLifecycleSummaryResponse {
  group_id: number
  group_name: string
  
  // Group timeline
  timeline: {
    created_at: string
    first_level_started: string | null
    last_level_ended: string | null
    total_active_duration_days: number
  }
  
  // Levels progression
  levels_timeline: {
    level_number: number
    status: 'active' | 'completed' | 'cancelled'
    start_date: string
    end_date: string | null
    duration_days: number
    course_name: string
    instructor_name: string
    
    // Level stats
    students_started: number
    students_completed: number
    students_dropped: number
  }[]
  
  // Enrollment transitions
  enrollment_transitions: {
    enrollment_id: number
    student_id: number
    student_name: string
    
    level_number: number
    level_entered_at: string
    level_completed_at: string | null
    level_dropped_at: string | null
    
    status: 'active' | 'completed' | 'dropped'
    
    // Transition history
    transitions: {
      action: 'enrolled' | 'transferred_in' | 'transferred_out' | 'withdrawn' | 'level_completed' | 'graduated'
      date: string
      from_group_id: number | null
      from_group_name: string | null
      to_group_id: number | null
      to_group_name: string | null
      notes: string | null
    }[]
  }[]
  
  // Course assignments history
  course_assignments: {
    course_id: number
    course_name: string
    assigned_at: string
    removed_at: string | null
    assigned_by: string | null
    notes: string | null
  }[]
  
  // Instructor assignments
  instructor_assignments: {
    instructor_id: number
    instructor_name: string
    start_date: string
    end_date: string | null
    assignment_type: 'primary' | 'substitute' | 'assistant'
    reason: string | null
  }[]
  
  // Competition history (if include_competitions=true)
  competitions: {
    competition_id: number
    competition_name: string
    level_participated: number
    team_name: string | null
    registration_date: string
    participation_status: 'registered' | 'completed' | 'withdrawn'
    result: string | null  // e.g., "1st Place", "Participated"
    award: string | null
  }[] | null
  
  // Summary stats
  summary: {
    total_enrollments_ever: number
    total_students_unique: number
    average_completion_rate: number
    average_attendance_rate: number
    total_revenue: number
    total_sessions_conducted: number
  }
  
  generated_at: string
  cache_ttl: number
}
```

---

## 4. Mutation Endpoints

### 4.1 PATCH /academics/groups/{group_id}

**Purpose:** Update group details (name, schedule, instructor, capacity, notes).

#### Request Body

```typescript
interface UpdateGroupRequest {
  name?: string
  default_day?: string
  default_time_start?: string  // HH:MM
  default_time_end?: string    // HH:MM
  max_capacity?: number
  status?: 'active' | 'inactive' | 'archived'
  notes?: string | null
  instructor_id?: number       // Changes current level instructor
}
```

#### Response

```typescript
interface UpdateGroupResponse {
  success: boolean
  data: {
    id: number
    name: string
    // ... updated group fields
  }
  message: string
}
```

---

### 4.2 POST /academics/groups/{group_id}/progress-level

**Purpose:** Progress group to next level (creates new level + optionally migrates students).

#### Request Body

```typescript
interface ProgressLevelRequest {
  target_level: number
  instructor_id?: number       // New instructor for new level
  course_id?: number            // New course (if changing)
  session_start_date?: string  // ISO 8601
  price_override?: number | null
  auto_migrate_enrollments: boolean  // Migrate active students to new level
  complete_current_level: boolean   // Mark current level as completed
}
```

#### Response

```typescript
interface ProgressLevelResponse {
  success: boolean
  data: {
    old_level_number: number
    new_level_number: number
    enrollments_migrated: number
    sessions_created: number
    new_level_id: number
    message: string
  }
}
```

---

### 4.3 POST /academics/groups/{group_id}/levels/{level_number}/complete

**Purpose:** Mark a level as completed (creates completion certificates, finalizes stats).

#### Response

```typescript
interface CompleteLevelResponse {
  success: boolean
  data: {
    completed_level: {
      id: number
      level_number: number
      status: 'completed'
      end_date: string
    }
    new_level: {
      id: number
      level_number: number
      status: 'active'
      start_date: string
    } | null  // null if no new level created
  }
  message: string
}
```

---

### 4.4 POST /academics/groups/{group_id}/levels/{level_number}/cancel

**Purpose:** Cancel an active level (with optional reason).

#### Request Body

```typescript
interface CancelLevelRequest {
  reason?: string
  notify_students?: boolean  // Send notification to enrolled students
}
```

#### Response

```typescript
interface CancelLevelResponse {
  success: boolean
  data: {
    level_id: number
    level_number: number
    status: 'cancelled'
    cancelled_at: string
    affected_enrollments: number  // Count of dropped students
  }
  message: string
}
```

---

### 4.5 POST /academics/enrollments/{enrollment_id}/transfer

**Purpose:** Transfer student enrollment to another group.

#### Request Body

```typescript
interface TransferEnrollmentRequest {
  to_group_id: number
  reason?: string
  keep_payment_history?: boolean  // Default: true
}
```

#### Response

```typescript
interface TransferEnrollmentResponse {
  success: boolean
  data: {
    original_enrollment: {
      id: number
      status: 'transferred_out'
      transferred_at: string
    }
    new_enrollment: {
      id: number
      group_id: number
      group_name: string
      level_number: number
      status: 'active'
    }
  }
  message: string
}
```

---

### 4.6 DELETE /academics/enrollments/{enrollment_id}

**Purpose:** Drop/remove student from group (soft delete).

#### Response

```typescript
interface DeleteEnrollmentResponse {
  success: boolean
  data: {
    enrollment_id: number
    status: 'dropped'
    dropped_at: string
  }
  message: string
}
```

---

## 5. Error Responses

All endpoints follow standard error response format:

### 400 Bad Request

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": [
      {
        "field": "level_number",
        "message": "Level 5 does not exist for this group"
      }
    ]
  }
}
```

### 401 Unauthorized

```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Missing or invalid authentication token"
  }
}
```

### 403 Forbidden

```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "Insufficient permissions to access this group"
  }
}
```

### 404 Not Found

```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Group with ID 123 not found"
  }
}
```

### 409 Conflict

```json
{
  "success": false,
  "error": {
    "code": "CONFLICT",
    "message": "Cannot cancel level with active enrollments",
    "details": {
      "active_enrollments_count": 12
    }
  }
}
```

### 500 Internal Server Error

```json
{
  "success": false,
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Failed to process request: [error details]"
  }
}
```

---

## 6. Implementation Notes for Backend Developers

### 6.1 Database Query Optimization

For the **dashboard endpoint**, use a 4-query batch strategy:

1. **Query 1:** Get group details + current level
   ```sql
   SELECT g.*, gl.*, c.name as course_name, e.name as instructor_name
   FROM groups g
   JOIN group_levels gl ON g.id = gl.group_id AND gl.status = 'active'
   JOIN courses c ON gl.course_id = c.id
   JOIN employees e ON gl.instructor_id = e.id
   WHERE g.id = :group_id
   ```

2. **Query 2:** Get level statistics
   ```sql
   SELECT level_number, 
          COUNT(*) as total_levels,
          SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_levels,
          -- ... other aggregates
   FROM group_levels
   WHERE group_id = :group_id
   GROUP BY level_number
   ```

3. **Query 3:** Get current level attendance (if requested)
   - Roster: Students with active enrollments in current level
   - Sessions: All sessions for current level with their attendance

4. **Query 4:** Get aggregated stats
   - Total students ever: Count distinct student_ids from enrollments
   - Total revenue: Sum from payments table
   - Attendance rate: Average from attendance records

### 6.2 Data Consistency

- All payment calculations should use **currency-safe decimal arithmetic** (not floating point)
- Attendance rates should be calculated as: `present_sessions / total_sessions * 100`
- Collection rates: `total_collected / total_expected` (handle division by zero)

### 6.3 Caching Strategy

**Recommended server-side caching:**

| Endpoint | Cache Duration | Cache Key |
|----------|----------------|-----------|
| `GET /dashboard` | 5 minutes | `group:{id}:dashboard` |
| `GET /levels/detailed` | 5 minutes | `group:{id}:levels` |
| `GET /payments` | 2 minutes | `group:{id}:payments` |
| `GET /enrollments/all` | 3 minutes | `group:{id}:enrollments` |
| `GET /lifecycle-summary` | 10 minutes | `group:{id}:lifecycle` |
| `GET /attendance` | 1 minute | `group:{id}:level:{n}:attendance` |

**Cache invalidation triggers:**
- Payment recorded → Invalidate `payments`, `dashboard`, `levels/detailed`
- Attendance marked → Invalidate `attendance`, `dashboard`
- Student enrolled/dropped → Invalidate `enrollments/all`, `dashboard`, `levels/detailed`
- Level progressed/completed/cancelled → Invalidate all group caches

### 6.4 Lookup Table Pattern

When returning lists of related entities, use lookup tables to avoid duplication:

```typescript
// ❌ DON'T: Duplicate data
{
  "enrollments": [
    { "id": 1, "student_name": "Omar", "student_phone": "..." },
    { "id": 2, "student_name": "Omar", "student_phone": "..." }  // Duplicated!
  ]
}

// ✅ DO: Use lookup table
{
  "students": {
    "1001": { "name": "Omar", "phone": "..." }
  },
  "enrollments": [
    { "id": 1, "student_id": 1001 },
    { "id": 2, "student_id": 1001 }
  ]
}
```

---

## 7. Changelog

### v1.0.0 (2026-04-23)
- Initial API specification
- 6 GET endpoints for data retrieval
- 6 mutation endpoints for group/enrollment management
- Lookup table pattern implementation
- On-demand tab loading architecture
- Comprehensive error response schemas

---

## 8. Appendix: Complete Endpoint Summary

| Method | Endpoint | Purpose | Tab/Feature |
|--------|----------|---------|-------------|
| GET | `/academics/groups/{id}/dashboard` | Consolidated initial data | Overview |
| GET | `/academics/groups/{id}/attendance` | Attendance grid data | Attendance |
| GET | `/academics/groups/{id}/levels/detailed` | Levels with payment summaries | Levels |
| GET | `/finance/groups/{id}/payments` | Payments grouped by level | Payments |
| GET | `/academics/groups/{id}/enrollments/all` | All enrollments grouped | Students |
| GET | `/academics/groups/{id}/lifecycle-summary` | Complete history | History |
| PATCH | `/academics/groups/{id}` | Update group | Edit Dialog |
| POST | `/academics/groups/{id}/progress-level` | Progress to new level | Progress Dialog |
| POST | `/academics/groups/{id}/levels/{n}/complete` | Complete level | History Tab |
| POST | `/academics/groups/{id}/levels/{n}/cancel` | Cancel level | History Tab |
| POST | `/academics/enrollments/{id}/transfer` | Transfer student | Students Tab |
| DELETE | `/academics/enrollments/{id}` | Drop student | Students Tab |

---

*Document Status: Ready for Backend Implementation*
