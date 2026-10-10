"""Facade lookup functions for auth module."""

from app.db.uow import unit_of_work
from app.modules.auth.models.auth_models import User
import app.modules.auth.repositories.auth_repository as repo


def lookup_user_by_supabase_uid(uid: str) -> User | None:
    """Look up a local user by Supabase UID.

    Opens a short UnitOfWork, reads via AuthRepository, and returns
    a detached user (expire_on_commit=False means the object stays usable
    after the session closes).
    """
    with unit_of_work() as uow:
        auth_repo = repo.AuthRepository(uow.session)
        user = auth_repo.get_user_by_supabase_uid(uid)
        if user:
            # Expunge to detach from session - the user object remains
            # usable because expire_on_commit=False
            uow.session.expunge(user)
        return user