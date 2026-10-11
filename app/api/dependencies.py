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
from typing import Annotated, Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.db.connection import get_session
from app.db.uow import UnitOfWork, unit_of_work
from app.core.supabase_clients import get_supabase_anon, get_supabase_admin
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


def get_uow() -> Generator[UnitOfWork, None, None]:
    """Per-request UnitOfWork. Uncommitted work is rolled back on exit; never commits."""
    with unit_of_work() as uow:
        yield uow


# scope="function" ends the dependency before the response is sent, so a
# failed commit surfaces as an error response instead of a 200 already sent.
UoW = Annotated[UnitOfWork, Depends(get_uow, scope="function")]


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

    from app.modules.auth import lookup_user_by_supabase_uid

    user = lookup_user_by_supabase_uid(supabase_uid)
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
require_system_admin = _require_roles(UserRole.SYSTEM_ADMIN)
# Any valid, active, authenticated user.
require_any = get_current_user


from app.modules.auth import AuthService

# Note: CRM service factories moved to app/modules/crm/api/deps.py
# Import StudentActivityService for use by other modules' factories
from app.modules.crm import StudentActivityService

# Note: Enrollments service factories moved to app/modules/enrollments/api/deps.py

def get_notification_service() -> Generator["NotificationService", None, None]:
    from app.modules.notifications.repositories.notification_repository import NotificationRepository
    from app.modules.notifications.services.notification_service import NotificationService
    from app.db.connection import get_session

    with get_session() as session:
        yield NotificationService(NotificationRepository(session))
        session.commit()


# ── Additional Service Factories (Standardizing DI pattern) ─────────────────────

# ── Coach Read-Only Guard ─────────────────────────────────────────────────────

from app.modules.competitions.models import Team


async def require_coach_or_admin(
    team_id: int,
    current_user: User = Depends(require_any),
) -> User:
    """Allows admin or the coach of the specified team to access."""
    if current_user.is_admin:
        return current_user
    with get_session() as db:
        team = db.get(Team, team_id)
        if team and current_user.employee_id and team.coach_id == current_user.employee_id:
            return current_user
    raise HTTPException(status_code=403, detail="Access denied. Admin or team coach required.")


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



# Tasks service
def get_task_service(
    session: Session = Depends(get_db),
    notification_svc: "NotificationService" = Depends(get_notification_service),
) -> "TaskService":
    """Returns TaskService with fresh Unit of Work per request."""
    from app.modules.tasks import TaskService, TasksUnitOfWork
    uow = TasksUnitOfWork(session)
    return TaskService(uow, notification_service=notification_svc)

