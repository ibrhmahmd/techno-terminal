"""
app/modules/analytics/repositories/bi_repository.py
───────────────────────────────────────────────────
Data access layer for BI analytics.
"""

from datetime import date
from sqlmodel import Session
from sqlalchemy import text
from app.modules.analytics.schemas import (
    EnrollmentTrendDTO,
    RetentionMetricsDTO,
    InstructorPerformanceDTO,
    LevelRetentionFunnelDTO,
    InstructorValueMatrixDTO,
    ScheduleUtilizationDTO,
    FlightRiskStudentDTO,
    RetentionCohortDTO,
)


def get_new_enrollments_trend(db: Session, cutoff_date: date) -> list[EnrollmentTrendDTO]:
    """Daily count of new enrollments since a given date."""
    stmt = text("""
        SELECT date(enrolled_at) as day, COUNT(id) as new_enrollments
        FROM enrollments
        WHERE date(enrolled_at) >= :cutoff
        GROUP BY day
        ORDER BY day
    """)
    rows = db.execute(stmt, {"cutoff": str(cutoff_date)}).all()
    return [EnrollmentTrendDTO(**r._mapping) for r in rows]


def get_retention_metrics(db: Session) -> list[RetentionMetricsDTO]:
    """Count of active vs dropped enrollments per course."""
    stmt = text("""
        SELECT 
            c.name as course_name,
            COUNT(e.id) FILTER (WHERE e.status = 'active') as active_count,
            COUNT(e.id) FILTER (WHERE e.status = 'dropped') as dropped_count,
            COUNT(e.id) as total_enrollments
        FROM courses c
        JOIN groups g ON c.id = g.course_id
        JOIN enrollments e ON g.id = e.group_id
        GROUP BY c.id, c.name
        ORDER BY total_enrollments DESC
    """)
    rows = db.execute(stmt).all()
    return [RetentionMetricsDTO(**r._mapping) for r in rows]


def get_instructor_performance(db: Session) -> list[InstructorPerformanceDTO]:
    """Active groups and enrollment counts by instructor."""
    stmt = text("""
        SELECT 
            emp.full_name as instructor_name,
            COUNT(DISTINCT g.id) as active_groups,
            COUNT(DISTINCT en.id) as active_students
        FROM employees emp
        JOIN users u ON u.employee_id = emp.id
        LEFT JOIN groups g ON emp.id = g.instructor_id AND g.status = 'active'
        LEFT JOIN enrollments en ON g.id = en.group_id AND en.status = 'active'
        WHERE u.role = 'instructor'
        GROUP BY emp.id, emp.full_name
        ORDER BY active_students DESC
    """)
    rows = db.execute(stmt).all()
    return [InstructorPerformanceDTO(**r._mapping) for r in rows]


def get_level_retention_funnel(db: Session) -> list[LevelRetentionFunnelDTO]:
    """How many students survive from Level 1 onwards in each course."""
    stmt = text("""
        SELECT c.name as course_name, 
               e.level_number, 
               COUNT(e.id) as student_count
        FROM enrollments e
        JOIN groups g ON e.group_id = g.id
        JOIN courses c ON g.course_id = c.id
        WHERE e.status != 'dropped'
        GROUP BY c.name, e.level_number
        ORDER BY c.name, e.level_number
    """)
    rows = db.execute(stmt).all()
    return [LevelRetentionFunnelDTO(**r._mapping) for r in rows]


def get_instructor_value_matrix(db: Session) -> list[InstructorValueMatrixDTO]:
    """Instructor Revenue vs Average Attendance (Retention marker)."""
    stmt = text("""
        WITH InstructorRev AS (
            SELECT g.instructor_id,
                   SUM(vb.total_paid) as generated_revenue
            FROM v_enrollment_balance vb
            JOIN groups g ON vb.group_id = g.id
            GROUP BY g.instructor_id
        ),
        InstructorAtt AS (
            SELECT g.instructor_id,
                   AVG(CASE WHEN vgs.total_sessions > 0
                       THEN 100.0 * COALESCE(att.sessions_attended, 0) / vgs.total_sessions
                       ELSE 0 END) as avg_attendance_pct
            FROM enrollments en
            JOIN groups g ON en.group_id = g.id
            LEFT JOIN v_enrollment_attendance att ON att.enrollment_id = en.id
            LEFT JOIN v_group_session_count vgs ON vgs.group_id = en.group_id AND vgs.level_number = en.level_number
            GROUP BY g.instructor_id
        )
        SELECT e.full_name as instructor_name,
               COALESCE(r.generated_revenue, 0) as total_revenue,
               ROUND(COALESCE(a.avg_attendance_pct, 0), 1) as avg_attendance_pct
        FROM employees e
        JOIN users u ON u.employee_id = e.id
        LEFT JOIN InstructorRev r ON r.instructor_id = e.id
        LEFT JOIN InstructorAtt a ON a.instructor_id = e.id
        WHERE u.role = 'instructor'
    """)
    rows = db.execute(stmt).all()
    return [InstructorValueMatrixDTO(**r._mapping) for r in rows]


