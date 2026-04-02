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
from app.core.supabase_clients import get_supabase_anon
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


# ── Service Factories (Pragmatic Bridge) ───────────────────────────────────────
# Each factory instantiates a fresh, stateless service per request.
# See BACKLOG.md §C1 for the deferred Session Injection refactor.

from app.modules.auth.services.auth_service import AuthService
from app.modules.crm.services.student_service import StudentService
from app.modules.crm.services.parent_service import ParentService
from app.modules.academics.services.course_service import CourseService
from app.modules.academics.services.group_service import GroupService
from app.modules.academics.services.session_service import SessionService
from app.modules.enrollments.services.enrollment_service import EnrollmentService
import app.modules.finance as finance_module  # flat module — free functions, not a class

def get_auth_service() -> AuthService:
    return AuthService()


def get_student_service() -> StudentService:
    return StudentService()


def get_parent_service() -> ParentService:
    return ParentService()


def get_course_service() -> CourseService:
    return CourseService()


def get_group_service() -> GroupService:
    return GroupService()


def get_session_service() -> SessionService:
    return SessionService()


def get_enrollment_service() -> EnrollmentService:
    return EnrollmentService()


def get_finance_module():
    """
    Finance is a flat module (free functions), not a class.
    Returns the module itself so routers can call finance_module.create_receipt_with_charge_lines(...).
    Will be replaced with a FinanceService class in the SOLID refactor (BACKLOG §C2).
    """
    return finance_module


# ── Additional Service Factories (Standardizing DI pattern) ─────────────────────

# Attendance service
from app.modules.attendance.attendance_service import AttendanceService

def get_attendance_service() -> AttendanceService:
    """Returns a fresh AttendanceService instance per request."""
    return AttendanceService()


# Competition services
from app.modules.competitions.competition_service import CompetitionService
from app.modules.competitions.team_service import TeamService

def get_competition_service() -> CompetitionService:
    """Returns a fresh CompetitionService instance per request."""
    return CompetitionService()

def get_team_service() -> TeamService:
    """Returns a fresh TeamService instance per request."""
    return TeamService()



# HR service wrapper (flat module pattern)
def get_hr_service():
    """
    HR is a flat module (free functions).
    Returns the module so routers can call hr.list_all_employees().
    Will be replaced with HRService class in SOLID refactor.
    """
    import app.modules.hr.hr_service as hr_service_module
    return hr_service_module


# Analytics services
from app.modules.analytics.services.academic_service import AcademicAnalyticsService
from app.modules.analytics.services.financial_service import FinancialAnalyticsService
from app.modules.analytics.services.bi_service import BIAnalyticsService

def get_academic_analytics_service() -> AcademicAnalyticsService:
    """Returns a fresh AcademicAnalyticsService instance per request."""
    return AcademicAnalyticsService()


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
