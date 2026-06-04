# Techno Terminal — Application Features Checklist

Use this document to walk through the system page-by-page with the client to verify each feature, control, configuration, and interface capability.

---

## 1. Authentication & Security Flow
### Sign In Page (`/login`)
- [ ] Email / Username text input
- [ ] Password text input with show/hide password visibility toggle (eye icon)
- [ ] Sign In submission with validation (checks for empty fields and formatting)
- [ ] Custom user role handling (redirects active users to dashboard, displays error for deactivated accounts)
- [ ] "Forgot Password?" navigation link
- [ ] "Sign Up / Register" navigation link (for new users)

### Registration / Account Sign-Up (`/register`)
- [ ] Full Name text input
- [ ] Email Address text input
- [ ] Primary Phone Number text input
- [ ] Password and Confirm Password inputs with matching validation
- [ ] Direct redirect to Login screen upon successful registration

### Recovery / Forgot Password (`/forgot-password`)
- [ ] Email Address text input
- [ ] Submit button to trigger password reset instructions link via email
- [ ] Confirmation success state with instructions panel

### Password Reset Callback (`/reset-password`)
- [ ] Secure token validation from incoming callback URL
- [ ] New Password and Confirm Password inputs
- [ ] Submits updates directly to backend database and forces login redirection

---

## 2. Main Dashboard (`/dashboard`)
### Quick Actions Panel
- [ ] **Enroll Student** quick link (opens Enrollments portal)
- [ ] **Search Directory** quick link (opens CRM/Directory page)
- [ ] **Create Receipt** quick link (opens Finance page)
- [ ] **Today's Session Counter** (displays count of groups scheduled for the selected day)

### Calendar Navigation & Filters
- [ ] **Day Selector Bar**:
  - [ ] Displays 7-day horizontal calendar bar with weekdays and dates
  - [ ] Highlights the active selection
  - [ ] Tapping a date filters the active groups session list below
- [ ] **Instructor Selector Bar**:
  - [ ] Shows a horizontal bar listing scheduled instructors for the selected date
  - [ ] Filters out "TBA" from the list of selectable filters
  - [ ] Filters scheduled sessions to only display the chosen instructor's groups

### Desktop Session List & Attendance Sheet
- [ ] Lists all groups scheduled for the selected day
- [ ] Displays group name, course name, instructor name, and time slots
- [ ] Displays Level/Session Progress indicator (e.g., "Session 5 of 12", "Level 2")
- [ ] Renders expandable Student Roster check-in drawer:
  - [ ] Displays checklist of students enrolled in the group
  - [ ] Inline check-in / check-out checkboxes
  - [ ] Real-time updates saving attendance status (Present / Absent) to the database

### Mobile Dashboard Experience
- [ ] Responsive navigation header (collapses sidebar into a bottom navigation bar)
- [ ] Mobile-first Day and Instructor Selector components
- [ ] **Mobile Group Cards**:
  - [ ] Collapsed cards optimizing screen space
  - [ ] "Check Attendance" CTA opening mobile sheet drawer
- [ ] **Attendance Mobile Sheet**:
  - [ ] Slides up from bottom of the screen
  - [ ] Lists students with large, finger-friendly "Check In" and "Check Out" toggle buttons
- [ ] **Floating Action Button (FAB)** for rapid access to quick actions

---

## 3. CRM & Directory (`/directory`)
### Directory Navigation Tabs
- [ ] **Students Tab**: View active student registry
- [ ] **Parents Tab**: View parent/guardian contacts registry
- [ ] **Waiting List Tab**: View list of students waiting for course openings
- [ ] **Advanced Search Tab**: Multi-variable filter panel (Grade, Age, School, Status)

### Global Actions & Filters
- [ ] Main Search Bar (queries names, phone numbers, and emails)
- [ ] **Alphabet Slider Bar (A–Z)**: Filters items based on first letter of name
- [ ] Grouping filter dropdown (e.g. group by Grade, School, or Grade level)
- [ ] **Add Student Button** (opens modal):
  - [ ] Inputs: Full Name, Date of Birth, Gender, School, Grade Level, Notes
  - [ ] Associated parent selector (search and link)
- [ ] **Add Parent Button** (opens modal):
  - [ ] Inputs: Full Name, Phone Primary, Phone Secondary, WhatsApp Number, Email, Home Address, Relationship type
