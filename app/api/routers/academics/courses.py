"""
app/api/routers/academics/courses.py
────────────────────────────────────
Courses router.

Endpoints for course management.
"""
from fastapi import APIRouter, Depends, Query

from app.api.schemas.common import ApiResponse, PaginatedResponse
from app.api.schemas.academics.course import CoursePublic
from app.api.dependencies import require_admin, require_any, get_course_service
from app.modules.academics.schemas import AddNewCourseInput, UpdateCourseDTO
from app.modules.auth import User
from app.modules.academics.services.course_service import CourseService

router = APIRouter(tags=["Academics — Courses"])


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
