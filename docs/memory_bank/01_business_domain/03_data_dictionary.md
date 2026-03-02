# Schema Mapping & Classification Rules

## The Unifying Schema

The python scripts map data to a universal relational structure containing the lowest common denominator fields across all business domains:

```json
{
  "record_id":      "UUID",
  "source_file":    "Relative Path String",
  "person_name":    "String",
  "phone":          "String",
  "course_name":    "String",
  "course_level":   "String",
  "session_day":    "String",
  "session_time":   "String",
  "instructor_name":"String",
  "team_name":      "String",
  "score":          "String/Numeric",
  "payment_status": "String",
  "attendance_date":"Date String",
  "attendance_status": 1, 0, or None (Integer),
  "extra_fields":   "JSON String of unmapped columns"
}
```

## Dictionary Mapping (The `FIELD_MAP`)

Because instructors named columns inconsistently, the system normalizes headers (lowercase, remove spaces/dots to underscores, strip Arabic diacritics) and checks against a synonym map:

- **person_name**: "name", "student_name", "pupils", "child_name", "اسم_الطالب", "employee", "client"
- **phone**: "phone", "mobile", "tel", "رقم_الهاتف", "number"
- **course_name**: "course", "subject", "program", "class"
- **payment_status**: "payment", "paid", "fee_paid", "fees", "month_paid"

*Note: Any column that cannot be mapped is stored in `extra_fields` JSON, ensuring 0% data loss.*

## Domain Classification Rules

Files are grouped into one of 4 domains (or Unclassified) by finding specific "strong" columns in their header:

1. **CourseAttendance**: `course_name`, `level`, `session_day` OR having >3 date-like columns.
2. **CompetitionTracking**: `team_name`, `category`, `fll`, `robofest`
3. **StaffAttendance**: `employee`, `salary`, `role`
4. **CRM_SAT**: `sat`, `enrollment`, `sat_group`

If a file has a completely unrecognizable header structure, it is pushed to `05_Unclassified`.
