# Backend API Request: Grouped Students Endpoint

**Feature:** Student Grouping in Directory Page  
**Priority:** Medium  
**Depends on:** Existing `/crm/students` endpoint  
**Status:** 🟡 Requested — Pending Backend Implementation

---

## Overview

The frontend needs a new endpoint to retrieve students pre-grouped by a specified field. This mirrors the existing `/academics/groups/grouped?group_by=` pattern used on the Groups page.

The grouped student data will power a **directory grouping UI** that displays students organized under collapsible dark-themed tab bars. Each group-by mode is a separate tab option the user can select.

---

## Endpoint Specification

### Request

```
GET /crm/students/grouped
```

#### Query Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `group_by` | `string` | ✅ Yes | One of: `day`, `competition`, `course`, `age`, `group` |

#### Full Example Requests

```
GET /crm/students/grouped?group_by=day
GET /crm/students/grouped?group_by=competition
GET /crm/students/grouped?group_by=course
GET /crm/students/grouped?group_by=age
GET /crm/students/grouped?group_by=group
```

---

### Response Shape

The response must be consistent across all `group_by` values:

```json
{
  "group_by": "day",
  "total_unique_students": 87,
  "groups": [
    {
      "key": "monday",
      "label": "Monday",
      "count": 23,
      "students": [ ...Student objects... ]
    },
    {
      "key": "unassigned",
      "label": "Unassigned",
      "count": 4,
      "students": [ ...Student objects... ]
    }
  ]
}
```

#### Response Fields

| Field | Type | Description |
|---|---|---|
| `group_by` | `string` | Echoes the `group_by` query param |
| `total_unique_students` | `int` | Count of **unique** students across all groups (may be less than sum of group counts for multi-appear modes) |
| `groups` | `GroupedStudents[]` | Array of group objects, see below |

#### `GroupedStudents` Object

| Field | Type | Description |
|---|---|---|
| `key` | `string` | Stable identifier for the group (slug/id, e.g. `"monday"`, `"unassigned"`) |
| `label` | `string` | Human-readable display name (e.g. `"Monday"`, `"Unassigned"`) |
| `count` | `int` | Number of students in this group |
| `students` | `Student[]` | Full student objects (same shape as `/crm/students` list items) |

#### Student Object (per group)

Each student in `students[]` should include at minimum:

```json
{
  "id": 1,
  "full_name": "Ahmed Mostafa",
  "phone": "01012345678",
  "date_of_birth": "2013-04-12",
  "gender": "male",
  "is_active": true,
  "status": "active",
  "current_group_id": 3,
  "current_group_name": "Monday Beginners",
  "notes": null
}
```

---

## Grouping Modes: Rules Per `group_by` Value

---

### `group_by=day`

Group students by the **day of the week of their current active group(s)**.

#### Rules

- Use the `default_day` field from the student's **active enrollments** (not archived).
- A student enrolled in **multiple active groups on different days** must appear in **each relevant day tab simultaneously**. Example: a student in "Monday Beginners" AND "Wednesday Advanced" appears in both `monday` and `wednesday`.
- A student with **no active group** must appear under `key: "unassigned"`, `label: "Unassigned"`.
- **Exclude archived groups entirely** — do not consider them for grouping or counting.
- Order groups by day of the week: Saturday → Sunday → Monday → Tuesday → Wednesday → Thursday → Friday, then Unassigned last.

#### Expected `key` Values

```
saturday | sunday | monday | tuesday | wednesday | thursday | friday | unassigned
```

#### Example Response

```json
{
  "group_by": "day",
  "total_unique_students": 87,
  "groups": [
    { "key": "monday",    "label": "Monday",     "count": 23, "students": [...] },
    { "key": "wednesday", "label": "Wednesday",   "count": 18, "students": [...] },
    { "key": "thursday",  "label": "Thursday",    "count": 31, "students": [...] },
    { "key": "unassigned","label": "Unassigned",  "count": 4,  "students": [...] }
  ]
}
```

> **Note:** Sum of counts (76) may exceed `total_unique_students` (87 minus multi-group students) due to multi-day appearances.

---

### `group_by=competition`

Group students by **each competition they are currently enrolled in** (active participation only).

#### Rules

- A student enrolled in **multiple competitions** must appear in **each competition tab** simultaneously.
- A student with **no active competition enrollment** must appear under `key: "unassigned"`, `label: "Unassigned"`.
- Only include **active/current competitions** — do not include past/completed competition enrollments.
- The `key` should be the competition's `id` cast to string (e.g. `"12"`).
- The `label` should be the competition's name (e.g. `"Winter Cup 2025"`).
- Order: alphabetically by competition name, Unassigned last.

#### Example Response

```json
{
  "group_by": "competition",
  "total_unique_students": 87,
  "groups": [
    { "key": "12", "label": "Regional Championship", "count": 15, "students": [...] },
    { "key": "7",  "label": "Winter Cup 2025",        "count": 22, "students": [...] },
    { "key": "unassigned", "label": "Unassigned",     "count": 54, "students": [...] }
  ]
}
```

---

### `group_by=course`

Group students by their **current active course**.

#### Rules

