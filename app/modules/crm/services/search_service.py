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
from app.modules.crm.interfaces.dtos import (
    StudentSummaryDTO,
    StudentStatusSummaryDTO,
    StudentGroupedResultDTO,
    StudentGroupBucketDTO,
    StudentFilterDTO,
    StudentFilterResultDTO,
    StudentFilterItemDTO,
)
from app.modules.crm.validators.student_validator import StudentValidator


class SearchService:
    """Service for student search and listing operations using raw SQL."""
    
    def __init__(self, uow: StudentUnitOfWork) -> None:
        self._uow = uow
    
    def search(self, query: str) -> List[Student]:
        """Search students by name or phone using raw SQL."""
        if not query or len(query.strip()) < 2:
            return []
        
        session = self._uow._session
        term = f"%{query.strip()}%"
        
        sql = text("""
            SELECT * FROM students 
            WHERE deleted_at IS NULL 
            AND (full_name ILIKE :term OR phone ILIKE :term)
            LIMIT 50
        """)
        
        result = session.exec(sql, params={"term": term})
        return [Student.model_validate(row) for row in result.mappings()]
    
    def list_all(self, skip: int = 0, limit: int = 200) -> List[Student]:
        """List all students with pagination using raw SQL."""
        session = self._uow._session
        
        sql = text("""
            SELECT * FROM students 
            WHERE deleted_at IS NULL 
            ORDER BY id 
            OFFSET :skip LIMIT :limit
        """)
        
        result = session.exec(sql, params={"skip": skip, "limit": limit})
        return [Student.model_validate(row) for row in result.mappings()]
    
    def list_all_enriched(self, include_inactive: bool = False) -> List[StudentSummaryDTO]:
        """List all students with enriched summary data using raw SQL with JOINs."""
        session = self._uow._session
        
        sql = text("""
            SELECT DISTINCT ON (s.id)
                s.id,
                s.full_name,
                s.phone,
                s.gender,
                s.status,
                s.date_of_birth,
                g.id as current_group_id,
                g.name as current_group_name
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
                date_of_birth=row.date_of_birth.date() if hasattr(row.date_of_birth, 'date') else row.date_of_birth
            ))
        return students
    
    def count(self, active_only: bool = True) -> int:
        """Count total students using raw SQL."""
        session = self._uow._session

        sql = text("""
            SELECT COUNT(*) FROM students
            WHERE deleted_at IS NULL
            AND (:active_only = false OR status = 'active')
        """)

        result = session.exec(sql, params={"active_only": active_only})
        return result.scalar()
    
    def count_by_status(self, status: StudentStatus) -> int:
        """Count students by specific status using raw SQL."""
        session = self._uow._session
        
        status_value = status.value if hasattr(status, 'value') else str(status)
        
        sql = text("""
            SELECT COUNT(*) FROM students 
            WHERE status = :status AND deleted_at IS NULL
        """)
        
        result = session.exec(sql, params={"status": status_value})
        return result.scalar()
    
    def get_by_status(self, status: StudentStatus) -> List[Student]:
        """Get all students with a specific status using raw SQL."""
        session = self._uow._session
        
        status_value = status.value if hasattr(status, 'value') else str(status)
        
        sql = text("""
            SELECT * FROM students 
            WHERE status = :status AND deleted_at IS NULL
            ORDER BY id
        """)
        
        result = session.exec(sql, params={"status": status_value})
        return [Student.model_validate(row) for row in result.mappings()]
    
    def get_waiting_list(self) -> List[Student]:
        """Get all students on the waiting list using raw SQL."""
        session = self._uow._session
        
        sql = text("""
            SELECT * FROM students 
            WHERE status = 'waiting' AND deleted_at IS NULL
            ORDER BY waiting_priority ASC NULLS LAST, waiting_since ASC
        """)
        
        result = session.exec(sql)
        return [Student.model_validate(row) for row in result.mappings()]
    
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
        # Get all enriched student data
        students = self._uow.students.get_all_enriched(include_inactive)

        # Group by strategy
        buckets: dict[str, list[StudentSummaryDTO]] = defaultdict(list)

        for student in students:
            if group_by == "status":
                key = student.status
            elif group_by == "gender":
                key = student.gender or "unknown"
            elif group_by == "age_bucket":
                age = StudentValidator.compute_age(student.date_of_birth)
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
        session = self._uow._session

        # Calculate date of birth bounds for age filtering
        today = date.today()
        max_dob = None
        min_dob = None
        if filters.min_age is not None:
            max_dob = date(today.year - filters.min_age, today.month, today.day)
        if filters.max_age is not None:
            min_dob = date(today.year - filters.max_age - 1, today.month, today.day) + timedelta(days=1)

        # Build course filter condition
        course_filter_sql = ""
        if filters.course_ids:
            course_ids_str = ",".join(str(c) for c in filters.course_ids)
            course_filter_sql = f"AND se.course_ids && ARRAY[{course_ids_str}]::integer[]"

        # Build instructor filter condition
        instructor_filter_sql = ""
        if filters.instructor_name:
            instructor_filter_sql = "AND ae.instructor_name ILIKE :instructor_pattern"

        # Build group day filter condition
        day_filter_sql = ""
        if filters.group_default_day:
            days_str = ",".join(f"'{d}'" for d in filters.group_default_day)
            day_filter_sql = f"AND ae.default_day = ANY(ARRAY[{days_str}])"

        # Build unpaid balance filter
        balance_filter_sql = ""
        if filters.has_unpaid_balance is not None:
            if filters.has_unpaid_balance:
                balance_filter_sql = "AND COALESCE(se.total_due, 0) > 0"
            else:
                balance_filter_sql = "AND COALESCE(se.total_due, 0) = 0"

        # Build enrollment count filter
        enrollment_count_sql = ""
        if filters.min_enrollments is not None:
            enrollment_count_sql += " AND COALESCE(se.enrollment_count, 0) >= :min_enrollments"
        if filters.max_enrollments is not None:
            enrollment_count_sql += " AND COALESCE(se.enrollment_count, 0) <= :max_enrollments"

        # Build main query with CTEs
        sql = text(f"""
            WITH student_enrollments AS (
                SELECT 
                    e.student_id,
                    COUNT(*) as enrollment_count,
                    ARRAY_AGG(DISTINCT g.course_id) FILTER (WHERE g.course_id IS NOT NULL) as course_ids,
                    SUM(COALESCE(e.amount_due, 0)) as total_due
                FROM enrollments e
                LEFT JOIN groups g ON g.id = e.group_id
                GROUP BY e.student_id
            ),
            active_enrollment_details AS (
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
            )
            SELECT 
                s.id,
                s.full_name,
                s.status,
                s.gender,
                s.phone,
                s.date_of_birth,
                COALESCE(se.enrollment_count, 0) as enrollment_count,
                COALESCE(se.course_ids, ARRAY[]::integer[]) as enrolled_courses,
                COALESCE(se.total_due, 0) as unpaid_balance,
                ae.group_id as current_group_id,
                ae.group_name as current_group_name,
                ae.default_day as group_default_day,
                ae.instructor_id,
                ae.instructor_name
            FROM students s
            LEFT JOIN student_enrollments se ON se.student_id = s.id
            LEFT JOIN active_enrollment_details ae ON ae.student_id = s.id
            WHERE s.deleted_at IS NULL
              AND (:min_age IS NULL OR s.date_of_birth <= :max_dob)
              AND (:max_age IS NULL OR s.date_of_birth >= :min_dob)
              AND (:statuses_empty OR s.status::text = ANY(:statuses))
              AND (:genders_empty OR s.gender::text = ANY(:genders))
              {instructor_filter_sql}
              {day_filter_sql}
              {course_filter_sql}
              {balance_filter_sql}
              {enrollment_count_sql}
            ORDER BY s.id
        """)

        params = {
            "min_age": filters.min_age,
            "max_dob": max_dob,
            "max_age": filters.max_age,
            "min_dob": min_dob,
            "statuses_empty": not filters.status,
            "statuses": filters.status or [],
            "genders_empty": not filters.gender,
            "genders": filters.gender or [],
            "min_enrollments": filters.min_enrollments,
            "max_enrollments": filters.max_enrollments,
        }

        if filters.instructor_name:
            params["instructor_pattern"] = f"%{filters.instructor_name}%"

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
                current_group_id=row.current_group_id,
                current_group_name=row.current_group_name,
                group_default_day=row.group_default_day,
                instructor_id=row.instructor_id,
                instructor_name=row.instructor_name,
                enrollment_count=row.enrollment_count,
                enrolled_courses=enrolled_courses,
                unpaid_balance=row.unpaid_balance if row.unpaid_balance > 0 else None,
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
