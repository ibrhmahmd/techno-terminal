from pydantic import BaseModel, field_validator
from typing import Optional
import re


class DailyReportRequest(BaseModel):
    email_recipients: Optional[list[str]] = None

    @field_validator("email_recipients")
    @classmethod
    def validate_emails(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is None:
            return v
        if not v:
            return None
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        for email in v:
            if not re.match(pattern, email):
                raise ValueError(f"Invalid email: {email}")
        return v

WeeklyReportRequest = DailyReportRequest
MonthlyReportRequest = DailyReportRequest
