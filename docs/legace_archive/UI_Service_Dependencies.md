# Techno Terminal UI - Service Dependencies Documentation

## Overview
This document maps each UI page and component to the backend services and endpoints it consumes.

---

## Pages

### 1. `pages/login.py`
**Purpose**: User authentication and login

**Dependencies**:
| Service | Function | Description |
|---------|----------|-------------|
| `app.core.supabase_clients` | `get_supabase_anon()` | Supabase anonymous client for auth |
| `app.modules.auth` | `get_user_by_supabase_uid()` | Fetch local user by Supabase UID |
| `app.modules.auth` | `update_last_login()` | Update user's last login timestamp |
| `app.ui.state` | `is_authenticated()`, `set_user()` | Session state management |

---

### 2. `pages/0_Dashboard.py`
**Purpose**: Daily operations hub with schedule, finance, and quick registration

**Dependencies**:
| Service | Function | Description |
|---------|----------|-------------|
| `app.modules.analytics` | `get_today_sessions(today)` | Get today's scheduled sessions |
| `app.modules.analytics` | `get_active_enrollment_count()` | Count of active enrollments |
| `app.modules.analytics` | `get_revenue_by_date(start, end)` | Daily collection metrics |
| `app.modules.analytics` | `get_today_unpaid_attendees(today)` | Outstanding balances for today |

**Child Components**:
- `finance_overview.render_finance_overview()`
- `finance_receipt.render_receipt_detail()`
- `dashboard_receipts.render_receipt_browser()`
- `quick_register.render_quick_register()`

---

### 3. `pages/1_Directory.py`
**Purpose**: People directory for parents and students

**Dependencies**: None directly (delegates to child components)

**Child Components**:
- `parent_overview.render_parent_overview()`
- `parent_detail.render_parent_detail()`
- `student_overview.render_student_overview()`
- `student_detail.render_student_detail()`

---

### 4. `pages/3_Course_Management.py`
**Purpose**: Course management interface

**Dependencies**: None directly (delegates to child components)

**Child Components**:
- `course_overview.render_course_overview()`
- `course_detail.render_course_detail()`

---

### 5. `pages/4_Group_Management.py`
**Purpose**: Group management and attendance marking

**Dependencies**: None directly (delegates to child components)

**Child Components**:
- `group_overview.render_group_overview()`
- `group_detail.render_group_detail()`

---

### 6. `pages/5_Enrollment.py`
**Purpose**: Student enrollment wizard and management

**Dependencies**:
| Service | Function | Description |
|---------|----------|-------------|
| `app.modules.crm` | `crm_service.search_students(q)` | Search students by name |
| `app.modules.academics` | `get_all_active_groups()` | List active groups |
| `app.modules.enrollments` | `enrollment_service.get_group_roster(group_id)` | Get group enrollment roster |
| `app.modules.enrollments` | `enrollment_service.get_student_enrollments(student_id)` | Get student's enrollments |
| `app.modules.enrollments` | `enrollment_service.enroll_student(EnrollStudentInput)` | Enroll student in group |
| `app.modules.enrollments` | `enrollment_service.apply_sibling_discount(enr_id)` | Apply discount |
| `app.modules.enrollments` | `enrollment_service.complete_enrollment(enr_id)` | Mark as complete |
| `app.modules.enrollments` | `enrollment_service.drop_enrollment(enr_id)` | Drop enrollment |
| `app.modules.enrollments` | `enrollment_service.transfer_student(TransferStudentInput)` | Transfer between groups |
| `app.modules.academics` | `get_active_courses()` | Get courses for pricing |

**Schemas Used**:
- `EnrollStudentInput`
- `TransferStudentInput`

---

### 7. `pages/6_Staff_Management.py`
**Purpose**: HR and employee management

**Dependencies**:
| Service | Function | Description |
|---------|----------|-------------|
| `app.ui.state` | `get_role()` | Check admin permissions |

**Child Components**:
- `employee.employee_directory.render_employee_directory()`
- `employee.employee_detail.render_employee_detail()`
- `employee.employee_form.render_add_employee_form()`

---

### 8. `pages/8_Competitions.py`
**Purpose**: Competition management

**Dependencies**: None directly (delegates to child components)

**Child Components**:
- `competition_detail.render_competition_detail()`
- `competition_overview.render_competition_overview()`

---

### 9. `pages/9_Reports.py`
**Purpose**: Analytics, reports, and business intelligence

