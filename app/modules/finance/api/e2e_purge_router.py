"""Staging-only E2E purge endpoint (#218).

``POST /internal/e2e/purge?run_id=`` is registered only when ``APP_ENVIRONMENT=staging``
(see ``create_app``). The handler re-checks both locks before any DB access: the
environment name AND the DATABASE_URL project ref must match the staging project.
"""
from typing import Optional

import logfire
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from app.api.deps import UoW
from app.api.schemas.common import ApiResponse
from app.core.config import settings
from app.shared.exceptions import ForbiddenError
from app.db.connection import _extract_db_project_ref
from app.modules.finance.schemas.e2e_purge import E2EPurgeResultDTO
from app.modules.finance.services.e2e_purge_service import E2EPurgeService

router = APIRouter(prefix="/internal/e2e", tags=["Internal — E2E (staging only)"])


def _verify_staging_target() -> None:
    ref = settings.staging_project_ref
    if (
        settings.app_environment != "staging"
        or not ref
        or _extract_db_project_ref(settings.database_url) != ref
    ):
        logfire.error("e2e_purge_refused_wrong_target")
        raise ForbiddenError("E2E purge is only allowed on the staging environment and database")


def _verify_purge_secret(x_e2e_purge_secret: Optional[str] = Header(default=None)) -> None:
    """401 on a missing header, a wrong value or an unconfigured (empty) secret."""
    secret = settings.e2e_purge_secret
    if not secret or x_e2e_purge_secret != secret:
        logfire.error("e2e_purge_secret_rejected")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid E2E purge secret")


@router.post(
    "/purge",
    response_model=ApiResponse[E2EPurgeResultDTO],
    summary="Delete E2E test data (staging only)",
    dependencies=[Depends(_verify_staging_target), Depends(_verify_purge_secret)],  # run before the UoW opens
    responses={401: {"description": "Bad secret"}, 403: {"description": "Not the staging target"}},
)
def purge_e2e_data(
    uow: UoW,
    run_id: Optional[str] = Query(None, description="Only rows named e2e-<run_id>*"),
) -> ApiResponse[E2EPurgeResultDTO]:
    result = E2EPurgeService(uow).purge(run_id or None)
    return ApiResponse(success=True, data=result, message="E2E data purged")
