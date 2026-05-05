"""Employee Validators

Pure validation functions for employee data.
"""
from app.modules.hr.constants import (
    MIN_NATIONAL_ID_LENGTH,
    MIN_PHONE_LENGTH,
    EMPLOYMENT_TYPES,
)
from app.shared.exceptions import ValidationError


def validate_national_id(nid: str) -> str:
    """Validate and clean national ID.
    
    Args:
        nid: Raw national ID string
        
    Returns:
        Cleaned national ID
        
    Raises:
        ValidationError: If ID is too short
    """
    cleaned = nid.strip()
    if len(cleaned) < MIN_NATIONAL_ID_LENGTH:
        raise ValidationError(
            f"National ID must be at least {MIN_NATIONAL_ID_LENGTH} characters"
        )
    return cleaned


def validate_phone(phone: str) -> str:
    """Validate and clean phone number.
    
    Args:
        phone: Raw phone string
        
    Returns:
        Cleaned phone (digits only)
        
    Raises:
        ValidationError: If phone is too short
    """
    cleaned = "".join(c for c in phone if c.isdigit())
    if len(cleaned) < MIN_PHONE_LENGTH:
        raise ValidationError(
            f"Phone must have at least {MIN_PHONE_LENGTH} digits"
        )
    return cleaned


def validate_employment_type(et: str) -> str:
    """Validate employment type.
    
    Args:
        et: Employment type string
        
    Returns:
        Validated employment type
        
    Raises:
        ValidationError: If invalid type
    """
    if et not in EMPLOYMENT_TYPES:
        raise ValidationError(
            f"Invalid employment_type {et!r}. "
            f"Allowed: {', '.join(sorted(EMPLOYMENT_TYPES))}"
        )
    return et
