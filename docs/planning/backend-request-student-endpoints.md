# Backend API Development Request - Student Detail Endpoints

**Requested By**: Frontend Team  
**Date**: April 13, 2026  
**Priority**: HIGH (Blocking Student Detail Page)  
**Status**: Required for Student Detail Page functionality

---

## Overview

The Student Detail Page requires two additional endpoints that are currently returning 404 errors:

1. `GET /crm/students/{id}/details` - Full student profile with relationships
2. `GET /students/{id}/siblings` - Student sibling information

These endpoints are critical for the Student Detail Page to function properly.

---

## Endpoint 1: Get Student with Full Details

### Specification

```yaml
Endpoint: GET /api/v1/crm/students/{id}/details
Authentication: Required (JWT Bearer Token)
Path Parameters:
  id: integer (required) - Student ID
Response Format: ApiResponse<StudentWithDetails>
```

### Purpose
Returns complete student profile including all relationships (parents, enrollments, courses, competitions, teams) in a single request. This reduces the need for multiple API calls from the frontend.

### Response Schema

```typescript
interface ApiResponse<T> {
  success: boolean
  data: T
}

interface StudentWithDetails {
  // Core student fields (same as Student model)
  id: number
  full_name: string
  phone?: string
  email?: string
  gender?: 'male' | 'female' | 'other'
  date_of_birth: string        // Format: YYYY-MM-DD
  age?: number                 // Calculated or stored
  school?: string
  grade?: string
  status: 'active' | 'waiting' | 'inactive'
  priority?: number            // For waiting list ordering
  notes?: string
  parent_id?: number
  parent_name?: string         // Denormalized for quick display
  created_at: string           // ISO 8601 format
  updated_at: string           // ISO 8601 format

  // Related data - nested objects/arrays
  parent?: Parent              // Full parent object if parent_id exists
  enrollments?: EnrollmentInfo[]
  siblings?: SiblingInfo[]     // Can be empty array or omitted
  balance?: StudentBalanceSummary  // Quick balance overview
  
  // Additional relationships (for other tabs)
  courses?: CourseInfo[]       // Currently enrolled courses
  competitions?: CompetitionInfo[]  // Competition registrations
  teams?: TeamInfo[]           // Team memberships
}

interface Parent {
  id: number
  full_name: string
  phone?: string
  phone_primary?: string      // Alternative phone
  phone_secondary?: string
  email?: string
  whatsapp?: string
  address?: string
  relation?: string            // 'father', 'mother', 'guardian', etc.
}

interface EnrollmentInfo {
  id: number                   // Enrollment ID
  group_id: number
  group_name: string
  course_name: string
  level_number: number         // 1-10 or course level
  status: 'active' | 'dropped' | 'transferred' | 'completed'
  enrolled_at: string          // ISO 8601
}

interface StudentBalanceSummary {
  total_amount_due: number     // Total fees across all enrollments
  total_discounts: number      // Total discounts applied
  total_paid: number           // Total payments received
  net_balance: number          // Positive = credit, Negative = owes
}
```

### Example Response

```json
{
  "success": true,
  "data": {
    "id": 15,
    "full_name": "Ahmed Mohammed",
    "phone": "+201234567890",
    "email": "ahmed@example.com",
    "gender": "male",
    "date_of_birth": "2010-05-15",
    "age": 15,
    "school": "International School",
    "grade": "10th",
    "status": "active",
    "notes": "Allergic to peanuts",
    "parent_id": 42,
    "parent_name": "Mohammed Ali",
    "created_at": "2023-01-15T10:30:00Z",
    "updated_at": "2026-04-10T14:20:00Z",
    "parent": {
      "id": 42,
      "full_name": "Mohammed Ali",
      "phone": "+201234567891",
      "phone_primary": "+201234567891",
      "email": "mohammed@example.com",
      "whatsapp": "+201234567891",
      "address": "123 Main St, Cairo",
      "relation": "father"
    },
    "enrollments": [
      {
        "id": 101,
        "group_id": 5,
        "group_name": "Robotics Level 3 - Group A",
        "course_name": "Advanced Robotics",
        "level_number": 3,
        "status": "active",
        "enrolled_at": "2025-09-01T09:00:00Z"
      }
    ],
    "balance": {
      "total_amount_due": 5000.00,
      "total_discounts": 500.00,
      "total_paid": 3000.00,
      "net_balance": -2500.00
    }
  }
}
```

### Backend Implementation Notes

