from datetime import date, datetime

from app.db.connection import get_session
from app.shared.datetime_utils import date_at_utc_midnight
from app.modules.crm.models.student_models import Student, StudentStatus
from app.modules.crm.schemas.student_schemas import UpdateStudentDTO, RegisterStudentCommandDTO
import app.modules.crm.repositories.student_repository as repo
import app.modules.crm.repositories.parent_repository as parent_repository
from app.shared.audit_utils import apply_create_audit, apply_update_audit
from app.shared.exceptions import NotFoundError

class StudentService:
    """Encapsulates all Student business logic and interactions."""

    def register_student(
        self,
        command_dto: RegisterStudentCommandDTO,
    ) -> tuple[Student, list[dict]]:
        """
        Registers a student and links them to an existing parent as primary contact
        using the unified RegisterStudentCommandDTO parameters.
        Returns (student, siblings) so the UI can offer the sibling discount.
        """

        with get_session() as session:
            if command_dto.parent_id is not None:
                parent = parent_repository.get_parent_by_id(session, command_dto.parent_id)
                if not parent:
                    raise NotFoundError(f"Parent with ID {command_dto.parent_id} not found.")

            dob = command_dto.student_data.date_of_birth
            if dob is not None and isinstance(dob, date) and not isinstance(dob, datetime):
                dob = date_at_utc_midnight(dob)

            student = Student(
                full_name=command_dto.student_data.full_name,
                date_of_birth=dob,
                gender=command_dto.student_data.gender,
                phone=command_dto.student_data.phone,
                notes=command_dto.student_data.notes,
            )
            apply_create_audit(student, user_id=command_dto.created_by_user_id)
            created_student = repo.create_student(session, student)
            
            if command_dto.parent_id is not None:
                repo.link_parent(
                    session=session,
                    student_id=created_student.id,
                    parent_id=command_dto.parent_id,
                    relationship=command_dto.relationship,
                    is_primary=True,
                )
            student_id = created_student.id
            student_obj = created_student

        # Sibling detection in a separate session so the committed link is visible
        siblings = self.find_siblings(student_id)
        return student_obj, siblings

    def get_student_by_id(self, student_id: int) -> Student | None:
        with get_session() as session:
            return repo.get_student_by_id(session, student_id)

    def get_student_parents(self, student_id: int) -> list:
        with get_session() as session:
            links = list(repo.get_student_parents(session, student_id))
            for link in links:
                _ = link.parent  # force lazy load inside session
            return links

    def search_students(self, query: str) -> list[Student]:
        if not query or len(query.strip()) < 2:
            return []
        with get_session() as session:
            return list(repo.search_students(session, query.strip()))

    def list_all_students(self, skip: int = 0, limit: int = 200) -> list[Student]:
        with get_session() as session:
            return list(repo.get_all_students(session, skip, limit))

    def count_students(self, active_only: bool = True) -> int:
        """Returns total count of students for pagination."""
        with get_session() as session:
            return repo.count_students(session, active_only)

    def update_student(self, student_id: int, data: UpdateStudentDTO) -> Student:
        """Updates an existing student's fields."""
        with get_session() as session:
            student = repo.get_student_by_id(session, student_id)
            if not student:
                raise NotFoundError(f"Student with ID {student_id} not found.")

            for key, value in data.model_dump(exclude_unset=True).items():
                if hasattr(student, key) and key != "id":
                    setattr(student, key, value)
            apply_update_audit(student)
            session.add(student)
            session.commit()
            session.refresh(student)
            return student

    def find_siblings(self, student_id: int) -> list[dict]:
        with get_session() as session:
            return repo.get_siblings(session, student_id)

    def get_parent_students(self, parent_id: int) -> list[Student]:
        with get_session() as session:
            return repo.get_students_by_parent_id(session, parent_id)

    # ── NEW: Status Management Methods ────────────────────────────────────────────

    def update_student_status(
        self,
        student_id: int,
        new_status: StudentStatus,
        user_id: int | None = None,
        notes: str | None = None
    ) -> Student:
        """Update student status with validation and audit logging."""
        with get_session() as session:
            # Validate status transition
            student = repo.get_student_by_id(session, student_id)
            if not student:
                raise NotFoundError(f"Student with ID {student_id} not found")
            
            # Perform update with audit
            updated = repo.update_student_status(
                session, student_id, new_status, user_id, notes
            )
            if not updated:
                raise NotFoundError(f"Student with ID {student_id} not found")
            
            apply_update_audit(updated)
            session.commit()
            session.refresh(updated)
            return updated

    def toggle_student_status(
        self,
        student_id: int,
        user_id: int | None = None,
        notes: str | None = None
    ) -> Student:
        """Toggle between active and waiting status."""
        with get_session() as session:
            student = repo.get_student_by_id(session, student_id)
            if not student:
                raise NotFoundError(f"Student with ID {student_id} not found")
            
            # Determine new status based on current state
            if student.status == StudentStatus.ACTIVE:
                new_status = StudentStatus.WAITING
            elif student.status == StudentStatus.WAITING:
                new_status = StudentStatus.ACTIVE
            else:
                raise ValueError(
                    f"Cannot toggle status from {student.status}. "
                    "Only active/waiting transitions are supported."
                )
            
            return self.update_student_status(student_id, new_status, user_id, notes)

    def get_waiting_list(
        self,
        skip: int = 0,
        limit: int = 200,
        order_by_priority: bool = True
    ) -> list[Student]:
        """Get students on waiting list."""
        with get_session() as session:
            return list(repo.get_waiting_list(session, skip, limit, order_by_priority))

    def set_waiting_priority(
        self,
        student_id: int,
        priority: int,
        user_id: int | None = None
    ) -> Student:
        """Set priority for a student on the waiting list."""
        with get_session() as session:
            student = repo.set_waiting_priority(session, student_id, priority)
            if not student:
                raise NotFoundError(
                    f"Student {student_id} not found or not on waiting list"
                )
            
            # Add audit note
            history = student.status_history or []
            if isinstance(history, str):
                import json
                history = json.loads(history) if history else []
            
            history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "changed_by": user_id,
                "action": "priority_change",
                "new_priority": priority
            })
            student.status_history = history
            
            apply_update_audit(student)
            session.commit()
            session.refresh(student)
            return student

    def get_students_by_status(
        self,
        status: StudentStatus,
        skip: int = 0,
        limit: int = 200
    ) -> list[Student]:
        """Get students by their enrollment status."""
        with get_session() as session:
            return list(repo.get_students_by_status(session, status, skip, limit))

    def get_student_status_summary(self) -> dict:
        """Get counts of students by status."""
        with get_session() as session:
            return {
                "total": repo.count_students(session, active_only=False),
                "active": repo.count_students_by_status(session, StudentStatus.ACTIVE),
                "waiting": repo.count_students_by_status(session, StudentStatus.WAITING),
                "inactive": repo.count_students_by_status(session, StudentStatus.INACTIVE),
                "graduated": repo.count_students_by_status(session, StudentStatus.GRADUATED),
            }

    def get_student_status_history(self, student_id: int) -> list[dict]:
        """Get status change history for a student."""
        with get_session() as session:
            student = repo.get_student_by_id(session, student_id)
            if not student:
                raise NotFoundError(f"Student with ID {student_id} not found")
            
            history = student.status_history or []
            if isinstance(history, str):
                import json
                return json.loads(history) if history else []
            return history if isinstance(history, list) else []

    def delete_student_by_id(self, student_id: int) -> bool:
        """Delete a student by ID."""
        with get_session() as session:
            return repo.delete_student_by_id(session, student_id)

    # ── NEW: Student Detail Methods ──────────────────────────────────────────────

    def get_student_with_details(self, student_id: int) -> "StudentWithDetails":
        """
        Get complete student profile with relationships and balance summary.
        
        Returns StudentWithDetails DTO including:
        - Core student fields
        - Primary parent information
        - Active enrollments with group/course details
        - Balance summary (total_due, discounts, paid, net_balance)
        - Siblings sharing the same parent
        """
        from datetime import datetime
        from app.api.schemas.crm.student_details import (
            StudentWithDetails, ParentInfo, StudentBalanceSummary
        )
        
        with get_session() as session:
            # Get student with primary parent
            student_with_parent = repo.get_student_with_parent(session, student_id)
            if not student_with_parent:
                raise NotFoundError(f"Student with ID {student_id} not found")
            
            student, primary_parent = student_with_parent
            
            # Get enrollments with group/course info
            enrollments_data = repo.get_student_enrollments_with_details(session, student_id)
            
            # Get balance summary
            balance_data = repo.get_student_balance_summary(session, student_id)
            
            # Get siblings
            siblings_data = repo.get_student_siblings_with_details(session, student_id)
            
            # Calculate age if DOB exists
            age = None
            if student.date_of_birth:
                today = datetime.now()
                age = today.year - student.date_of_birth.year
                if (today.month, today.day) < (student.date_of_birth.month, student.date_of_birth.day):
                    age -= 1
            
            # Build and return DTO
            return StudentWithDetails(
                id=student.id,
                full_name=student.full_name,
                date_of_birth=student.date_of_birth,
                age=age,
                gender=student.gender,
                phone=student.phone,
                notes=student.notes,
                status=str(student.status) if student.status else "active",
                is_active=student.is_active,
                waiting_since=student.waiting_since,
                waiting_priority=student.waiting_priority,
                waiting_notes=student.waiting_notes,
                created_at=student.created_at,
                updated_at=student.updated_at,
                primary_parent=ParentInfo.model_validate(primary_parent) if primary_parent else None,
                enrollments=enrollments_data,
                balance_summary=balance_data if balance_data else StudentBalanceSummary(),
                siblings=siblings_data,
            )

    def get_student_siblings_enhanced(self, student_id: int) -> "list[SiblingInfo]":
        """
        Get siblings with detailed information including enrollment counts.
        
        Returns list of SiblingInfo DTOs who share the same parent(s).
        """
        from app.api.schemas.crm.student_details import SiblingInfo
        
        with get_session() as session:
            siblings = repo.get_student_siblings_with_details(session, student_id)
            return siblings
