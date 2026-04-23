"""
app/modules/analytics/repositories/dashboard_repository.py
──────────────────────────────────────────────────────────
Data access layer for dashboard analytics.

Implements the 4-query strategy:
1. Get groups with sessions on target date
2. Get group metadata (batch fetch)
3. Get ALL sessions for current levels (batch fetch)
4. Get attendance records (batch fetch)
"""

from datetime import date, time
from typing import Optional
from sqlmodel import Session
from sqlalchemy import text

from app.modules.analytics.schemas.dashboard_schemas import (
    GroupSessionInfoDTO,
    GroupMetadataResultDTO,
    GroupInfoDTO,
    InstructorInfoDTO,
    SessionWithAttendanceDTO,
    AttendanceRecordDTO,
    StudentRosterDTO,
)


def get_groups_with_sessions_on_date(
    db: Session, target_date: date
) -> list[GroupSessionInfoDTO]:
    """
    Query 1: Get groups that have sessions on the target date.
    
    Returns list of GroupSessionInfoDTO with strict typing.
    
    Sorted by default_time_start ASC, then group_name ASC.
    """
    stmt = text("""
        SELECT DISTINCT 
            s.group_id,
            s.id AS session_id,
            s.session_date,
            s.start_time,
            s.end_time,
            s.status,
            g.level_number,
            g.default_time_start,
            g.name AS group_name
        FROM sessions s
        JOIN groups g ON s.group_id = g.id
        WHERE s.session_date = :target_date
          AND g.status = 'active'
        ORDER BY g.default_time_start ASC, g.name ASC
    """)
    rows = db.execute(stmt, {"target_date": str(target_date)}).all()
    
    result: list[GroupSessionInfoDTO] = []
    for row in rows:
        mapping = row._mapping
        result.append(GroupSessionInfoDTO(
            group_id=mapping['group_id'],
            session_id=mapping['session_id'],
            session_date=str(mapping['session_date']),
            start_time=str(mapping['start_time'])[:5] if mapping['start_time'] else None,
            end_time=str(mapping['end_time'])[:5] if mapping['end_time'] else None,
            status=mapping['status'],
            level_number=mapping['level_number'],
            default_time_start=str(mapping['default_time_start']) if mapping['default_time_start'] else None,
            group_name=mapping['group_name'],
        ))
    return result


def get_group_metadata(
    db: Session, group_ids: list[int]
) -> GroupMetadataResultDTO:
    """
    Query 2: Get group metadata and instructor info for all groups.
    
    Returns GroupMetadataResultDTO containing:
    - groups: List of GroupInfoDTO (for lookup table)
    - instructors: List of InstructorInfoDTO (deduplicated from groups)
    """
    if not group_ids:
        return GroupMetadataResultDTO(groups=[], instructors=[])
    
    # Convert to tuple for SQL IN clause
    ids_tuple = tuple(group_ids) if len(group_ids) > 1 else (group_ids[0],)
    
    stmt = text("""
        SELECT 
            g.id,
            g.name,
            g.level_number AS current_level,
            c.name AS course_name,
            g.instructor_id,
            COALESCE(e.full_name, 'Unassigned') AS instructor_name,
            g.default_day,
            g.default_time_start,
            g.default_time_end,
            g.max_capacity,
            COUNT(en.id) AS student_count
        FROM groups g
        JOIN courses c ON g.course_id = c.id
        LEFT JOIN employees e ON g.instructor_id = e.id
        LEFT JOIN enrollments en ON en.group_id = g.id AND en.status = 'active'
        WHERE g.id IN :group_ids
        GROUP BY g.id, c.name, e.id, e.full_name
    """)
    
    rows = db.execute(stmt, {"group_ids": ids_tuple}).all()
    
    groups: list[GroupInfoDTO] = []
    instructors_map: dict[int, str] = {}
    
    for row in rows:
        mapping = row._mapping
        
        # Format schedule_display: "Sat 3:00-4:30 PM"
        schedule_display = _format_schedule_display(
            mapping.get('default_day') or '',
            mapping.get('default_time_start'),
            mapping.get('default_time_end')
        )
        
        # Build GroupInfoDTO
        group = GroupInfoDTO(
            id=mapping['id'],
            name=mapping['name'],
            course_name=mapping['course_name'],
            instructor_id=mapping['instructor_id'] or 0,
            current_level=mapping['current_level'] or 1,
            default_day=mapping.get('default_day') or '',
            default_time_start=str(mapping['default_time_start']) if mapping['default_time_start'] else '',
            default_time_end=str(mapping['default_time_end']) if mapping['default_time_end'] else '',
            schedule_display=schedule_display,
            max_capacity=mapping.get('max_capacity') or 0,
            student_count=mapping.get('student_count') or 0,
        )
        groups.append(group)
        
        # Collect instructors for lookup table
        if mapping['instructor_id']:
            instructors_map[mapping['instructor_id']] = mapping['instructor_name']
    
    # Build InstructorInfoDTO list
    instructors: list[InstructorInfoDTO] = [
        InstructorInfoDTO(id=inst_id, name=name)
        for inst_id, name in instructors_map.items()
    ]
    
    return GroupMetadataResultDTO(groups=groups, instructors=instructors)


