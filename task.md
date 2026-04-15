# CRM Student Module — Execution Tasks

## Phase 1 — Model & Critical Bug Fixes
- [x] 1.1 Unify `StudentStatus` Enum (Remove `GRADUATED`)
- [x] 1.2 Add `StatusHistoryEntryDTO` and replace `list[dict]`
- [x] 1.3 Fix `UpdateStudentStatusDTO` to use Enum
- [x] 1.4 Create DB Index Migration (`022_student_indexes.sql`)

## Phase 2 — Finance-Pattern SOLID Architecture Migration
- [ ] 2.1 Create `interfaces/__init__.py` with Protocol interfaces and DTOs
- [ ] 2.2 Rewrite `StudentRepository` as a class with injected Session
- [ ] 2.3 Rewrite `ParentRepository` as a class with injected Session
- [ ] 2.4 Create `unit_of_work.py` (`StudentUnitOfWork`)
- [ ] 2.5 Create `validators/student_validator.py`
- [ ] 2.6 Create 4 focused service classes (`StudentService`, `SearchService`, `GroupingService`, `ReportingService`)
- [ ] 2.7 Clean up `crm/__init__.py`
- [ ] 2.8 Update `dependencies.py` to use new service factories

## Phase 3 — API Contract Fixes
- [ ] 3.1 Fix `StudentPublic` (Add `status` field)
- [ ] 3.2 Fix `StudentListItem` (Real data via Enriched Query)
- [ ] 3.3 Fix `student_details.py` schemas
- [ ] 3.4 Fix `students_history.py` (Add `/crm` prefix, type `svc`)
- [ ] 3.5 Fix `students.py` router
- [ ] 3.6 Remove Dead DTOs from `activity.py`

## Phase 4 — Grouped Students Endpoint
- [ ] 4.1 Create Response DTOs (`student_grouped.py`)
- [ ] 4.2 Implement `GroupingService` strategies
- [ ] 4.3 Create Router (`students_grouped.py`)

## Phase 5 — Enriched Student Details
- [ ] 5.1 Add `AttendanceStats` DTO and attach to `StudentWithDetails`
- [ ] 5.2 Implement `ReportingService.get_attendance_stats`

## Phase 6 — Test Suite Expansion
- [ ] 6.1 Add/Update tests in `tests/test_crm.py`
- [ ] 6.2 Create `tests/test_crm_grouped.py`
- [ ] 6.3 Create `tests/test_crm_details.py`