- [ ] **Trash Bin toggling**:
  - [ ] Toggle button to "Show Deleted" (displays soft-deleted records)
  - [ ] Restore button (reverses soft deletion)
  - [ ] Hard Delete button (permanently purges the record)

### Student Detail Profile Page (`/students/:id`)
- [ ] Student identity header card (displays name, status badge, grade, age, school, and registration details)
- [ ] Parent / Guardian relationship card:
  - [ ] Shows primary parent name, phone, email, and relationship
  - [ ] Edit parent connection button (link to existing parent or swap)
  - [ ] Unlink parent relationship option
- [ ] Siblings connection panel (links to related students)
- [ ] **Enrollments Overview**:
  - [ ] Lists active course enrollments, current levels, and associated groups
  - [ ] Displays enrollment details (Original Cost, Discount applied, Final Price, Date Enrolled)
  - [ ] Direct quick link to modify or drop the enrollment
- [ ] Course-level history list
- [ ] Competitions & Teams tracker (lists teams student belongs to and placement ranks)
- [ ] Invoices & Payment History grid:
  - [ ] Displays payment logs for all enrollments
  - [ ] Tracks balance, paid amount, and outstanding dues per invoice
- [ ] **Student Activity / Audit Log**:
  - [ ] Displays chronological timeline of all student actions (check-ins, enrollment modifications, payments collected)

### Parent Detail Profile Page (`/parents/:id`)
- [ ] Contact details card (displays address, phones, email, WhatsApp status)
- [ ] Connected Children List:
  - [ ] Renders details for each linked child
  - [ ] Navigation link directly to child's profile
  - [ ] "Add Child" quick association button

---

## 4. Academic Course Catalog (`/courses`)
### Course Index Page
- [ ] Switch views between Grid Cards and Table rows
- [ ] Search bar for course title or category keywords
- [ ] Pagination controls (10, 20, 50 records per page)
- [ ] Column sorting headers (ID, Title, Category, Price, Session Count)
- [ ] **Create Course Modal**:
  - [ ] Inputs: Title, Category, Price per Level, Session Count per Level, Description, Status (Active/Inactive)
- [ ] **Edit Course Modal**: Pre-fills fields for modification
- [ ] **Delete Course Dialog**: Confirms deletion (blocks deletion if active groups are using it)

### Course Details Page (`/courses/:id`)
- [ ] Stats Strip (displays active groups count, total enrolled students, average attendance rate)
- [ ] **Details Tab**: Detailed list of course duration, level fees, status, description, and setup dates
- [ ] **Groups Tab**:
  - [ ] Lists all active, completed, and archived groups assigned to the course
  - [ ] Grid displays: Group Name, Instructor, active Level, student capacity count, group status
  - [ ] Direct navigation to group detail view upon selection

---

## 5. Academic Groups & Rosters (`/groups`)
### Groups Directory Index Page
- [ ] Layout toggle (Table list or Grid Cards)
- [ ] Search bar for Group Name
- [ ] **Group By Selector Bar**:
  - [ ] Group by Day (filters list by days of the week)
  - [ ] Group by Instructor (filters by assigned instructor)
  - [ ] Group by Course (filters by course catalog)
  - [ ] Group by Status (Active, Completed, Archived)
- [ ] **Advanced Filter Toggle Panel**:
  - [ ] Multiselect Course filter
  - [ ] Multiselect Instructor filter
  - [ ] Multiselect Days of the week filter
  - [ ] Multiselect Levels filter
  - [ ] Multiselect Status filter (Active, Completed, Archived)
- [ ] Filter Tags strip (shows active filters with single-click removal cross buttons and "Clear All" link)
- [ ] Pagination control (supports 10, 20, 50, 100 rows per page with page index)
- [ ] **Create Group Modal**:
  - [ ] Inputs: Group Name, Course, Instructor, Capacity limit, Start Date
  - [ ] Schedule Builder: select Day, Start Time, End Time
- [ ] **Edit Group Modal**: Allows updating schedule, instructor, name, capacity, and start date

### Group Detail Page (`/groups/:id`)
- [ ] Group description header (status badge, assigned instructor, course, capacity, and active level)
- [ ] Quick actions: Edit Group, Archive/Unarchive Group, Delete Group
- [ ] **Level Up / Progress Level buttons**:
  - [ ] Level Up: Instant migration to next level using default settings
  - [ ] Progress Level Dialog: Advanced progression allowing changes to Group Name, Instructor, Course, or custom Price Override for the next level
