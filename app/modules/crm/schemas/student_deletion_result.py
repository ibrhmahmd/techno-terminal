from pydantic import BaseModel


class StudentDeletionResult(BaseModel):
    """Result of a soft/hard delete or restore operation."""
    student_id: int
    status: str  # soft_deleted, restored, permanently_deleted
