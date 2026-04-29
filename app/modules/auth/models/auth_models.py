from datetime import datetime
from typing import Optional
from pydantic import field_validator
from sqlmodel import SQLModel, Field

from app.modules.hr.models import Employee
from app.modules.auth.constants import ALL_ROLE_VALUES

class UserBase(SQLModel):
    username: str = Field(unique=True)
    role: str
    is_active: bool = True
    employee_id: Optional[int] = Field(default=None, foreign_key="employees.id")

    @field_validator("role")
    @classmethod
    def role_must_be_known(cls, v: str) -> str:
        if v not in ALL_ROLE_VALUES:
            raise ValueError(f"role must be one of {sorted(ALL_ROLE_VALUES)}")
        return v

class User(UserBase, table=True):
    """The raw database user table containing safe Supabase references."""
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    supabase_uid: str = Field(unique=True)
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
