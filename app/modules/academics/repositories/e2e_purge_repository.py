"""Hard deletes of E2E test data in academics' own tables (#218). Staging only."""
from sqlalchemy import delete, or_, select
from sqlmodel import Session

from app.modules.academics.models.course_models import Course
from app.modules.academics.models.group_level_models import GroupCourseHistory, GroupLevel
from app.modules.academics.models.group_models import Group
from app.modules.academics.models.session_models import CourseSession


class AcademicsE2EPurgeRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def _ids(self, stmt) -> list[int]:
        return list(self._session.execute(stmt).scalars())

    def find_course_ids(self, prefix: str) -> list[int]:
        return self._ids(select(Course.id).where(Course.name.startswith(prefix, autoescape=True)))

    def find_group_ids(self, prefix: str, course_ids: list[int]) -> list[int]:
        # groups.course_id is RESTRICT, so every group of a seed course goes too
        return self._ids(select(Group.id).where(or_(
            Group.name.startswith(prefix, autoescape=True), Group.course_id.in_(course_ids),
        )))

    def find_session_ids(self, group_ids: list[int]) -> list[int]:
        return self._ids(select(CourseSession.id).where(CourseSession.group_id.in_(group_ids)))

    def find_level_ids(self, group_ids: list[int], course_ids: list[int]) -> list[int]:
        return self._ids(select(GroupLevel.id).where(or_(
            GroupLevel.group_id.in_(group_ids), GroupLevel.course_id.in_(course_ids),
        )))

    def delete_sessions(self, group_ids: list[int]) -> int:
        return self._session.execute(
            delete(CourseSession).where(CourseSession.group_id.in_(group_ids))
        ).rowcount

    def delete_course_history(self, group_ids: list[int], course_ids: list[int]) -> int:
        return self._session.execute(delete(GroupCourseHistory).where(or_(
            GroupCourseHistory.group_id.in_(group_ids), GroupCourseHistory.course_id.in_(course_ids),
        ))).rowcount

    def delete_levels(self, level_ids: list[int]) -> int:
        return self._session.execute(delete(GroupLevel).where(GroupLevel.id.in_(level_ids))).rowcount

    def delete_groups(self, group_ids: list[int]) -> int:
        return self._session.execute(delete(Group).where(Group.id.in_(group_ids))).rowcount

    def delete_courses(self, course_ids: list[int]) -> int:
        return self._session.execute(delete(Course).where(Course.id.in_(course_ids))).rowcount
