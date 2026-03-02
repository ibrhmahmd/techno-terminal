# Phase 2 — Technical Plan: CRM Core & Academics

---

## 1. Scope & Objective

Phase 2 builds the core data entry systems for the people (Guardians & Students) and the curriculum (Courses & Groups).

**Key Deliverables:**

- Ability to register Guardians and Students (with Sibling detection).
- Ability to define Courses (e.g., CSS L1) and schedule Groups (e.g., Fridays 2-4 PM).
- Streamlit pages for data entry, search, and tabular listing.

**Modules Touched:**

- `app/modules/crm/` (Guardians, Students)
- `app/modules/academics/` (Courses, Groups)
- `app/ui/pages/` (Streamlit CRM pages)

---

## 2. File-by-File Breakdown: `crm` Module

### `app/modules/crm/models.py`

**Mission:** SQLModel definitions mapping directly to the `guardians`, `students`, and `student_guardians` tables.

**Properties/Fields:**

- `Guardian`: `id`, `full_name`, `phone_primary`, `phone_secondary`, `email`, `relation`, `notes`, `created_at`, `updated_at`
- `Student`: `id`, `full_name`, `birth_date`, `school_name`, `gender`, `is_active`, `notes`, `created_at`, `updated_at`
- `StudentGuardian`: `student_id` (FK), `guardian_id` (FK), `relationship`, `is_primary_contact`, `created_at`

*(Note: Every model requires `__table_args__ = {"extend_existing": True}` for Streamlit compatibility).*

### `app/modules/crm/repository.py`

**Mission:** Raw, logic-less database access for CRM entities.

**Functions:**

- `create_guardian(session, guardian: Guardian) -> Guardian`
- `get_guardian(session, guardian_id: int) -> Guardian | None`
- `search_guardians(session, query: str) -> list[Guardian]` — *Uses `ILIKE` on name/phone.*
- `create_student(session, student: Student) -> Student`
- `link_guardian(session, student_id: int, guardian_id: int, relation: str, is_primary: bool)`
- `get_student_with_guardians(session, student_id: int)` — *Queries the `v_students` view.*
- `get_siblings(session, student_id: int) -> list[dict]` — *Queries the `v_siblings` view.*

### `app/modules/crm/service.py`

**Mission:** The business logic entry point. Manages workflows, opens its own sessions, and ensures data integrity.

**Functions:**

- `register_guardian(data: dict) -> Guardian`
  - *Logic*: Validates phone number format. Checks for existing phone to avoid duplicate accounts.
- `register_student(student_data: dict, guardian_id: int, relation: str) -> Student`
  - *Logic*: Opens session. Calls `repo.create_student()`. Calls `repo.link_guardian()` ensuring `is_primary=True` for the first linked guardian. Commits transaction automatically via `get_session()`.
- `find_siblings(student_id: int) -> list[dict]`
  - *Logic*: Returns formatted sibling data for the UI using the database view.

---

## 3. File-by-File Breakdown: `academics` Module

### `app/modules/academics/models.py`

**Mission:** SQLModel definitions for `courses` and `groups`.

**Properties/Fields:**

- `Course`: `id`, `name`, `description`, `price_egp`, `sessions_per_level`, `is_active`
- `Group`: `id`, `course_id` (FK), `instructor_id` (FK), `level_number`, `max_capacity`, `default_day`, `default_start_time`, `default_end_time`, `status`

### `app/modules/academics/repository.py`

**Mission:** Raw database operations for curriculum.

**Functions:**

- `create_course(session, course: Course) -> Course`
- `list_active_courses(session) -> list[Course]`
- `create_group(session, group: Group) -> Group`
- `list_groups_by_course(session, course_id: int) -> list[Group]`

### `app/modules/academics/service.py`

**Mission:** Business logic for managing the curriculum.

**Functions:**

- `add_new_course(data: dict) -> Course`
  - *Logic*: Validates `price_egp > 0` and `sessions_per_level > 0`.
