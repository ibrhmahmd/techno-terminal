# Techno Terminal - Frontend API Reference (Full API Map)
This document automatically maps all endpoints listed in the OpenAPI specification.
---

## 🔐 Global Authentication
Most API requests MUST include a Bearer token in the `Authorization` header.
```http
Authorization: Bearer <access_token>
```

---

## Academics — Courses

### List all active courses ([GET] /api/v1/academics/courses)
**Method**: `GET`  
**Endpoint**: `/api/v1/academics/courses`  
**Parameters**:
- `skip` a integer in query (optional)
- `limit` a integer in query (optional)

**Responses**:
- `200`: Successful Response (Schema: `PaginatedResponse_CoursePublic_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Create a new course ([POST] /api/v1/academics/courses)
**Method**: `POST`  
**Endpoint**: `/api/v1/academics/courses`  
**Request Body** (JSON): `AddNewCourseInput`  

**Responses**:
- `201`: Successful Response (Schema: `ApiResponse_CoursePublic_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Update a course ([PATCH] /api/v1/academics/courses/{course_id})
**Method**: `PATCH`  
**Endpoint**: `/api/v1/academics/courses/{course_id}`  
**Parameters**:
- `course_id` a integer in path (required)

**Request Body** (JSON): `UpdateCourseDTO`  

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_CoursePublic_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

## Academics — Groups

### List all active groups ([GET] /api/v1/academics/groups)
**Method**: `GET`  
**Endpoint**: `/api/v1/academics/groups`  
**Parameters**:
- `skip` a integer in query (optional)
- `limit` a integer in query (optional)

**Responses**:
- `200`: Successful Response (Schema: `PaginatedResponse_GroupListItem_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Schedule a new group ([POST] /api/v1/academics/groups)
**Method**: `POST`  
**Endpoint**: `/api/v1/academics/groups`  
**Request Body** (JSON): `ScheduleGroupInput`  

**Responses**:
- `201`: Successful Response (Schema: `ApiResponse_GroupPublic_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Get group by ID ([GET] /api/v1/academics/groups/{group_id})
**Method**: `GET`  
**Endpoint**: `/api/v1/academics/groups/{group_id}`  
**Parameters**:
- `group_id` a integer in path (required)

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_GroupPublic_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Update a group ([PATCH] /api/v1/academics/groups/{group_id})
**Method**: `PATCH`  
**Endpoint**: `/api/v1/academics/groups/{group_id}`  
**Parameters**:
- `group_id` a integer in path (required)

**Request Body** (JSON): `UpdateGroupDTO`  

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_GroupPublic_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### List sessions for a group (optionally filter by level) ([GET] /api/v1/academics/groups/{group_id}/sessions)
**Method**: `GET`  
**Endpoint**: `/api/v1/academics/groups/{group_id}/sessions`  
**Parameters**:
- `group_id` a integer in path (required)
- `level` a integer in query (optional)

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_list_SessionPublic__`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Progress group to the next level ([POST] /api/v1/academics/groups/{group_id}/progress-level)
**Method**: `POST`  
**Endpoint**: `/api/v1/academics/groups/{group_id}/progress-level`  
**Parameters**:
- `group_id` a integer in path (required)

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_GroupPublic_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

## Academics — Sessions

### Add an extra session to a group ([POST] /api/v1/academics/groups/{group_id}/sessions)
**Method**: `POST`  
**Endpoint**: `/api/v1/academics/groups/{group_id}/sessions`  
**Parameters**:
- `group_id` a integer in path (required)

**Request Body** (JSON): `AddExtraSessionInput`  

**Responses**:
- `201`: Successful Response (Schema: `ApiResponse_SessionPublic_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Get daily session schedule ([GET] /api/v1/academics/sessions/daily-schedule)
**Method**: `GET`  
**Endpoint**: `/api/v1/academics/sessions/daily-schedule`  
**Parameters**:
- `target_date` a string in query (optional)

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_list_DailyScheduleItem__`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Get session details ([GET] /api/v1/academics/sessions/{session_id})
**Method**: `GET`  
**Endpoint**: `/api/v1/academics/sessions/{session_id}`  
**Parameters**:
- `session_id` a integer in path (required)

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_SessionPublic_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Update a session (date, time, status, notes) ([PATCH] /api/v1/academics/sessions/{session_id})
**Method**: `PATCH`  
**Endpoint**: `/api/v1/academics/sessions/{session_id}`  
**Parameters**:
- `session_id` a integer in path (required)

**Request Body** (JSON): `UpdateSessionDTO`  

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_SessionPublic_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Delete a session ([DELETE] /api/v1/academics/sessions/{session_id})
**Method**: `DELETE`  
**Endpoint**: `/api/v1/academics/sessions/{session_id}`  
**Parameters**:
- `session_id` a integer in path (required)

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_NoneType_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Cancel a session ([POST] /api/v1/academics/sessions/{session_id}/cancel)
**Method**: `POST`  
**Endpoint**: `/api/v1/academics/sessions/{session_id}/cancel`  
**Parameters**:
- `session_id` a integer in path (required)

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_SessionPublic_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Mark substitute instructor ([POST] /api/v1/academics/sessions/{session_id}/substitute)
**Method**: `POST`  
**Endpoint**: `/api/v1/academics/sessions/{session_id}/substitute`  
**Parameters**:
- `session_id` a integer in path (required)

**Request Body** (JSON): `SubstituteInstructorRequest`  

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_SessionPublic_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

## Analytics — Academic

### Get high-level dashboard aggregates ([GET] /api/v1/analytics/dashboard/summary)
**Method**: `GET`  
**Endpoint**: `/api/v1/analytics/dashboard/summary`  
**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_DashboardSummaryPublic_`)

---

### Get unpaid attendees for today ([GET] /api/v1/analytics/academics/unpaid-attendees)
**Method**: `GET`  
**Endpoint**: `/api/v1/analytics/academics/unpaid-attendees`  
**Parameters**:
- `target_date` a string in query (optional)

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_list_UnpaidAttendeeDTO__`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Get group roster ([GET] /api/v1/analytics/academics/groups/{group_id}/roster)
**Method**: `GET`  
**Endpoint**: `/api/v1/analytics/academics/groups/{group_id}/roster`  
**Parameters**:
- `group_id` a integer in path (required)
- `level_number` a integer in query (required)

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_list_GroupRosterRowDTO__`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Get attendance heatmap for group ([GET] /api/v1/analytics/academics/groups/{group_id}/heatmap)
**Method**: `GET`  
**Endpoint**: `/api/v1/analytics/academics/groups/{group_id}/heatmap`  
**Parameters**:
- `group_id` a integer in path (required)
- `level_number` a integer in query (required)

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_list_AttendanceHeatmapRowDTO__`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

## Analytics — BI

### Get enrollment trend over time ([GET] /api/v1/analytics/bi/enrollment-trend)
**Method**: `GET`  
**Endpoint**: `/api/v1/analytics/bi/enrollment-trend`  
**Parameters**:
- `cutoff` a string in query (optional)

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_list_EnrollmentTrendDTO__`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Get retention metrics by course ([GET] /api/v1/analytics/bi/retention)
**Method**: `GET`  
**Endpoint**: `/api/v1/analytics/bi/retention`  
**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_list_RetentionMetricsDTO__`)

---

### Get instructor performance metrics ([GET] /api/v1/analytics/bi/instructor-performance)
**Method**: `GET`  
**Endpoint**: `/api/v1/analytics/bi/instructor-performance`  
**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_list_InstructorPerformanceDTO__`)

