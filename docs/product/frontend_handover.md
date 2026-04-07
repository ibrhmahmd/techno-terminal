# Techno Terminal CRM — Frontend Handover & Product Specification

**Audience:** Frontend Developers & UI/UX Designers  
**Goal:** Rebuild the UI from scratch in a modern framework (React / Next.js / Vue / Flutter) consuming the FastAPI layer at `/api/v1`.  
**Base URL:** `http://<server>:8000/api/v1`  
**Auth:** Every request must include the header: `Authorization: Bearer <JWT>`

---

## Table of Contents

1. [Global Layout & Auth](#1-global-layout--auth)
2. [Page Priority Order](#2-page-priority-order)
3. [Page 1 — Dashboard (Active Operations)](#3-page-1--dashboard-active-operations)  
4. [Page 2 — Group Management](#4-page-2--group-management)  
5. [Page 3 — Directory (Students & Parents)](#5-page-3--directory-students--parents)  
6. [Page 4 — Enrollments](#6-page-4--enrollments)  
7. [Page 5 — Finance & Receipts](#7-page-5--finance--receipts)  
8. [Page 6 — Reports & Business Intelligence](#8-page-6--reports--business-intelligence)  
9. [Page 7 — Staff / HR (Under Construction)](#9-page-7--staff--hr-under-construction)  
10. [Page 8 — Competitions (Under Construction)](#10-page-8--competitions-under-construction)  
11. [Component: The Attendance Grid (Critical)](#11-component-the-attendance-grid-critical)  
12. [Component: Edit Session Popup](#12-component-edit-session-popup)

---

## 1. Global Layout & Auth

### Sidebar Navigation
A persistent, collapsible sidebar contains links to all pages in priority order. Active page is visually highlighted.

### Login Page (`/login`)
A centered, minimal login form.
- **Fields:** Email, Password
- **Action:** On submit → `POST /api/v1/auth/login` (or Supabase Auth directly)
- **On success:** Store JWT in memory/secure storage. Redirect to Dashboard.

### Global State (must be available app-wide)
| Key | Description |
|-----|-------------|
| `access_token` | JWT for all API calls |
| `current_user.role` | `admin`, `manager`, `instructor`, `receptionist` |
| `current_user.id` | Used to tag `created_by` on write operations |

### Role-Based UI Rules
- `admin` / `manager` → Full access to all pages and actions.
- `instructor` → Access to Dashboard (view/mark attendance for their groups only) and Directory (read-only).
- `receptionist` → Directory (read/create), Enrollments, Finance receipts.

---

## 2. Page Priority Order

| Priority | Page | Reason |
|:--------:|------|--------|
| 1 | **Dashboard** | The daily operations "war room" — admins live here |
| 2 | **Group Management** | Core product — managing classes, sessions, attendance |
| 3 | **Directory** | Every workflow starts with finding a student or parent |
| 4 | **Enrollments** | Transactional — driven from Group or Student pages |
| 5 | **Finance** | Receipts and payments, triggered from Student profile |
| 6 | **Reports** | Weekly/monthly review — lower daily traffic |
| 7 | **Staff / HR** | Under construction — design only |
| 8 | **Competitions** | Under construction — design only |

---

## 3. Page 1 — Dashboard (Active Operations)

> This is the most important page. It is designed for the admin to see ALL of today's active groups and their attendance at a glance, without navigating away.

### Layout

```
┌──────────────────────────────────────────────────────────────┐
│  [Day Selector Dropdown]    (auto-defaults to TODAY)         │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ── Group: "Robotics A | Saturday 3:00 PM" ──────────────── │
│  [Session Notes: "Extra makeup session"]  [Edit Group Info]  │
│  [Full Attendance Grid for this group's session today]       │
│                                                              │
│  ── Group: "Python B | Saturday 5:00 PM" ─────────────────  │
│  [Attendance Grid for this group's session today]            │
│                                                              │
│  ...one section per group scheduled for the selected day...  │
└──────────────────────────────────────────────────────────────┘
```

### Day Selector
- A **dropdown/date-picker or a 7-day pill filter bar** (Mon–Sun) at the top.
- **Defaults to today's day name** on every page load.
- When the user changes the day, all sections below reload to show groups for that new day.

### Group Section Cards
Each group scheduled on the selected day gets its own labeled section/card. Sections are arranged by scheduled start time (earliest first).

**Each section header displays:**
- Group Name + Course Name
- Scheduled Time (e.g., `3:00 PM – 4:30 PM`)
- Instructor Name
- Session Notes (if any session notes exist for this specific date, they are displayed in a collapsed/expandable note box)
- An **"Edit Group Info" button** → opens the [Edit Group Popup](#edit-group-popup)

**Below the header:**
- The full **[Attendance Grid](#11-component-the-attendance-grid-critical)** for that group's current level, filtered to show the session for that day prominently.

### API Mapping — Dashboard

| Action | Method | Endpoint |
|--------|--------|----------|
| Get groups for a day | `GET` | `/api/v1/academics/groups?day={dayName}` |
| Get sessions per group | `GET` | `/api/v1/academics/groups/{id}/sessions` |
| Get roster + attendance | `GET` | `/api/v1/attendance/session/{session_id}` |
| Save attendance | `POST` | `/api/v1/attendance/session/{id}/mark` |

---

## 4. Page 2 — Group Management

The dedicated management page for creating and managing class groups and their session schedules.

### 4.1 Groups List View

**Top Bar:**
- A **day filter bar** — 7 pill buttons (Sat, Sun, Mon, Tue, Wed, Thu, Fri). Auto-selects today.
- A **search bar** for filtering by group name, course, or instructor.
- A **"＋ Create Group" button** → opens Create Group modal.

**Groups Table:**
Columns: `Group Name`, `Course`, `Instructor`, `Level`, `Day`, `Start Time`, `End Time`, `Capacity`

Clicking a row navigates to the **Group Detail View** for that group.

### 4.2 Group Detail View

**Header:**
Shows: Group Name, Course, Instructor, Day & Time, Current Level, Max Capacity.
Has an **"Edit Group" button** → Edit Group modal (see below).
Has an expandable **"Notes"** section if `group.notes` is not empty.

**Level Selector:**
A number input or tab strip allowing the user to switch between viewing Level 1, Level 2, etc. of sessions and roster for the same group.

**Enrollment Roster Table (inside Group Detail):**
Shows all active students enrolled in the selected level.  
Columns: `Student Name`, `Enrollment Date`, `Discount Applied`, `Amount Due`, `Balance (EGP)`, `Attendance (✅/❌)`, `Status`

**The Attendance Grid:**
The full interactive attendance grid for that group and level lives below the roster (full description in [Section 11](#11-component-the-attendance-grid-critical)).

**"Add Extra Session" Action:**
A form (can be an inline drawer or modal) to add a makeup/extra session.  
Fields: `Date` (auto-suggests the next scheduled weekday for this group).  
API: `POST /api/v1/academics/groups/{id}/sessions`

**Level Completion Alert:**
If all sessions in the current level are marked complete (business rule from the backend), the UI shows a prominent success banner:  
`"🎓 Level X Complete! Click to progress students to Level X+1 and generate billing."`  
This button triggers a backend workflow — **API TBD (under construction for billing)**.

### 4.3 Modals

#### Create Group Modal
Fields:
| Field | Type | Required |
|-------|------|----------|
| Course | Dropdown (from `GET /api/v1/academics/courses`) | ✅ |
| Instructor | Dropdown (from `GET /api/v1/hr/employees`) | ✅ |
| Max Capacity | Number input | ✅ |
| Day | Dropdown (Sat–Fri) | ✅ |
| Start Time | Time picker | ✅ |
| End Time | Time picker | ✅ |

API: `POST /api/v1/academics/groups`

#### Edit Group Modal
Same fields as Create Group, pre-filled with current values.  
API: `PATCH /api/v1/academics/groups/{id}`

---

## 5. Page 3 — Directory (Students & Parents)

### Layout
Two tabs: **Families (Parents)** and **Students**. Both share a search-first design.

### 5.1 Parents Tab

**Search & List:**
- Type-ahead search bar (min 2 chars to trigger search).
- Results table:

| Column | Value |
|--------|-------|
| `ID` | Integer |
| `Full Name` | String |
| `Primary Phone` | String |

Clicking a row navigates to the **Parent Detail View**.

**"Register Parent" Button:**
Opens a modal form.  
Fields: `Full Name` (*), `Primary Phone` (*), `Secondary Phone`, `Email`, `Relation` (e.g., Father/Mother/Guardian), `Notes`.  
API: `POST /api/v1/crm/parents`

#### Parent Detail View
**Header:** Name, Primary Phone, Secondary Phone, Email, Relation.  
**"Edit" button** → pre-filled modal → `PATCH /api/v1/crm/parents/{id}`

**Linked Students Table:**  
Lists all students associated with this parent.  
Columns: `Student Name`, `Gender`, `DOB` — each row links to that Student's Detail View.  
API: `GET /api/v1/crm/students/{student_id}/parents` (or parent→students reverse — will be added in API)

---

### 5.2 Students Tab

**Search & List:**
- Type-ahead search bar (min 2 chars).
- "Browse All Students" button for paginated browsing (page size: 15).
- Results table:

| Column | Value |
|--------|-------|
| `ID` | Integer |
| `Full Name` | String |
| `Date of Birth` | Date |
| `Gender` | `Male` / `Female` |
| `Phone` | String or empty |
| `Status` | Active 🟢 / Inactive 🔴 |

Clicking a row navigates to the **Student Detail View**.

**"Register Student" Button:**
Two-step modal:
1. **Step 1 — Link Parent:** Search box for parent (by name/phone). Select from dropdown results.  
   - If no match: Show message "Please register the parent first."
2. **Step 2 — Student Form:**
   | Field | Type |
   |-------|------|
   | Full Name | Text (*) |
   | Date of Birth | Date picker |
   | Gender | Dropdown: Male / Female |
   | Phone | Text (optional) |
   | Notes (Medical / Staff) | Textarea (optional) |

   On success: Show confirmation. If the system detects siblings via the same parent, show a **Sibling Alert Banner**: `"Sibling(s) detected: [Name]. Admin may apply 50 EGP discount per level when enrolling."`

API: `POST /api/v1/crm/students`

#### Student Detail View

**Header:**
- Student Full Name + Active Status indicator (🟢 Active / 🔴 Inactive)
- Stats row: `Date of Birth`, `Gender`, `Phone`
- If `notes` exist: expandable "View Notes" section
- **"Edit Student Info" button** → Edit modal → `PATCH /api/v1/crm/students/{id}`

**Section 1 — Parent Details:**
Shows linked parents, sorted primary first.  
Format per parent: `[Full Name] ([Relationship]) — 🏆 Primary | 📞 [Phone]`  
API: `GET /api/v1/crm/students/{id}/parents`

**Section 2 — Enrollments & Academic History Table:**

| Column | Value |
|--------|-------|
| Group | Group name |
| Level | `L1`, `L2`… |
| Status | `Active`, `Completed`, `Dropped` |
| Amount Due | `XXX EGP` |
| Discount | `-XX EGP` if applied |
| Account Balance | Positive = credit, Negative = debt (shown in red) |
| Attendance | `✅ X   ❌ Y` counts |
| Enrolled On | Date |

If any active enrollment has a negative balance, show a prominent **"💰 Go to Finance — Create Receipt"** action button.  
API: `GET /api/v1/enrollments/student/{id}`, Balance from `GET /api/v1/finance/balance/student/{id}`

**Section 3 — "Enroll in Group" Quick Action:**
A button that navigates to the Enrollments page.

**Section 4 — Competition History Table:**
| Column | Value |
|--------|-------|
| Competition Name | String |
| Edition | String |
| Category | String |
| Team | String |
| Fee Status | ✅ Paid / ❌ Unpaid |

---

## 6. Page 4 — Enrollments

Handles enrolling, transferring, and dropping student–group registrations.

### Layout
Three action panels (tabs or cards) on one page:

**Panel A — Enroll Student**  
Fields:
| Field | How |
|-------|-----|
| Student | Search by name (live) |
| Group | Search/select from active groups |
| Level | Auto-filled from group's current level |
| Amount Due | Auto-calculated, editable |
| Discount Applied | Number input (EGP) — flag if sibling |
| Notes | Textarea |

API: `POST /api/v1/enrollments`  
On success: Show confirmation + "💰 Collect Payment Now" shortcut.

**Panel B — Transfer Student**  
Select an existing active enrollment, then select a new group.  
API: `POST /api/v1/enrollments/transfer`

**Panel C — Drop Enrollment**  
Select enrollment to drop (with confirmation dialog).  
API: `DELETE /api/v1/enrollments/{id}`

---

## 7. Page 5 — Finance & Receipts

### 7.1 Create Receipt
Triggered primarily from the Student Detail View debt alert, but also accessible directly.  
Fields:
| Field | Value |
|-------|-------|
| Payer Name | Text (optional, auto-fill from student) |
| Payment Method | Dropdown: `cash`, `card`, `wallet` |
| Notes | Textarea |
| Allow Credit | Toggle (allow overpayment as credit) |
| Line Items | Dynamic list — add/remove rows |

Each line item: `Student` (search), `Enrollment` (dropdown), `Amount (EGP)`, `Type` (tuition/registration/competition fee), `Discount (EGP)`.  
API: `POST /api/v1/finance/receipts`

### 7.2 Search Receipts
Date range filter + optional filters: Payer Name, Student ID, Receipt Number.  
Results table: `Receipt #`, `Payer`, `Method`, `Date`, `Amount`.  
Clicking a receipt opens its detail view.  
API: `GET /api/v1/finance/receipts?from_date=&to_date=`

### 7.3 Receipt Detail View
Shows full receipt header + line items table.  
API: `GET /api/v1/finance/receipts/{id}`

### 7.4 Issue Refund
Fields: `Payment ID`, `Amount`, `Reason`, `Method`.  
API: `POST /api/v1/finance/refunds`

---

## 8. Page 6 — Reports & Business Intelligence

A read-only analytics dashboard for weekly/monthly review. Lower daily priority.

| Report Section | API Endpoint |
|----------------|-------------|
| Revenue by date range | `GET /api/v1/analytics/dashboard/summary` |
| Daily collections | *(Coming soon)* |
| Outstanding balances | *(Coming soon)* |
| Top debtors | *(Coming soon)* |
| Attendance heatmap | *(Coming soon)* |
| New enrollment trends | *(Coming soon)* |
| Instructor performance | *(Coming soon)* |

> Most analytics endpoints are fully implemented server-side but not yet exposed via API — this is a documented backlog item.

---

## 9. Page 7 — Staff / HR *(Under Construction — Design Target)*

Design these screens now; backend will wire up APIs in the next sprint.

### 9.1 Staff Directory
Card grid or table of all employees.  
Columns/fields: `Name`, `Role` (Instructor/Receptionist/Manager), `Employment Type` (Full-time/Part-time/Freelance), `Phone`, `Status (Active/Inactive)`.  
Action: Click → Staff Detail Profile.

### 9.2 Staff Detail Profile
- Contact info, employment type, assigned subjects.
- **Mini Performance Panel:** Total active groups taught, student count, average attendance rate.

### 9.3 Staff Attendance Log
A daily log UI for the receptionist to record when an instructor physically arrives at and leaves the center.  
Fields: `Employee`, `Date`, `Status` (Present/Absent/Late), `Notes`.

### 9.4 Manage Staff Accounts
Table showing linked system users, their login role, and active status.  
Admin can toggle active/inactive or change role.

---

## 10. Page 8 — Competitions *(Under Construction — Design Target)*

### 10.1 Competition Hub
A list/card view of all competitions: `Name`, `Edition`, `Date Range`, `Status` (Upcoming/Active/Closed).  
Clicking a competition opens its detail page.

### 10.2 Competition Detail
- Overview: Name, edition, date, categories.
- **Teams table:** `Team Name`, `Members`, `Category`, `Fee Status` (✅ Paid / ❌ Unpaid).

### 10.3 Team Builder
A modal or dedicated slide-out panel.  
Fields:
- `Competition` (select)
- `Category` (select from competition's configured categories)
- `Team Name` (text)
- `Members` (multi-select from enrolled students, 2–5 members)
- `Fee Paid` (toggle)

### 10.4 Leaderboard / Bracket
Visual bracket or ranking table. Data structure TBD.

---

## 11. Component: The Attendance Grid (Critical)

This is the most interactive component in the entire application. It appears on both the **Dashboard** (in a read-specific form) and the **Group Detail View** (in edit mode). It must be responsive and keyboard-friendly.

### Visual Structure

```
┌──────────────────┬─────────────────┬─────────────────┬─────────────────┐
│  Student Name    │   Session #1    │   Session #2    │   Session #3    │
│                  │  Ali Mahmoud    │  Ali Mahmoud    │  (Unassigned)   │
│                  │  Dec 7, 2024    │  Dec 14, 2024   │  Dec 21, 2024   │
│                  │  [✏️][🚫][🗑️]   │  [✏️][🚫][🗑️]   │  [✏️][🚫][🗑️]   │
├──────────────────┼─────────────────┼─────────────────┼─────────────────┤
│ 🟢 Ahmed Salem   │       ✅        │       ❌        │       ◻️        │
│ 🔴 Sara Khaled   │       ❌        │       ◻️        │       ◻️        │
│ 🟢 Omar Hassan   │       ✅        │       ✅        │       ◻️        │
└──────────────────┴─────────────────┴─────────────────┴─────────────────┘
                                                             [💾 Save All]
```

### Column Headers (Sessions)
Each column header cell displays:
- **Session Number** (bold): e.g., `Session 3`
- **Instructor Name** (sub-text): who actually taught that session (may differ from the group's default instructor for one-offs)
- **Date** (sub-text): `Dec 7, 2024`
- **3 action icon buttons** below the date:
  - `✏️ Edit` — opens the [Edit Session Popup](#12-component-edit-session-popup)
  - `🚫 Cancel` — triggers a **2-step confirmation** (first click shows "Are you sure?" state, second click confirms). Cancelled sessions are displayed with strikethrough styling on the header text. Attendance cells in that column are **disabled** (greyed out, not clickable).
  - `🗑️ Delete` — same 2-step confirmation pattern. Disabled if attendance records already exist for the session (the backend will reject it; the UI should show a helpful error: "Clear attendance first before deleting this session.")

### Row Headers (Students)
The left column shows the student's name with a **financial status badge**:
- `🟢 [PAID]` — enrollment balance is ≥ 0 (no debt)
- `🔴 [UNPAID]` — enrollment balance is < 0 (has debt)

Clicking the student's name navigates directly to that **Student Detail View** page.

API for balance: `GET /api/v1/finance/balance/student/{id}` (get the `balance` field per enrollment).

### Grid Cells (Interactive Toggles)
Each cell is a clickable button that cycles through states on click:

| State | Display | What it means |
|-------|---------|---------------|
| `null` / Unmarked | `◻️` | Not yet recorded |
| `present` | `✅` | Student was present |
| `absent` | `❌` | Student was absent |

> **Late** (`🕒`) and **Excused** (`➖`) states exist in the database. They are set via the Edit Session popup or a context menu on the cell, not the quick-click cycle. If a cell currently holds a `late` or `excused` value, clicking it resets it to `null`.

**Cells in a cancelled session column are fully disabled (greyed out).**

### Local State Management (Critical for Performance)
The grid must maintain a **local in-memory state dictionary** of all changes.  
**Do NOT fire an API call on every single cell toggle.** This would cause excessive requests.

Instead:
1. On page load, fetch the current attendance state from the API and populate the local state.
2. All cell clicks only update local state (instant, no network call).
3. A **"💾 Save All Attendance Changes"** primary button at the bottom of the grid collects all unsaved changes and fires API calls — one call per session column that has changes.

### API Mapping — Attendance Grid

| Action | Method | Endpoint | Notes |
|--------|--------|----------|-------|
| Load initial cell states | `GET` | `/api/v1/attendance/session/{session_id}` | Returns list of `{student_id, status}`. Call for each session column. |
| Load roster (row list) | `GET` | `/api/v1/enrollments/student/{student_id}` | Or group roster endpoint |
| **Save all changes** | `POST` | `/api/v1/attendance/session/{session_id}/mark` | Body: `{"student_statuses": {"101": "present", "102": "absent"}}` |
| Cancel a session | `PATCH` | `/api/v1/academics/sessions/{session_id}` | Body: `{"status": "cancelled"}` |
| Delete a session | *TBD — API endpoint to be added* | | |

---

## 12. Component: Edit Session Popup

Triggered by the `✏️` button in the attendance grid column header. Opens as a **modal dialog** (not a full page navigation).

### Fields

| Field | Type | Notes |
|-------|------|-------|
| Session Date | Date picker | Current date pre-filled |
| Actual Instructor | Dropdown | Pre-filled from group default. Select from `GET /api/v1/hr/employees`. Allows assigning a substitute. |
| Status | Dropdown | `scheduled`, `completed`, `cancelled` |
| Session Notes | Textarea | Notes for this specific session (e.g., "Makeup session", "Covered extra topic") |

### Buttons
- **"Save Changes"** → `PATCH /api/v1/academics/sessions/{session_id}`
- **"Cancel"** → Closes the popup with no changes

### API Call Body
```json
{
  "session_date": "2024-12-14",
  "actual_instructor_id": 3,
  "status": "completed",
  "notes": "Covered robotics chapter 4"
}
```

---

> **Design Philosophy Note:**  
> Keep the UI clean, fast, and focused. The admin uses this app in the middle of a busy class day. Priority features (Dashboard → Groups → Directory) should be instantly accessible and require minimum clicks. Use modals for quick edits, slide-out drawers for forms, and avoid full page navigations for common actions.
