"""Typed rows of the integrity checks (one DTO per audit view) and the scenario summary."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict

Severity = Literal["ERROR", "WARNING", "INFO"]


class AuditScenarioDTO(BaseModel):
    """One integrity check with its current number of anomalies."""

    code: str
    label: str
    severity: Severity
    anomaly_count: int


class _Row(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ZeroChargeEnrollmentRowDTO(_Row):
    """A: active enrollment with no charge."""

    enrollment_id: int
    student_name: str | None
    student_phone: str | None
    group_name: str | None
    course_name: str | None
    level_number: int | None
    enrolled_at: date | None
    amount_due: Decimal | None
    discount_applied: Decimal | None
    notes: str | None
    created_at: datetime | None


class OverpaidEnrollmentRowDTO(_Row):
    """B: enrollment paid beyond its net due (credit balance)."""

    enrollment_id: int
    student_name: str | None
    phone: str | None
    group_name: str | None
    course_name: str | None
    level_number: int | None
    enrollment_status: str | None
    amount_due: Decimal | None
    discount_applied: Decimal | None
    net_due: Decimal | None
    total_paid: Decimal | None
    overpaid_by: Decimal | None


class OrphanedPaymentRowDTO(_Row):
    """C: payment not linked to an enrollment."""

    payment_id: int
    receipt_number: str | None
    student_name: str | None
    phone: str | None
    amount: Decimal | None
    transaction_type: str | None
    payment_type: str | None
    payment_notes: str | None
    paid_at: datetime | None
    payment_method: str | None
    created_at: datetime | None


class DuplicateEnrollmentRowDTO(_Row):
    """D: a student with more than one active enrollment in the same group."""

    student_id: int
    student_name: str | None
    phone: str | None
    group_id: int | None
    group_name: str | None
    course_name: str | None
    active_enrollment_count: int
    enrollment_ids: str | None
    first_enrolled: date | None
    last_enrolled: date | None
    total_amount_due_across_duplicates: Decimal | None


class DeadGroupEnrollmentRowDTO(_Row):
    """E: active enrollment on a group that is no longer active."""

    enrollment_id: int
    student_name: str | None
    phone: str | None
    group_id: int | None
    group_name: str | None
    group_status: str | None
    course_name: str | None
    level_number: int | None
    enrolled_at: date | None
    amount_due: Decimal | None
    discount_applied: Decimal | None
    notes: str | None


class UnrefundedExitRowDTO(_Row):
    """F: dropped or transferred enrollment that still holds collected money."""

    enrollment_id: int
    student_name: str | None
    phone: str | None
    group_name: str | None
    course_name: str | None
    level_number: int | None
    enrollment_status: str | None
    amount_due: Decimal | None
    discount_applied: Decimal | None
    net_collected: Decimal | None
    transferred_from: int | None
    notes: str | None


class LevelMismatchRowDTO(_Row):
    """G: enrollment level with no matching group_levels row."""

    enrollment_id: int
    student_name: str | None
    phone: str | None
    group_id: int | None
    group_name: str | None
    course_name: str | None
    enrollment_level: int | None
    enrollment_status: str | None
    amount_due: Decimal | None
    enrolled_at: date | None
    notes: str | None


class GhostPaymentRowDTO(_Row):
    """H: active payment that belongs to a soft-deleted student."""

    payment_id: int
    student_id: int | None
    deleted_student_name: str | None
    student_deleted_at: datetime | None
    amount: Decimal | None
    transaction_type: str | None
    enrollment_id: int | None
    receipt_number: str | None
    paid_at: datetime | None
    created_at: datetime | None


class OverdiscountedEnrollmentRowDTO(_Row):
    """I: discount of 100% or more."""

    enrollment_id: int
    student_name: str | None
    phone: str | None
    group_name: str | None
    course_name: str | None
    level_number: int | None
    enrollment_status: str | None
    amount_due: Decimal | None
    discount_applied: Decimal | None
    discount_pct: Decimal | None
    net_due: Decimal | None
    notes: str | None
    enrolled_at: date | None


AuditRowDTO = (
    ZeroChargeEnrollmentRowDTO
    | OverpaidEnrollmentRowDTO
    | OrphanedPaymentRowDTO
    | DuplicateEnrollmentRowDTO
    | DeadGroupEnrollmentRowDTO
    | UnrefundedExitRowDTO
    | LevelMismatchRowDTO
    | GhostPaymentRowDTO
    | OverdiscountedEnrollmentRowDTO
)

ROW_DTO_BY_VIEW: dict[str, type[_Row]] = {
    "v_audit_zero_charge_enrollments": ZeroChargeEnrollmentRowDTO,
    "v_audit_overpaid_enrollments": OverpaidEnrollmentRowDTO,
    "v_audit_orphaned_payments": OrphanedPaymentRowDTO,
    "v_audit_duplicate_enrollments": DuplicateEnrollmentRowDTO,
    "v_audit_dead_group_enrollments": DeadGroupEnrollmentRowDTO,
    "v_audit_unrefunded_exits": UnrefundedExitRowDTO,
    "v_audit_level_mismatch": LevelMismatchRowDTO,
    "v_audit_ghost_payments": GhostPaymentRowDTO,
    "v_audit_overdiscounted_enrollments": OverdiscountedEnrollmentRowDTO,
}


class AuditScenarioRowsResult(BaseModel):
    """One page of a check's anomalies."""

    code: str
    total: int
    rows: list[AuditRowDTO]
