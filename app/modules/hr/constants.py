"""HR Module Constants

Domain constants and field definitions for the HR module.
"""
from typing import Final, FrozenSet

# Employee field whitelist for create/update operations
EMPLOYEE_FIELD_KEYS: Final[FrozenSet[str]] = frozenset(
    {
        "full_name",
        "phone",
        "email",
        "national_id",
        "university",
        "major",
        "is_graduate",
        "job_title",
        "employment_type",
        "monthly_salary",
        "contract_percentage",
        "is_active",
    }
)

# Validation constants
MIN_NATIONAL_ID_LENGTH: Final[int] = 14
MIN_PHONE_LENGTH: Final[int] = 11
EMPLOYEE_PAGE_SIZE: Final[int] = 20
MAX_PAGE_SIZE: Final[int] = 100

# Default values
DEFAULT_CONTRACT_PERCENTAGE: Final[float] = 25.0