1. **Database Query Strategy**:
   - Primary: Student record by ID
   - Join: Parent (if parent_id exists)
   - Join: Enrollments with active status + Group info
   - Aggregate: Balance summary from finance tables

2. **Performance Considerations**:
   - Use database joins to minimize queries
   - Consider materialized view for balance summary
   - Cache frequently accessed student profiles

3. **Error Responses**:
   ```json
   // 404 - Student not found
   {
     "success": false,
     "error": "Student not found",
     "detail": "No student found with ID 15"
   }

   // 403 - Forbidden (accessing other center's student)
   {
     "success": false,
     "error": "Access denied",
     "detail": "You do not have permission to view this student"
   }
   ```

---

## Endpoint 2: Get Student Siblings

### Specification

```yaml
Endpoint: GET /api/v1/students/{id}/siblings
Authentication: Required (JWT Bearer Token)
Path Parameters:
  id: integer (required) - Student ID
Response Format: ApiResponse<SiblingInfo[]>
```

### Purpose
Returns list of students who share the same parent. Used in the Overview tab to show family relationships.

### Response Schema

```typescript
interface ApiResponse<T> {
  success: boolean
  data: T
}

interface SiblingInfo {
  student_id: number           // Sibling's student ID
  full_name: string            // Sibling's full name
  age: number                  // Current age
  parent_id: number            // Shared parent ID
  parent_name: string          // Parent's name for reference
  // Optional additional fields:
  status?: 'active' | 'waiting' | 'inactive'
  enrollments_count?: number   // Number of active enrollments
}
```

### Example Response

```json
{
  "success": true,
  "data": [
    {
      "student_id": 16,
      "full_name": "Sara Mohammed",
      "age": 13,
      "parent_id": 42,
      "parent_name": "Mohammed Ali",
      "status": "active",
      "enrollments_count": 2
    },
    {
      "student_id": 17,
      "full_name": "Omar Mohammed",
      "age": 10,
      "parent_id": 42,
      "parent_name": "Mohammed Ali",
      "status": "waiting",
      "enrollments_count": 0
    }
  ]
}
```

### Edge Cases

1. **No Siblings**: Return empty array `[]` (not 404)
2. **No Parent**: Return empty array `[]` if student has no parent_id
3. **Self-Exclusion**: Exclude the requesting student from the list

### Backend Implementation Notes

1. **Query Logic**:
   ```sql
   -- Get parent_id of requested student
   SELECT parent_id FROM students WHERE id = :student_id
   
   -- Get all other students with same parent_id
   SELECT id, full_name, age, parent_id, status
   FROM students
   WHERE parent_id = :parent_id
     AND id != :student_id
     AND status != 'deleted'  -- Soft delete check
   ```

2. **Performance**:
   - Index on `students.parent_id`
   - Simple query, should be very fast

3. **Error Responses**:
   ```json
   // 404 - Student not found (base student doesn't exist)
   {
     "success": false,
     "error": "Student not found",
     "detail": "No student found with ID 15"
   }

   // 200 - Success but no siblings
   {
     "success": true,
     "data": []
   }
   ```

---

## Current Workaround (Frontend)

Until these endpoints are implemented, the frontend will:

1. **For `/crm/students/{id}/details`**: Use basic `GET /crm/students/{id}` and load tab data separately
2. **For `/students/{id}/siblings`**: Hide siblings section or show "Feature coming soon"

---

## Related Existing Endpoints

These endpoints are already working and can be referenced:

- `GET /crm/students/{id}` - Basic student info ✓
- `GET /students/{id}/balance` - Student balance ✓
- `GET /academics/groups` - Groups list ✓
- `POST /enrollments` - Create enrollment ✓

---

## Questions for Backend Team

1. **Field Naming**: Should we use `snake_case` consistently across all endpoints?
2. **Date Format**: Is ISO 8601 (`2023-01-15T10:30:00Z`) acceptable?
3. **Denormalized Fields**: Can we include `parent_name` and `age` as computed fields?
4. **Soft Deletes**: How are deleted students handled? (status='inactive' vs hard delete)
5. **Performance**: Should we add pagination to the siblings endpoint? (unlikely to exceed 10-20 siblings)

---

## Contact

**Requestor**: Frontend Development Team  
**Priority**: HIGH - Student Detail Page currently shows 404 errors  
**Estimated Effort**: 2-4 hours for both endpoints  

Please confirm receipt and estimated completion date.
