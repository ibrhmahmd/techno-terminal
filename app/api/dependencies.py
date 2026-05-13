"""
app/api/dependencies.py
────────────────────────
FastAPI Dependency Injection bindings.

Two layers:
  1. Core deps (get_db, get_current_user) — infrastructure
  2. Role guards (require_admin, require_instructor, etc.) — authorization
  3. Service factories — pragmatic bridge (Option A) to existing service classes

Role guard pattern:
    require_admin      → UserRole.admin, UserRole.manager
    require_instructor → UserRole.instructor, UserRole.admin, UserRole.manager
    require_any        → any authenticated user (alias for get_current_user)

Service factory pattern:
    Every service is instantiated fresh per request (stateless).
    This is safe because all state lives in the DB session.
    Session injection refactor is deferred — see docs/planning/BACKLOG.md §C1.
"""
import logging
from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.db.connection import get_session
from app.core.supabase_clients import get_supabase_anon, get_supabase_admin
from app.modules.auth import get_user_by_supabase_uid
from app.modules.auth import User
from app.modules.auth.constants import UserRole

logger = logging.getLogger(__name__)

# ── Infrastructure ─────────────────────────────────────────────────────────────

http_bearer = HTTPBearer(auto_error=True)


def get_db() -> Generator[Session, None, None]:
    """Yields a database session that automatically closes when the request finishes."""
    with get_session() as session:
        yield session
        session.commit()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
) -> User:
    """
    Validates the Bearer JWT with Supabase and returns the mapped local User.
    Raises 401 for missing/invalid tokens, 403 for inactive accounts.
    """
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials with Supabase",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        supabase = get_supabase_anon()
        auth_response = supabase.auth.get_user(token)
        if not auth_response or not auth_response.user:
            raise credentials_exception
        supabase_uid = auth_response.user.id

    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Supabase JWT validation failed: %s", type(e).__name__)
        raise credentials_exception

    user = get_user_by_supabase_uid(supabase_uid)
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user


# ── Role Guards ────────────────────────────────────────────────────────────────

def _require_roles(*roles: UserRole):
    """
    Factory that returns a FastAPI dependency enforcing one of the given roles.

    Usage:
        @router.post("/something")
        def do_thing(_user: User = Depends(require_admin)):
            ...
    """
    role_values = {r.value for r in roles}

    async def _guard(user: User = Depends(get_current_user)) -> User:
        if user.role not in role_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {sorted(role_values)}",
            )
        return user

    return _guard


# Convenience shortcuts — use these directly in router Depends() calls.
require_admin = _require_roles(
    UserRole.ADMIN,
    UserRole.SYSTEM_ADMIN,
)
# Any valid, active, authenticated user.
require_any = get_current_user


from app.modules.auth.services.auth_service import AuthService

# ── CRM Service Factories ────────────────────────────────────
from app.modules.crm.repositories.unit_of_work import StudentUnitOfWork
from app.modules.crm.services import (
    StudentCrudService,
    ParentCrudService,
    SearchService,
    StudentProfileService,
    StudentActivityService,
)

from app.modules.academics.course.service import CourseService
from app.modules.academics.group.core.service import GroupCoreService
from app.modules.academics.group.directory.service import GroupDirectoryService
from app.modules.academics.group.level.service import GroupLevelService
from app.modules.academics.group.competition.service import GroupCompetitionService
from app.modules.academics.session.service import SessionService
from app.modules.academics.group.analytics.service import GroupAnalyticsService

from app.modules.enrollments.services.enrollment_service import EnrollmentService
from app.modules.enrollments.services.enrollment_migration_service import EnrollmentMigrationService

def get_auth_service() -> AuthService:
    return AuthService()


def get_student_crud_service(
    session: Session = Depends(get_db),
) -> StudentCrudService:
    """Returns a StudentCrudService with a fresh UnitOfWork and activity logging."""
    uow = StudentUnitOfWork(session=session)
    activity_svc = StudentActivityService(uow)
    return StudentCrudService(uow, activity_svc=activity_svc)

