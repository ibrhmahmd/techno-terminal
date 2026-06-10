"""
Test database utilities for creating test data.
Comprehensive factories covering all 10 business modules.
"""
from sqlmodel import Session
from typing import Optional
from datetime import date, time, datetime, timedelta
import time as _time
import uuid


def _unique(prefix: str) -> str:
    return f"{prefix}-{_time.time_ns()}"


# ── CRM: Parent ──────────────────────────────────────────────────────────────

def create_test_parent(
    session: Session,
    full_name: str = "Test Parent",
    phone_primary: str = "+201000000001",
    email: Optional[str] = None
):
    from app.modules.crm.models import Parent
    parent = Parent(full_name=full_name, phone_primary=phone_primary, email=email)
    session.add(parent)
    session.commit()
    session.refresh(parent)
    return parent


# ── CRM: Student ─────────────────────────────────────────────────────────────

def create_test_student(
    session: Session,
    full_name: str = "Test Student",
    birth_date: Optional[str] = None,
    parent_id: Optional[int] = None,
    status: str = "active",
    gender: Optional[str] = None,
    phone: Optional[str] = None,
):
    from app.modules.crm.models import Student
    student = Student(
        full_name=full_name,
        date_of_birth=birth_date,
        status=status,
        gender=gender,
        phone=phone,
    )
    session.add(student)
    session.commit()
    session.refresh(student)
    if parent_id:
        from app.modules.crm.models import StudentParent
        link = StudentParent(student_id=student.id, parent_id=parent_id, is_primary=True)
        session.add(link)
        session.commit()
    return student


# ── CRM: Student-Parent Link ─────────────────────────────────────────────────

def link_student_parent(
    session: Session,
    student_id: int,
    parent_id: int,
    is_primary: bool = True,
):
    from app.modules.crm.models import StudentParent
    link = StudentParent(student_id=student_id, parent_id=parent_id, is_primary=is_primary)
    session.add(link)
    session.commit()
    return link


# ── HR: Employee ─────────────────────────────────────────────────────────────

def create_test_employee(
    session: Session,
    full_name: str = "Test Instructor",
    phone: Optional[str] = None,
    email: Optional[str] = None,
    national_id: Optional[str] = None,
    university: str = "Test University",
    major: str = "Computer Science",
    is_graduate: bool = True,
    job_title: Optional[str] = None,
    employment_type: str = "full_time",
    monthly_salary: Optional[float] = None,
    is_active: bool = True,
):
    from app.modules.hr.models.employee_models import Employee
    emp = Employee(
        full_name=full_name,
        phone=phone or f"010{str(uuid.uuid4().int)[:8]}",
        email=email,
        national_id=national_id or f"NID{str(uuid.uuid4().int)[:12]}",
        university=university,
        major=major,
        is_graduate=is_graduate,
        job_title=job_title,
        employment_type=employment_type,
        monthly_salary=monthly_salary,
        is_active=is_active,
    )
    session.add(emp)
    session.commit()
    session.refresh(emp)
    return emp


# ── Academics: Course ────────────────────────────────────────────────────────

def create_test_course(
    session: Session,
    name: str = None,
    category: str = "software",
    price_per_level: float = 1000.0,
    sessions_per_level: Optional[int] = None,
    description: Optional[str] = None,
    is_active: bool = True,
):
    from app.modules.academics.models import Course
    if name is None:
        name = _unique("Course")
    course = Course(
        name=name,
        category=category,
        price_per_level=price_per_level,
        sessions_per_level=sessions_per_level,
        description=description,
        is_active=is_active,
    )
    session.add(course)
    session.commit()
    session.refresh(course)
    return course


# ── Academics: Group ─────────────────────────────────────────────────────────

def create_test_group(
    session: Session,
    course_id: int,
    name: str = None,
    instructor_id: Optional[int] = None,
    level_number: int = 1,
    max_capacity: Optional[int] = None,
    default_day: Optional[str] = None,
    default_time_start: Optional[time] = None,
    default_time_end: Optional[time] = None,
    status: str = "active",
    notes: Optional[str] = None,
):
    from app.modules.academics.models import Group
    if name is None:
        name = _unique("Group")
    if default_time_start is None:
        default_time_start = time(14, 0)
    if default_time_end is None:
        default_time_end = time(15, 30)
    group = Group(
        name=name,
        course_id=course_id,
        instructor_id=instructor_id,
        level_number=level_number,
        max_capacity=max_capacity,
        default_day=default_day,
        default_time_start=default_time_start,
        default_time_end=default_time_end,
        status=status,
        notes=notes,
    )
    session.add(group)
    session.commit()
    session.refresh(group)
    return group