---

### Get level retention funnel ([GET] /api/v1/analytics/bi/retention-funnel)
**Method**: `GET`  
**Endpoint**: `/api/v1/analytics/bi/retention-funnel`  
**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_list_LevelRetentionFunnelDTO__`)

---

### Get instructor value matrix ([GET] /api/v1/analytics/bi/instructor-value)
**Method**: `GET`  
**Endpoint**: `/api/v1/analytics/bi/instructor-value`  
**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_list_InstructorValueMatrixDTO__`)

---

### Get schedule utilization ([GET] /api/v1/analytics/bi/schedule-utilization)
**Method**: `GET`  
**Endpoint**: `/api/v1/analytics/bi/schedule-utilization`  
**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_list_ScheduleUtilizationDTO__`)

---

### Get flight-risk students ([GET] /api/v1/analytics/bi/flight-risk)
**Method**: `GET`  
**Endpoint**: `/api/v1/analytics/bi/flight-risk`  
**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_list_FlightRiskStudentDTO__`)

---

## Analytics — Competition

### Get competition fee summary ([GET] /api/v1/analytics/competitions/fee-summary)
**Method**: `GET`  
**Endpoint**: `/api/v1/analytics/competitions/fee-summary`  
**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_list_CompetitionFeeSummaryDTO__`)

---

## Analytics — Financial

### Get revenue breakdown by date ([GET] /api/v1/analytics/finance/revenue-by-date)
**Method**: `GET`  
**Endpoint**: `/api/v1/analytics/finance/revenue-by-date`  
**Parameters**:
- `start` a string in query (required)
- `end` a string in query (required)

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_list_RevenueByDateDTO__`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Get revenue breakdown by payment method ([GET] /api/v1/analytics/finance/revenue-by-method)
**Method**: `GET`  
**Endpoint**: `/api/v1/analytics/finance/revenue-by-method`  
**Parameters**:
- `start` a string in query (required)
- `end` a string in query (required)

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_list_RevenueByMethodDTO__`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Get outstanding balances by group ([GET] /api/v1/analytics/finance/outstanding-by-group)
**Method**: `GET`  
**Endpoint**: `/api/v1/analytics/finance/outstanding-by-group`  
**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_list_OutstandingByGroupDTO__`)

