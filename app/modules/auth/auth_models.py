from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

# --- Employee Schemas ---

class EmployeeBase(SQLModel):
    full_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    job_title: Optional[str] = None
    employment_type: Optional[str] = None
    monthly_salary: Optional[float] = None
    contract_percentage: Optional[float] = 25.00
    is_active: bool = True

class Employee(EmployeeBase, table=True):
    __tablename__ = "employees"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    hired_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeRead(EmployeeBase):
    id: int
    hired_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# --- User Schemas ---

class UserBase(SQLModel):
    username: str = Field(unique=True)
    role: str
    is_active: bool = True
    employee_id: Optional[int] = Field(default=None, foreign_key="employees.id")

class User(UserBase, table=True):
    """The raw database user table containing sensitive hashes."""
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    password_hash: str
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None

class UserCreate(UserBase):
    """Network-facing DTO for creating a new user, accepts a raw password to be hashed."""
    password: str

class UserRead(UserBase):
    """Safe network-facing response that completely excludes the password_hash."""
    id: int
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None