# TODO Audit Report — Codebase Comprehensive Scan

**Date:** 2026-05-02  
**Scope:** Full codebase (`app/`, `tests/`)  
**Patterns Searched:** `TODO`, `FIXME`, `HACK`, `XXX`, `BUG`, `NOTE`

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Total TODOs Found** | 37 |
| **FIXME/HACK/XXX/BUG Found** | 0 |
| **Affected Files** | 20 |
| **Affected Modules** | 7 + API layer |

### Category Breakdown

| Category | Count | % |
|----------|-------|---|
| Refactoring — Replace `dict` with typed DTOs | 30 | 81% |
| Feature Implementation — Missing functionality | 3 | 8% |
| Refactoring — Architectural move | 1 | 3% |
| Bug Fixes — Loose return types | 1 | 3% |
| Feature Implementation — Pass-through values | 1 | 3% |
| Documentation — Typo | 1 | 3% |

**Dominant Pattern:** 81% of all TODOs are `#TODO remove Dict and write a typed DTO class` — a systemic codebase-wide pattern of using untyped `dict` returns instead of strict Pydantic DTOs.

---

## Detailed Findings

### Category 1: Refactoring — Replace `dict` with Typed DTOs (30 items)

#### Module: `app/modules/academics` (10 items)

| # | File | Line | TODO Text | Context |
|---|------|------|-----------|---------|
| 1 | `services/group_details_service.py` | 236 | `#TODO remove Dict and write a typed DTO class` | `_get_enrollment_stats_for_levels() -> dict[int, dict]` |
| 2 | `services/group_details_service.py` | 268 | `#TODO remove Dict and write a typed DTO class` | `_get_payment_stats_for_levels() -> dict[int, dict]` |
| 3 | `services/group_details_service.py` | 321 | `#TODO remove Dict and write a typed DTO class` | `_build_courses_lookup() -> dict[int, CourseLookupDTO]` |
| 4 | `services/group_details_service.py` | 335 | `#TODO remove Dict and write a typed DTO class` | `_build_instructors_lookup() -> dict[int, InstructorLookupDTO]` |
| 5 | `services/group_lifecycle_service.py` | 436 | `#TODO remove Dict and write a typed DTO class` | `_serialize_session() -> dict` |
| 6 | `services/group_competition_service.py` | 122 | `#TODO remove Dict and write a typed DTO class` | `get_group_competitions() -> list[dict]` |
| 7 | `services/group_competition_service.py` | 204 | `#TODO remove Dict and write a typed DTO class` | `withdraw_from_competition() -> dict` |
| 8 | `services/group_competition_service.py` | 243 | `#TODO remove Dict and write a typed DTO class` | `link_existing_team() -> dict` |
| 9 | `schemas/scheduling_dtos.py` | 140 | `#TODO remove Dict and write a typed DTO class` | `SessionGenerationResult.sessions: List[dict]` |
| 10 | `schemas/scheduling_dtos.py` | 175 | `#TODO remove Dict and write a typed DTO class` | `GroupCreationResult.sessions: List[dict]` |
| 11 | `repositories/group_repository.py` | 312 | `#TODO remove Dict and write a typed DTO class` | `get_transfer_options() -> list[dict]` |
| 12 | `repositories/group_history_repository.py` | 134 | `#TODO remove Dict and write a typed DTO class` | `get_level_student_counts() -> dict[int, int]` |
| 13 | `repositories/group_history_repository.py` | 180 | `#TODO remove Dict and write a typed DTO class` | `get_group_enrollment_stats() -> dict` |

#### Module: `app/modules/analytics` (3 items)

| # | File | Line | TODO Text | Context |
|---|------|------|-----------|---------|
| 14 | `schemas/bi_schemas.py` | 60 | `#TODO remove Dict and write a typed DTO classs` | `retention_by_month: dict[str, int]` (typo: "classs") |
| 15 | `schemas/bi_schemas.py` | 61 | `#TODO remove Dict and write a typed DTO class` | `retention_rates: dict[str, float]` |
| 16 | `repositories/dashboard_repository.py` | 158 | `#TODO remove Dict and write a typed DTO class` | `get_sessions_for_levels(group_level_map: dict[int, int])` |

#### Module: `app/modules/auth` (2 items)

