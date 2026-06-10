"""
tests/seed_data.py
──────────────────
CI-compatible seed data fixture using SQLModel models.

Creates minimum viable records that satisfy all FK constraints across
the 16+ database tables, enabling integration tests to run in CI.

Idempotent: calls TRUNCATE CASCADE before inserting.
Returns a dict mapping entity names to created model instances.
"""

from datetime import date, datetime, time
from typing import Any
from sqlmodel import Session, text

# ── Auth ──────────────────────────────────────────────────────────────────────
from app.modules.auth.models.auth_models import User

# ── HR ───────────────────────────────────────────────────────────────────────
from app.modules.hr.models import Employee

# ── CRM ───────────────────────────────────────────────────────────────────────
from app.modules.crm.models.student_models import Student
from app.modules.crm.models.parent_models import Parent
from app.modules.crm.models.link_models import StudentParent

# ── Academics ─────────────────────────────────────────────────────────────────
from app.modules.academics.models.course_models import Course
from app.modules.academics.models.group_models import Group
from app.modules.academics.models.session_models import CourseSession

# ── Enrollments ───────────────────────────────────────────────────────────────
from app.modules.enrollments.models.enrollment_models import Enrollment

# ── Attendance ────────────────────────────────────────────────────────────────
from app.modules.attendance.models.attendance_models import Attendance

# ── Finance ───────────────────────────────────────────────────────────────────
from app.modules.finance.models.receipt import Receipt
from app.modules.finance.models.payment import Payment

# ── Competitions ──────────────────────────────────────────────────────────────
from app.modules.competitions.models.competition_models import Competition
from app.modules.competitions.models.team_models import Team, TeamMember


# Tables in reverse FK dependency order (children first, parents last)
# Used by TRUNCATE CASCADE for idempotency.
REVERSE_ORDER_TABLES = [
    "attendance",
    "payments",
    "receipts",
    "team_members",
    "teams",
    "competitions",
    "enrollments",
    "student_parents",
    "sessions",
    "group_levels",
    "groups",
    "students",
    "parents",
    "courses",
    "employees",
    "users",
]


