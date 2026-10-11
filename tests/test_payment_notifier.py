"""PaymentNotifier port wiring and behaviour (ADR-0007, ticket #22)."""

from app.db.uow import unit_of_work
from app.modules.finance import CreateReceiptServiceDTO, PaymentNotifier, ReceiptLineInput, ReceiptService
from app.modules.finance.api.deps import get_payment_notifier as finance_deps_get_notifier
from app.modules.notifications.adapters import get_payment_notifier as adapters_get_notifier
from tests.characterization.test_finance_api import _seed_enrollment
from tests.utils.payment_notifier_fake import FakePaymentNotifier


def test_fake_satisfies_the_port():
    notifier: PaymentNotifier = FakePaymentNotifier()
    notifier.payment_received(receipt_id=1, student_id=2, amount="10", receipt_number="R-1")
    assert notifier.calls[0][0] == "payment_received"


def test_create_app_overrides_the_notifier_with_the_adapter():
    from app.api.main import create_app

    app = create_app()
    assert app.dependency_overrides[finance_deps_get_notifier] is adapters_get_notifier


def _create(notifier, student, enrollment):
    with unit_of_work() as uow:
        return ReceiptService(uow, notifier=notifier).create(
            CreateReceiptServiceDTO(
                lines=[ReceiptLineInput(student_id=student.id, enrollment_id=enrollment.id, amount=100.0)],
                payer_name="Parent",
                payment_method="cash",
                received_by_user_id=None,
                allow_credit=True,
            )
        )


def test_create_receipt_notifies_once_after_commit(db_session):
    _, _, student, enrollment = _seed_enrollment(db_session)
    fake = FakePaymentNotifier()

    result = _create(fake, student, enrollment)

    assert [c[0] for c in fake.calls] == ["payment_received"]
    kwargs = fake.calls[0][1]
    assert kwargs["receipt_id"] == result.receipt_id
    assert kwargs["student_id"] == student.id
    assert kwargs["amount"] == "100.0"


def test_notifier_failure_never_fails_the_receipt(db_session):
    _, _, student, enrollment = _seed_enrollment(db_session)

    result = _create(FakePaymentNotifier(should_raise=True), student, enrollment)

    assert result.receipt_id