| # | File | Line | TODO Text | Context |
|---|------|------|-----------|---------|
| 17 | `repositories/auth_repository.py` | 18 | `#TODO remove Dict and write a typed DTO class` | `create_user(user_data: dict) -> User` |
| 18 | `repositories/auth_repository.py` | 30 | `#TODO remove Dict and write a typed DTO class` | `update_user(user_data: dict) -> User | None` |

#### Module: `app/modules/crm` (5 items)

| # | File | Line | TODO Text | Context |
|---|------|------|-----------|---------|
| 19 | `services/student_crud_service.py` | 31 | `#TODO remove Dict and write a typed DTO class` | `register_student() -> Tuple[Student, List[dict]]` |
| 20 | `repositories/parent_repository.py` | 53 | `#TODO remove Dict and write a typed DTO class` | `update(parent_id, data: dict) -> Optional[Parent]` |
| 21 | `repositories/activity_repository.py` | 370 | `#TODO remove Dict and write a typed DTO class` | `get_activity_summary() -> Dict[str, Any]` |
| 22 | `models/activity_models.py` | 79 | `#TODO remove Dict and write a typed DTO class` | `activities_by_type: dict[str, int]` |
| 23 | `interfaces/__init__.py` | 59 | `#TODO remove Dict and write a typed DTO class` | `update(parent_id, data: dict) -> Optional[Parent]` (interface) |
| 24 | `interfaces/iactivity_repository.py` | 60 | `#TODO remove Dict and write a typed DTO class` | `get_activity_summary() -> Dict[str, Any]` (interface) |
| 25 | `interfaces/dtos/activity_summary_dto.py` | 16 | `#TODO remove Dict and write a typed DTO class` | `activities_by_type: Dict[str, int]` |

#### Module: `app/modules/notifications` (5 items)

| # | File | Line | TODO Text | Context |
|---|------|------|-----------|---------|
| 26 | `services/report_notifications.py` | 164 | `#TODO remove Dict and write a typed DTO class` | `_fetch_daily_aggregates() -> dict` |
| 27 | `services/report_notifications.py` | 312 | `#TODO remove Dict and write a typed DTO class` | `_fetch_weekly_aggregates() -> dict` |
| 28 | `services/report_notifications.py` | 356 | `#TODO remove Dict and write a typed DTO class` | `_fetch_monthly_aggregates() -> dict` |
| 29 | `services/report_notifications.py` | 397 | `#TODO remove Dict and write a typed DTO class` | `send_bulk(extra_vars: dict)` |
| 30 | `schemas/admin_settings_dto.py` | 36 | `#TODO remove Dict and write a typed DTO class` | `settings: Dict[str, bool]` |

#### API Layer: `app/api` (6 items)

| # | File | Line | TODO Text | Context |
|---|------|------|-----------|---------|
| 31 | `schemas/students/activity.py` | 114 | `#TODO remove Dict and write a typed DTO class` | `StudentHistoryItemDTO.data: Dict[str, Any]` |
| 32 | `schemas/analytics/bi.py` | 82 | `#TODO remove Dict and write a typed DTO class` | `feature_usage: dict[str, int]` |
| 33 | `schemas/analytics/bi.py` | 91 | `#TODO remove Dict and write a typed DTO class` | `retention_by_month: dict[str, int]` |
| 34 | `schemas/analytics/bi.py` | 92 | `#TODO remove Dict and write a typed DTO class` | `retention_rates: dict[str, float]` |
| 35 | `schemas/academics/group_level.py` | 36 | `#TODO remove Dict and write a typed DTO class` | `sessions: list[dict]` in ScheduleLevelResponse |
| 36 | `schemas/academics/group_level.py` | 42 | `#TODO remove Dict and write a typed DTO class` | `completed_level: dict` in GroupLevelCompletionResponse |
| 37 | `schemas/academics/group_level.py` | 43 | `#TODO remove Dict and write a typed DTO class` | `new_level: dict` in GroupLevelCompletionResponse |
| 38 | `schemas/academics/grouped.py` | 24 | `#TODO remove Dict and write a typed DTO class` | `groups: list[dict]` in GroupedGroupItem |

#### API Routers (8 items)