def get_sessions_for_levels(
    db: Session, 
    group_level_map: dict[int, int]  # group_id -> current_level
) -> list[SessionWithAttendanceDTO]:
    """
    Query 3: Get ALL sessions for the current levels of specified groups.
    
    Args:
        group_level_map: Mapping of group_id -> current_level_number
    
    Returns list of SessionWithAttendanceDTO (without attendance data yet).
    """
    if not group_level_map:
        return []
    
    # Build WHERE clause for (group_id, level_number) pairs
    conditions = []
    params = {}
    for i, (group_id, level) in enumerate(group_level_map.items()):
        param_g = f"g{i}"
        param_l = f"l{i}"
        conditions.append(f"(s.group_id = :{param_g} AND s.level_number = :{param_l})")
        params[param_g] = group_id
        params[param_l] = level
    
    where_clause = " OR ".join(conditions)
    
    stmt = text(f"""
        SELECT 
            s.id AS session_id,
            s.group_id,
            s.level_number,
            s.session_number,
            s.session_date,
            s.start_time,
            s.end_time,
            s.status,
            s.is_extra_session,
            s.actual_instructor_id,
            s.is_substitute,
            COALESCE(e.full_name, 'Unassigned') AS instructor_name
        FROM sessions s
        LEFT JOIN employees e ON s.actual_instructor_id = e.id
        WHERE {where_clause}
        ORDER BY s.group_id, s.session_date
    """)
    
    rows = db.execute(stmt, params).all()
    
    sessions = []
    for row in rows:
        row_dict = dict(row._mapping)
        session = SessionWithAttendanceDTO(
            session_id=row_dict['session_id'],
            session_number=row_dict['session_number'],
            date=str(row_dict['session_date']),
            time_start=str(row_dict['start_time'])[:5] if row_dict['start_time'] else '',
            time_end=str(row_dict['end_time'])[:5] if row_dict['end_time'] else '',
            status=row_dict['status'],
            is_extra_session=row_dict.get('is_extra_session') or False,
            actual_instructor_id=row_dict['actual_instructor_id'] or 0,
            instructor_name=row_dict.get('instructor_name'),
            is_substitute=row_dict.get('is_substitute') or False,
        )
        sessions.append(session)
    
    return sessions


def get_attendance_for_sessions(
    db: Session, session_ids: list[int]
) -> list[AttendanceRecordDTO]:
    """
    Query 4: Get attendance records for specified sessions.
    
    Returns list of AttendanceRecordDTO.
    """
    if not session_ids:
        return []
    
    # Convert to tuple for SQL IN clause
    ids_tuple = tuple(session_ids) if len(session_ids) > 1 else (session_ids[0],)
    
    stmt = text("""
        SELECT 
            ar.session_id,
            ar.student_id,
            st.full_name AS student_name,
            st.gender,
            ar.status
        FROM attendance ar
        JOIN students st ON ar.student_id = st.id
        WHERE ar.session_id IN :session_ids
        ORDER BY ar.session_id, st.full_name
    """)
    
    rows = db.execute(stmt, {"session_ids": ids_tuple}).all()
    
    attendance: list[AttendanceRecordDTO] = []
    for row in rows:
        mapping = row._mapping
        record = AttendanceRecordDTO(
            student_id=mapping['student_id'],
            student_name=mapping['student_name'],
            gender=mapping['gender'] or 'male',
            status=mapping['status'],
        )
        attendance.append(record)
    
    return attendance


