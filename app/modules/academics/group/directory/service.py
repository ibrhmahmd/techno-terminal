"""
app/modules/academics/group/directory/service.py
──────────────────────────────────────
Service class for Group Directory business logic.
"""
from datetime import date
from app.db.connection import get_session
from app.modules.academics.constants import DAY_ORDER
from app.modules.academics.group.core.schemas import EnrichedGroupDTO
from app.modules.academics.group.directory.schemas import (
    GroupedItemDTO,
    GroupedGroupsResult,
    GroupFilterDTO,
    GroupFilterResultDTO,
)
import app.modules.academics.group.directory.repository as repo


class GroupDirectoryService:
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

            # Sort by Arabic/Islamic week order (Friday=0 … Thursday=6, Unspecified=99)
            all_items.sort(key=lambda x: DAY_ORDER.get(x.label, 99))

            # Apply pagination at the group level
            total_groups = len(all_items)
            paginated_items = all_items[skip : skip + limit]

            return GroupedGroupsResult(
                groups=paginated_items,
                total=total_groups,
                group_by=group_by
            )

    def filter_groups(self, filters: GroupFilterDTO) -> GroupFilterResultDTO:
        """Filter groups by multiple criteria with pagination.

        Delegates to repository for raw SQL execution. Day normalization
        (abbreviation → full name) must be done by the caller (router).
        """
        with get_session() as session:
            rows, total = repo.filter_groups_query(session, filters)
            return GroupFilterResultDTO(
                groups=rows,
                total=total,
                skip=filters.skip,
                limit=filters.limit,
            )