| # | File | Line | TODO Text | Context |
|---|------|------|-----------|---------|
| 39 | `routers/notifications/bulk_router.py` | 11 | `#TODO remove Dict and write a typed DTO class` | `response_model=ApiResponse[dict]` |
| 40 | `routers/notifications/admin_settings_router.py` | 112 | `#TODO remove Dict and write a typed DTO class` | `response_model=ApiResponse[Dict[str, bool]]` |
| 41 | `routers/notifications/admin_settings_router.py` | 276 | `#TODO remove Dict and write a typed DTO class` | `response_model=ApiResponse[Dict[str, str]]` |
| 42 | `routers/crm/students_router.py` | 399 | `#TODO remove Dict and write a typed DTO class` | `response_model=ApiResponse[List[dict]]` (status-history) |
| 43 | `routers/crm/students_router.py` | 495 | `#TODO remove Dict and write a typed DTO class` | `response_model=ApiResponse[dict]` (soft delete) |
| 44 | `routers/crm/students_router.py` | 523 | `#TODO remove Dict and write a typed DTO class` | `response_model=ApiResponse[dict]` (restore) |
| 45 | `routers/crm/students_router.py` | 548 | `#TODO remove Dict and write a typed DTO class` | `response_model=ApiResponse[dict]` (hard delete) |
| 46 | `routers/competitions/competitions_router.py` | 50 | `#TODO remove Dict and write a typed DTO class` | `categories: list[dict]` in CompetitionSummaryResponse |
| 47 | `routers/academics/group_lifecycle_router.py` | 43 | `#TODO remove Dict and write a typed DTO class` | `complete` endpoint response |
| 48 | `routers/academics/group_lifecycle_router.py` | 79 | `#TODO remove Dict and write a typed DTO class` | `cancel` endpoint response |
| 49 | `routers/academics/group_competitions_router.py` | 22 | `#TODO remove Dict and write a typed DTO class` | `list` competitions response |
| 50 | `routers/academics/group_competitions_router.py` | 79 | `#TODO remove Dict and write a typed DTO class` | `link` team response |
| 51 | `routers/academics/group_competitions_router.py` | 104 | `#TODO remove Dict and write a typed DTO class` | `register` competition response |
| 52 | `routers/academics/group_competitions_router.py` | 146 | `#TODO remove Dict and write a typed DTO class` | `complete` participation response |
| 53 | `routers/academics/group_competitions_router.py` | 177 | `#TODO remove Dict and write a typed DTO class` | `withdraw` competition response |

---

### Category 2: Feature Implementation — Missing Functionality (3 items)

| # | File | Line | TODO Text | Severity | Context |
|---|------|------|-----------|----------|---------|
| 1 | `finance/services/receipt_service.py` | 322 | `# TODO: Implement when notification tracking is added` | Medium | `mark_as_sent()` — stub with `pass` |
| 2 | `enrollments/services/enrollment_migration_service.py` | 108 | `# TODO: Trigger level progression notification` | Medium | After level progression, notification not wired |
| 3 | `enrollments/services/enrollment_migration_service.py` | 169 | `# TODO: Trigger enrollment completed notification` | Medium | After enrollment completion, notification not wired |

### Category 3: Refactoring — Architectural Move (1 item)

| # | File | Line | TODO Text | Severity | Context |
|---|------|------|-----------|----------|---------|
| 1 | `notifications/services/notification_service.py` | 145 | `# TODO: Move to BulkNotificationService if needed` | Low | `send_bulk()` delegated from NotificationService |

### Category 4: Bug Fixes — Loose Return Types (1 item)

| # | File | Line | TODO Text | Severity | Context |
|---|------|------|-----------|----------|---------|
| 1 | `academics/repositories/group_history_repository.py` | 222 | `#TODO remove loose return types and write a typed DTO class` | Medium | `get_group_instructors_summary()` returns `Sequence[tuple[int, str, datetime, datetime, int, bool]]` |

### Category 5: Feature Implementation — Pass-Through Values (1 item)

| # | File | Line | TODO Text | Severity | Context |
|---|------|------|-----------|----------|---------|
| 1 | `academics/services/group_competition_service.py` | 114 | `performed_by=None, # TODO: Pass from caller` | Low | Activity log missing audit trail for who performed action |

---

## File Distribution Analysis

