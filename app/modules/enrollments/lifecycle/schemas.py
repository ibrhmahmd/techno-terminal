from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel


class MigrateEnrollmentsDTO(BaseModel):
    group_id: int
    from_level: int
    to_level: int
    price_override: Optional[Decimal] = None
    preserve_discounts: bool = True


class EnrollmentMigrationResult(BaseModel):
    count: int
    old_level: int
    new_level: int
    migrated_enrollment_ids: List[int]
    new_enrollment_ids: List[int]
    total_amount_due: float = 0.0
