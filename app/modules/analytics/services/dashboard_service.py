"""
app/modules/analytics/services/dashboard_service.py
───────────────────────────────────────────────────
Domain service for dashboard analytics.

Orchestrates the 4-query repository pattern to build the daily overview
response with lookup tables and nested session/attendance data.
"""

from datetime import date, datetime
from app.db.connection import get_session
from sqlalchemy import text

from app.modules.analytics.repositories import dashboard_repository as repo
from app.modules.analytics.schemas.dashboard_schemas import (
    DashboardDailyOverviewDTO,
    DashboardSummaryDTO,
    ScheduledGroupDTO,
    CurrentLevelDTO,
    TodaySessionDTO,
    SessionWithAttendanceDTO,
    AttendanceRecordDTO,
)


class DashboardService:
    """
    Service handling the daily dashboard overview API.
    
    Implements the lookup table pattern and 4-query strategy
    as specified in the Dashboard API Requirements.
    """

    def get_daily_overview(
        self, 
        target_date: date, 
        include_attendance: bool = True
    ) -> DashboardDailyOverviewDTO:
        """
        Get daily dashboard overview for the specified date.
        
        Args:
            target_date: The date to query (YYYY-MM-DD)
            include_attendance: Whether to include full attendance grid data
        
        Returns:
            DashboardDailyOverviewDTO with lookup tables and scheduled groups
        """
        with get_session() as db:
            # Query 1: Get groups with sessions on target date
            groups_with_sessions = repo.get_groups_with_sessions_on_date(db, target_date)
            
            if not groups_with_sessions:
                return self._build_empty_response(target_date)
            
            # Extract unique group IDs
            group_ids = list(set(session_info.group_id for session_info in groups_with_sessions))
            
            # Build today session mapping
            today_session_by_group: dict[int, TodaySessionDTO] = {}
            for session_info in groups_with_sessions:
                group_id = session_info.group_id
                if group_id not in today_session_by_group:
                    today_session_by_group[group_id] = TodaySessionDTO(
                        session_id=session_info.session_id,
                        date=session_info.session_date,
                        time_start=session_info.start_time or '',
                        time_end=session_info.end_time or '',
                        status=session_info.status,
                    )
            
            # Query 2: Get group metadata and instructors
            metadata_result = repo.get_group_metadata(db, group_ids)
            
            # Build lookup tables
            groups_lookup = {g.id: g for g in metadata_result.groups}
            instructors_lookup = {inst.id: inst for inst in metadata_result.instructors}
            
            # Build level mapping for Query 3
            group_level_map = {g.id: g.current_level for g in metadata_result.groups}
            
            # Query 3: Get all sessions for current levels
            all_level_sessions = repo.get_sessions_for_levels(db, group_level_map)
            
            # Get all session IDs
            session_ids = [s.session_id for s in all_level_sessions]
            
            # Build session_id -> group_id mapping
            session_to_group: dict[int, int] = {
                session_info.session_id: session_info.group_id 
                for session_info in groups_with_sessions
            }
            
            # Fetch remaining group mappings for historical sessions
            if session_ids:
                all_ids = set(session_ids)
                mapped_ids = set(session_to_group.keys())
                unmapped = list(all_ids - mapped_ids)
                
                if unmapped:
                    ids_tuple = tuple(unmapped) if len(unmapped) > 1 else (unmapped[0],)
                    stmt = text("SELECT id, group_id FROM sessions WHERE id IN :session_ids")
                    result = db.execute(stmt, {"session_ids": ids_tuple}).all()
                    for row in result:
                        session_to_group[row.id] = row.group_id
            
            # Query 4: Get attendance if requested
            attendance_by_session: dict[int, list[AttendanceRecordDTO]] = {}
            if include_attendance and session_ids:
                attendance_list = repo.get_attendance_for_sessions(db, session_ids)
                # Group attendance by session_id - need to query session_id since DTO doesn't have it
                # Re-query to get the mapping
                if attendance_list:
                    # Get session_id for each attendance record from the query result
                    # The attendance records don't include session_id, so we need to fetch it
                    stmt = text("""
                        SELECT ar.id, ar.session_id, ar.student_id 
                        FROM attendance ar 
                        WHERE ar.session_id IN :session_ids
                    """)
                    ids_tuple = tuple(session_ids) if len(session_ids) > 1 else (session_ids[0],)
                    att_result = db.execute(stmt, {"session_ids": ids_tuple}).all()
                    
                    # Map student_id -> session_id
                    student_to_session: dict[int, int] = {}
                    for row in att_result:
                        student_to_session[row.student_id] = row.session_id
                    
                    # Build attendance_by_session
                    for record in attendance_list:
                        session_id = student_to_session.get(record.student_id)
                        if session_id:
                            if session_id not in attendance_by_session:
                                attendance_by_session[session_id] = []
                            attendance_by_session[session_id].append(record)
            
            # Group sessions by group_id
            sessions_by_group: dict[int, list[SessionWithAttendanceDTO]] = {}
            for session in all_level_sessions:
                group_id = session_to_group.get(session.session_id)
                if group_id:
                    if group_id not in sessions_by_group:
                        sessions_by_group[group_id] = []
                    
                    # Add attendance if requested
                    if include_attendance:
                        session.attendance = attendance_by_session.get(session.session_id, [])
                    
                    sessions_by_group[group_id].append(session)
            
            # Build scheduled_groups
            scheduled_groups: list[ScheduledGroupDTO] = []
            for group_id in groups_lookup.keys():
                today_session = today_session_by_group.get(group_id)
                level_sessions = sessions_by_group.get(group_id, [])
                
                if level_sessions:
                    group_info = groups_lookup[group_id]
                    
                    # Query 5: Get roster for this group/level
                    roster = repo.get_roster_for_group_level(db, group_id, group_info.current_level)
                    
                    scheduled_group = ScheduledGroupDTO(
                        group_id=group_id,
                        today_session=today_session,
                        current_level=CurrentLevelDTO(
                            level_number=group_info.current_level,
                            sessions=level_sessions
                        ),
                        roster=roster
                    )
                    scheduled_groups.append(scheduled_group)
            
            # Sort by start time
            def sort_key(sg: ScheduledGroupDTO) -> tuple:
                g_info = groups_lookup.get(sg.group_id)
                if g_info and g_info.default_time_start:
                    return (g_info.default_time_start, g_info.name)
                return ('', '')
            
            scheduled_groups.sort(key=sort_key)
            
            # Calculate summary
            unique_instructor_ids = list(set(
                g.instructor_id for g in groups_lookup.values() if g.instructor_id
            ))
            
            summary = DashboardSummaryDTO(
                total_groups_today=len(scheduled_groups),
                total_instructors_today=len(unique_instructor_ids),
                unique_instructor_ids=unique_instructor_ids,
            )
            
            return DashboardDailyOverviewDTO(
                date=str(target_date),
                generated_at=datetime.utcnow().isoformat() + 'Z',
                cache_ttl=300,
                groups=groups_lookup,
                instructors=instructors_lookup,
                scheduled_groups=scheduled_groups,
                summary=summary,
            )

    def _build_empty_response(self, target_date: date) -> DashboardDailyOverviewDTO:
        """Build empty response when no groups have sessions on target date."""
        return DashboardDailyOverviewDTO(
            date=str(target_date),
            generated_at=datetime.utcnow().isoformat() + 'Z',
            cache_ttl=300,
            groups={},
            instructors={},
            scheduled_groups=[],
            summary=DashboardSummaryDTO(
                total_groups_today=0,
                total_instructors_today=0,
                unique_instructor_ids=[],
            ),
        )
