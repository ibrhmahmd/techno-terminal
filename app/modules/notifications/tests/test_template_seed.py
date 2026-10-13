"""Every template the code looks up by name exists in a schema-built DB (#156).

The task templates were missing from ``db/schema/90_seed_data.sql`` (and
migration 078 targeted a dropped ``code`` column), so lookups silently skipped
sending. This scans the notification services for literal template names.
"""
import pathlib
import re

from sqlmodel import select

from app.modules.notifications.models.notification_template import NotificationTemplate

_SERVICES = pathlib.Path(__file__).resolve().parents[1] / "services"
_LOOKUP = re.compile(r'get_template_by_name\("([a-z_]+)"\)')


def _names_used_in_code() -> set[str]:
    return {
        name
        for path in _SERVICES.rglob("*.py")
        for name in _LOOKUP.findall(path.read_text())
    }


def test_every_looked_up_template_is_seeded(db_session):
    used = _names_used_in_code()
    seeded = set(db_session.exec(select(NotificationTemplate.name)).all())

    assert {"task_assigned", "task_status_changed", "task_comment_added", "user_invite"} <= used
    assert used - seeded == set()