- [ ] **Levels & Sessions Tab**:
  - [ ] Displays all academic levels the group has gone through
  - [ ] Shows session attendance checklist and log per level (Session Number, Date, Time, Attendance Rate)
  - [ ] Shows Level Payments overview (compares fees due, paid, and outstanding for all students in the level)
- [ ] **Roster & Student management**:
  - [ ] Lists all students in the active level
  - [ ] Renders payment status badges: Paid (Green), Partial (Blue), Pending (Amber)
  - [ ] Renders remaining balance for each student
  - [ ] **Add Student to Group** (opens combobox selector)
  - [ ] **Remove Student from Group** (removes student from roster; blocks if they have already paid fees for the level)
  - [ ] **Roster Payment Dialog** (opens within level roster):
    - [ ] Records payment for the student
    - [ ] Optional parent association search
    - [ ] Logs payment in finance ledger, and prints/emails receipt
- [ ] **Roster History Tab**: Logs additions, drops, and graduations of student members with timestamps
- [ ] **Competitions Tab**: Displays team achievements and registrations linked to this group

---

## 6. Enrollments Management (`/enrollments`)
### New Enrollment Panel (`EnrollPanel`)
- [ ] Student selection (searchable combobox)
- [ ] Course catalog selector
- [ ] Target Academic Level selector
- [ ] Target Group selector (automatically displays groups matching selected course/level and with open seats)
- [ ] Discount field: Flat EGP discount or percentage discount options
- [ ] Pricing Breakdown section: shows standard course price, discount deduction, final amount due
- [ ] Payment Method Selector: Cash, Card, Installment Plan
- [ ] Confirmation submit button (generates enrollment, assigns student to group, and creates billing invoice)

### Modify Enrollment Panel (`ModifyEnrollmentPanel`)
- [ ] Select active student enrollment to modify
- [ ] Discount adjuster (modify flat discount or percentage)
- [ ] Override standard price field
- [ ] Live billing updates breakdown (compares original cost, paid amount, new amount due, and remaining balance)
- [ ] Form submission validation (blocks modifications that would result in a negative remaining balance)
- [ ] Explanatory Notes text input (stored in enrollment metadata for audit logs)
- [ ] Automatically dispatches email update to parent inbox upon save

### Drop Enrollment Panel (`DropEnrollmentPanel`)
- [ ] Select enrollment to drop
- [ ] Unpaid balance choices:
  - [ ] Forgive outstanding balance (adjusts billing invoice to match amount already paid)
  - [ ] Request outstanding balance (keeps outstanding dues active in billing)
- [ ] Drop date selector and Reason text area input
- [ ] Submits updates, de-registers student from group roster, and locks enrollment status to "Dropped"

---

## 7. Financial Ledger (`/finance`)
### Today's Receipts Tab
- [ ] Renders a table of all receipts printed/processed today
- [ ] Columns: Receipt ID, Student, Parent, Amount Paid, Payment Method, Date/Time
- [ ] Action: View PDF receipt attachment in a new browser tab for printing/saving