def get_student_search_service(
    session: Session = Depends(get_db),
) -> SearchService:
    """Returns a SearchService with a fresh UnitOfWork."""
    uow = StudentUnitOfWork(session=session)
    return SearchService(uow)

def get_student_profile_service(
    session: Session = Depends(get_db),
) -> StudentProfileService:
    """Returns a StudentProfileService with a fresh UnitOfWork."""
    uow = StudentUnitOfWork(session=session)
    return StudentProfileService(uow)

def get_student_activity_service(
    session: Session = Depends(get_db),
) -> StudentActivityService:
    """Returns a StudentActivityService with a fresh UnitOfWork."""
    uow = StudentUnitOfWork(session=session)
    return StudentActivityService(uow)

def get_parent_crud_service(
    session: Session = Depends(get_db),
) -> ParentCrudService:
    """Returns a ParentCrudService with a fresh UnitOfWork."""
    uow = StudentUnitOfWork(session=session)
    return ParentCrudService(uow)


def get_course_service() -> CourseService:
    return CourseService()


def get_group_service() -> GroupCoreService:
    """Returns a fresh GroupCoreService instance per request."""
    return GroupCoreService()


def get_group_directory_service() -> GroupDirectoryService:
    """Returns a fresh GroupDirectoryService instance per request."""
    return GroupDirectoryService()


def get_group_level_service() -> GroupLevelService:
    """Returns a fresh GroupLevelService instance per request."""
    return GroupLevelService()


def get_group_competition_service() -> GroupCompetitionService:
    """Returns a fresh GroupCompetitionService instance per request (stateless)."""
    return GroupCompetitionService()


def get_session_service() -> SessionService:
    return SessionService()


def get_group_analytics_service() -> GroupAnalyticsService:
    """Returns a fresh GroupAnalyticsService instance per request."""
    return GroupAnalyticsService()


def get_notification_service() -> Generator["NotificationService", None, None]:
    from app.modules.notifications.repositories.notification_repository import NotificationRepository
    from app.modules.notifications.services.notification_service import NotificationService
    from app.db.connection import get_session

    with get_session() as session:
        yield NotificationService(NotificationRepository(session))

def get_enrollment_service(
    session: Session = Depends(get_db),
    notification_svc: "NotificationService" = Depends(get_notification_service),
) -> EnrollmentService:
    """Returns an EnrollmentService with activity logging and notifications."""
    uow = StudentUnitOfWork(session=session)
    activity_svc = StudentActivityService(uow)
    return EnrollmentService(
        activity_svc=activity_svc,
            notification_svc=notification_svc
        )


def get_enrollment_migration_service(
    notification_svc: "NotificationService" = Depends(get_notification_service),
) -> EnrollmentMigrationService:
    """Returns an EnrollmentMigrationService with notification support."""
    return EnrollmentMigrationService(notification_svc=notification_svc)


# ── Finance Service Factories (SOLID Refactored) ──────────────────────────────

from app.modules.finance.repositories.unit_of_work import FinanceUnitOfWork
from app.modules.finance.services.receipt_service import ReceiptService
from app.modules.finance.services.refund_service import RefundService
from app.modules.finance.services.balance_service import BalanceService
from app.modules.finance.services.reporting_service import ReportingService


def get_receipt_service(
    session: Session = Depends(get_db),
    notification_svc: "NotificationService" = Depends(get_notification_service),
) -> ReceiptService:
    """Returns a ReceiptService with activity logging and notifications."""
    finance_uow = FinanceUnitOfWork(session=session)
    crm_uow = StudentUnitOfWork(session=session)
    activity_svc = StudentActivityService(crm_uow)
    return ReceiptService(
        finance_uow, 
        activity_svc=activity_svc,
        notification_svc=notification_svc
    )


