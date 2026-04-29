"""
Test database utilities for creating test data.
"""
from sqlmodel import Session
from typing import Optional


def create_test_parent(
    session: Session,
    full_name: str = "Test Parent",
    phone_primary: str = "+201000000001",
    email: Optional[str] = None
):
    """
    Create a test parent record.
    
    Args:
        session: Database session
        full_name: Parent's full name
        phone_primary: Primary phone number
        email: Optional email address
        
    Returns:
        Created Parent instance
    """
    from app.modules.crm.models import Parent
    
    parent = Parent(
        full_name=full_name,
        phone_primary=phone_primary,
        email=email
    )
    session.add(parent)
    session.commit()
    session.refresh(parent)
    return parent


def create_test_student(
    session: Session,
    full_name: str = "Test Student",
    birth_date: Optional[str] = None,
    parent_id: Optional[int] = None
):
    """
    Create a test student record.
    
    Args:
        session: Database session
        full_name: Student's full name
        birth_date: Birth date (YYYY-MM-DD format)
        parent_id: Optional parent ID to link
        
    Returns:
        Created Student instance
    """
    from app.modules.crm.models import Student
    
    student = Student(
        full_name=full_name,
        birth_date=birth_date
    )
    session.add(student)
    session.commit()
    session.refresh(student)
    
    # Link to parent if provided
    if parent_id:
        from app.modules.crm.models import StudentParent
        link = StudentParent(
            student_id=student.id,
            parent_id=parent_id,
            is_primary=True
        )
        session.add(link)
        session.commit()
    
    return student


def create_test_course(
    session: Session,
    name: str = None,  # Will generate unique name if not provided
    category: str = "software",
    price_per_level: float = 1000.0
):
    """
    Create a test course record.
    
    Args:
        session: Database session
        name: Course name (auto-generated with timestamp if not provided)
        category: Course category (software, hardware, steam, other)
        price_per_level: Price per level
        
    Returns:
        Created Course instance
    """
    from app.modules.academics.models import Course
    import time
    
    # Generate unique name if not provided
    if name is None:
        name = f"Test Course {int(time.time() * 1000)}"
    
    course = Course(
        name=name,
        category=category,
        price_per_level=price_per_level
    )
    session.add(course)
    session.commit()
    session.refresh(course)
    return course


def create_test_group(
    session: Session,
    course_id: int,
    name: str = None,  # Will generate unique name if not provided
    level_number: int = 1,
    status: str = "active"
):
    """
    Create a test group record.
    
    Args:
        session: Database session
        course_id: Associated course ID
        name: Group name (auto-generated with timestamp if not provided)
        level_number: Current level number
        status: Group status (active, completed, cancelled)
        
    Returns:
        Created Group instance
    """
    from app.modules.academics.models import Group
    import time
    
    # Generate unique name if not provided
    if name is None:
        name = f"Test Group {int(time.time() * 1000)}"
    
    group = Group(
        name=name,
        course_id=course_id,
        level_number=level_number,
        status=status
    )
    session.add(group)
    session.commit()
    session.refresh(group)
    return group
