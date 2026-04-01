"""
app/api/routers/academics.py
──────────────────────────────
Academics domain router — Courses, Groups, Sessions.

Prefix: /api/v1  (mounted in main.py)
Tag:    Academics

Role policy:
  READ  (GET)   → require_any
  WRITE (POST/PATCH) → require_admin

Note on schedule_group: returns (group, sessions) — we drop sessions here;
they're accessible via GET /academics/groups/{id}/sessions.
"""

from fastapi import APIRouter, Depends, Query

from app.api.schemas.common import ApiResponse, PaginatedResponse
from app.api.schemas.academics.course import CoursePublic
from app.api.schemas.academics.group import GroupPublic, GroupListItem
from app.api.schemas.academics.session import SessionPublic
from app.api.dependencies import (
    require_admin,
    require_any,
    get_course_service,
    get_group_service,
    get_session_service,
)
from app.modules.academics.schemas import (
    AddNewCourseInput,
    UpdateCourseDTO,
    ScheduleGroupInput,
    UpdateGroupDTO,
    AddExtraSessionInput,
    UpdateSessionDTO,
)
from app.modules.auth import User
from app.modules.academics.services.course_service import CourseService
from app.modules.academics.services.group_service import GroupService
from app.modules.academics.services.session_service import SessionService

router = APIRouter(tags=["Academics"])


# ── Courses ────────────────────────────────────────────────────────────────────


# list all active courses
@router.get(
    "/academics/courses",
    response_model=PaginatedResponse[CoursePublic],
    summary="List all active courses",
)
def list_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _user: User = Depends(require_any),
    svc: CourseService = Depends(get_course_service),
):
    results = svc.get_active_courses()
    page = results[skip : skip + limit]
    return PaginatedResponse(
        data=[CoursePublic.model_validate(c) for c in page],
        total=len(results),
        skip=skip,
        limit=limit,
    )


# create a new course
@router.post(
    "/academics/courses",
    response_model=ApiResponse[CoursePublic],
    status_code=201,
    summary="Create a new course",
)
def create_course(
    body: AddNewCourseInput,
    _user: User = Depends(require_admin),
    svc: CourseService = Depends(get_course_service),
):
    course = svc.add_new_course(body)
    return ApiResponse(
        data=CoursePublic.model_validate(course),
        message="Course created successfully.",
    )


# update a course
@router.patch(
    "/academics/courses/{course_id}",
    response_model=ApiResponse[CoursePublic],
    summary="Update a course",
)
def update_course(
    course_id: int,
    body: UpdateCourseDTO,
    _user: User = Depends(require_admin),
    svc: CourseService = Depends(get_course_service),
):
    course = svc.update_course(course_id, body)
    return ApiResponse(data=CoursePublic.model_validate(course))


# ── Groups ─────────────────────────────────────────────────────────────────────


# list all active groups
@router.get(
    "/academics/groups",
    response_model=PaginatedResponse[GroupListItem],
    summary="List all active groups",
)
def list_groups(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _user: User = Depends(require_any),
    svc: GroupService = Depends(get_group_service),
):
    results = svc.get_all_active_groups()
    page = results[skip : skip + limit]
    return PaginatedResponse(
        data=[GroupListItem.model_validate(g) for g in page],
        total=len(results),
        skip=skip,
        limit=limit,
    )


# get group by ID
@router.get(
    "/academics/groups/{group_id}",
    response_model=ApiResponse[GroupPublic],
    summary="Get group by ID",
)
def get_group(
    group_id: int,
    _user: User = Depends(require_any),
    svc: GroupService = Depends(get_group_service),
):
    group = svc.get_group_by_id(group_id)
    return ApiResponse(data=GroupPublic.model_validate(group))


# create a new group
@router.post(
    "/academics/groups",
    response_model=ApiResponse[GroupPublic],
    status_code=201,
    summary="Schedule a new group",
)
def create_group(
    body: ScheduleGroupInput,
    _user: User = Depends(require_admin),
    svc: GroupService = Depends(get_group_service),
):
    # schedule_group returns (group, sessions) — sessions accessible via /groups/{id}/sessions
    group, _sessions = svc.schedule_group(body)
    return ApiResponse(
        data=GroupPublic.model_validate(group),
        message="Group scheduled successfully.",
    )


# update a group
@router.patch(
    "/academics/groups/{group_id}",
    response_model=ApiResponse[GroupPublic],
    summary="Update a group",
)
def update_group(
    group_id: int,
    body: UpdateGroupDTO,
    _user: User = Depends(require_admin),
    svc: GroupService = Depends(get_group_service),
):
    group = svc.update_group(group_id, body)
    return ApiResponse(data=GroupPublic.model_validate(group))


# ── Sessions ───────────────────────────────────────────────────────────────────


# list sessions for a group (optionally filter by level)
@router.get(
    "/academics/groups/{group_id}/sessions",
    response_model=ApiResponse[list[SessionPublic]],
    summary="List sessions for a group (optionally filter by level)",
)
def list_group_sessions(
    group_id: int,
    level: int = Query(None, description="Filter to a specific level number"),
    _user: User = Depends(require_any),
    svc: SessionService = Depends(get_session_service),
):
    sessions = svc.list_group_sessions(group_id, level_number=level)
    return ApiResponse(data=[SessionPublic.model_validate(s) for s in sessions])


# add an extra session to a group
@router.post(
    "/academics/groups/{group_id}/sessions",
    response_model=ApiResponse[SessionPublic],
    status_code=201,
    summary="Add an extra session to a group",
)
def add_extra_session(
    group_id: int,
    body: AddExtraSessionInput,
    _user: User = Depends(require_admin),
    svc: SessionService = Depends(get_session_service),
):
    session = svc.add_extra_session(body)
    return ApiResponse(
        data=SessionPublic.model_validate(session),
        message="Extra session added.",
    )


# update a session (date, time, status, notes)
@router.patch(
    "/academics/sessions/{session_id}",
    response_model=ApiResponse[SessionPublic],
    summary="Update a session (date, time, status, notes)",
)
def update_session(
    session_id: int,
    body: UpdateSessionDTO,
    _user: User = Depends(require_admin),
    svc: SessionService = Depends(get_session_service),
):
    session = svc.update_session(session_id, body)
    return ApiResponse(data=SessionPublic.model_validate(session))