def seed_database(session: Session) -> dict[str, Any]:
    """
    Create minimum viable seed records for CI test runs.

    Idempotent: truncates all tables before inserting.
    Returns a dict mapping logical names to created model instances::

        result = seed_database(session)
        user = result["admin_user"]
        student1 = result["student_one"]

    Args:
        session: An active SQLModel Session (caller manages commit/rollback).

    Returns:
        Dict[str, Any]: Mapping of logical names to created ORM instances.
    """
    # ── Idempotent cleanup ───────────────────────────────────────────────
    for table in REVERSE_ORDER_TABLES:
        session.exec(text(f"TRUNCATE TABLE {table} CASCADE"))
    session.commit()

    created: dict[str, Any] = {}

    # ═════════════════════════════════════════════════════════════════════
    # 1. User + Employee
    # ═════════════════════════════════════════════════════════════════════
    admin_user = User(
        username="ci_admin",
        role="admin",
        is_active=True,
        supabase_uid="ci-admin-001",
    )
    session.add(admin_user)
    session.flush()
    created["admin_user"] = admin_user

    employee = Employee(
        full_name="Ci Employee",
        phone="01000000000",
        national_id="1234567890",
        university="Cairo University",
        major="Computer Science",
        is_graduate=True,
        job_title="Instructor",
        employment_type="full_time",
        user_id=admin_user.id,
    )
    session.add(employee)
    session.flush()
    created["employee"] = employee

    # ═════════════════════════════════════════════════════════════════════
    # 2. Student + Parent
    # ═════════════════════════════════════════════════════════════════════
    student_one = Student(
        full_name="Ahmed Ali",
        date_of_birth=datetime(2010, 5, 15),
        gender="male",
        phone="01000000001",
        status="active",
        created_by=admin_user.id,
    )
    session.add(student_one)
    session.flush()
    created["student_one"] = student_one

    student_two = Student(
        full_name="Sara Hassan",
        date_of_birth=datetime(2012, 3, 20),
        gender="female",
        phone="01000000002",
        status="active",
        created_by=admin_user.id,
    )
    session.add(student_two)
    session.flush()
    created["student_two"] = student_two

    parent = Parent(
        full_name="Ali Ahmed",
        phone_primary="01000000010",
        relation="father",
    )
    session.add(parent)
    session.flush()
    created["parent"] = parent

    student_parent = StudentParent(
        student_id=student_one.id,
        parent_id=parent.id,
        relationship="father",
        is_primary=True,
    )
    session.add(student_parent)
    session.flush()
    created["student_parent"] = student_parent

    # ═════════════════════════════════════════════════════════════════════
    # 3. Course + Group + Sessions
    # ═════════════════════════════════════════════════════════════════════
    course = Course(
        name="Mathematics Basics",
        category="software",
        price_per_level=500.0,
        sessions_per_level=4,
        is_active=True,
    )
    session.add(course)
    session.flush()
    created["course"] = course

    group = Group(
        name="Group A",
        course_id=course.id,
        instructor_id=employee.id,
        level_number=1,
        max_capacity=15,
        default_day="Saturday",
        default_time_start=time(14, 0),
        default_time_end=time(16, 0),
        status="active",
    )
    session.add(group)
    session.flush()
    created["group"] = group

    session_one = CourseSession(
        group_id=group.id,
        level_number=1,
        session_number=1,
        session_date=date(2026, 6, 15),
        start_time=time(14, 0),
        end_time=time(16, 0),
        actual_instructor_id=employee.id,
        status="scheduled",
    )
    session.add(session_one)
    session.flush()
    created["session_one"] = session_one

    session_two = CourseSession(
        group_id=group.id,
        level_number=1,
        session_number=2,
        session_date=date(2026, 6, 22),
        start_time=time(14, 0),
        end_time=time(16, 0),
        actual_instructor_id=employee.id,
        status="scheduled",
    )
    session.add(session_two)
    session.flush()
    created["session_two"] = session_two

    # ═════════════════════════════════════════════════════════════════════
    # 4. Enrollment
    # ═════════════════════════════════════════════════════════════════════
    enrollment = Enrollment(
        student_id=student_one.id,
        group_id=group.id,
        level_number=1,
        amount_due=500.0,
        discount_applied=0.0,
        status="active",
        created_by=admin_user.id,
    )
    session.add(enrollment)
    session.flush()
    created["enrollment"] = enrollment

    # ═════════════════════════════════════════════════════════════════════
    # 5. Attendance
    # ═════════════════════════════════════════════════════════════════════
    attendance_one = Attendance(
        student_id=student_one.id,
        session_id=session_one.id,
        enrollment_id=enrollment.id,
        status="present",
        marked_by=admin_user.id,
    )
    session.add(attendance_one)
    session.flush()
    created["attendance_one"] = attendance_one

    attendance_two = Attendance(
        student_id=student_one.id,
        session_id=session_two.id,
        enrollment_id=enrollment.id,
        status="absent",
        marked_by=admin_user.id,
    )
    session.add(attendance_two)
    session.flush()
    created["attendance_two"] = attendance_two

    # ═════════════════════════════════════════════════════════════════════
    # 6. Receipt + Payment
    # ═════════════════════════════════════════════════════════════════════
    receipt = Receipt(
        payer_name="Ahmed Ali",
        payment_method="cash",
        received_by=admin_user.id,
        receipt_number="CI-RCP-001",
        paid_at=datetime(2026, 6, 10),
    )
    session.add(receipt)
    session.flush()
    created["receipt"] = receipt

    payment = Payment(
        receipt_id=receipt.id,
        student_id=student_one.id,
        enrollment_id=enrollment.id,
        amount=500.0,
        transaction_type="charge",
        payment_type="course_level",
    )
    session.add(payment)
    session.flush()
    created["payment"] = payment

    # ═════════════════════════════════════════════════════════════════════
    # 7. Competition + Team + TeamMember
    # ═════════════════════════════════════════════════════════════════════
    competition = Competition(
        name="Robotics Challenge",
        edition_year=2026,
        competition_date=date(2026, 8, 15),
        location="Techno Center",
        fee_per_student=200.0,
    )
    session.add(competition)
    session.flush()
    created["competition"] = competition

    team = Team(
        competition_id=competition.id,
        group_id=group.id,
        team_name="RoboStars",
        coach_id=employee.id,
        category="Robotics",
        subcategory="Junior",
        project_name="Line Follower",
    )
    session.add(team)
    session.flush()
    created["team"] = team

    team_member = TeamMember(
        team_id=team.id,
        student_id=student_one.id,
        amount_due=200.0,
        amount_paid=200.0,
    )
    session.add(team_member)
    session.flush()
    created["team_member"] = team_member

    # ── Final commit ────────────────────────────────────────────────────
    session.commit()

    return created


if __name__ == "__main__":
    """Allow direct execution for verification: python tests/seed_data.py"""
    from app.db.connection import get_session
    with get_session() as session:
        result = seed_database(session)
        print("✅ Seed data created successfully")
        for name, obj in result.items():
            print(f"  • {name}: {obj.__class__.__name__} (id={obj.id})")
