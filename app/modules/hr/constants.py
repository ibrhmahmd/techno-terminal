"""HR Module Constants

Domain constants and field definitions for the HR module.
"""
from typing import Final, FrozenSet, Literal, TypeAlias

# Employment types
EmploymentType: TypeAlias = Literal["full_time", "part_time", "contract"]
EMPLOYMENT_TYPES: list[EmploymentType] = ["full_time", "part_time", "contract"]
_EMPLOYMENT_TYPE_SET: Final[FrozenSet[str]] = frozenset(EMPLOYMENT_TYPES)


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

# Pagination defaults
EMPLOYEE_PAGE_SIZE: Final[int] = 20
MAX_PAGE_SIZE: Final[int] = 100

# Default values
DEFAULT_CONTRACT_PERCENTAGE: Final[float] = 25.0
