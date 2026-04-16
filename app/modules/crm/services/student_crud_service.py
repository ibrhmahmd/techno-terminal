"""
StudentCrudService - Handles student CRUD operations and status management.
Implements IStudentService protocol with automatic activity logging.
"""
from datetime import date, datetime
from typing import Optional, Tuple, List

from app.shared.datetime_utils import date_at_utc_midnight
from app.modules.crm.models.student_models import Student, StudentStatus
from app.modules.crm.schemas.student_schemas import UpdateStudentDTO, RegisterStudentCommandDTO
from app.modules.crm.repositories.unit_of_work import StudentUnitOfWork
from app.modules.crm.services.activity_service import StudentActivityService
from app.shared.audit_utils import apply_create_audit, apply_update_audit
from app.shared.exceptions import NotFoundError


class StudentCrudService:
    """Service for student CRUD operations and status management with activity logging."""
    
    def __init__(
        self,
        uow: StudentUnitOfWork,
        activity_svc: Optional[StudentActivityService] = None,
    ) -> None:
        self._uow = uow
        self._activity_svc = activity_svc
    
    def register_student(
        self,
        command_dto: RegisterStudentCommandDTO,
    ) -> Tuple[Student, List[dict]]:
        """
        Registers a student and links them to an existing parent as primary contact.
        Returns (student, siblings) so the UI can offer the sibling discount.
        """
        # Validate parent exists if provided
        if command_dto.parent_id is not None:
            parent = self._uow.parents.get_by_id(command_dto.parent_id)
            if not parent:
                raise NotFoundError(f"Parent with ID {command_dto.parent_id} not found.")
        
        # Prepare date of birth
        dob = command_dto.student_data.date_of_birth
        if dob is not None and isinstance(dob, date) and not isinstance(dob, datetime):
            dob = date_at_utc_midnight(dob)
        
        # Create student
        student = Student(
            full_name=command_dto.student_data.full_name,
            date_of_birth=dob,
            gender=command_dto.student_data.gender,
            phone=command_dto.student_data.phone,
            notes=command_dto.student_data.notes,
        )
        apply_create_audit(student, user_id=command_dto.created_by_user_id)
        
        # Save student
        created_student = self._uow.students.create(student)
        self._uow.flush()
        
        # Link parent if provided
        if command_dto.parent_id is not None:
            self._uow.students.link_parent(
                student_id=created_student.id,
                parent_id=command_dto.parent_id,
                relationship=command_dto.relationship,
                is_primary=True,
            )
        
        self._uow.commit()

        # Log registration activity
        if self._activity_svc:
            from app.modules.crm.interfaces.dtos.log_registration_dto import LogRegistrationDTO
            self._activity_svc.log_registration(
                LogRegistrationDTO(
                    student_id=created_student.id,
                    student_name=created_student.full_name,
                    performed_by=getattr(command_dto, 'created_by', None),
                )
            )

        # Get siblings for discount calculation
        siblings = self.find_siblings(created_student.id)
        return created_student, siblings
    
    def get_by_id(self, student_id: int) -> Optional[Student]:
        """Get a student by ID."""
        return self._uow.students.get_by_id(student_id)
    
    def update_student(self, student_id: int, data: UpdateStudentDTO) -> Student:
        """Updates an existing student's fields."""
        student = self._uow.students.get_by_id(student_id)
        if not student:
            raise NotFoundError(f"Student with ID {student_id} not found.")
        
        for key, value in data.model_dump(exclude_unset=True).items():
            if hasattr(student, key) and key != "id":
                setattr(student, key, value)
        
        apply_update_audit(student)
        self._uow.commit()
        self._uow.flush()
        return student
    
    def update_status(
        self,
        student_id: int,
        new_status: StudentStatus,
        notes: Optional[str] = None,
        changed_by_user_id: Optional[int] = None,
    ) -> Student:
        """Update student status with audit logging."""
        student = self._uow.students.get_by_id(student_id)
        if not student:
            raise NotFoundError(f"Student with ID {student_id} not found.")
        
        old_status = student.status
        student.status = new_status
        apply_update_audit(student)
        
        # Log status change
        self._uow.students.log_status_change(
            student_id=student_id,
            previous_status=old_status.value if old_status else None,
            new_status=new_status.value,
            changed_by_user_id=changed_by_user_id,
            notes=notes,
        )
        
        # Log status change activity
        if student.status != new_status and self._activity_svc:
            from app.modules.crm.interfaces.dtos.log_status_change_dto import LogStatusChangeDTO
            self._activity_svc.log_status_change(
                LogStatusChangeDTO(
                    student_id=student.id,
                    old_status=student.status.value if hasattr(student.status, 'value') else str(student.status),
                    new_status=new_status.value if hasattr(new_status, 'value') else str(new_status),
                    performed_by=changed_by_user_id,
                )
            )

        return student

    def toggle_status(self, student_id: int, performed_by: Optional[int] = None) -> Student:
        """Toggle student between active and inactive."""
        student = self._uow.students.get_by_id(student_id)
        if not student:
            raise NotFoundError(f"Student with ID {student_id} not found.")

        old_status = student.status

        # Toggle is_active flag
        student.is_active = not student.is_active

        # Update status based on is_active
        if not student.is_active and student.status == StudentStatus.ACTIVE:
            student.status = StudentStatus.INACTIVE
        elif student.is_active and student.status == StudentStatus.INACTIVE:
            student.status = StudentStatus.ACTIVE

        apply_update_audit(student)
        self._uow.commit()

        # Log status change activity
        if self._activity_svc:
            from app.modules.crm.interfaces.dtos.log_status_change_dto import LogStatusChangeDTO
            self._activity_svc.log_status_change(
                LogStatusChangeDTO(
                    student_id=student.id,
                    old_status=old_status.value if hasattr(old_status, 'value') else str(old_status),
                    new_status=student.status.value if hasattr(student.status, 'value') else str(student.status),
                    performed_by=performed_by,
                )
            )

        return student
    
    def set_waiting_priority(
        self,
        student_id: int,
        priority: int,
        notes: Optional[str] = None,
    ) -> Student:
        """Set waiting list priority for a student."""
        student = self._uow.students.get_by_id(student_id)
        if not student:
            raise NotFoundError(f"Student with ID {student_id} not found.")
        
        old_priority = student.waiting_priority
        student.waiting_priority = priority
        
        if notes:
            student.waiting_notes = notes
        
        apply_update_audit(student)
        
        # Log priority change
        self._uow.students.log_status_change(
            student_id=student_id,
            previous_status=student.status.value if student.status else None,
            new_status=student.status.value if student.status else "waiting",
            notes=f"Priority changed from {old_priority} to {priority}. {notes or ''}",
            action="priority_change",
            new_priority=priority,
        )
        
        self._uow.commit()
        return student
    
    def delete_student(self, student_id: int, performed_by: Optional[int] = None) -> bool:
        """Delete a student by ID."""
        student = self._uow.students.get_by_id(student_id)
        if not student:
            return False

        student_name = student.full_name  # Save before deletion

        self._uow.students.delete(student_id)
        self._uow.commit()

        # Log deletion activity
        if self._activity_svc:
            from app.modules.crm.interfaces.dtos.log_deletion_dto import LogDeletionDTO
            self._activity_svc.log_deletion(
                LogDeletionDTO(
                    student_id=student_id,
                    student_name=student_name,
                    performed_by=performed_by,
                )
            )

        return True
    
    def find_siblings(self, student_id: int) -> List[dict]:
        """Find siblings for a student (share same parent)."""
        # Get student's parents
        parent_links = list(self._uow.students.get_student_parents(student_id))
        if not parent_links:
            return []
        
        # Get all sibling IDs (other children of these parents)
        sibling_ids = set()
        for link in parent_links:
            parent_id = link.parent_id
            children = self._uow.parents.get_parent_students(parent_id)
            for child_link in children:
                if child_link.student_id != student_id:
                    sibling_ids.add(child_link.student_id)
        
        # Get sibling details
        siblings = []
        for sid in sibling_ids:
            sib = self._uow.students.get_by_id(sid)
            if sib:
                siblings.append({
                    "id": sib.id,
                    "full_name": sib.full_name,
                    "date_of_birth": sib.date_of_birth,
                })
        
        return siblings
    
    def get_student_parents(self, student_id: int) -> list:
        """Get all parent links for a student."""
        return list(self._uow.students.get_student_parents(student_id))