**Dependencies**:
| Service | Function | Description |
|---------|----------|-------------|
| `app.modules.analytics` | `get_revenue_by_method(start, end)` | Revenue by payment method |
| `app.modules.analytics` | `get_revenue_by_date(start, end)` | Daily revenue trend |
| `app.modules.analytics` | `get_outstanding_by_group()` | Outstanding balances by group |
| `app.modules.analytics` | `get_top_debtors(limit)` | Top debtors list |
| `app.modules.analytics` | `get_group_roster(group_id, level)` | Group roster with attendance % |
| `app.modules.analytics` | `get_competition_fee_summary()` | Competition fees summary |
| `app.modules.analytics` | `get_attendance_heatmap(group_id, level)` | Attendance heatmap data |
| `app.modules.academics` | `get_all_active_groups(include_inactive)` | List groups for reports |

**Child Components** (BI Charts):
- `charts.retention_funnel.render_retention_funnel()`
- `charts.instructor_matrix.render_instructor_matrix()`
- `charts.schedule_utilization.render_schedule_utilization()`
- `charts.financial_risk.render_financial_risk()`

---

## Components

### 10. `components/attendance_grid.py`
**Purpose**: Interactive attendance marking grid

**Dependencies**:
| Service | Function | Description |
|---------|----------|-------------|
| `app.modules.attendance` | `get_session_roster_with_attendance(sess_id)` | Get attendance records |
| `app.modules.attendance` | `mark_session_attendance(sess_id, payload, None)` | Save attendance |
| `app.modules.crm` | `Student` | Student model for name lookup |
| `app.modules.hr` | `hr_service.get_active_instructors()` | Instructor lookup |
| `app.modules.academics` | `update_session(sess_id, UpdateSessionDTO)` | Update session notes |
| `app.modules.academics` | `cancel_session(sess_id)` | Cancel session |
| `app.modules.academics` | `delete_session(sess_id)` | Delete session |

**Schemas Used**:
- `UpdateSessionDTO`

---

### 11. `components/course_overview.py`
**Purpose**: Course listing and creation

**Dependencies**:
| Service | Function | Description |
|---------|----------|-------------|
| `app.modules.academics` | `get_active_courses()` | List active courses |
| `app.modules.academics` | `get_all_course_stats()` | Get course statistics |
| `app.modules.academics` | `add_new_course(AddNewCourseInput)` | Create new course |

**Schemas Used**:
- `AddNewCourseInput`

---

### 12. `components/course_detail.py`
**Purpose**: Course details and group listing

**Dependencies**:
| Service | Function | Description |
|---------|----------|-------------|
| `app.modules.academics` | `get_course_by_id(course_id)` | Get course details |
| `app.modules.academics` | `get_groups_by_course(course_id)` | Get course groups |
| `app.modules.academics` | `update_course_price(course_id, new_price)` | Update pricing |
| `app.modules.academics` | `get_course_stats(course_id)` | Course statistics |
| `app.modules.hr` | `hr_service.get_active_instructors()` | Instructor list |
| `app.modules.academics` | `get_active_courses()` | Course list |
| `app.modules.academics` | `update_course(course_id, UpdateCourseDTO)` | Update course |

**Schemas Used**:
- `UpdateCourseDTO`

---

### 13. `components/group_overview.py`
**Purpose**: Group listing by day and creation

**Dependencies**:
| Service | Function | Description |
|---------|----------|-------------|
| `app.modules.academics` | `get_active_courses()` | Courses for group creation |
| `app.modules.hr` | `hr_service.get_active_instructors()` | Instructors for group creation |
| `app.modules.academics` | `schedule_group(ScheduleGroupInput)` | Create new group |
| `app.modules.academics` | `get_all_active_groups_enriched()` | List all groups |

**Schemas Used**:
- `ScheduleGroupInput`

**Exceptions Handled**:
- `ValidationError`, `NotFoundError`, `ConflictError`

---

### 14. `components/group_detail.py`
**Purpose**: Group management, attendance, sessions

**Dependencies**:
| Service | Function | Description |
|---------|----------|-------------|
| `app.modules.academics` | `get_group_by_id(group_id)` | Get group details |
| `app.modules.academics` | `list_group_sessions(group_id, level)` | List sessions |
| `app.modules.enrollments` | `enrollment_service.get_group_roster(group_id, level)` | Get roster |
| `app.modules.academics` | `add_extra_session(AddExtraSessionInput)` | Add extra session |
| `app.modules.academics` | `check_level_complete(group_id, level)` | Check completion |
| `app.modules.academics` | `progress_group_level(group_id)` | Advance level |
| `app.modules.academics` | `delete_group(group_id)` | Soft delete group |
| `app.modules.academics` | `update_session(sess_id, UpdateSessionDTO)` | Update session notes |
| `app.modules.hr` | `hr_service.get_active_instructors()` | Instructors for edit |
| `app.modules.academics` | `get_active_courses()` | Courses for edit |

