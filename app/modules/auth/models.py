from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Employee(SQLModel, table=True):
    __tablename__ = "employees"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    job_title: Optional[str] = None
    employment_type: Optional[str] = None
    monthly_salary: Optional[float] = None
    contract_percentage: Optional[float] = 25.00
    is_active: bool = True
    hired_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True)
    password_hash: str
    employee_id: Optional[int] = Field(default=None, foreign_key="employees.id")
    role: str
    is_active: bool = True
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