def get_roster_for_group_level(
    db: Session, 
    group_id: int, 
    level_number: int
) -> list[StudentRosterDTO]:
    """
    Query 5: Fetch active enrollments with student details and calculated billing status.
    
    Balance formula: (amount_due - discount_applied) - total_payments
    billing_status: 'due' if balance > 0 else 'paid'
    
    Returns list of StudentRosterDTO ordered by student name.
    """
    stmt = text("""
        SELECT 
            s.id AS student_id,
            s.full_name AS student_name,
            s.gender,
            e.amount_due,
            COALESCE(e.discount_applied, 0) AS discount_applied,
            COALESCE(p.total_paid, 0) AS total_paid,
            (e.amount_due - COALESCE(e.discount_applied, 0) - COALESCE(p.total_paid, 0)) AS balance
        FROM enrollments e
        JOIN students s ON e.student_id = s.id
        LEFT JOIN (
            SELECT enrollment_id, SUM(amount) as total_paid
            FROM payments
            WHERE deleted_at IS NULL
            GROUP BY enrollment_id
        ) p ON e.id = p.enrollment_id
        WHERE e.group_id = :group_id
            AND e.level_number = :level_number
            AND e.status = 'active'
        ORDER BY s.full_name
    """)
    
    rows = db.execute(stmt, {"group_id": group_id, "level_number": level_number}).all()
    
    result: list[StudentRosterDTO] = []
    for row in rows:
        mapping = row._mapping
        balance = float(mapping['balance'])
        result.append(StudentRosterDTO(
            student_id=mapping['student_id'],
            student_name=mapping['student_name'],
            gender=mapping['gender'] or 'male',
            billing_status='due' if balance > 0 else 'paid',
            balance=balance
        ))
    return result


def _format_schedule_display(
    day: str, 
    start_time: Optional[time | str], 
    end_time: Optional[time | str]
) -> str:
    """
    Format schedule display as "Sat 3:00-4:30 PM".
    
    Args:
        day: Day name (e.g., "Saturday")
        start_time: Time object or string
        end_time: Time object or string
    
    Returns formatted string or empty string if inputs are invalid.
    """
    if not day or not start_time or not end_time:
        return ''
    
    # Convert to string if needed
    start_str = str(start_time)[:5] if start_time else ''
    end_str = str(end_time)[:5] if end_time else ''
    
    if not start_str or not end_str:
        return ''
    
    # Parse hours and minutes
    try:
        start_parts = start_str.split(':')
        end_parts = end_str.split(':')
        
        start_hour = int(start_parts[0])
        start_min = start_parts[1]
        end_hour = int(end_parts[0])
        end_min = end_parts[1]
        
        # Convert to 12-hour format
        start_period = 'AM' if start_hour < 12 else 'PM'
        end_period = 'AM' if end_hour < 12 else 'PM'
        
        start_hour_12 = start_hour % 12 if start_hour % 12 != 0 else 12
        end_hour_12 = end_hour % 12 if end_hour % 12 != 0 else 12
        
        # Format: "Sat 3:00-4:30 PM" (using period from end time if different)
        # If both AM or both PM, show period once at end
        if start_period == end_period:
            return f"{day[:3]} {start_hour_12}:{start_min}-{end_hour_12}:{end_min} {start_period}"
        else:
            return f"{day[:3]} {start_hour_12}:{start_min} {start_period}-{end_hour_12}:{end_min} {end_period}"
    except (ValueError, IndexError):
        return f"{day[:3]} {start_str}-{end_str}"