**Child Components**:
- `attendance_grid.render_attendance_grid()`
- `forms.edit_group_form.render_edit_group_form()`

**Schemas Used**:
- `UpdateSessionDTO`
- `AddExtraSessionInput`

---

### 15. `components/student_overview.py`
**Purpose**: Student search and registration

**Dependencies**:
| Service | Function | Description |
|---------|----------|-------------|
| `app.modules.crm` | `crm_service.search_students(q)` | Search students |
| `app.modules.crm` | `crm_service.list_all_students(limit)` | List all students |
| `app.modules.crm` | `crm_service.search_parents(q)` | Search parents |
| `app.modules.crm` | `register_student(RegisterStudentCommandDTO)` | Register student |
| `app.modules.crm` | `RegisterStudentDTO` | Student data schema |
| `app.modules.crm` | `RegisterStudentCommandDTO` | Command schema |

**Exceptions Handled**:
- `NotFoundError`, `ValidationError`, `BusinessRuleError`

---

### 16. `components/student_detail.py`
**Purpose**: Student profile and enrollment details

**Dependencies**:
| Service | Function | Description |
|---------|----------|-------------|
| `app.modules.crm` | `crm_service.get_student_by_id(student_id)` | Get student details |
| `app.modules.crm` | `crm_service.get_student_parents(student_id)` | Get linked parents |
| `app.modules.enrollments` | `enrollment_service.get_student_enrollments(student_id)` | Get enrollments |
| `app.modules.crm` | `crm_service.find_siblings(student_id)` | Find siblings |
| `app.modules.crm` | `update_student(student_id, UpdateStudentDTO)` | Update student |

**Schemas Used**:
- `UpdateStudentDTO`

---

### 17. `components/parent_overview.py`
**Purpose**: Parent search and registration

**Dependencies**:
| Service | Function | Description |
|---------|----------|-------------|
| `app.modules.crm` | `crm_service.search_parents(q)` | Search parents |
| `app.modules.crm` | `crm_service.list_all_parents(limit)` | List all parents |
| `app.modules.crm` | `crm_service.register_parent(RegisterParentInput)` | Register parent |

**Schemas Used**:
- `RegisterParentInput`

**Exceptions Handled**:
- `ConflictError`, `ValidationError`, `NotFoundError`

---

### 18. `components/parent_detail.py`
**Purpose**: Parent profile and linked students

**Dependencies**:
| Service | Function | Description |
|---------|----------|-------------|
| `app.modules.crm` | `crm_service.get_parent_by_id(parent_id)` | Get parent details |
| `app.modules.crm` | `crm_service.get_parent_students(parent_id)` | Get linked students |
| `app.modules.crm` | `update_parent(parent_id, UpdateParentDTO)` | Update parent |

**Schemas Used**:
- `UpdateParentDTO`

---

### 19. `components/finance_overview.py`
**Purpose**: Payment processing and receipt creation

**Dependencies**:
| Service | Function | Description |
|---------|----------|-------------|
| `app.modules.crm` | `crm_service.search_students(q)` | Search students |
| `app.modules.enrollments` | `enrollment_service.get_student_enrollments(student_id)` | Get enrollments |
| `app.modules.finance` | `finance_service.get_enrollment_balance(enr_id)` | Get balance |
| `app.modules.finance` | `finance_service.get_unpaid_competition_fees(student_id)` | Competition fees |
| `app.modules.finance` | `finance_service.preview_overpayment_risk(lines)` | Check overpayment |
| `app.modules.finance` | `finance_service.create_receipt_with_charge_lines(...)` | Create receipt |
| `app.shared.constants` | `PAYMENT_METHODS` | Payment method options |

**Schemas Used**:
- `ReceiptLineInput`

---

### 20. `components/quick_register.py`
**Purpose**: Combined parent+student quick registration

**Dependencies**:
| Service | Function | Description |
|---------|----------|-------------|
| `app.modules.crm` | `crm_service.find_or_create_parent(RegisterParentInput)` | Find/create parent |
| `app.modules.crm` | `crm_service.register_student(RegisterStudentCommandDTO)` | Register student |
| `app.modules.crm` | `RegisterParentInput` | Parent data schema |
| `app.modules.crm` | `RegisterStudentDTO` | Student data schema |
| `app.modules.crm` | `RegisterStudentCommandDTO` | Command schema |
| `app.ui.state` | `get_current_user_id()` | Current user ID |

