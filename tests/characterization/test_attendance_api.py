"""Characterization tests for the Attendance HTTP API (ticket #20).

Pins the status codes, envelopes and field shapes of the two endpoints under
``/api/v1/attendance`` served by ``app/api/routers/attendance_router.py`` BEFORE
the HTTP layer moves into ``app/modules/attendance/``:

    GET  /attendance/session/{session_id}
    POST /attendance/session/{session_id}/mark

Buckets
-------
* ``AttendanceService`` opens its own ``get_session()`` and the mark route really
  commits, so every test seeds committed, uuid-tagged rows through ``db_session``
  and reads results back through the API or ``db_session``. ``session_date`` is a
  real ``date`` (ISSUES #3 broke production on a DATE/datetime mismatch).
* Neither route schedules a notification.

Pinned quirks (pinned, not endorsed)
------------------------------------
* GET for an unknown session is a 200 with an empty ``data`` list, not a 404.
* POST with duplicate student ids in one request crashes with 500 (the 422 handler
  cannot serialise the validator's ValueError context).
* POST silently skips students without an active enrolment in the session's group
  AT the session's level (``skipped`` lists their ids); it never fails for them.

Run
---
GMAIL_SENDER_ADDRESS= GMAIL_APP_PASSWORD= TWILIO_ACCOUNT_SID= TWILIO_AUTH_TOKEN= SUPABASE_URL=http://127.0.0.1:9 /home/ibrahim/Desktop/techno-projects/techno-terminal/.venv/bin/python -m pytest tests/characterization/test_attendance_api.py -q -p no:cacheprovider
"""

from datetime import date

from sqlmodel import select

from app.modules.attendance.models.attendance_models import Attendance
from tests.characterization.test_academics_courses_sessions_api import _make_session
from tests.characterization.test_enrollments_reads_api import (
    _make_course,
    _make_enrollment,
    _make_group,
    _make_student,
)


def _seed(db_session, *, level_number: int = 1):
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    student = _make_student(db_session)
    enrollment = _make_enrollment(db_session, student.id, group.id, level_number=level_number)
    session = _make_session(
        db_session, group.id, level_number=level_number, session_number=1,
        session_date=date(2026, 6, 15),
    )
    return group, student, enrollment, session


def _mark(client, headers, session_id, entries):
    return client.post(
        f"/api/v1/attendance/session/{session_id}/mark",
        headers=headers,
        json={"entries": entries},
    )


# ── POST /attendance/session/{session_id}/mark ────────────────────────────────


def test_mark_attendance_happy_path(client_with_uow, override_auth, mock_admin_headers, db_session, uow):
    _, student, enrollment, session = _seed(db_session)

    r = _mark(client_with_uow, mock_admin_headers, session.id,
              [{"student_id": student.id, "status": "present"}])

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["data"] == {"marked": 1, "skipped": []}
    assert body["message"] == "Attendance marked: 1 records updated."

    # The use case commits through the injected UnitOfWork (a savepoint of the uow
    # fixture's transaction), so read the result through that same session.
    row = uow.session.exec(
        select(Attendance).where(Attendance.session_id == session.id)
    ).one()
    assert row.student_id == student.id
    assert row.enrollment_id == enrollment.id
    assert row.status == "present"


def test_mark_attendance_upserts_existing_row(client_with_uow, override_auth, mock_admin_headers, db_session, uow):
    _, student, _, session = _seed(db_session)

    _mark(client_with_uow, mock_admin_headers, session.id,
          [{"student_id": student.id, "status": "present"}])
    r = _mark(client_with_uow, mock_admin_headers, session.id,
              [{"student_id": student.id, "status": "absent"}])

    assert r.status_code == 200
    assert r.json()["data"] == {"marked": 1, "skipped": []}
    rows = uow.session.exec(
        select(Attendance).where(Attendance.session_id == session.id)
    ).all()
    assert len(rows) == 1
    uow.session.refresh(rows[0])
    assert rows[0].status == "absent"


def test_mark_attendance_skips_unenrolled_student(client_with_uow, override_auth, mock_admin_headers, db_session):
    """current behaviour (pinned, not endorsed): unenrolled students are skipped, not an error."""
    _, student, _, session = _seed(db_session)
    outsider = _make_student(db_session)

    r = _mark(client_with_uow, mock_admin_headers, session.id, [
        {"student_id": student.id, "status": "present"},
        {"student_id": outsider.id, "status": "present"},
    ])

    assert r.status_code == 200
    assert r.json()["data"] == {"marked": 1, "skipped": [outsider.id]}