---

### Get top debtors ([GET] /api/v1/analytics/finance/top-debtors)
**Method**: `GET`  
**Endpoint**: `/api/v1/analytics/finance/top-debtors`  
**Parameters**:
- `limit` a integer in query (optional)

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_list_TopDebtorDTO__`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

## Attendance

### Get session roster with attendance status ([GET] /api/v1/attendance/session/{session_id})
**Method**: `GET`  
**Endpoint**: `/api/v1/attendance/session/{session_id}`  
**Parameters**:
- `session_id` a integer in path (required)

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_list_SessionAttendanceRowDTO__`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Mark / update attendance for a session ([POST] /api/v1/attendance/session/{session_id}/mark)
**Method**: `POST`  
**Endpoint**: `/api/v1/attendance/session/{session_id}/mark`  
**Parameters**:
- `session_id` a integer in path (required)

**Request Body** (JSON): `MarkAttendanceRequest`  

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_MarkAttendanceResponseDTO_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

## Authentication

### Login with Email and Password ([POST] /api/v1/auth/login)
**Method**: `POST`  
**Endpoint**: `/api/v1/auth/login`  
**Request Body** (JSON): `LoginRequest`  

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_TokenResponse_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Refresh Supabase JWT ([POST] /api/v1/auth/refresh)
**Method**: `POST`  
**Endpoint**: `/api/v1/auth/refresh`  
**Request Body** (JSON): `RefreshRequest`  

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_TokenResponse_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Logout user ([POST] /api/v1/auth/logout)
**Method**: `POST`  
**Endpoint**: `/api/v1/auth/logout`  
**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_NoneType_`)

---

### Get current authenticated user ([GET] /api/v1/auth/me)
**Method**: `GET`  
**Endpoint**: `/api/v1/auth/me`  
**Responses**:
- `200`: Successful Response (Schema: `UserPublic`)

---

### Create a new login user ([POST] /api/v1/auth/users)
**Method**: `POST`  
**Endpoint**: `/api/v1/auth/users`  
**Request Body** (JSON): `CreateUserRequest`  

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_UserPublic_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Force reset a user's password ([POST] /api/v1/auth/users/{user_id}/reset-password)
**Method**: `POST`  
**Endpoint**: `/api/v1/auth/users/{user_id}/reset-password`  
**Parameters**:
- `user_id` a integer in path (required)

**Request Body** (JSON): `ResetPasswordRequest`  

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_NoneType_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

## CRM — Parents

### List / search parents ([GET] /api/v1/crm/parents)
**Method**: `GET`  
**Endpoint**: `/api/v1/crm/parents`  
**Parameters**:
- `q` a string in query (optional)
- `skip` a integer in query (optional)
- `limit` a integer in query (optional)

**Responses**:
- `200`: Successful Response (Schema: `PaginatedResponse_ParentListItem_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Register a new parent ([POST] /api/v1/crm/parents)
**Method**: `POST`  
**Endpoint**: `/api/v1/crm/parents`  
**Request Body** (JSON): `RegisterParentInput`  