**Exceptions Handled**:
- `ValidationError`, `ConflictError`

---

### 21. `components/competition_overview.py`
**Purpose**: Competition listing and management

**Dependencies**:
| Service | Function | Description |
|---------|----------|-------------|
| `app.modules.competitions` | `competition_service.list_competitions()` | List competitions |
| `app.modules.competitions` | `competition_service.create_competition(...)` | Create competition |
| `app.modules.competitions` | `competition_service.update_competition(...)` | Update competition |
| `app.modules.competitions` | `competition_service.delete_competition(id)` | Delete competition |
| `app.modules.competitions` | `competition_service.add_team(...)` | Add team |
| `app.modules.competitions` | `competition_service.add_team_member(...)` | Add member |
| `app.modules.competitions` | `competition_service.remove_team_member(...)` | Remove member |
| `app.modules.competitions` | `competition_service.get_teams(comp_id)` | Get teams |
| `app.modules.competitions` | `competition_service.get_team_members(team_id)` | Get members |
| `app.modules.crm` | `crm_service.search_students(q)` | Search students |

---

### 22. `components/dashboard_receipts.py`
**Purpose**: Receipt browsing and search

**Dependencies**:
| Service | Function | Description |
|---------|----------|-------------|
| `app.modules.finance` | `finance_service.get_recent_receipts(limit)` | Get recent receipts |
| `app.modules.finance` | `finance_service.search_receipts(q)` | Search receipts |
| `app.modules.finance` | `finance_service.get_receipt_by_id(receipt_id)` | Get receipt details |
| `app.modules.finance` | `finance_service.void_receipt(receipt_id, reason)` | Void receipt |

---

### 23. `components/finance_receipt.py`
**Purpose**: Receipt detail view and printing

**Dependencies**:
| Service | Function | Description |
|---------|----------|-------------|
| `app.modules.finance` | `finance_service.get_receipt_by_id(receipt_id)` | Get receipt |
| `app.modules.finance` | `finance_service.void_receipt(receipt_id, reason)` | Void receipt |

---

## Forms (Sub-components)

### 24. `components/forms/edit_group_form.py`
**Dependencies**:
| Service | Function | Description |
|---------|----------|-------------|
| `app.modules.academics` | `update_group(group_id, UpdateGroupDTO)` | Update group |

**Schemas Used**:
- `UpdateGroupDTO`

### 25. `components/forms/edit_session_form.py`
**Dependencies**:
| Service | Function | Description |
|---------|----------|-------------|
| `app.modules.academics` | `update_session(sess_id, UpdateSessionDTO)` | Update session |
| `app.modules.hr` | `hr_service.get_active_instructors()` | Instructors |
| `app.modules.academics` | `mark_substitute_instructor(sess_id, inst_id)` | Mark substitute |

**Schemas Used**:
- `UpdateSessionDTO`

### 26. `components/forms/edit_student_form.py`
**Dependencies**:
| Service | Function | Description |
|---------|----------|-------------|
| `app.modules.crm` | `update_student(student_id, UpdateStudentDTO)` | Update student |

### 27. `components/forms/edit_parent_form.py`
**Dependencies**:
| Service | Function | Description |
|---------|----------|-------------|
| `app.modules.crm` | `update_parent(parent_id, UpdateParentDTO)` | Update parent |

### 28. `components/forms/edit_course_form.py`
**Dependencies**:
| Service | Function | Description |
|---------|----------|-------------|
| `app.modules.academics` | `update_course(course_id, UpdateCourseDTO)` | Update course |

---

## Chart Components (BI)

### 29. `components/charts/retention_funnel.py`
**Dependencies**:
| Service | Function | Description |
|---------|----------|-------------|
| `app.modules.analytics` | `get_retention_funnel()` | Retention data |

### 30. `components/charts/instructor_matrix.py`
**Dependencies**:
| Service | Function | Description |
|---------|----------|-------------|
| `app.modules.analytics` | `get_instructor_performance()` | Instructor metrics |

### 31. `components/charts/schedule_utilization.py`
**Dependencies**:
| Service | Function | Description |
|---------|----------|-------------|
| `app.modules.analytics` | `get_schedule_utilization()` | Schedule utilization |

### 32. `components/charts/financial_risk.py`
**Dependencies**:
| Service | Function | Description |
|---------|----------|-------------|
| `app.modules.analytics` | `get_financial_risk_report()` | Risk analysis |

