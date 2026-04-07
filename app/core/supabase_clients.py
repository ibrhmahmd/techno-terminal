"""
Lazy Supabase client factories. Avoid creating the admin client at import time
so modules like hr_service can be imported without SUPABASE_SERVICE_ROLE_KEY set.
"""
from functools import lru_cache
from supabase import Client, create_client

from app.core.config import settings


@lru_cache(maxsize=1)
def get_supabase_anon() -> Client:
    return create_client(settings.supabase_url, settings.supabase_anon_key)


def get_supabase_admin() -> Client:
    """
    Service-role client for admin APIs (create user, password reset).
    Not cached: allows tests to swap env; callers typically use once per request.
    """
    key = settings.supabase_service_role_key
    if not key:
        raise RuntimeError(
            "SUPABASE_SERVICE_ROLE_KEY is not set. Required for admin Supabase operations "
            "(staff provisioning, password reset, seeding)."
        )
    return create_client(settings.supabase_url, key)
