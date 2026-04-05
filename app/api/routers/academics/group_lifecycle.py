"""
app/api/routers/academics/group_lifecycle.py
───────────────────────────────────────────
Router for group lifecycle and history endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas.common import ApiResponse
from app.api.dependencies import require_any, require_admin, get_group_service, get_group_history_service, get_group_level_service
from app.modules.auth import User
from app.modules.academics.services.group_service import GroupService
from app.modules.academics.services.group_history_service import GroupHistoryService
from app.modules.academics.services.group_level_service import GroupLevelService

router = APIRouter(tags=["Academics — Group Lifecycle"])


@router.get(
    "/academics/groups/{group_id}/history",
    response_model=ApiResponse[dict],
    summary="Get full lifecycle history for a group",
)
def get_group_lifecycle_history(
    group_id: int,
    _user: User = Depends(require_any),
    svc: GroupHistoryService = Depends(get_group_history_service),
):
    """
    Returns complete lifecycle data for a group including:
    - Levels timeline (chronological)
    - Course assignment history
    - Enrollment transitions
    """
    history = svc.get_full_lifecycle(group_id)
    if not history:
        raise HTTPException(status_code=404, detail=f"Group {group_id} not found")
    return ApiResponse(data=history)


@router.get(
    "/academics/groups/{group_id}/levels",
    response_model=ApiResponse[list[dict]],
    summary="List all level snapshots for a group",
)
def list_group_levels(
    group_id: int,
    status: str | None = None,
    include_inactive: bool = False,
    _user: User = Depends(require_any),
    svc: GroupLevelService = Depends(get_group_level_service),
):
    """
    Returns all level snapshots for a group.
    Query params:
    - status: Filter by status (active, completed, cancelled)
    - include_inactive: Include inactive levels if True
    """
    levels = svc.get_level_history(group_id)
    
    # Apply filters
    if status:
        levels = [l for l in levels if l.status == status]
    elif not include_inactive:
        levels = [l for l in levels if l.status == "active"]
    
    return ApiResponse(data=levels)


@router.get(
    "/academics/groups/{group_id}/levels/{level_number}",
    response_model=ApiResponse[dict],
    summary="Get specific level details",
)
def get_group_level(
    group_id: int,
    level_number: int,
    _user: User = Depends(require_any),
    svc: GroupLevelService = Depends(get_group_level_service),
):
    """Returns details for a specific level snapshot."""
    from app.db.connection import get_session
    from app.modules.academics.repositories import get_group_level_by_number
    from app.modules.academics.models import Course
    from app.modules.hr.hr_models import Employee
    
    with get_session() as session:
        level = get_group_level_by_number(session, group_id, level_number)
        if not level:
            raise HTTPException(status_code=404, detail=f"Level {level_number} not found for group {group_id}")
        
        course = session.get(Course, level.course_id)
        instructor = session.get(Employee, level.instructor_id) if level.instructor_id else None
        
        return ApiResponse(data={
            "id": level.id,
            "group_id": level.group_id,
            "level_number": level.level_number,
            "course_id": level.course_id,
            "course_name": course.name if course else None,
            "instructor_id": level.instructor_id,
            "instructor_name": instructor.full_name if instructor else None,
            "sessions_planned": level.sessions_planned,
            "price_override": float(level.price_override) if level.price_override else None,
            "status": level.status,
            "effective_from": level.effective_from,
            "effective_to": level.effective_to,
            "created_at": level.created_at,
        })


@router.post(
    "/academics/groups/{group_id}/levels/{level_number}/complete",
    response_model=ApiResponse[dict],
    summary="Complete a level and progress to next",
)
def complete_group_level(
    group_id: int,
    level_number: int,
    _user: User = Depends(require_admin),
    svc: GroupLevelService = Depends(get_group_level_service),
):
    """
    Mark a level as completed and create next level snapshot.
    Requires admin privileges.
    """
    try:
        completed, new_level = svc.complete_current_level(group_id)
        return ApiResponse(
            data={
                "completed_level": {
                    "id": completed.id,
                    "level_number": completed.level_number,
                    "status": completed.status,
                },
                "new_level": {
                    "id": new_level.id,
                    "level_number": new_level.level_number,
                    "status": new_level.status,
                },
            },
            message=f"Group progressed from level {completed.level_number} to level {new_level.level_number}",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/academics/groups/{group_id}/courses/history",
    response_model=ApiResponse[list[dict]],
    summary="Get course assignment history",
)
def get_group_course_history(
    group_id: int,
    _user: User = Depends(require_any),
    svc: GroupHistoryService = Depends(get_group_history_service),
):
    """Returns chronological course assignment history for a group."""
    history = svc.get_course_assignments(group_id)
    return ApiResponse(data=history)


@router.get(
    "/academics/groups/{group_id}/enrollments/history",
    response_model=ApiResponse[list[dict]],
    summary="Get enrollment level transitions",
)
def get_group_enrollment_history(
    group_id: int,
    student_id: int | None = None,
    _user: User = Depends(require_any),
    svc: GroupHistoryService = Depends(get_group_history_service),
):
    """
    Returns enrollment level transitions for a group.
    Optionally filter by specific student.
    """
    transitions = svc.get_enrollment_transitions(group_id, student_id)
    return ApiResponse(data=transitions)
