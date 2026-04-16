# New SOLID services only - no legacy exports
from .student_crud_service import StudentCrudService
from .parent_crud_service import ParentCrudService
from .search_service import SearchService
from .student_profile_service import StudentProfileService
from .activity_service import StudentActivityService

__all__ = [
    "StudentCrudService",
    "ParentCrudService",
    "SearchService",
    "StudentProfileService",
    "StudentActivityService",
]