def get_schedule_utilization(db: Session) -> list[ScheduleUtilizationDTO]:
    """Slot heatmaps showing filled vs max capacity."""
    stmt = text("""
        SELECT
            g.default_day as day,
            CAST(g.default_time_start AS TEXT) as time_start,
            COUNT(e.id) as total_enrolled,
            COALESCE(SUM(g.max_capacity), 1) as total_capacity,
            ROUND(100.0 * COUNT(e.id) / NULLIF(SUM(g.max_capacity), 0), 1) as utilization_pct
        FROM groups g
        LEFT JOIN enrollments e ON e.group_id = g.id AND e.status = 'active'
        WHERE g.status = 'active' AND g.default_day IS NOT NULL AND g.default_time_start IS NOT NULL
        GROUP BY g.default_day, g.default_time_start
        ORDER BY g.default_day, g.default_time_start
    """)
    rows = db.execute(stmt).all()
    return [ScheduleUtilizationDTO(**r._mapping) for r in rows]


def get_flight_risk_students(db: Session) -> list[FlightRiskStudentDTO]:
    """Students who both owe money AND have missed multiple sessions."""
    stmt = text("""
        SELECT
            st.full_name as student_name,
            c.name as course_name,
            -vb.balance AS amount_owed,
            att.sessions_missed
        FROM enrollments en
        JOIN students st ON en.student_id = st.id
        JOIN groups g ON en.group_id = g.id
        JOIN courses c ON g.course_id = c.id
        JOIN v_enrollment_balance vb ON vb.enrollment_id = en.id
        JOIN v_enrollment_attendance att ON att.enrollment_id = en.id
        WHERE en.status = 'active'
          AND vb.balance < 0
          AND att.sessions_missed > 0
        ORDER BY att.sessions_missed DESC, amount_owed DESC
    """)
    rows = db.execute(stmt).all()
    return [FlightRiskStudentDTO(**r._mapping) for r in rows]


def get_retention_cohorts(db: Session, months: int = 6) -> list[RetentionCohortDTO]:
    """Cohort-based retention analysis showing student retention over time."""
    from dateutil.relativedelta import relativedelta
    from datetime import date
    
    cutoff_date = date.today().replace(day=1) - relativedelta(months=months)

    stmt = text("""
        WITH monthly_cohorts AS (
            SELECT 
                DATE_TRUNC('month', enrolled_at)::date as cohort_month,
                id,
                status
            FROM enrollments
            WHERE enrolled_at >= :cutoff_date
            AND enrolled_at IS NOT NULL
        )
        SELECT 
            TO_CHAR(cohort_month, 'YYYY-MM') as cohort_month,
            COUNT(DISTINCT id) as initial_enrollments,
            COUNT(DISTINCT id) FILTER (WHERE status IN ('active', 'completed')) as retained_count
        FROM monthly_cohorts
        GROUP BY cohort_month
        ORDER BY cohort_month DESC
    """)
    
    rows = db.execute(stmt, {"cutoff_date": str(cutoff_date)}).all()
    
    result = []
    for r in rows:
        retained = r.retained_count
        total = r.initial_enrollments
        rate = round((retained / total) * 100, 2) if total > 0 else 0
        
        # Populate basic retention dict for current state
        retention_data = {
            "Month 0": "100%",
            "Current": f"{rate}%"
        }
        
        result.append(RetentionCohortDTO(
            cohort_month=str(r.cohort_month),
            initial_enrollments=total,
            retention_by_month=retention_data,
            retention_rates={"overall_retention_pct": rate}
        ))
    
    return result
