"""Install no-op notifier providers so no test can dispatch real email/SMS/WhatsApp.

Characterization tests that exercise write endpoints use this instead of letting the real
adapters (which wrap the notification services) run.
"""

from contextlib import contextmanager


class Noop:
    """Any attribute / call chain is a no-op."""

    def __getattr__(self, name):
        return self

    def __call__(self, *args, **kwargs):
        return None


@contextmanager
def noop_notifiers(app):
    from app.modules.auth.api.deps import get_auth_notifier
    from app.modules.competitions.api.deps import get_competition_notifier
    from app.modules.enrollments.api.deps import get_enrollment_notifier
    from app.modules.finance.api.deps import get_payment_notifier
    from app.modules.tasks.api.deps import get_task_notifier

    providers = [
        get_auth_notifier,
        get_competition_notifier,
        get_enrollment_notifier,
        get_payment_notifier,
        get_task_notifier,
    ]
    saved = {p: app.dependency_overrides.get(p) for p in providers}
    stub = Noop()
    for p in providers:
        app.dependency_overrides[p] = lambda: stub
    try:
        yield stub
    finally:
        for p, original in saved.items():
            if original is None:
                app.dependency_overrides.pop(p, None)
            else:
                app.dependency_overrides[p] = original