**Responses**:
- `201`: Successful Response (Schema: `ApiResponse_ParentPublic_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Get parent by ID ([GET] /api/v1/crm/parents/{parent_id})
**Method**: `GET`  
**Endpoint**: `/api/v1/crm/parents/{parent_id}`  
**Parameters**:
- `parent_id` a integer in path (required)

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_ParentPublic_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Update parent profile ([PATCH] /api/v1/crm/parents/{parent_id})
**Method**: `PATCH`  
**Endpoint**: `/api/v1/crm/parents/{parent_id}`  
**Parameters**:
- `parent_id` a integer in path (required)

**Request Body** (JSON): `UpdateParentDTO`  

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_ParentPublic_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

## CRM — Students

### List / search students ([GET] /api/v1/crm/students)
**Method**: `GET`  
**Endpoint**: `/api/v1/crm/students`  
**Parameters**:
- `q` a string in query (optional)
- `skip` a integer in query (optional)
- `limit` a integer in query (optional)

**Responses**:
- `200`: Successful Response (Schema: `PaginatedResponse_StudentListItem_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Register a new student ([POST] /api/v1/crm/students)
**Method**: `POST`  
**Endpoint**: `/api/v1/crm/students`  
**Request Body** (JSON): `RegisterStudentCommandDTO`  

**Responses**:
- `201`: Successful Response (Schema: `ApiResponse_StudentPublic_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Get student by ID ([GET] /api/v1/crm/students/{student_id})
**Method**: `GET`  
**Endpoint**: `/api/v1/crm/students/{student_id}`  
**Parameters**:
- `student_id` a integer in path (required)

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_StudentPublic_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Update student profile ([PATCH] /api/v1/crm/students/{student_id})
**Method**: `PATCH`  
**Endpoint**: `/api/v1/crm/students/{student_id}`  
**Parameters**:
- `student_id` a integer in path (required)

**Request Body** (JSON): `UpdateStudentDTO`  

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_StudentPublic_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Get all parents linked to a student ([GET] /api/v1/crm/students/{student_id}/parents)
**Method**: `GET`  
**Endpoint**: `/api/v1/crm/students/{student_id}/parents`  
**Parameters**:
- `student_id` a integer in path (required)

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_list_ParentPublic__`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

## Competitions

### List all competitions ([GET] /api/v1/competitions)
**Method**: `GET`  
**Endpoint**: `/api/v1/competitions`  
**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_list_CompetitionDTO__`)

---

### Create a new competition ([POST] /api/v1/competitions)
**Method**: `POST`  
**Endpoint**: `/api/v1/competitions`  
**Request Body** (JSON): `CreateCompetitionInput`  

**Responses**:
- `201`: Successful Response (Schema: `ApiResponse_CompetitionDTO_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Get single competition details ([GET] /api/v1/competitions/{competition_id})
**Method**: `GET`  
**Endpoint**: `/api/v1/competitions/{competition_id}`  
**Parameters**:
- `competition_id` a integer in path (required)

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_CompetitionDTO_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### List categories for a competition ([GET] /api/v1/competitions/{competition_id}/categories)
**Method**: `GET`  
**Endpoint**: `/api/v1/competitions/{competition_id}/categories`  
**Parameters**:
- `competition_id` a integer in path (required)

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_list_CompetitionCategoryDTO__`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Add a category to a competition ([POST] /api/v1/competitions/{competition_id}/categories)
**Method**: `POST`  
**Endpoint**: `/api/v1/competitions/{competition_id}/categories`  
**Parameters**:
- `competition_id` a integer in path (required)

**Request Body** (JSON): `AddCategoryInput`  

**Responses**:
- `201`: Successful Response (Schema: `ApiResponse_CompetitionCategoryDTO_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Register a team for a competition ([POST] /api/v1/competitions/register)
**Method**: `POST`  
**Endpoint**: `/api/v1/competitions/register`  
**Request Body** (JSON): `RegisterTeamInput`  

**Responses**:
- `201`: Successful Response (Schema: `ApiResponse_TeamRegistrationResultDTO_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### List teams in a competition category ([GET] /api/v1/competitions/{competition_id}/categories/{category_id}/teams)
**Method**: `GET`  
**Endpoint**: `/api/v1/competitions/{competition_id}/categories/{category_id}/teams`  
**Parameters**:
- `competition_id` a integer in path (required)
- `category_id` a integer in path (required)

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_list_TeamWithMembersDTO__`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Mark competition fee as paid (bypass Finance Desk) ([POST] /api/v1/competitions/team-members/{team_member_id}/pay)
**Method**: `POST`  
**Endpoint**: `/api/v1/competitions/team-members/{team_member_id}/pay`  
**Parameters**:
- `team_member_id` a integer in path (required)

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_NoneType_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

## Enrollments

### Enroll a student in a group ([POST] /api/v1/enrollments)
**Method**: `POST`  
**Endpoint**: `/api/v1/enrollments`  
**Request Body** (JSON): `EnrollStudentInput`  

**Responses**:
- `201`: Successful Response (Schema: `ApiResponse_EnrollmentPublic_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Drop an enrollment ([DELETE] /api/v1/enrollments/{enrollment_id})
**Method**: `DELETE`  
**Endpoint**: `/api/v1/enrollments/{enrollment_id}`  
**Parameters**:
- `enrollment_id` a integer in path (required)

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_EnrollmentPublic_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Transfer a student to a new group ([POST] /api/v1/enrollments/transfer)
**Method**: `POST`  
**Endpoint**: `/api/v1/enrollments/transfer`  
**Request Body** (JSON): `TransferStudentInput`  

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_EnrollmentPublic_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Get student enrollment history ([GET] /api/v1/enrollments/student/{student_id})
**Method**: `GET`  
**Endpoint**: `/api/v1/enrollments/student/{student_id}`  
**Parameters**:
- `student_id` a integer in path (required)

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_list_EnrollmentPublic__`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

## Finance

### Create a new receipt ([POST] /api/v1/finance/receipts)
**Method**: `POST`  
**Endpoint**: `/api/v1/finance/receipts`  
**Request Body** (JSON): `CreateReceiptRequest`  

**Responses**:
- `201`: Successful Response (Schema: `ApiResponse_ReceiptCreatedPublic_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Search receipts ([GET] /api/v1/finance/receipts)
**Method**: `GET`  
**Endpoint**: `/api/v1/finance/receipts`  
**Parameters**:
- `from_date` a string in query (required)
- `to_date` a string in query (required)
- `payer_name` a string in query (optional)
- `student_id` a string in query (optional)
- `receipt_number` a string in query (optional)
- `limit` a integer in query (optional)

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_list_ReceiptListItem__`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Get receipt details ([GET] /api/v1/finance/receipts/{receipt_id})
**Method**: `GET`  
**Endpoint**: `/api/v1/finance/receipts/{receipt_id}`  
**Parameters**:
- `receipt_id` a integer in path (required)

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_ReceiptDetailPublic_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Issue a refund ([POST] /api/v1/finance/refunds)
**Method**: `POST`  
**Endpoint**: `/api/v1/finance/refunds`  
**Request Body** (JSON): `IssueRefundRequest`  

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_RefundResultPublic_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Get student balances ([GET] /api/v1/finance/balance/student/{student_id})
**Method**: `GET`  
**Endpoint**: `/api/v1/finance/balance/student/{student_id}`  
**Parameters**:
- `student_id` a integer in path (required)

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_list_FinancialSummaryPublic__`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Get unpaid competition fees ([GET] /api/v1/finance/competition-fees/student/{student_id})
**Method**: `GET`  
**Endpoint**: `/api/v1/finance/competition-fees/student/{student_id}`  
**Parameters**:
- `student_id` a integer in path (required)

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_list_UnpaidCompFeeItem__`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Preview overpayment risk ([POST] /api/v1/finance/receipts/preview-risk)
**Method**: `POST`  
**Endpoint**: `/api/v1/finance/receipts/preview-risk`  
**Request Body** (JSON): `PreviewRiskRequest`  

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_list_OverpaymentRiskItem__`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Download PDF receipt ([GET] /api/v1/finance/receipts/{receipt_id}/pdf)
**Method**: `GET`  
**Endpoint**: `/api/v1/finance/receipts/{receipt_id}/pdf`  
**Parameters**:
- `receipt_id` a integer in path (required)

**Responses**:
- `200`: Returns the PDF document (Schema: `Unknown`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

## HR

### List all employees ([GET] /api/v1/hr/employees)
**Method**: `GET`  
**Endpoint**: `/api/v1/hr/employees`  
**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_list_EmployeeListItem__`)

---

### Create employee record ([POST] /api/v1/hr/employees)
**Method**: `POST`  
**Endpoint**: `/api/v1/hr/employees`  
**Request Body** (JSON): `EmployeeCreateInput`  

**Responses**:
- `201`: Successful Response (Schema: `ApiResponse_EmployeePublic_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Get employee by ID ([GET] /api/v1/hr/employees/{employee_id})
**Method**: `GET`  
**Endpoint**: `/api/v1/hr/employees/{employee_id}`  
**Parameters**:
- `employee_id` a integer in path (required)

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_EmployeePublic_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### Update employee record ([PUT] /api/v1/hr/employees/{employee_id})
**Method**: `PUT`  
**Endpoint**: `/api/v1/hr/employees/{employee_id}`  
**Parameters**:
- `employee_id` a integer in path (required)

**Request Body** (JSON): `EmployeeCreateInput`  

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_EmployeePublic_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

### List staff accounts ([GET] /api/v1/hr/staff-accounts)
**Method**: `GET`  
**Endpoint**: `/api/v1/hr/staff-accounts`  
**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_list_StaffAccountPublic__`)

---

### Log employee attendance (Stub) ([POST] /api/v1/hr/attendance/log)
**Method**: `POST`  
**Endpoint**: `/api/v1/hr/attendance/log`  
**Request Body** (JSON): `AttendanceLogInput`  

**Responses**:
- `200`: Successful Response (Schema: `ApiResponse_AttendanceLogOutput_`)
- `422`: Validation Error (Schema: `HTTPValidationError`)

---

## Health

### Health Check ([GET] /health)
**Method**: `GET`  
**Endpoint**: `/health`  
**Responses**:
- `200`: Successful Response (Schema: `Unknown`)

---

