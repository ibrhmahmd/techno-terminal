from pydantic import BaseModel


class AttendanceStatsDTO(BaseModel):
    total_sessions: int
    attended: int
    absent: int
    cancelled: int
    attendance_rate: float

    model_config = {"frozen": True}