def get_refund_service(
    session: Session = Depends(get_db),
) -> RefundService:
    """Returns a RefundService with activity logging."""
    finance_uow = FinanceUnitOfWork(session=session)
    crm_uow = StudentUnitOfWork(session=session)
    activity_svc = StudentActivityService(crm_uow)
    return RefundService(finance_uow, activity_svc=activity_svc)


def get_balance_service(
    session: Session = Depends(get_db),
) -> BalanceService:
    """Returns a BalanceService with a fresh UnitOfWork."""
    uow = FinanceUnitOfWork(session=session)
    return BalanceService(uow)


def get_reporting_service(
    session: Session = Depends(get_db),
) -> ReportingService:
    """Returns a ReportingService with a fresh UnitOfWork."""
    uow = FinanceUnitOfWork(session=session)
    return ReportingService(uow)


def get_student_payment_service(
    session: Session = Depends(get_db),
) -> "StudentPaymentService":
    """Returns a StudentPaymentService with a fresh UnitOfWork."""
    from app.modules.finance.services.student_payment_service import StudentPaymentService
    uow = FinanceUnitOfWork(session=session)
    return StudentPaymentService(uow)


# ── Additional Service Factories (Standardizing DI pattern) ─────────────────────

# Attendance service
from app.modules.attendance.services.attendance_service import AttendanceService

def get_attendance_service() -> AttendanceService:
    """Returns a fresh AttendanceService instance per request."""
    return AttendanceService()


# Competition services
from app.modules.competitions.services.competition_service import CompetitionService
from app.modules.competitions.services.team_service import TeamService

def get_competition_service() -> CompetitionService:
    """Returns a fresh CompetitionService instance per request."""
    return CompetitionService()

def get_team_service() -> TeamService:
    """Returns a fresh TeamService instance per request."""
    return TeamService()



# HR SOLID services
from app.modules.hr import EmployeeCrudService, StaffAccountService, HRUnitOfWork


def get_employee_crud_service(
    session: Session = Depends(get_db),
) -> EmployeeCrudService:
    """Returns EmployeeCrudService with fresh Unit of Work per request."""
    uow = HRUnitOfWork(session)
    return EmployeeCrudService(uow)


def get_staff_account_service(
    session: Session = Depends(get_db),
    supabase_client = Depends(get_supabase_admin),
) -> StaffAccountService:
    """Returns StaffAccountService with fresh Unit of Work per request."""
    uow = HRUnitOfWork(session)
    return StaffAccountService(uow, supabase_client)


# Analytics services
from app.modules.analytics.services.academic_service import AcademicAnalyticsService
from app.modules.analytics.services.financial_service import FinancialAnalyticsService
from app.modules.analytics.services.bi_service import BIAnalyticsService
from app.modules.analytics.services.dashboard_service import DashboardService

def get_academic_analytics_service() -> AcademicAnalyticsService:
    """Returns a fresh AcademicAnalyticsService instance per request."""
    return AcademicAnalyticsService()


def get_dashboard_service() -> DashboardService:
    """Returns a fresh DashboardService instance per request."""
    return DashboardService()


def get_financial_analytics_service() -> FinancialAnalyticsService:
    """Returns a fresh FinancialAnalyticsService instance per request."""
    return FinancialAnalyticsService()


def get_bi_analytics_service() -> BIAnalyticsService:
    """Returns a fresh BIAnalyticsService instance per request."""
    return BIAnalyticsService()


# Competition Analytics service
from app.modules.analytics.services.competition_service import CompetitionAnalyticsService

def get_competition_analytics_service() -> CompetitionAnalyticsService:
    """Returns a fresh CompetitionAnalyticsService instance per request."""
    return CompetitionAnalyticsService()



# Group Analytics service
def get_group_analytics_service() -> GroupAnalyticsService:
    """Returns a fresh GroupAnalyticsService instance per request."""
    return GroupAnalyticsService()