### Create Receipt Tab
- [ ] Student selector (searchable combobox)
- [ ] Associated parent selector (auto-links if parent is connected to student; allows custom parent selection search)
- [ ] Lists student's enrollments with unpaid balances
- [ ] Amount Paid text input (supports full or partial payments)
- [ ] Payment Method selector: Cash, Card, Bank Transfer, Instapay
- [ ] Submit button (updates student's remaining balance, creates receipt log, and emails receipt to parent)

### Unpaid Enrollments Tab
- [ ] Lists all students with outstanding balances across the system
- [ ] Table displays: Student Name, Parent Contact, Course, Group, Total Cost, Amount Paid, Balance Due
- [ ] Action: "Collect Payment" button (navigates directly to Create Receipt tab pre-filled with student details)

### Refunds Tab
- [ ] Interface container (placeholder panel for refund records and voiding receipts)

---

## 8. Competitions & Projects (`/competitions`)
### Competitions Index Page
- [ ] View switchers (Table or Cards view)
- [ ] Search bar by Competition Title
- [ ] Add Competition Modal:
  - [ ] Inputs: Name, Location, Registration Fee, Date, Description, Status
- [ ] Edit Competition Modal
- [ ] Delete Competition confirmation (blocks if teams are registered)

### Competition Profile Details (`/competitions/:id`)
- [ ] Header summary (title, location, date, fee per student, total teams, total participants)
- [ ] **About Tab**: Displays date, rules/description, and location details
- [ ] **Categories Tab**:
  - [ ] Add Subcategory form (creates division/age category)
  - [ ] Lists teams registered per subcategory
  - [ ] **Register Team Button**:
    - [ ] Inputs: Team Name, Coach selection, Subcategory selection
    - [ ] Participant selector (search and add multiple students)
    - [ ] Custom registration fee input
- [ ] **Teams Tab**:
  - [ ] Lists all registered teams
  - [ ] Renders team name, coach, category, participants count, and payment state
  - [ ] "Pay Fee" modal launcher for quick payment collection
  - [ ] **Placement Ranking Form**:
    - [ ] Input Rank Number (e.g. 1st, 2nd, etc.)
    - [ ] Input Rank Label (e.g. Gold, Silver, Bronze, or Certificate of Merit)

### Team Profile Detail Page (`/teams/:id`)
- [ ] Team identity header (name, placement rank badge, coach, category/subcategory)
- [ ] Actions: Edit Team details, Delete Team (blocks if member payments exist)
- [ ] **Project Panel**: Displays Team Project Name and Project Description
- [ ] **Roster & Members Tab**:
  - [ ] List of students registered on the team
  - [ ] Show Member Due, Paid, Remaining fees, and Status badge (Paid, Partial, Pending)
  - [ ] Action: **Remove Member** (de-registers member; blocks if payment exists)
  - [ ] Action: **Add Member** (composes combobox search to add new student)
  - [ ] Action: **Collect Member Payment**:
    - [ ] Input amount, select payment method, select paying parent (optional)
    - [ ] Updates team roster balance, saves invoice log, and emails receipt
- [ ] **Placement Management Section**: Sets and saves placement rank and certificate label

---

## 9. Staff & HR Management (`/staff`)
### Staff Index Page
- [ ] Search bar for staff member names
- [ ] Quick filter options by employment type (Full-time, Part-time, Contractor)
- [ ] **Add Employee Modal**:
  - [ ] Inputs: Full Name, Job Title, Employment Type, Phone, Email, Salary, Hire Date, Status
- [ ] **Edit Employee Modal**: Modifies employee fields
- [ ] **Employee Profile Card**: Displays employee details, role, contact info, salary, and status
- [ ] **Account Creation Modal**:
  - [ ] Links employee record with an authentication account
  - [ ] Inputs: Email, Password, System Role (System Admin, Admin, Instructor, Agent)
- [ ] Pagination controls for staff index

---

## 10. Global & Admin Settings (`/settings`)
### Profile Tab
- [ ] Personal details editor (Full Name, Phone Primary, Avatar upload)
- [ ] **MFA Security Settings**: Shows Multi-Factor Authentication status with setup wizard

### Active Sessions Tab
- [ ] Lists all browsers, devices, OS platforms, and IP locations currently logged into this account
- [ ] **Sign Out Other Devices** CTA (invalidates other session cookies/tokens)

### User Accounts Tab (Admin / System Admin only)
- [ ] Table of all system user accounts
- [ ] Displays Name, Email, Role, Account Status
- [ ] **Invite User Dialog**: Email input, select system role, sends invite email
- [ ] **Soft-Deactivate Toggle**: Disables user login capabilities without purging data
- [ ] **Delete User Account CTA**: Permanently purges user auth login credentials

### System Audit Log Tab (System Admin only)
- [ ] Chronological feed of all logins (successful, failed attempts) with IP addresses and browsers
- [ ] Log of system configuration changes (password updates, user deactivations)

---

## 11. Bulk Messaging & Notifications (`/notifications`)
### Automated Alerts Setup
- [ ] Configuration selectors for automated payment alerts, enrollment warnings, and progress reports

### SMTP & Dispatch Logs
- [ ] Renders table of notifications sent (Recipients, Type e.g. Email/WhatsApp, Status e.g. Sent/Failed, Sent Time)
- [ ] Action: "Resend Notification" button

### Bulk Message Dispatcher
- [ ] Target audience filter (e.g. send to all students, parents, specific course, or specific group)
- [ ] Message composer (rich text area supporting variables like `{{student_name}}`, `{{parent_name}}`)
- [ ] WhatsApp & Email dispatch toggle switches
- [ ] Dispatch Progress Monitor (tracks send count, success rate, and completion status)
