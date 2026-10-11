"""Enrollments module ports (ADR-0007)."""

from typing import Optional, Protocol


class EnrollmentNotifier(Protocol):
    """Port for enrollment notifications, called after the use case commits.

    Implementations must not raise; the caller logs and swallows failures.
    """

    def enrollment_created(
        self, *, student_id: int, enrollment_id: int, group_id: int, level_number: int
    ) -> None: ...

    def enrollment_updated(
        self,
        *,
        student_id: int,
        enrollment_id: int,
        group_id: int,
        changes_summary: str,
        performed_by: Optional[int],
    ) -> None: ...

    def enrollment_transferred(
        self,
        *,
        student_id: int,
        from_enrollment_id: int,
        to_enrollment_id: int,
        from_group_id: int,
        to_group_id: int,
        transferred_by: Optional[int],
    ) -> None: ...

    def enrollment_dropped(
        self,
        *,
        student_id: int,
        enrollment_id: int,
        group_id: int,
        reason: Optional[str],
        dropped_by: Optional[int],
    ) -> None: ...
