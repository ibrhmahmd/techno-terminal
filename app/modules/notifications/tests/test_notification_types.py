"""NotificationType lists exactly the types the services resolve recipients for (#141)."""
import pathlib
import re
import typing

from app.modules.notifications.constants import NotificationType

_SERVICES = pathlib.Path(__file__).resolve().parents[1] / "services"
_CALL = re.compile(r'_resolve_notification_recipients\(\s*(?:notification_type=)?"([a-z_]+)"')


def test_notification_type_matches_the_services():
    used = {name for path in _SERVICES.rglob("*.py") for name in _CALL.findall(path.read_text())}

    assert used == set(typing.get_args(NotificationType))
