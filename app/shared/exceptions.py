"""
app/shared/exceptions.py
────────────────────────
Typed exception hierarchy for the Techno Kids CRM.

All service-layer errors must raise one of these classes instead of the
built-in ValueError.  This lets the UI (and the future REST API layer)
handle each error condition differently:

    NotFoundError     → 404  (record does not exist)
    ValidationError   → 422  (input fails format / content rules)
    BusinessRuleError → 409  (valid input violates a domain rule)
    ConflictError     → 409  (uniqueness constraint would be violated)
    AuthError         → 401  (authentication / authorisation failure)

Usage in a service:
    from app.shared.exceptions import NotFoundError, BusinessRuleError

    def enroll_student(student_id: int, ...):
        student = repo.get_student_by_id(session, student_id)
        if not student:
            raise NotFoundError(f"Student {student_id} not found.")
        if not student.is_active:
            raise BusinessRuleError(f"Student '{student.full_name}' is inactive.")

Usage in the UI:
    from app.shared.exceptions import NotFoundError, BusinessRuleError, ValidationError

    try:
        enroll_srv.enroll_student(...)
    except NotFoundError as e:
        st.warning(f"⚠️ Not found: {e.message}")
    except BusinessRuleError as e:
        st.error(f"❌ Not allowed: {e.message}")
    except ValidationError as e:
        st.error(f"❌ Invalid input: {e.message}")
    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")
"""


class AppError(Exception):
    """
    Base class for all domain errors in this application.

    Carries a ``message`` that is safe to display to the user, and an
    optional ``detail`` field for extra technical context (logs only).
    """

    def __init__(self, message: str, detail: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail  # never shown to the user; for structured logs


class NotFoundError(AppError):
    """
    A required record was not found in the database.

    Raise when a lookup by ID (or other unique key) returns None and the
    calling code cannot continue without it.

    Examples:
        raise NotFoundError(f"Student {student_id} not found.")
        raise NotFoundError(f"Receipt {receipt_id} not found.")
    """


class ValidationError(AppError):
    """
    User input fails a format or content rule.

    Raise when the *shape* of an input is wrong, before any business logic
    is evaluated — e.g. a phone number that is too short, a price of zero,
    or a missing required field.

    Examples:
        raise ValidationError("Phone must contain at least 10 digits.")
        raise ValidationError("Amount must be greater than 0.")
    """


class BusinessRuleError(AppError):
    """
    A valid input violates a domain business rule.

    Raise when the input is well-formed but cannot be acted upon in the
    current application state — e.g. enrolling an inactive student,
    refunding an already-refunded receipt, or transferring a dropped
    enrollment.

    Examples:
        raise BusinessRuleError(f"Student '{name}' is not active.")
        raise BusinessRuleError("Can only transfer an active enrollment.")
    """


class ConflictError(AppError):
    """
    An operation would violate a uniqueness constraint.

    Raise when adding a record that already exists — e.g. registering a
    phone number that is already in use, or enrolling a student in a group
    they are already enrolled in.

    Examples:
        raise ConflictError(f"Phone {phone} is already registered.")
        raise ConflictError("Student is already enrolled in this group.")
    """


class AuthError(AppError):
    """
    An authentication or authorisation failure.

    Raise for wrong passwords, missing credentials, or insufficient
    permissions.

    Examples:
        raise AuthError("Current password is incorrect.")
        raise AuthError("User not found.")
    """
