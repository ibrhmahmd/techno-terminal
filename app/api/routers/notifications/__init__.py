from fastapi import APIRouter

from .notifications_router import router as logs_router
from .templates_router import router as templates_router
from .bulk_router import router as bulk_router
from .admin_settings_router import router as admin_settings_router

router = APIRouter(prefix="/notifications", tags=["Notifications"])

router.include_router(logs_router)
router.include_router(templates_router)
router.include_router(bulk_router)
router.include_router(admin_settings_router)