# ── Academics: GroupLevel ────────────────────────────────────────────────────

def create_test_group_level(
    session: Session,
    group_id: int,
    level_number: int = 1,
    course_id: Optional[int] = None,
    instructor_id: Optional[int] = None,
    sessions_planned: int = 5,
    status: str = "active",
    price_override: Optional[float] = None,
):
    from app.modules.academics.models.group_level_models import GroupLevel
    level = GroupLevel(
        group_id=group_id,
        level_number=level_number,
        course_id=course_id or 0,
        instructor_id=instructor_id,
        sessions_planned=sessions_planned,
        status=status,
        price_override=price_override,
    )
    session.add(level)
    session.commit()
    session.refresh(level)
    return level


# ── Academics: CourseSession ─────────────────────────────────────────────────

def create_test_session(
    session: Session,
    group_id: int,
    level_number: int = 1,
    session_number: int = 1,
    session_date: Optional[date] = None,
    start_time: Optional[time] = None,
    end_time: Optional[time] = None,
    actual_instructor_id: Optional[int] = None,
    status: str = "scheduled",
    is_extra_session: bool = False,
    notes: Optional[str] = None,
    group_level_id: Optional[int] = None,
):
    from app.modules.academics.models.session_models import CourseSession
    if session_date is None:
        session_date = date.today() + timedelta(days=session_number * 7)
    if start_time is None:
        start_time = time(14, 0)
    if end_time is None:
        end_time = time(15, 30)
    session_obj = CourseSession(
        group_id=group_id,
        group_level_id=group_level_id,
        level_number=level_number,
        session_number=session_number,
        session_date=session_date,
        start_time=start_time,
        end_time=end_time,
        actual_instructor_id=actual_instructor_id,
        status=status,
        is_extra_session=is_extra_session,
        notes=notes,
    )
    session.add(session_obj)
    session.commit()
    session.refresh(session_obj)
    return session_obj


# ── Enrollments: Enrollment ──────────────────────────────────────────────────

def create_test_enrollment(
    session: Session,
    student_id: int,
    group_id: int,
    level_number: int = 1,
    status: str = "active",
    amount_due: Optional[float] = None,
    discount_applied: float = 0.0,
    notes: Optional[str] = None,
    created_by: Optional[int] = None,
    transferred_from: Optional[int] = None,
):
    from app.modules.enrollments.models.enrollment_models import Enrollment
    from datetime import datetime
    enrollment = Enrollment(
        student_id=student_id,
        group_id=group_id,
        level_number=level_number,
        status=status,
        amount_due=amount_due,
        discount_applied=discount_applied,
        notes=notes,
        created_by=created_by,
        transferred_from=transferred_from,
        enrolled_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )
    session.add(enrollment)
    session.commit()
    session.refresh(enrollment)
    return enrollment


# ── Attendance ───────────────────────────────────────────────────────────────

def create_test_attendance(
    session: Session,
    student_id: int,
    session_id: int,
    enrollment_id: int,
    status: str = "present",
    marked_by: Optional[int] = None,
):
    from app.modules.attendance.models.attendance_models import Attendance
    from datetime import datetime
    att = Attendance(
        student_id=student_id,
        session_id=session_id,
        enrollment_id=enrollment_id,
        status=status,
        marked_by=marked_by,
        marked_at=datetime.utcnow(),
    )
    session.add(att)
    session.commit()
    session.refresh(att)
    return att


# ── Competitions ─────────────────────────────────────────────────────────────

def create_test_competition(
    session: Session,
    name: Optional[str] = None,
    edition_year: int = 2025,
    competition_date: Optional[date] = None,
    location: Optional[str] = None,
    fee_per_student: float = 0.0,
    notes: Optional[str] = None,
):
    from app.modules.competitions.models.competition_models import Competition
    if name is None:
        name = _unique("Comp")
    if competition_date is None:
        competition_date = date.today() + timedelta(days=90)
    comp = Competition(
        name=name,
        edition_year=edition_year,
        competition_date=competition_date,
        location=location,
        fee_per_student=fee_per_student,
        notes=notes,
    )
    session.add(comp)
    session.commit()
    session.refresh(comp)
    return comp