---

## Employee Components

### 33. `components/employee/employee_directory.py`
**Dependencies**:
| Service | Function | Description |
|---------|----------|-------------|
| `app.modules.hr` | `hr_service.get_all_employees()` | List employees |
| `app.modules.hr` | `hr_service.search_employees(q)` | Search employees |

### 34. `components/employee/employee_detail.py`
**Dependencies**:
| Service | Function | Description |
|---------|----------|-------------|
| `app.modules.hr` | `hr_service.get_employee_by_id(emp_id)` | Get employee |
| `app.modules.hr` | `hr_service.update_employee(emp_id, ...)` | Update employee |
| `app.modules.hr` | `hr_service.update_employee_login(emp_id, ...)` | Update login |

### 35. `components/employee/employee_form.py`
**Dependencies**:
| Service | Function | Description |
|---------|----------|-------------|
| `app.modules.hr` | `hr_service.create_employee(...)` | Create employee |
| `app.modules.hr` | `hr_service.get_all_employees()` | List for reference |

---

## Summary: Service Module Usage

### Most Used Services

1. **`app.modules.academics`** - Used by: Dashboard, Enrollment, Reports, Group Management, Course Management
   - `get_all_active_groups()`, `get_group_by_id()`, `list_group_sessions()`
   - `update_session()`, `delete_session()`, `cancel_session()`
   - `add_extra_session()`, `schedule_group()`, `delete_group()`
   - `get_active_courses()`, `add_new_course()`, `update_course()`

2. **`app.modules.crm`** - Used by: Directory, Quick Register, Finance, Enrollment
   - `search_students()`, `search_parents()`, `register_student()`, `register_parent()`
   - `get_student_by_id()`, `get_parent_by_id()`, `find_siblings()`
   - `update_student()`, `update_parent()`

3. **`app.modules.enrollments`** - Used by: Enrollment, Group Detail, Finance, Reports
   - `get_group_roster()`, `get_student_enrollments()`
   - `enroll_student()`, `transfer_student()`, `drop_enrollment()`
   - `apply_sibling_discount()`, `complete_enrollment()`

4. **`app.modules.finance`** - Used by: Dashboard, Finance Overview, Receipts
   - `get_enrollment_balance()`, `create_receipt_with_charge_lines()`
   - `get_receipt_by_id()`, `get_recent_receipts()`, `void_receipt()`
   - `get_unpaid_competition_fees()`, `preview_overpayment_risk()`

5. **`app.modules.analytics`** - Used by: Dashboard, Reports
   - `get_today_sessions()`, `get_revenue_by_date()`, `get_revenue_by_method()`
   - `get_group_roster()`, `get_attendance_heatmap()`, `get_top_debtors()`
   - `get_competition_fee_summary()`, `get_retention_funnel()`

6. **`app.modules.hr`** - Used by: Staff Management, Group Management, Course Management
   - `get_active_instructors()`, `get_all_employees()`, `get_employee_by_id()`
   - `create_employee()`, `update_employee()`

7. **`app.modules.attendance`** - Used by: Attendance Grid
   - `get_session_roster_with_attendance()`, `mark_session_attendance()`

8. **`app.modules.competitions`** - Used by: Competitions
   - `list_competitions()`, `create_competition()`, `add_team()`, `add_team_member()`

---

## DTOs/Schemas Used in UI

### Academics Module
- `AddNewCourseInput` - Course creation
- `ScheduleGroupInput` - Group creation
- `UpdateGroupDTO` - Group updates
- `UpdateCourseDTO` - Course updates
- `UpdateSessionDTO` - Session updates (notes, time, instructor)
- `AddExtraSessionInput` - Extra session creation

### CRM Module
- `RegisterParentInput` - Parent registration
- `RegisterStudentDTO` - Student data
- `RegisterStudentCommandDTO` - Student registration command
- `UpdateStudentDTO` - Student updates
- `UpdateParentDTO` - Parent updates

### Enrollments Module
- `EnrollStudentInput` - Enrollment creation
- `TransferStudentInput` - Transfer between groups

### Finance Module
- `ReceiptLineInput` - Receipt line items

---

## Authentication & Authorization

All pages (except login) use:
- `app.ui.components.auth_guard.require_auth()` - Ensures user is authenticated
- `app.ui.state.get_role()` - For role-based access (admin/instructor)
- `app.ui.state.get_current_user_id()` - For audit trails

---

*Document generated for Techno Terminal v1.0*
