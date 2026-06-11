"""
SearchService - Handles student search, listing, and counting operations.
Uses raw SQL queries for performance.
"""
from typing import List, Literal
from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy import text

from app.modules.crm.models.student_models import Student, StudentStatus
from app.modules.crm.repositories.unit_of_work import StudentUnitOfWork
from app.modules.crm.schemas.student_schemas import StudentStatusSummaryDTO
from app.modules.crm.interfaces.dtos import (
    StudentSummaryDTO,
    StudentGroupedResultDTO,
    StudentGroupBucketDTO,
    StudentFilterDTO,
    StudentFilterResultDTO,
    StudentFilterItemDTO,
)
from app.modules.crm.validators.student_validator import StudentValidator
from app.modules.crm.schemas.waiting_list import WaitingListStudentDTO


class SearchService:
    """Service for student search and listing operations using raw SQL."""
    
    def __init__(self, uow: StudentUnitOfWork) -> None:
        self._uow = uow
    
    def search(self, query: str) -> List[StudentSummaryDTO]:
        """Search students by name or phone using raw SQL."""
        if not query or len(query.strip()) < 2:
            return []
        
        session = self._uow.session
        term = f"%{query.strip()}%"
        
        sql = text("""
            SELECT DISTINCT ON (s.id)
                s.id,
                s.full_name,
                s.phone,
                s.gender,
                s.status,
                s.date_of_birth,
                g.id as current_group_id,
                g.name as current_group_name,
                EXISTS (
                    SELECT 1 FROM v_unpaid_enrollments vue 
                    WHERE vue.student_id = s.id
                ) AS has_unpaid_balance
            FROM students s
            LEFT JOIN enrollments e ON e.student_id = s.id AND e.status = 'active'
            LEFT JOIN groups g ON g.id = e.group_id
            WHERE s.deleted_at IS NULL 
              AND (s.full_name ILIKE :term OR s.phone ILIKE :term)
            ORDER BY s.id, e.id DESC
            LIMIT 50
        """)
        
        result = session.exec(sql, params={"term": term})
        
        students = []
        for row in result.mappings():
            status_val = row.status
            if isinstance(status_val, str):
                status_str = status_val
            elif hasattr(status_val, 'value'):
                status_str = status_val.value
            else:
                status_str = "inactive"

            students.append(StudentSummaryDTO(
                id=row.id,
                full_name=row.full_name,
                phone=row.phone,
                gender=row.gender,
                status=status_str,
                current_group_id=row.current_group_id,
                current_group_name=row.current_group_name,
                date_of_birth=row.date_of_birth.date() if (row.date_of_birth and hasattr(row.date_of_birth, 'date')) else row.date_of_birth,
                has_unpaid_balance=row.has_unpaid_balance or False
            ))
        return students
    
    def list_all(self, skip: int = 0, limit: int = 200) -> List[StudentSummaryDTO]:
        """List all students with pagination using raw SQL."""
        session = self._uow.session
        
        sql = text("""
            SELECT DISTINCT ON (s.id)
                s.id,
                s.full_name,
                s.phone,
                s.gender,
                s.status,
                s.date_of_birth,
                g.id as current_group_id,
                g.name as current_group_name,
                EXISTS (
                    SELECT 1 FROM v_unpaid_enrollments vue 
                    WHERE vue.student_id = s.id
                ) AS has_unpaid_balance
            FROM students s
            LEFT JOIN enrollments e ON e.student_id = s.id AND e.status = 'active'
            LEFT JOIN groups g ON g.id = e.group_id
            WHERE s.deleted_at IS NULL
            ORDER BY s.id, e.id DESC
            OFFSET :skip LIMIT :limit
        """)
        
        result = session.exec(sql, params={"skip": skip, "limit": limit})
        
        students = []
        for row in result.mappings():
            status_val = row.status
            if isinstance(status_val, str):
                status_str = status_val
            elif hasattr(status_val, 'value'):
                status_str = status_val.value
            else:
                status_str = "inactive"

            students.append(StudentSummaryDTO(
                id=row.id,
                full_name=row.full_name,
                phone=row.phone,
                gender=row.gender,
                status=status_str,
                current_group_id=row.current_group_id,
                current_group_name=row.current_group_name,
                date_of_birth=row.date_of_birth.date() if (row.date_of_birth and hasattr(row.date_of_birth, 'date')) else row.date_of_birth,
                has_unpaid_balance=row.has_unpaid_balance or False
            ))
        return students
    
    def _list_all_enriched(self, include_inactive: bool = False) -> List[StudentSummaryDTO]:
        """List all students with enriched summary data using raw SQL with JOINs."""
        session = self._uow.session
        
        sql = text("""
            SELECT DISTINCT ON (s.id)
                s.id,
                s.full_name,
                s.phone,
                s.gender,
                s.status,
                s.date_of_birth,
                g.id as current_group_id,
                g.name as current_group_name,
                EXISTS (
                    SELECT 1 FROM v_unpaid_enrollments vue 
                    WHERE vue.student_id = s.id
                ) AS has_unpaid_balance
            FROM students s
            LEFT JOIN enrollments e ON e.student_id = s.id AND e.status = 'active'
            LEFT JOIN groups g ON g.id = e.group_id
            WHERE s.deleted_at IS NULL
              AND (:include_inactive OR s.status = 'active')
            ORDER BY s.id, e.id DESC
        """)

        result = session.exec(sql, params={"include_inactive": include_inactive})

        students = []
        for row in result.mappings():
            status_val = row.status
            if isinstance(status_val, str):
                status_str = status_val
            elif hasattr(status_val, 'value'):
                status_str = status_val.value
            else:
                status_str = "inactive"

            students.append(StudentSummaryDTO(
                id=row.id,
                full_name=row.full_name,
                phone=row.phone,
                gender=row.gender,
                status=status_str,
                current_group_id=row.current_group_id,
                current_group_name=row.current_group_name,
                date_of_birth=row.date_of_birth.date() if hasattr(row.date_of_birth, 'date') else row.date_of_birth,
                has_unpaid_balance=row.has_unpaid_balance or False
            ))
        return students
    
    def count(self, active_only: bool = True) -> int:
        """Count total students using raw SQL."""
        session = self._uow.session

        sql = text("""
            SELECT COUNT(*) FROM students
            WHERE deleted_at IS NULL
            AND (:active_only = false OR status = 'active')
        """)

        result = session.exec(sql, params={"active_only": active_only})
        return result.scalar()
    
    def count_by_status(self, status: StudentStatus) -> int:
        """Count students by specific status using raw SQL."""
        session = self._uow.session
        
        status_value = status.value if hasattr(status, 'value') else str(status)
        
        sql = text("""
            SELECT COUNT(*) FROM students 
            WHERE status = :status AND deleted_at IS NULL
        """)
        
        result = session.exec(sql, params={"status": status_value})
        return result.scalar()
    
    def get_by_status(self, status: StudentStatus) -> List[Student]:
        """Get all students with a specific status using raw SQL."""
        session = self._uow.session
        
        status_value = status.value if hasattr(status, 'value') else str(status)
        
        sql = text("""
            SELECT * FROM students 
            WHERE status = :status AND deleted_at IS NULL
            ORDER BY id
        """)
        
        result = session.exec(sql, params={"status": status_value})
        return [Student.model_validate(row) for row in result.mappings()]
    
    def get_waiting_list(self) -> List[WaitingListStudentDTO]:
        """Get all students on the waiting list with unpaid balance and age."""
        session = self._uow.session

        sql = text("""
            SELECT
                s.id,
                s.full_name,
                s.phone,
                s.gender,
                s.status,
                s.date_of_birth,
                s.waiting_since,
                s.waiting_priority,
                s.waiting_notes,
                EXISTS (
                    SELECT 1 FROM v_enrollment_balance veb
                    WHERE veb.student_id = s.id AND veb.amount_remaining > 0
                ) AS has_unpaid_balance
            FROM students s
            WHERE s.status = 'waiting' AND s.deleted_at IS NULL
            ORDER BY s.waiting_priority ASC NULLS LAST, s.waiting_since ASC
        """)

        result = session.exec(sql)
        students = []
        for row in result.mappings():
            students.append(WaitingListStudentDTO(
                id=row.id,
                full_name=row.full_name,
                phone=row.phone,
                gender=row.gender,
                status=str(row.status) if row.status else "waiting",
                date_of_birth=row.date_of_birth,
                age=StudentValidator.compute_age(row.date_of_birth),
                has_unpaid_balance=row.has_unpaid_balance or False,
                waiting_since=row.waiting_since,
                waiting_priority=row.waiting_priority,
                waiting_notes=row.waiting_notes,
            ))
        return students
    
    def get_status_summary(self) -> StudentStatusSummaryDTO:
        """Get summary counts by status."""
        total_active = self.count(active_only=True)
        total_inactive = self.count(active_only=False) - total_active
        
        return StudentStatusSummaryDTO(
            total=total_active + total_inactive,
            active=total_active,
            inactive=total_inactive,
            waiting=self.count_by_status(StudentStatus.WAITING),
        )
    
    def get_grouped(
        self,
        group_by: Literal["status", "gender", "age_bucket"],
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> StudentGroupedResultDTO:
        """
        Group students by specified criteria.

        Args:
            group_by: Grouping strategy - "status", "gender", or "age_bucket"
            include_inactive: Whether to include inactive students
            skip: Number of students to skip per group (pagination)
            limit: Max students per group (pagination)
        """
        # Get all enriched student data (includes has_unpaid_balance)
        students = self._list_all_enriched(include_inactive)

        # Rebuild with age computed (can't mutate frozen DTOs)
        enriched = []
        for s in students:
            enriched.append(StudentSummaryDTO(
                id=s.id,
                full_name=s.full_name,
                phone=s.phone,
                gender=s.gender,
                status=s.status,
                current_group_id=s.current_group_id,
                current_group_name=s.current_group_name,
                date_of_birth=s.date_of_birth,
                has_unpaid_balance=s.has_unpaid_balance,
                age=StudentValidator.compute_age(s.date_of_birth),
            ))
        students = enriched

        # Group by strategy
        buckets: dict[str, list[StudentSummaryDTO]] = defaultdict(list)

        for student in students:
            if group_by == "status":
                key = student.status
            elif group_by == "gender":
                key = student.gender or "unknown"
            elif group_by == "age_bucket":
                age = student.age if student.age is not None else StudentValidator.compute_age(student.date_of_birth)
                key = StudentValidator.classify_age_bracket(age)
            else:
                key = "other"

            buckets[key].append(student)

        # Build result buckets with pagination applied to each group
        groups = []
        for key, students_list in sorted(buckets.items()):
            total_in_group = len(students_list)
            # Apply pagination: slice [skip:skip+limit]
            paginated_students = students_list[skip:skip + limit]
            groups.append(
                StudentGroupBucketDTO(
                    key=key,
                    label=key.replace("_", " ").title() if group_by != "status" else key.capitalize(),
                    count=total_in_group,  # Total count (unpaginated)
                    students=paginated_students,  # Paginated list
                )
            )

        return StudentGroupedResultDTO(
            group_by=group_by,
            total_unique_students=len(students),
            groups=groups,
            total=sum(len(g.students) for g in groups),
        )

    def filter_students(self, filters: StudentFilterDTO) -> StudentFilterResultDTO:
        """
        Filter students based on multiple criteria using optimized raw SQL with CTEs.
        """
        session = self._uow.session

        # Calculate date of birth bounds for age filtering
        today = date.today()
        max_dob = None
        min_dob = None
        if filters.min_age is not None:
            max_dob = date(today.year - filters.min_age, today.month, today.day)
        if filters.max_age is not None:
            min_dob = date(today.year - filters.max_age - 1, today.month, today.day) + timedelta(days=1)

        # Build CTEs dynamically
        ctes = [
            """student_enrollments AS (
                SELECT 
                    e.student_id,
                    COUNT(*) as current_enrollment_count,
                    ARRAY_AGG(DISTINCT g.course_id) FILTER (WHERE g.course_id IS NOT NULL) as course_ids,
                    SUM(COALESCE(e.amount_due, 0)) as total_due
                FROM enrollments e
                LEFT JOIN groups g ON g.id = e.group_id
                GROUP BY e.student_id
            )""",
            """active_enrollment_details AS (
                SELECT DISTINCT ON (e.student_id)
                    e.student_id,
                    g.id as group_id,
                    g.name as group_name,
                    g.default_day,
                    g.instructor_id,
                    COALESCE(emp.full_name, 'Unknown') as instructor_name
                FROM enrollments e
                JOIN groups g ON g.id = e.group_id
                LEFT JOIN employees emp ON emp.id = g.instructor_id
                WHERE e.status = 'active'
                ORDER BY e.student_id, e.id DESC
            )"""
        ]

        has_activity_filter = (
            filters.min_activity_count is not None
            or filters.max_activity_count is not None
            or filters.activity_types
            or filters.activity_date_from
            or filters.activity_date_to
        )
        if has_activity_filter:
            ctes.append(
                """student_activity_counts AS (
                    SELECT 
                        student_id,
                        COUNT(*) as activity_count
                    FROM student_activity_log
                    WHERE 1=1
                      AND (:has_activity_types = FALSE OR activity_type = ANY(:activity_types))
                      AND (:activity_date_from IS NULL OR created_at >= :activity_date_from)
                      AND (:activity_date_to IS NULL OR created_at <= :activity_date_to)
                    GROUP BY student_id
                )"""
            )

        cte_sql = "WITH " + ",\n".join(ctes)

        # Build Select and Joins
        select_sql = """
            SELECT 
                s.id,
                s.full_name,
                s.status,
                s.gender,
                s.phone,
                s.date_of_birth,
                COALESCE(se.current_enrollment_count, 0) as current_enrollment_count,
                COALESCE(se.course_ids, ARRAY[]::integer[]) as enrolled_courses,
                (COALESCE(se.total_due, 0) > 0) as has_unpaid_balance,
                ae.group_id as current_group_id,
                ae.group_name as current_group_name,
                ae.default_day as group_default_day,
                ae.instructor_id,
                ae.instructor_name
            FROM students s
            LEFT JOIN student_enrollments se ON se.student_id = s.id
            LEFT JOIN active_enrollment_details ae ON ae.student_id = s.id
        """
        if has_activity_filter:
            select_sql += "            LEFT JOIN student_activity_counts sac ON sac.student_id = s.id\n"

        # Build WHERE clauses dynamically
        where_clauses = ["s.deleted_at IS NULL"]
        if filters.min_age is not None:
            where_clauses.append("s.date_of_birth <= :max_dob")
        if filters.max_age is not None:
            where_clauses.append("s.date_of_birth >= :min_dob")
        if filters.status:
            where_clauses.append("s.status::text = ANY(:statuses)")
        if filters.gender:
            where_clauses.append("s.gender::text = ANY(:genders)")
        if filters.instructor_name:
            where_clauses.append("ae.instructor_name ILIKE :instructor_pattern")
        if filters.group_default_day:
            days_str = ",".join(f"'{d}'" for d in filters.group_default_day)
            where_clauses.append(f"ae.default_day = ANY(ARRAY[{days_str}])")
        if filters.has_any_outstanding_balance is not None:
            if filters.has_any_outstanding_balance:
                where_clauses.append("COALESCE(se.total_due, 0) > 0")
            else:
                where_clauses.append("COALESCE(se.total_due, 0) = 0")
        if filters.min_enrollments is not None:
            where_clauses.append("COALESCE(se.current_enrollment_count, 0) >= :min_enrollments")
        if filters.max_enrollments is not None:
            where_clauses.append("COALESCE(se.current_enrollment_count, 0) <= :max_enrollments")

        # Course inclusion with optional date range
        if filters.course_ids or filters.course_enrollment_date_from or filters.course_enrollment_date_to:
            where_clauses.append("""EXISTS (
                SELECT 1 
                FROM enrollments e_filter
                JOIN groups g_filter ON g_filter.id = e_filter.group_id
                WHERE e_filter.student_id = s.id
                  AND (:has_course_ids = FALSE OR g_filter.course_id = ANY(:course_ids))
                  AND (:course_enrollment_date_from IS NULL OR COALESCE(e_filter.enrolled_at, e_filter.created_at) >= :course_enrollment_date_from)
                  AND (:course_enrollment_date_to IS NULL OR COALESCE(e_filter.enrolled_at, e_filter.created_at) <= :course_enrollment_date_to)
            )""")

        # Course exclusion
        if filters.exclude_course_ids:
            where_clauses.append("""NOT EXISTS (
                SELECT 1 
                FROM enrollments e_exc
                JOIN groups g_exc ON g_exc.id = e_exc.group_id
                WHERE e_exc.student_id = s.id
                  AND g_exc.course_id = ANY(:exclude_course_ids)
            )""")

        # Activity count bounds
        if filters.min_activity_count is not None:
            where_clauses.append("COALESCE(sac.activity_count, 0) >= :min_activity_count")
        if filters.max_activity_count is not None:
            where_clauses.append("COALESCE(sac.activity_count, 0) <= :max_activity_count")

        # Activity search term
        if filters.activity_search_term:
            where_clauses.append("""EXISTS (
                SELECT 1 
                FROM student_activity_log al_search
                WHERE al_search.student_id = s.id
                  AND (
                      al_search.description ILIKE :activity_pattern 
                      OR al_search.meta::text ILIKE :activity_pattern
                      OR al_search.activity_type ILIKE :activity_pattern
                      OR al_search.activity_subtype ILIKE :activity_pattern
                  )
            )""")

        where_sql = " AND ".join(where_clauses)
        sql = text(f"{cte_sql}\n{select_sql}\nWHERE {where_sql}\nORDER BY s.id")

        params = {
            "min_age": filters.min_age,
            "max_dob": max_dob,
            "max_age": filters.max_age,
            "min_dob": min_dob,
            "statuses": filters.status or [],
            "genders": filters.gender or [],
            "min_enrollments": filters.min_enrollments,
            "max_enrollments": filters.max_enrollments,
            "has_course_ids": bool(filters.course_ids),
            "course_ids": filters.course_ids or [],
            "course_enrollment_date_from": filters.course_enrollment_date_from,
            "course_enrollment_date_to": filters.course_enrollment_date_to,
            "exclude_course_ids": filters.exclude_course_ids or [],
            "has_activity_types": bool(filters.activity_types),
            "activity_types": filters.activity_types or [],
            "activity_date_from": filters.activity_date_from,
            "activity_date_to": filters.activity_date_to,
            "min_activity_count": filters.min_activity_count,
            "max_activity_count": filters.max_activity_count,
        }

        if filters.instructor_name:
            params["instructor_pattern"] = f"%{filters.instructor_name}%"

        if filters.activity_search_term:
            params["activity_pattern"] = f"%{filters.activity_search_term}%"

        result = session.exec(sql, params=params)

        # Build result items
        students = []
        for row in result.mappings():
            age = StudentValidator.compute_age(row.date_of_birth)

            enrolled_courses = list(row.enrolled_courses) if row.enrolled_courses else []

            students.append(StudentFilterItemDTO(
                id=row.id,
                full_name=row.full_name,
                age=age,
                status=row.status,
                gender=row.gender,
                phone=row.phone,
                date_of_birth=row.date_of_birth,
                current_group_id=row.current_group_id,
                current_group_name=row.current_group_name,
                group_default_day=row.group_default_day,
                instructor_id=row.instructor_id,
                instructor_name=row.instructor_name,
                current_enrollment_count=row.current_enrollment_count,
                enrolled_courses=enrolled_courses,
                has_unpaid_balance=bool(row.has_unpaid_balance),
            ))

        # Apply pagination
        total = len(students)
        paginated = students[filters.skip : filters.skip + filters.limit]

        return StudentFilterResultDTO(
            students=paginated,
            total=total,
            skip=filters.skip,
            limit=filters.limit,
        )