Top files by TODO count:

| File | TODOs | Module |
|------|-------|--------|
| `app/api/routers/academics/group_competitions_router.py` | 5 | API |
| `app/api/routers/crm/students_router.py` | 4 | API |
| `app/modules/notifications/services/report_notifications.py` | 4 | Notifications |
| `app/modules/academics/services/group_details_service.py` | 4 | Academics |
| `app/modules/academics/services/group_competition_service.py` | 3 | Academics |
| `app/api/schemas/analytics/bi.py` | 3 | API |
| `app/api/schemas/academics/group_level.py` | 3 | API |
| `app/modules/academics/repositories/group_history_repository.py` | 2 | Academics |
| `app/modules/auth/repositories/auth_repository.py` | 2 | Auth |
| `app/modules/crm/interfaces/*` | 3 | CRM |

## Module Distribution

| Module | TODOs | % |
|--------|-------|---|
| API Layer (routers + schemas) | 18 | 49% |
| Academics | 10 | 27% |
| CRM | 5 | 14% |
| Notifications | 5 | 14% |
| Analytics | 3 | 8% |
| Auth | 2 | 5% |
| Finance | 1 | 3% |
| Enrollments | 2 | 5% |

---

## Implementation Plan

### Phase 1: Dict→DTO Conversion (High Impact, Medium Effort)
**Target:** 30 items | **Timeline:** 2-3 weeks

Batched by module:

1. **Academics DTOs** (10 items) — Create typed DTOs for:
   - `EnrollmentStatsDTO`, `PaymentStatsDTO` (service returns)
   - `SessionSummaryDTO` (serialize_session)
   - `CompetitionParticipationDTO`, `CompetitionWithdrawalDTO`, `TeamLinkDTO`
   - `TransferOptionDTO` (reuse from group_details_schemas)
   - `LevelStudentCountsDTO`, `GroupEnrollmentStatsDTO`
   - `SessionGenerationItemDTO`, `GroupCreationSessionDTO`

2. **API Router DTOs** (8 items) — Create response DTOs for:
   - Competition router responses (5 endpoints)
   - Student CRUD responses (4 endpoints)
   - Notification settings responses (2 endpoints)
   - Level completion/cancellation responses (2 endpoints)

3. **CRM DTOs** (5 items) — Create:
   - `StudentSiblingDTO`, `ParentUpdateDTO`, `ActivitySummaryResultDTO`
   - Update interface definitions accordingly

4. **Notifications DTOs** (5 items) — Create:
   - `DailyAggregatesDTO`, `WeeklyAggregatesDTO`, `MonthlyAggregatesDTO`
   - `BulkEmailVarsDTO`, `NotificationSettingsMapDTO`

5. **Analytics DTOs** (3 items) — Create:
   - `RetentionByMonthDTO`, `RetentionRatesDTO`, `GroupLevelMapDTO`

6. **Auth DTOs** (2 items) — Create:
   - `CreateUserDTO`, `UpdateUserDTO`

### Phase 2: Missing Functionality (Medium Impact, Medium Effort)
**Target:** 3 items | **Timeline:** 1 week

1. Wire `mark_as_sent()` in receipt_service to notification tracking
2. Wire level progression notification in enrollment_migration_service
3. Wire enrollment completed notification in enrollment_migration_service

### Phase 3: Code Quality (Low Impact, Low Effort)
**Target:** 3 items | **Timeline:** 2-3 days

1. Move `send_bulk()` to BulkNotificationService
2. Create `InstructorSummaryDTO` for `get_group_instructors_summary()`
3. Pass `performed_by` from caller in competition service

---

## Priority Matrix

```
         HIGH IMPACT                    LOW IMPACT
HIGH  ┌─────────────────────┐    ┌──────────────────┐
EFFORT│ Phase 1: Dict→DTO   │    │ Phase 2: Notifs  │
      │ (30 items, 2-3 wks) │    │ (3 items, 1 wk)  │
      ├─────────────────────┤    ├──────────────────┤
LOW   │ Quick wins:         │    │ Phase 3: Quality  │
      │ - Fix typo "classs" │    │ (3 items, 2 days) │
      │ - Pass performed_by │    │                   │
      └─────────────────────┘    └──────────────────┘
```
