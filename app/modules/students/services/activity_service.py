"""
app/modules/students/services/activity_service.py
────────────────────────────────────────────────
Student activity logging and history tracking service.
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from sqlmodel import Session, select, func

from app.db.connection import get_session
from app.modules.students.models.activity_models import (
    StudentActivityLog,
    StudentActivityLogCreate,
    StudentActivityLogRead,
    StudentEnrollmentHistory,
    StudentPaymentHistory,
    StudentCompetitionHistory,
    ActivityTimelineFilter,
    StudentActivitySummary,
)
from app.modules.crm.models.student_models import Student
from app.modules.students.schemas.activity_schemas import (
    LogActivityRequestDTO,
    EnrollmentChangeRequestDTO,
    ActivitySearchRequestDTO,
    ActivityFilterRequestDTO,
)
from app.shared.exceptions import NotFoundError


class ActivityService:
    """Service for logging and querying student activities."""
    
    def __init__(self, db = None):
        """Initialize with optional database session."""
        self._db = db
        self._own_session = db is None
    
    def _get_db(self):
        """Get or create database session."""
        if self._db is None:
            self._db = get_session().__enter__()
        return self._db
    
    def __del__(self):
        """Cleanup session if owned."""
        if self._own_session and self._db:
            self._db.close()
    
    def log_activity(
        self,
        activity: StudentActivityLogCreate
    ) -> StudentActivityLog:
        """
        Log a student activity.
        
        Args:
            activity: Activity details to log
            
        Returns:
            Created activity log entry
        """
        db = self._get_db()
        
        log_entry = StudentActivityLog(
            student_id=activity.student_id,
            activity_type=activity.activity_type,
            activity_subtype=activity.activity_subtype,
            reference_type=activity.reference_type,
            reference_id=activity.reference_id,
            description=activity.description,
            metadata=activity.metadata or {},
            performed_by=activity.performed_by,
            created_at=datetime.utcnow()
        )
        
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        
        return log_entry
    
    def log_activity_simple(
        self,
        request: LogActivityRequestDTO
    ) -> StudentActivityLog:
        """
        Quick method to log an activity using a request DTO.
        Args:
            request: LogActivityRequestDTO containing all activity details
        Returns:
            Created activity log entry
        """
        activity = StudentActivityLogCreate(
            student_id=request.student_id,
            activity_type=request.activity_type,
            activity_subtype=request.activity_subtype,
            reference_type=request.reference_type,
            reference_id=request.reference_id,
            description=request.description,
            metadata=request.metadata,
            performed_by=request.performed_by
        )
        
        return self.log_activity(activity)
    
    def get_activity_timeline(
        self,
        student_id: int,
        filter_params: Optional[ActivityTimelineFilter] = None
    ) -> List[StudentActivityLogRead]:
        """
        Get activity timeline for a student.
        
        Args:
            student_id: Student to query
            filter_params: Optional filter parameters
            
        Returns:
            List of activity log entries
        """
        db = self._get_db()
        
        query = select(StudentActivityLog).where(
            StudentActivityLog.student_id == student_id
        )
        
        # Apply filters
        if filter_params:
            if filter_params.activity_types:
                query = query.where(
                    StudentActivityLog.activity_type.in_(filter_params.activity_types)
                )
            
            if filter_params.date_from:
                query = query.where(StudentActivityLog.created_at >= filter_params.date_from)
            
            if filter_params.date_to:
                query = query.where(StudentActivityLog.created_at <= filter_params.date_to)
            
            if filter_params.performed_by:
                query = query.where(StudentActivityLog.performed_by == filter_params.performed_by)
            
            if filter_params.reference_type:
                query = query.where(StudentActivityLog.reference_type == filter_params.reference_type)
            
            if filter_params.reference_id:
                query = query.where(StudentActivityLog.reference_id == filter_params.reference_id)
            
            # Pagination
            query = query.offset(filter_params.skip).limit(filter_params.limit)
        else:
            query = query.order_by(StudentActivityLog.created_at.desc()).limit(50)
        
        activities = db.exec(query.order_by(StudentActivityLog.created_at.desc())).all()
        
        # Enrich with performer names
        result = []
        for activity in activities:
            read_model = StudentActivityLogRead(
                id=activity.id,
                student_id=activity.student_id,
                activity_type=activity.activity_type,
                activity_subtype=activity.activity_subtype,
                reference_type=activity.reference_type,
                reference_id=activity.reference_id,
                description=activity.description,
                metadata=activity.metadata,
                performed_by=activity.performed_by,
                performed_by_name=None,  # Will be populated if needed
                created_at=activity.created_at
            )
            result.append(read_model)
        
        return result
    
    def get_activity_summary(self, student_id: int) -> StudentActivitySummary:
        """
        Get summary of student activities.
        
        Args:
            student_id: Student to summarize
            
        Returns:
            Activity summary statistics
        """
        db = self._get_db()
        
        # Count by type
        type_counts = db.exec(
            select(
                StudentActivityLog.activity_type,
                func.count(StudentActivityLog.id)
            )
            .where(StudentActivityLog.student_id == student_id)
            .group_by(StudentActivityLog.activity_type)
        ).all()
        
        activities_by_type = {t: c for t, c in type_counts}
        
        # Total activities
        total = sum(activities_by_type.values())
        
        # First and last activity dates
        first_activity = db.exec(
            select(StudentActivityLog.created_at)
            .where(StudentActivityLog.student_id == student_id)
            .order_by(StudentActivityLog.created_at.asc())
        ).first()
        
        last_activity = db.exec(
            select(StudentActivityLog.created_at)
            .where(StudentActivityLog.student_id == student_id)
            .order_by(StudentActivityLog.created_at.desc())
        ).first()
        
        return StudentActivitySummary(
            student_id=student_id,
            total_activities=total,
            activities_by_type=activities_by_type,
            first_activity_date=first_activity[0] if first_activity else None,
            last_activity_date=last_activity[0] if last_activity else None
        )
    
    def get_recent_activities(
        self,
        days: int = 7,
        limit: int = 100
    ) -> List[StudentActivityLogRead]:
        """
        Get recent activities across all students.
        
        Args:
            days: Number of days to look back
            limit: Maximum results to return
            
        Returns:
            List of recent activity log entries
        """
        db = self._get_db()
        
        since = datetime.utcnow() - timedelta(days=days)
        
        activities = db.exec(
            select(StudentActivityLog)
            .where(StudentActivityLog.created_at >= since)
            .order_by(StudentActivityLog.created_at.desc())
            .limit(limit)
        ).all()
        
        return [
            StudentActivityLogRead(
                id=a.id,
                student_id=a.student_id,
                activity_type=a.activity_type,
                activity_subtype=a.activity_subtype,
                reference_type=a.reference_type,
                reference_id=a.reference_id,
                description=a.description,
                metadata=a.metadata,
                performed_by=a.performed_by,
                performed_by_name=None,
                created_at=a.created_at
            )
            for a in activities
        ]
    
    def search_activities(
        self,
        activity_type: Optional[str] = None,
        reference_type: Optional[str] = None,
        reference_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[StudentActivityLogRead]:
        """
        Search activities with filters.
        
        Args:
            activity_type: Filter by activity type
            reference_type: Filter by reference type
            reference_id: Filter by reference ID
            date_from: Start date
            date_to: End date
            skip: Pagination skip
            limit: Pagination limit
            
        Returns:
            List of matching activity log entries
        """
        db = self._get_db()
        
        query = select(StudentActivityLog)
        
        if activity_type:
            query = query.where(StudentActivityLog.activity_type == activity_type)
        
        if reference_type:
            query = query.where(StudentActivityLog.reference_type == reference_type)
        
        if reference_id:
            query = query.where(StudentActivityLog.reference_id == reference_id)
        
        if date_from:
            query = query.where(StudentActivityLog.created_at >= date_from)
        
        if date_to:
            query = query.where(StudentActivityLog.created_at <= date_to)
        
        activities = db.exec(
            query.order_by(StudentActivityLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        ).all()
        
        return [
            StudentActivityLogRead(
                id=a.id,
                student_id=a.student_id,
                activity_type=a.activity_type,
                activity_subtype=a.activity_subtype,
                reference_type=a.reference_type,
                reference_id=a.reference_id,
                description=a.description,
                metadata=a.metadata,
                performed_by=a.performed_by,
                performed_by_name=None,
                created_at=a.created_at
            )
            for a in activities
        ]
    
    def log_enrollment_change(
        self,
        request: EnrollmentChangeRequestDTO
    ) -> StudentEnrollmentHistory:
        """
        Log an enrollment change in the history table.
        
        Args:
            request: EnrollmentChangeRequestDTO containing all enrollment change details
            
        Returns:
            Created enrollment history record
        """
        db = self._get_db()
        
        history = StudentEnrollmentHistory(
            student_id=request.student_id,
            enrollment_id=request.enrollment_id,
            group_id=request.group_id,
            level_number=request.level_number,
            action=request.action,
            action_date=datetime.utcnow(),
            previous_group_id=request.previous_group_id,
            previous_level_number=request.previous_level_number,
            amount_due=request.amount_due,
            performed_by=request.performed_by,
            notes=request.notes,
            created_at=datetime.utcnow()
        )
        
        db.add(history)
        db.commit()
        db.refresh(history)
        
        # Also log as activity
        self.log_activity_simple(
            LogActivityRequestDTO(
                student_id=request.student_id,
                activity_type='enrollment',
                activity_subtype=f'enrollment_{request.action}',
                description=f'Enrollment {request.action} - Group {request.group_id}, Level {request.level_number}',
                reference_type='enrollment',
                reference_id=request.enrollment_id,
                metadata={
                    'previous_group_id': request.previous_group_id,
                    'previous_level_number': request.previous_level_number,
                    'amount_due': request.amount_due
                },
                performed_by=request.performed_by
            )
        )
        
        return history
    
    def get_enrollment_history(
        self,
        student_id: int,
        enrollment_id: Optional[int] = None
    ) -> List[StudentEnrollmentHistory]:
        """
        Get enrollment history for a student.
        Args:
            student_id: Student ID
            enrollment_id: Optional specific enrollment to filter by
        Returns:
            List of enrollment history entries
        """
        db = self._get_db()
        
        query = select(StudentEnrollmentHistory).where(
            StudentEnrollmentHistory.student_id == student_id
        )
        
        if enrollment_id:
            query = query.where(StudentEnrollmentHistory.enrollment_id == enrollment_id)
        
        return db.exec(
            query.order_by(StudentEnrollmentHistory.action_date.desc())
        ).all()


def get_activity_service(db = None):
    """Factory function to create ActivityService instance."""
    return ActivityService(db)