def test_mark_attendance_skips_student_enrolled_at_other_level(
    client_with_uow, override_auth, mock_admin_headers, db_session
):
    """current behaviour (pinned, not endorsed): enrolment level must equal the session level."""
    group, student, _, _ = _seed(db_session, level_number=1)
    level2_session = _make_session(
        db_session, group.id, level_number=2, session_number=1, session_date=date(2026, 7, 1)
    )

    r = _mark(client_with_uow, mock_admin_headers, level2_session.id,
              [{"student_id": student.id, "status": "present"}])

    assert r.status_code == 200
    assert r.json()["data"] == {"marked": 0, "skipped": [student.id]}


def test_mark_attendance_unknown_session_is_404(client_with_uow, override_auth, mock_admin_headers):
    r = _mark(client_with_uow, mock_admin_headers, 999999999,
              [{"student_id": 1, "status": "present"}])

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFoundError"
    assert body["message"] == "Session ID 999999999 not found."


def test_mark_attendance_validation(client_with_uow, override_auth, mock_admin_headers):
    url = "/api/v1/attendance/session/1/mark"
    h = mock_admin_headers
    assert client_with_uow.post(url, headers=h, json={"entries": []}).status_code == 422
    assert client_with_uow.post(url, headers=h, json={}).status_code == 422
    assert client_with_uow.post(
        url, headers=h, json={"entries": [{"student_id": 1, "status": "late"}]}
    ).status_code == 422
    assert client_with_uow.post(
        url, headers=h, json={"entries": [{"student_id": 0, "status": "present"}]}
    ).status_code == 422


def test_mark_attendance_duplicate_student_ids_crash_with_500(app, client_with_uow, override_auth, mock_admin_headers):
    """current behaviour (pinned, not endorsed): the duplicate-id validator raises a
    ValueError whose context the 422 handler cannot JSON-serialise, so the response
    is a 500 instead of a 422 (see the bug issue linked from #20)."""
    from fastapi.testclient import TestClient

    client = TestClient(app, raise_server_exceptions=False)
    r = client.post(
        "/api/v1/attendance/session/1/mark",
        headers=mock_admin_headers,
        json={"entries": [
            {"student_id": 1, "status": "present"},
            {"student_id": 1, "status": "absent"},
        ]},
    )
    assert r.status_code == 500


# ── GET /attendance/session/{session_id} ──────────────────────────────────────


def test_get_session_attendance_lists_marked_rows(client_with_uow, override_auth, mock_admin_headers, db_session):
    _, student, _, session = _seed(db_session)
    _mark(client_with_uow, mock_admin_headers, session.id,
          [{"student_id": student.id, "status": "present"}])

    r = client_with_uow.get(f"/api/v1/attendance/session/{session.id}", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["data"] == [{"student_id": student.id, "status": "present"}]


def test_get_session_attendance_empty_when_nothing_marked(
    client_with_uow, override_auth, mock_admin_headers, db_session
):
    """current behaviour (pinned, not endorsed): the 'roster' is only rows already marked."""
    _, _, _, session = _seed(db_session)

    r = client_with_uow.get(f"/api/v1/attendance/session/{session.id}", headers=mock_admin_headers)

    assert r.status_code == 200
    assert r.json()["data"] == []


def test_get_session_attendance_unknown_session_is_200_empty(client_with_uow, override_auth, mock_admin_headers):
    """current behaviour (pinned, not endorsed): unknown session returns 200 with an empty list."""
    r = client_with_uow.get("/api/v1/attendance/session/999999999", headers=mock_admin_headers)

    assert r.status_code == 200
    assert r.json()["data"] == []


def test_get_session_attendance_bad_id_is_422(client_with_uow, override_auth, mock_admin_headers):
    r = client_with_uow.get("/api/v1/attendance/session/abc", headers=mock_admin_headers)
    assert r.status_code == 422


# ── Auth ──────────────────────────────────────────────────────────────────────


def test_attendance_endpoints_require_auth(client):
    assert client.get("/api/v1/attendance/session/1").status_code == 401
    assert client.post(
        "/api/v1/attendance/session/1/mark",
        json={"entries": [{"student_id": 1, "status": "present"}]},
    ).status_code == 401
