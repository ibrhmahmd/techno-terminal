"""
app/shared/base_repository.py
─────────────────────────────
Structural (Protocol-based) typing interface for all repository modules.

Purpose:
  1. Provides a common typed contract for CRUD operations.
  2. Enables API-layer dependency injection and mock stubs in tests.
  3. Does NOT require any repo to inherit or change — Python's structural
     subtyping (duck typing) means any module satisfying the signatures
     is automatically compatible.

Usage in API tests (future):
  class FakeEnrollmentRepo:
      def get_by_id(self, session, id): return MOCK_DATA[id]
      def create(self, session, entity): return entity
      def list_all(self, session): return list(MOCK_DATA.values())

  # mypy / pyright verifies FakeEnrollmentRepo satisfies RepositoryProtocol[Enrollment]
"""
from typing import Protocol, TypeVar, Sequence, runtime_checkable
from sqlmodel import Session

T = TypeVar("T")


@runtime_checkable
class RepositoryProtocol(Protocol[T]):
    """
    The minimum CRUD contract every repository must satisfy.
    All three methods accept a SQLModel Session as the first argument.

    Repos satisfy this Protocol structurally — no inheritance required.
    A module that defines module-level functions (not class methods) does NOT
    automatically satisfy the Protocol's instance-method signatures; the aliases
    added to each repo are standalone functions that match the same signature.
    """

    def get_by_id(self, session: Session, id: int) -> T | None:
        """Fetch a single entity by primary key. Returns None if not found."""
        ...

    def create(self, session: Session, entity: T) -> T:
        """Persist a new entity and return it with the DB-assigned ID."""
        ...

    def list_all(self, session: Session) -> Sequence[T]:
        """Return all entities. Individual repos may add filter arguments."""
        ...
