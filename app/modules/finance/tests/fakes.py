"""Test fake for the PaymentNotifier port."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FakePaymentNotifier:
    """Records every call as (method_name, kwargs) for test assertions."""

    calls: list[tuple[str, dict]] = field(default_factory=list)
    should_raise: bool = False
    raise_exception: Optional[Exception] = None

    def _record(self, name: str, **kwargs) -> None:
        if self.should_raise:
            raise self.raise_exception or RuntimeError("Notifier failure")
        self.calls.append((name, kwargs))

    def payment_received(self, **kwargs) -> None:
        self._record("payment_received", **kwargs)

    def competition_fee_paid(self, **kwargs) -> None:
        self._record("competition_fee_paid", **kwargs)

    def reset(self) -> None:
        self.calls.clear()