- Use only the student's **current active course enrollment** (`status = 'in_progress'`). Do not include completed or dropped courses.
- Each student should appear in **at most one course tab** (their current active course).
- A student with **no active course** must appear under `key: "unassigned"`, `label: "Unassigned"`.
- The `key` should be the course's `id` cast to string.
- The `label` should be the course's name (e.g. `"Robotics Level 2"`).
- Order: alphabetically by course name, Unassigned last.

#### Example Response

```json
{
  "group_by": "course",
  "total_unique_students": 87,
  "groups": [
    { "key": "3",  "label": "Robotics Level 1", "count": 28, "students": [...] },
    { "key": "5",  "label": "Robotics Level 2", "count": 19, "students": [...] },
    { "key": "unassigned", "label": "Unassigned", "count": 12, "students": [...] }
  ]
}
```

---

### `group_by=age`

Group students by **age bracket**, calculated from `date_of_birth` as of today's date.

#### Age Brackets (Fixed, Non-configurable)

| Key | Label | Range |
|---|---|---|
| `age_4_7` | `4 – 7 years` | 4 ≤ age < 7 |
| `age_7_9` | `7 – 9 years` | 7 ≤ age < 9 |
| `age_9_12` | `9 – 12 years` | 9 ≤ age < 12 |
| `age_12_15` | `12 – 15 years` | 12 ≤ age < 15 |
| `age_15_plus` | `15+ years` | age ≥ 15 |
| `unknown` | `Unknown Age` | `date_of_birth` is null |

> **Boundary Rule:** Lower bound is **inclusive**, upper bound is **exclusive**. A student who is exactly 7 years old falls into `age_7_9`. A student who is exactly 12 falls into `age_12_15`.

#### Rules

- Each student appears in **exactly one** bracket (or `unknown`).
- Students with no `date_of_birth` go into `key: "unknown"`, `label: "Unknown Age"`.
- **Do not include empty brackets** in the response — omit a bracket entirely if it has 0 students.
- Order: youngest to oldest, `unknown` last.

#### Example Response

```json
{
  "group_by": "age",
  "total_unique_students": 87,
  "groups": [
    { "key": "age_4_7",    "label": "4 – 7 years",  "count": 12, "students": [...] },
    { "key": "age_7_9",    "label": "7 – 9 years",  "count": 24, "students": [...] },
    { "key": "age_9_12",   "label": "9 – 12 years", "count": 31, "students": [...] },
    { "key": "age_12_15",  "label": "12 – 15 years","count": 14, "students": [...] },
    { "key": "age_15_plus","label": "15+ years",    "count": 4,  "students": [...] },
    { "key": "unknown",    "label": "Unknown Age",  "count": 2,  "students": [...] }
  ]
}
```

---

### `group_by=group`

Group students by their **current active group name**.

#### Rules

- Use only the student's `current_group_id` / `current_group_name` (active enrollment only).
- **Exclude archived groups** — if a student's current group is archived, treat them as Unassigned.
- A student with **no current active group** must appear under `key: "unassigned"`, `label: "Unassigned"`.
- The `key` should be the group's `id` cast to string.
- The `label` should be the group's name (e.g. `"Monday Beginners"`).
- Order: alphabetically by group name, Unassigned last.

#### Example Response

```json
{
  "group_by": "group",
  "total_unique_students": 87,
  "groups": [
    { "key": "3",  "label": "Monday Beginners",   "count": 12, "students": [...] },
    { "key": "7",  "label": "Thursday Advanced",  "count": 9,  "students": [...] },
    { "key": "unassigned", "label": "Unassigned", "count": 4,  "students": [...] }
  ]
}
```

---

## Global Constraints (Apply to All Modes)

| Rule | Detail |
|---|---|
| No archived data | Never include students based on archived group, course, or competition records |
| Unassigned always last | The `unassigned` / `unknown` tab must always be the last entry in `groups[]` |
| Empty groups omitted | Do not return a group object if its `count` is 0 |
| No pagination inside groups | Return all students per group (the frontend handles the tab switch) |
| Active students only | By default, only include `is_active = true` students. Include inactive if `include_inactive=true` query param is passed. |

---

## Error Responses

```json
// Invalid group_by value
HTTP 422 Unprocessable Entity
{
  "detail": "Invalid group_by value. Must be one of: day, competition, course, age, group"
}
```

---

## Deferred Features (Future Scope — Not Part of This Request)

| Feature | Reason Deferred |
|---|---|
| `group_by=balance` | Balance grouping requires financial categorization rules still being defined |
| `group_by=school` | School name field not yet in student database schema |
| Pagination inside groups | Not needed at current student volumes |

---

## Frontend Integration Notes

The frontend will consume this endpoint via a new hook `useStudentGrouping.ts`, following the exact same pattern as `useGroups.ts`. The response will be mapped to `GroupItem<Student>[]` and passed to the existing `<DataTable groupedData={...}>` component that already supports the grouped view.

```typescript
// Frontend mapping:
groups.map(g => ({
  key: g.key,
  label: g.label,
  count: g.count,
  items: g.students     // ← mapped from 'students' to 'items' for GroupItem<T>
}))
```

The endpoint URL and query shape is designed to exactly mirror `/academics/groups/grouped?group_by=` for consistency.