- `schedule_group(data: dict) -> Group`
  - *Logic*: Validates time geometry (`start_time < end_time`). Ensures instructor is an active Employee.

---

## 4. File-by-File Breakdown: UI Layer

**UI Note:** Streamlit automatically orders the sidebar navigation alphabetically by filename. We use numbered prefixes to control the order.

### `app/ui/pages/1_👥_Guardian_Management.py`

**Mission:** Screen to add new parents or search existing ones.

- **Components:**
  - Search bar (by phone/name).
  - Data table (`st.dataframe`) listing search results.
  - Sidebar or Expander containing the "Add New Guardian" form (`st.form`).
- **Interactions:** Calls `crm.service.search_guardians()` and `crm.service.register_guardian()`.

### `app/ui/pages/2_🎓_Student_Management.py`

**Mission:** Central hub for student registration.

- **Components:**
  - Multi-step conceptually, but executed in one UI form:
    1. Select existing Guardian (or prompt to create one first).
    2. Enter Student details.
  - "Student Profile" view showing linked guardians and a "Detected Siblings" alert.
- **Interactions:** Calls `crm.service.register_student()`.

### `app/ui/pages/3_📚_Course_Management.py`

**Mission:** Admin screen to define courses and schedule physical groups.

- **Components:**
  - Tabs: `st.tabs(["Courses", "Groups"])`
  - Tab 1: Form to Add Course, Table of active courses.
  - Tab 2: Form to Add Group (requires selecting a Course and Instructor), Table of active groups.
- **Interactions:** Calls `academics.service.add_new_course()` and `academics.service.schedule_group()`.

---

## 5. File Interaction Map & Data Flow

```text
UI: 2_🎓_Student_Management.py
 └──► crm.service.register_student(student_data, guardian_id)
       │
       ├──► db.connection.get_session() [OPENS TRANSACTION]
       │
       ├──► crm.repository.create_student(session, student_data)
       │     └──► DB INSERT INTO students
       │
       ├──► crm.repository.link_guardian(session, student_id, guardian_id)
       │     └──► DB INSERT INTO student_guardians
       │
       └──► [TRANSACTION COMMITS / CLOSES ON SUCCESS]
```

---

## 6. Suggested Code Style Approaches

### 6.1 Service Layer Validation (Pydantic / Plain Dict)

Use plain Python typing for service boundaries, raising `ValueError` for bad data so the UI can catch and display it gracefully using `st.error()`.

```python
# app/modules/academics/service.py
from datetime import time

def schedule_group(course_id: int, instructor_id: int, start: time, end: time) -> Group:
    if start >= end:
        raise ValueError("End time must be strictly after start time.")
    
    with get_session() as session:
        # DB calls here...
```

### 6.2 Streamlit Form Pattern

To prevent excessive UI re-runs, group database writes inside `st.form`.

```python
# app/ui/pages/1_Guardian_Management.py
import streamlit as st
from app.modules.crm import service as crm_srv

with st.form("new_guardian_form", clear_on_submit=True):
    name = st.text_input("Full Name")
    phone = st.text_input("Primary Phone")
    
    if st.form_submit_button("Register Guardian"):
        try:
            new_guardian = crm_srv.register_guardian({"full_name": name, "phone_primary": phone})
            st.success(f"Successfully registered {new_guardian.full_name}!")
        except ValueError as e:
            st.error(str(e))
```

---

## 7. Phase 2 Completion Checklist

- [ ] `app/modules/crm/models.py`
- [ ] `app/modules/crm/repository.py`
- [ ] `app/modules/crm/service.py`
- [ ] `app/modules/academics/models.py`
- [ ] `app/modules/academics/repository.py`
- [ ] `app/modules/academics/service.py`
- [ ] `app/ui/pages/1_👥_Guardian_Management.py`
- [ ] `app/ui/pages/2_🎓_Student_Management.py`
- [ ] `app/ui/pages/3_📚_Course_Management.py`
- [ ] UI gracefully handles Database Integrity Errors (e.g., duplicate phone numbers).
