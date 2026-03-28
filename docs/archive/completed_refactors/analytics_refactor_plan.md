# Analytics Module Refactoring Plan

**Date:** March 2026

## Objective
To restructure the [analytics](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/db/init_db.py#116-125) module from a monolithic, functional architecture into a highly segregated, Object-Oriented, and strictly-typed (DTO-driven) design that complies with the Techno Kids CRM Refactoring SOP.

## Phase 1: Foundation (Constants & Setup)
*   **Create `app/modules/analytics/constants.py`**
    *   Currently, there are no explicit external constants in [analytics](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/db/init_db.py#116-125), but we will establish this file for future scalar defaults or status strings if any emerge from the SQL definitions.

## Phase 2: DTO Schema Design (Typing the Contracts)
*   **Create `app/modules/analytics/schemas/` directory.**
*   **Subdivide into domain-specific schema files:**
    *   `financial_schemas.py` (e.g., `RevenueTrendDTO`, `PaymentMethodRevenueDTO`, `GroupOutstandingDTO`, `DebtorDTO`)
    *   `academic_schemas.py` (e.g., `TodaySessionDTO`, `StudentDebtStatusDTO`, `GroupRosterRowDTO`, `AttendanceHeatmapDTO`)
    *   `competition_schemas.py` (e.g., `CompetitionFeeSummaryDTO`)
    *   `bi_schemas.py` (e.g., `DailyEnrollmentTrendDTO`, `CourseRetentionDTO`, `InstructorPerformanceDTO`, `RetenionFunnelDTO`, `InstructorValueDTO`, `ScheduleUtilizationDTO`, `FlightRiskDTO`)
*   **Implementation Rule:** Every DTO must inherit from `pydantic.BaseModel` and perfectly match the aliases selected in the raw SQL `text()` queries.
*   **Create [schemas/__init__.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/academics/schemas/__init__.py)** to selectively forward-export these DTOs.

## Phase 3 & 4: Data Layer Split (Repositories)
*   **Create `app/modules/analytics/repositories/` directory.**
*   **Decompose [analytics_repository.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/analytics/analytics_repository.py) (391 lines) into 4 distinct repositories:**
    *   `financial_repository.py`
    *   `academic_repository.py`
    *   `competition_repository.py`
    *   `bi_repository.py`
*   **Contract Update:** Update the raw `[dict(r._mapping) for r in rows]` returns. The repositories should return the raw SQLAlchemy rows or maps, and the Service layer will cast them to DTOs, OR the Repositories can yield the Pydantic DTOs directly (e.g. `return [RevenueTrendDTO(**r._mapping) for r in rows]`). We will implement the DTO casting inside the Repositories for maximum boundary safety.

## Phase 5: Business Logic Split (Services)
*   **Create `app/modules/analytics/services/` directory.**
*   **Decompose [analytics_service.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/analytics/analytics_service.py) into distinct OOP classes:**
    *   `FinancialAnalyticsService`
    *   `AcademicAnalyticsService`
    *   `CompetitionAnalyticsService`
    *   `BIAnalyticsService`
*   **Method Signatures:** Change every function from `def get_X(db) -> list[dict]:` to an instance method `def get_X(self) -> list[X_DTO]:` wrapping the DB context via `with get_session()`.

## Phase 6: Compatibility Facade
*   **Update [app/modules/analytics/__init__.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/analytics/__init__.py).**
*   **Instantiate the new service classes:**
    ```python
    from .services.financial_service import FinancialAnalyticsService
    _fin_svc = FinancialAnalyticsService()
    
    get_revenue_by_date = _fin_svc.get_revenue_by_date
    get_revenue_by_method = _fin_svc.get_revenue_by_method
    # ... map all 16 original functions
    ```
*   This mapping guarantees that [app/ui/pages/9_Reports.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/ui/pages/9_Reports.py) will not crash upon import, as the function names and locations visually match the legacy code.

## Phase 7: UI Adapter Cleanup
*   **Update [app/ui/pages/9_Reports.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/ui/pages/9_Reports.py), [app/ui/pages/5_Enrollment.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/ui/pages/5_Enrollment.py), etc.**
*   The UI relies on Pandas DataFrames constructed from `list[dict]`. Since the backend will now return `list[BaseModel]`, we must update the UI instantiation:
    *   *Legacy:* `df = pd.DataFrame(data)`
    *   *New:* `df = pd.DataFrame([d.model_dump() for d in data])`
*   Ensure any stray `.get()` calls on individual metrics in the UI are updated to attribute dot-notation.

---
**Status:** Ready to execute Phase 1 and 2 upon User approval.
