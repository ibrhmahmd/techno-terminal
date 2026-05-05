"""
app/modules/academics/group/directory/service.py
──────────────────────────────────────
Service class for Group Directory business logic.
"""
from datetime import date
from app.db.connection import get_session
from app.modules.academics.models import Group
from app.modules.academics.group.core.schemas import EnrichedGroupDTO
from app.modules.academics.group.directory.schemas import GroupedItemDTO, GroupedGroupsResult
import app.modules.academics.group.directory.repository as repo


class GroupDirectoryService:
    def get_all_active_groups(self, include_inactive: bool = False) -> list[Group]:
        with get_session() as session:
            return list(repo.list_all_active_groups(session, include_inactive))

    def get_all_active_groups_enriched(self) -> list[EnrichedGroupDTO]:
        """Returns groups with instructor_name and course_name joined for display."""
        with get_session() as session:
            return repo.get_enriched_groups(session)

    def get_todays_groups_enriched(self) -> list[EnrichedGroupDTO]:
        """Returns active groups that have at least one session scheduled for today."""
        with get_session() as session:
            return repo.get_enriched_groups_by_date(session, date.today().isoformat())

    def get_enriched_group_by_id(self, group_id: int) -> EnrichedGroupDTO | None:
        with get_session() as session:
            return repo.get_enriched_group_by_id(session, group_id)

    def search_groups(
        self,
        query: str,
        status: str | None = None,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[list[Group], int]:
        """Search groups by name with optional status filter."""
        with get_session() as session:
            results, total = repo.search_groups(session, query, status, skip, limit)
            return list(results), total

    def get_groups_by_type(
        self,
        group_type: str,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[Group], int]:
        """Get groups filtered by type."""
        with get_session() as session:
            results, total = repo.get_groups_by_type(session, group_type, status, skip, limit)
            return list(results), total


    def get_all_archived_groups(self, include_inactive: bool = False) -> list[Group]:
        """Get all archived groups."""
        with get_session() as session:
            return list(repo.get_all_archived_groups(session, include_inactive))

    def get_groups_by_course(
        self,
        course_id: int,
        include_inactive: bool = False,
        level_number: int | None = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[Group], int]:
        """Get all groups for a specific course."""
        with get_session() as session:
            results, total = repo.get_groups_by_course(
                session, course_id, include_inactive, level_number, skip, limit
            )
            return list(results), total

    def get_groups_grouped(
        self,
        group_by: str,
        skip: int = 0,
        limit: int = 50,
        search: str | None = None
    ) -> GroupedGroupsResult:
        """
        Get groups grouped by a specific field with pagination.
        """
        # Validate group_by field
        valid_fields = {"day", "course", "instructor", "status"}
        if group_by not in valid_fields:
            raise ValueError(f"Invalid group_by field. Must be one of: {valid_fields}")
        
        with get_session() as session:
            # Get all active groups with enrichment
            groups = repo.get_enriched_groups(session)
            
            # Apply search filter if provided
            if search:
                search_lower = search.lower()
                groups = [
                    g for g in groups
                    if search_lower in g.group_name.lower()
                    or search_lower in (g.course_name or "").lower()
                    or search_lower in (g.instructor_name or "").lower()
                ]
            
            # Group the results
            grouped_data: dict[str, dict] = {}
            
            for group in groups:
                # Determine the key based on group_by field
                if group_by == "day":
                    key = (group.default_day or "unspecified").lower()
                    label = group.default_day or "Unspecified"
                elif group_by == "course":
                    key = str(group.course_id)
                    label = group.course_name or "Unknown Course"
                elif group_by == "instructor":
                    key = str(group.instructor_id) if group.instructor_id else "none"
                    label = group.instructor_name or "No Instructor"
                elif group_by == "status":
                    key = group.status.lower()
                    label = group.status.title()
                else:
                    continue
                
                if key not in grouped_data:
                    grouped_data[key] = {
                        "key": key,
                        "label": label,
                        "groups": []
                    }
                grouped_data[key]["groups"].append(group)
            
            # Convert to DTOs and apply pagination
            all_items = [
                GroupedItemDTO(
                    key=item["key"],
                    label=item["label"],
                    count=len(item["groups"]),
                    groups=item["groups"]
                )
                for item in grouped_data.values()
            ]
            
            # Sort by label for consistent ordering
            all_items.sort(key=lambda x: x.label)
            
            # Apply pagination at the group level
            total_groups = len(all_items)
            paginated_items = all_items[skip : skip + limit]
            
            return GroupedGroupsResult(
                groups=paginated_items,
                total=total_groups,
                group_by=group_by
            )
