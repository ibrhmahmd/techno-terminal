"""
app/shared/validators.py
─────────────────────────
Cross-domain validators reusable across all modules and the future API layer.

Rules:
  - Each function validates a SINGLE concern and raises ValidationError on failure.
  - Functions return the cleaned/normalised value where applicable.
  - Module-specific rules (e.g. STEM time window, sessions count) stay in their module.
"""
import re
from app.shared.exceptions import ValidationError


def validate_phone(phone: str) -> str:
    """
    Strips all non-digit characters and checks minimum length (10 digits).
    Returns the cleaned phone string on success.

    Reusable for: parent primary phone, parent secondary phone,
                  student phone, future HR employee contact.
    """
    if not phone:
        raise ValidationError("Phone number is required.")
    cleaned = re.sub(r"\D", "", phone)
    if len(cleaned) < 10:
        raise ValidationError(
            f"Phone number '{phone}' looks invalid — must contain at least 10 digits."
        )
    return cleaned


def validate_positive_amount(value: float, field: str = "amount") -> None:
    """
    Raises ValidationError if value is <= 0.
    Use for any monetary amount: charge, refund, course price, fee.

    Example:
        validate_positive_amount(amount, field="charge amount")
        validate_positive_amount(new_price, field="price")
    """
    if value <= 0:
        raise ValidationError(f"{field.capitalize()} must be greater than 0.")


def validate_required_fields(data: dict, fields: list[str]) -> None:
    """
    Raises ValidationError for the first missing or blank required field.
    Pass the field names as they appear in the dict keys.

    Example:
        validate_required_fields(data, ["full_name", "phone_primary"])
    """
    for field in fields:
        if not data.get(field):
            raise ValidationError(
                f"'{field.replace('_', ' ').title()}' is required."
            )


def validate_non_empty_string(value: str, field: str = "value") -> str:
    """
    Raises ValidationError if value is empty or whitespace-only.
    Returns the stripped string on success.

    Example:
        name = validate_non_empty_string(name, field="competition name")
    """
    if not value or not value.strip():
        raise ValidationError(f"{field.capitalize()} cannot be empty.")
    return value.strip()