def create_test_team(
    session: Session,
    competition_id: int,
    team_name: Optional[str] = None,
    category: str = "Robotics",
    subcategory: Optional[str] = None,
    coach_id: Optional[int] = None,
    group_id: Optional[int] = None,
    project_name: Optional[str] = None,
    notes: Optional[str] = None,
):
    from app.modules.competitions.models.team_models import Team
    if team_name is None:
        team_name = _unique("Team")
    team = Team(
        competition_id=competition_id,
        team_name=team_name,
        category=category,
        subcategory=subcategory,
        coach_id=coach_id,
        group_id=group_id,
        project_name=project_name,
        notes=notes,
    )
    session.add(team)
    session.commit()
    session.refresh(team)
    return team


def create_test_team_member(
    session: Session,
    team_id: int,
    student_id: int,
    amount_due: float = 0.0,
    amount_paid: float = 0.0,
):
    from app.modules.competitions.models.team_models import TeamMember
    tm = TeamMember(
        team_id=team_id,
        student_id=student_id,
        amount_due=amount_due,
        amount_paid=amount_paid,
    )
    session.add(tm)
    session.commit()
    session.refresh(tm)
    return tm


# ── Finance: Receipt ─────────────────────────────────────────────────────────

def create_test_receipt(
    session: Session,
    payer_name: Optional[str] = "Test Payer",
    payment_method: str = "cash",
    received_by: Optional[int] = None,
    receipt_number: Optional[str] = None,
    notes: Optional[str] = None,
    paid_at: Optional[datetime] = None,
):
    from app.modules.finance.models.receipt import Receipt
    from datetime import datetime
    if paid_at is None:
        paid_at = datetime.utcnow()
    receipt = Receipt(
        payer_name=payer_name,
        payment_method=payment_method,
        received_by=received_by,
        receipt_number=receipt_number,
        notes=notes,
        paid_at=paid_at,
    )
    session.add(receipt)
    session.commit()
    session.refresh(receipt)
    return receipt


def create_test_payment(
    session: Session,
    receipt_id: int,
    student_id: int,
    amount: float,
    enrollment_id: Optional[int] = None,
    team_member_id: Optional[int] = None,
    transaction_type: str = "payment",
    payment_type: Optional[str] = "course_level",
    discount_amount: float = 0.0,
    notes: Optional[str] = None,
):
    from app.modules.finance.models.payment import Payment
    from datetime import datetime
    pmt = Payment(
        receipt_id=receipt_id,
        student_id=student_id,
        enrollment_id=enrollment_id,
        team_member_id=team_member_id,
        amount=amount,
        transaction_type=transaction_type,
        payment_type=payment_type,
        discount_amount=discount_amount,
        notes=notes,
        created_at=datetime.utcnow(),
    )
    session.add(pmt)
    session.commit()
    session.refresh(pmt)
    return pmt


# ── Bundle: Minimal course + group + level + sessions ───────────────────────

def create_minimal_group_bundle(
    session: Session,
    course_name: Optional[str] = None,
    group_name: Optional[str] = None,
    instructor_id: Optional[int] = None,
    session_count: int = 3,
    level_number: int = 1,
):
    """Creates a course, group, group_level, and sessions in one call."""
    course = create_test_course(session, name=course_name)
    group = create_test_group(session, course_id=course.id, name=group_name, instructor_id=instructor_id)
    level = create_test_group_level(
        session, group_id=group.id, level_number=level_number, course_id=course.id,
        instructor_id=instructor_id, sessions_planned=session_count,
    )
    sessions = []
    for i in range(1, session_count + 1):
        s = create_test_session(
            session, group_id=group.id, level_number=level_number,
            session_number=i, group_level_id=level.id,
        )
        sessions.append(s)
    return course, group, level, sessions


# ── Bundle: Student + parent + enrollment ───────────────────────────────────

def create_student_with_enrollment(
    session: Session,
    group_id: int,
    level_number: int = 1,
    student_name: Optional[str] = None,
    parent_name: Optional[str] = None,
    amount_due: Optional[float] = None,
):
    """Creates a parent, student, link, and enrollment in one call."""
    parent = create_test_parent(session, full_name=parent_name or _unique("Parent"))
    student = create_test_student(session, full_name=student_name or _unique("Student"), parent_id=parent.id)
    enrollment = create_test_enrollment(
        session, student_id=student.id, group_id=group_id,
        level_number=level_number, amount_due=amount_due,
    )
    return parent, student, enrollment
