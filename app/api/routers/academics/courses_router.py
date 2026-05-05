"""
app/api/routers/academics/courses.py
────────────────────────────────────
Courses router.

Endpoints for course management.
"""
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.schemas.common import ApiResponse, PaginatedResponse
from app.api.schemas.academics import CoursePublic, GroupListItem
from app.api.dependencies import require_admin, require_any, get_course_service, get_group_directory_service
from app.modules.academics.course.schemas import AddNewCourseInput, UpdateCourseDTO, CourseStatsDTO
from app.modules.auth import User
from app.modules.academics.course.service import CourseService
from app.modules.academics.group.directory.service import GroupDirectoryService

router = APIRouter(tags=["Academics — Courses"])

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
    results = svc.list_active_courses()
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


# get course stats (must be before /{course_id})
@router.get(
    "/academics/courses/{course_id}/stats",
    response_model=ApiResponse[CourseStatsDTO],
    summary="Get course statistics",
)
def get_course_stats(
    course_id: int,
    _user: User = Depends(require_any),
    svc: CourseService = Depends(get_course_service),
):
    stats = svc.get_course_stats(course_id)
    if not stats:
        raise HTTPException(status_code=404, detail=f"Course {course_id} not found")
    return ApiResponse(data=stats)


# get groups for a course (must be before /{course_id})
@router.get(
    "/academics/courses/{course_id}/groups",
    response_model=PaginatedResponse[GroupListItem],
    summary="Get groups for a course",
)
def get_course_groups(
    course_id: int,
    include_inactive: bool = Query(False),
    level_number: int | None = Query(None, gt=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _user: User = Depends(require_any),
    group_svc: GroupDirectoryService = Depends(get_group_directory_service),
):
    from app.api.schemas.academics.group import GroupListItem
    results, total = group_svc.get_groups_by_course(
        course_id=course_id,
        include_inactive=include_inactive,
        level_number=level_number,
        skip=skip,
        limit=limit,
    )
    return PaginatedResponse(
        data=[GroupListItem.model_validate(g) for g in results],
        total=total,
        skip=skip,
        limit=limit,
    )


# get a single course by ID
@router.get(
    "/academics/courses/{course_id}",
    response_model=ApiResponse[CoursePublic],
    summary="Get a course by ID",
)
def get_course(
    course_id: int,
    _user: User = Depends(require_any),
    svc: CourseService = Depends(get_course_service),
):
    course = svc.get_course_by_id(course_id)
    return ApiResponse(data=CoursePublic.model_validate(course))


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


# soft delete (archive) a course
@router.delete(
    "/academics/courses/{course_id}",
    response_model=ApiResponse[CoursePublic],
    summary="Soft delete (archive) a course",
)
def delete_course(
    course_id: int,
    _user: User = Depends(require_admin),
    svc: CourseService = Depends(get_course_service),
):
    course = svc.update_course(course_id, UpdateCourseDTO(is_active=False))
    return ApiResponse(
        data=CoursePublic.model_validate(course),
        message="Course archived successfully.",
    )
